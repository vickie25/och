"""
Institutional Billing Service - Automated billing engine for educational institutions.
Handles contract management, seat adjustments, and invoice generation.
"""
import logging
from datetime import date, timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

from users.models import User

from .institutional_models import (
    InstitutionalBilling,
    InstitutionalBillingSchedule,
    InstitutionalContract,
    InstitutionalSeatAdjustment,
    InstitutionalStudent,
)

logger = logging.getLogger(__name__)


class InstitutionalBillingService:
    """Service class for institutional billing operations"""

    @staticmethod
    def create_contract(organization, seat_count, billing_cycle='monthly',
                       billing_contact_name='', billing_contact_email='',
                       start_date=None, created_by=None, **kwargs):
        """
        Create a new institutional contract with 12-month minimum term.

        Args:
            organization: Organization instance
            seat_count: Number of student seats
            billing_cycle: 'monthly', 'quarterly', or 'annual'
            billing_contact_name: Primary billing contact
            billing_contact_email: Billing contact email
            start_date: Contract start date (defaults to today)
            created_by: User who created the contract
            **kwargs: Additional contract fields

        Returns:
            InstitutionalContract instance
        """
        if not start_date:
            start_date = date.today()

        # Minimum 12-month term
        end_date = start_date + relativedelta(years=1)

        with transaction.atomic():
            contract = InstitutionalContract.objects.create(
                organization=organization,
                start_date=start_date,
                end_date=end_date,
                student_seat_count=seat_count,
                billing_cycle=billing_cycle,
                billing_contact_name=billing_contact_name,
                billing_contact_email=billing_contact_email,
                created_by=created_by,
                status='draft',
                **kwargs
            )

            # Generate billing schedule
            InstitutionalBillingSchedule.generate_schedule_for_contract(contract)

            logger.info(f"Created institutional contract {contract.contract_number} for {organization.name}")
            return contract

    @staticmethod
    def realign_contract_to_academic_calendar(contract_id):
        """
        If a contract has an academic calendar with billing_aligned_to_calendar enabled,
        align contract start/end to the next academic-year start and regenerate billing schedules
        based on calendar periods.
        """
        from .institutional_management_models import InstitutionalAcademicCalendar

        contract = InstitutionalContract.objects.get(id=contract_id)
        cal = InstitutionalAcademicCalendar.objects.filter(contract=contract).first()
        if not cal or not cal.billing_aligned_to_calendar:
            return {'aligned': False, 'reason': 'No academic calendar alignment enabled'}

        today = date.today()
        # Pick the next period start >= today; fallback to academic_year_start in next year.
        period_starts = []
        for p in cal.periods or []:
            try:
                period_starts.append(date.fromisoformat(p['start']))
            except Exception:
                continue
        period_starts = sorted({d for d in period_starts if d})
        new_start = next((d for d in period_starts if d >= today), None)
        if new_start is None:
            # derive next year academic start from current academic_year_start month/day
            ys = cal.academic_year_start
            new_start = date(today.year + 1, ys.month, ys.day)

        new_end = new_start + relativedelta(years=1) - timedelta(days=1)

        with transaction.atomic():
            # Clear existing unprocessed schedules and recreate.
            contract.billing_schedules.filter(is_processed=False).delete()
            contract.start_date = new_start
            contract.end_date = new_end
            contract.save(update_fields=['start_date', 'end_date', 'updated_at'])
            InstitutionalBillingSchedule.generate_schedule_for_contract(contract)

        return {'aligned': True, 'start_date': new_start.isoformat(), 'end_date': new_end.isoformat()}

    @staticmethod
    def activate_contract(contract_id, signed_by=None):
        """
        Activate a contract and start billing.

        Args:
            contract_id: Contract UUID
            signed_by: User who signed the contract

        Returns:
            Updated contract instance
        """
        try:
            contract = InstitutionalContract.objects.get(id=contract_id)

            if contract.status != 'draft':
                raise ValueError(f"Contract {contract.contract_number} is not in draft status")

            with transaction.atomic():
                contract.status = 'active'
                contract.signed_by = signed_by
                contract.signed_at = timezone.now()
                contract.save()

                # Generate first invoice if billing date has passed
                today = date.today()
                first_schedule = contract.billing_schedules.filter(
                    is_processed=False,
                    next_billing_date__lte=today
                ).first()

                if first_schedule:
                    InstitutionalBillingService.process_scheduled_billing(first_schedule.id)

                logger.info(f"Activated contract {contract.contract_number}")
                return contract

        except InstitutionalContract.DoesNotExist:
            raise ValueError(f"Contract {contract_id} not found")

    @staticmethod
    def adjust_seat_count(contract_id, new_seat_count, effective_date=None,
                         reason='', created_by=None):
        """
        Adjust seat count with proration calculation.

        Args:
            contract_id: Contract UUID
            new_seat_count: New number of seats
            effective_date: When adjustment takes effect (defaults to today)
            reason: Reason for adjustment
            created_by: User making the adjustment

        Returns:
            InstitutionalSeatAdjustment instance
        """
        if not effective_date:
            effective_date = date.today()

        try:
            contract = InstitutionalContract.objects.get(id=contract_id)

            if contract.status != 'active':
                raise ValueError(f"Contract {contract.contract_number} is not active")

            if new_seat_count == contract.student_seat_count:
                raise ValueError("New seat count is the same as current count")

            previous_count = contract.student_seat_count
            delta = new_seat_count - previous_count
            adjustment_type = 'increase' if delta > 0 else 'decrease'

            # Seat reductions: schedule for next renewal only (no mid-contract refunds).
            if adjustment_type == 'decrease':
                old_terms = {
                    'student_seat_count': previous_count,
                    'pending_renewal_seat_count': contract.pending_renewal_seat_count,
                }
                contract.pending_renewal_seat_count = new_seat_count
                contract.save(update_fields=['pending_renewal_seat_count', 'updated_at'])
                try:
                    from .institutional_models import InstitutionalContractAmendment

                    InstitutionalContractAmendment.objects.create(
                        contract=contract,
                        amendment_type='seat_reduction_scheduled',
                        requested_by=created_by,
                        previous_terms=old_terms,
                        new_terms={'pending_renewal_seat_count': new_seat_count},
                        notes=reason or '',
                    )
                except Exception:
                    pass

                return {
                    'scheduled': True,
                    'effective_at_renewal': True,
                    'previous_seat_count': previous_count,
                    'pending_renewal_seat_count': new_seat_count,
                }

            # Find current billing period
            current_schedule = contract.billing_schedules.filter(
                billing_period_start__lte=effective_date,
                billing_period_end__gte=effective_date,
                is_processed=False
            ).first()

            if not current_schedule:
                raise ValueError("No active billing period found for adjustment date")

            # Calculate proration
            total_days = (current_schedule.billing_period_end - current_schedule.billing_period_start).days + 1
            remaining_days = (current_schedule.billing_period_end - effective_date).days + 1

            with transaction.atomic():
                # Create adjustment record
                adjustment = InstitutionalSeatAdjustment.objects.create(
                    contract=contract,
                    adjustment_type=adjustment_type,
                    previous_seat_count=previous_count,
                    new_seat_count=new_seat_count,
                    adjustment_amount=delta,
                    effective_date=effective_date,
                    days_in_billing_period=total_days,
                    days_remaining=remaining_days,
                    reason=reason,
                    created_by=created_by
                )

                # Update contract seat count
                contract.student_seat_count = new_seat_count
                # Recalculate per-student rate based on new volume
                contract.per_student_rate = contract.calculate_per_student_rate()
                contract.save()

                # Audit amendment
                try:
                    from .institutional_models import InstitutionalContractAmendment

                    InstitutionalContractAmendment.objects.create(
                        contract=contract,
                        amendment_type='seat_increase',
                        requested_by=created_by,
                        previous_terms={'student_seat_count': previous_count},
                        new_terms={'student_seat_count': new_seat_count, 'per_student_rate': float(contract.per_student_rate)},
                        notes=reason or '',
                    )
                except Exception:
                    pass

                logger.info(f"Adjusted seats for {contract.contract_number}: {previous_count} -> {new_seat_count}")
                return adjustment

        except InstitutionalContract.DoesNotExist:
            raise ValueError(f"Contract {contract_id} not found")

    @staticmethod
    def process_scheduled_billing(schedule_id):
        """
        Process a scheduled billing and generate invoice.

        Args:
            schedule_id: InstitutionalBillingSchedule UUID

        Returns:
            InstitutionalBilling instance
        """
        try:
            schedule = InstitutionalBillingSchedule.objects.get(id=schedule_id)

            if schedule.is_processed:
                raise ValueError(f"Schedule {schedule_id} already processed")

            contract = schedule.contract

            if contract.status != 'active':
                raise ValueError(f"Contract {contract.contract_number} is not active")

            with transaction.atomic():
                # Bill based on active enrolled students, capped by licensed seats.
                enrolled_active = contract.enrolled_students.filter(is_active=True).count()
                licensed = int(contract.student_seat_count or 0)
                billable_seats = min(enrolled_active, licensed) if licensed > 0 else enrolled_active

                # Calculate billing amounts
                base_amount = InstitutionalBillingService._calculate_base_amount(
                    contract, schedule.billing_period_start, schedule.billing_period_end, billable_seats
                )

                # Get seat adjustments for this period
                adjustments = contract.seat_adjustments.filter(
                    effective_date__gte=schedule.billing_period_start,
                    effective_date__lte=schedule.billing_period_end
                )

                adjustment_amount = sum(adj.prorated_amount for adj in adjustments)

                # Calculate discounts
                discount_amount = Decimal('0.00')
                if contract.custom_discount > 0:
                    discount_amount = base_amount * (contract.custom_discount / 100)

                if (contract.billing_cycle == 'annual' and
                    contract.annual_payment_discount > 0):
                    annual_discount = base_amount * (contract.annual_payment_discount / 100)
                    discount_amount += annual_discount

                # Create invoice
                invoice = InstitutionalBilling.objects.create(
                    contract=contract,
                    billing_period_start=schedule.billing_period_start,
                    billing_period_end=schedule.billing_period_end,
                    billing_cycle=contract.billing_cycle,
                    base_seat_count=contract.student_seat_count,
                    active_seat_count=billable_seats,
                    base_amount=base_amount,
                    adjustment_amount=adjustment_amount,
                    discount_amount=discount_amount,
                    status='pending'
                )

                # Generate line items
                invoice.generate_line_items()
                invoice.save()

                # Mark schedule as processed
                schedule.is_processed = True
                schedule.processed_at = timezone.now()
                schedule.invoice = invoice
                schedule.save()

                logger.info(f"Generated invoice {invoice.invoice_number} for contract {contract.contract_number}")
                return invoice

        except InstitutionalBillingSchedule.DoesNotExist:
            raise ValueError(f"Schedule {schedule_id} not found")
        except Exception as e:
            # Update schedule with error
            schedule.processing_attempts += 1
            schedule.last_error = str(e)
            schedule.save()
            logger.error(f"Failed to process schedule {schedule_id}: {str(e)}")
            raise

    @staticmethod
    def _calculate_base_amount(contract, period_start, period_end):
        """Calculate base billing amount for a period"""
        raise NotImplementedError("Use _calculate_base_amount(contract, start, end, billable_seats)")

    @staticmethod
    def _calculate_base_amount(contract, period_start, period_end, billable_seats: int):
        """
        Calculate base billing amount for a period based on billable active seats.
        Uses daily proration from monthly per-student rate (30-day month) so partial periods are handled.
        """
        days = (period_end - period_start).days + 1
        if days <= 0 or billable_seats <= 0:
            return Decimal('0.00')

        daily_per_student = (contract.per_student_rate / Decimal('30')).quantize(Decimal('0.0001'))

        # Academic calendar summer accommodations (reduced rate or pause), if configured.
        try:
            cal = getattr(contract, 'academic_calendar', None)
        except Exception:
            cal = None

        if cal and getattr(cal, 'billing_aligned_to_calendar', False) and getattr(cal, 'summer_program_enabled', False):
            mode = getattr(cal, 'summer_billing_mode', 'full_rate') or 'full_rate'
            discount_rate = Decimal(str(getattr(cal, 'summer_discount_rate', 0) or 0))

            amount_days = Decimal('0.00')
            for i in range(days):
                d = period_start + timedelta(days=i)
                # Pause billing in June-August inclusive (per earlier confirmed policy).
                if mode == 'pause' and d.month in (6, 7, 8):
                    continue
                day_multiplier = Decimal('1.00')
                # Reduced rate in July-August inclusive (per earlier confirmed policy).
                if mode == 'reduced_rate' and d.month in (7, 8) and discount_rate > 0:
                    day_multiplier = (Decimal('100.00') - discount_rate) / Decimal('100.00')
                    if day_multiplier < 0:
                        day_multiplier = Decimal('0.00')
                amount_days += day_multiplier

            amount = (Decimal(billable_seats) * daily_per_student * amount_days).quantize(Decimal('0.01'))
            return amount

        amount = (Decimal(billable_seats) * daily_per_student * Decimal(days)).quantize(Decimal('0.01'))
        return amount

    @staticmethod
    def send_invoice_email(invoice_id):
        """
        Send invoice email to billing contact.

        Args:
            invoice_id: InstitutionalBilling UUID

        Returns:
            Boolean indicating success
        """
        try:
            invoice = InstitutionalBilling.objects.select_related(
                'contract__organization'
            ).get(id=invoice_id)

            contract = invoice.contract
            organization = contract.organization

            # Prepare email context
            context = {
                'invoice': invoice,
                'contract': contract,
                'organization': organization,
                'line_items': invoice.line_items,
                'payment_url': f"{settings.FRONTEND_URL}/institutional/payment/{invoice.id}",
                'portal_url': f"{settings.FRONTEND_URL}/institutional/portal/{contract.id}"
            }

            # Render email template
            subject = f"Invoice {invoice.invoice_number} - {organization.name}"
            html_content = render_to_string('organizations/emails/institutional_invoice.html', context)
            text_content = render_to_string('organizations/emails/institutional_invoice.txt', context)

            # Send email
            send_mail(
                subject=subject,
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[contract.billing_contact_email],
                html_message=html_content,
                fail_silently=False
            )

            # Mark as sent
            invoice.send_invoice()

            logger.info(f"Sent invoice email {invoice.invoice_number} to {contract.billing_contact_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send invoice email {invoice_id}: {str(e)}")
            return False

    @staticmethod
    def enroll_student(contract_id, user_id, enrollment_type='director_enrolled', created_by=None):
        """
        Enroll a student under an institutional contract.

        Args:
            contract_id: InstitutionalContract UUID
            user_id: User ID to enroll
            enrollment_type: Type of enrollment
            created_by: User who created the enrollment

        Returns:
            InstitutionalStudent instance
        """
        try:
            contract = InstitutionalContract.objects.get(id=contract_id)
            user = User.objects.get(id=user_id)

            if contract.status != 'active':
                raise ValueError(f"Contract {contract.contract_number} is not active")

            # Check seat availability
            active_students = contract.enrolled_students.filter(is_active=True).count()
            if active_students >= contract.student_seat_count:
                raise ValueError(f"Contract {contract.contract_number} has no available seats")

            # Create or reactivate enrollment
            enrollment, created = InstitutionalStudent.objects.get_or_create(
                contract=contract,
                user=user,
                defaults={
                    'enrollment_type': enrollment_type,
                    'created_by': created_by,
                    'is_active': True
                }
            )

            if not created and not enrollment.is_active:
                enrollment.reactivate()

            logger.info(f"Enrolled student {user.email} in contract {contract.contract_number}")
            return enrollment

        except (InstitutionalContract.DoesNotExist, User.DoesNotExist) as e:
            raise ValueError(str(e))

    @staticmethod
    def auto_enroll_user_by_domain(user):
        """
        Domain-based auto-enrollment for institutions with active SSO configs.
        Runs on first login (or any login) and is idempotent.
        """
        try:
            email = (getattr(user, 'email', '') or '').strip().lower()
            if not email or '@' not in email:
                return None
            domain = email.split('@', 1)[1]

            from .institutional_management_models import InstitutionalSSO

            cfgs = InstitutionalSSO.objects.select_related('contract').filter(
                status='active',
                auto_enrollment_enabled=True,
            )
            match = None
            for cfg in cfgs:
                domains = [d.lower().strip() for d in (cfg.auto_enrollment_domains or []) if d]
                if domain in domains:
                    if cfg.contract and cfg.contract.status == 'active':
                        match = cfg
                        break

            if not match:
                return None

            # Ensure org membership exists
            try:
                from organizations.models import OrganizationMember

                OrganizationMember.objects.get_or_create(
                    organization=match.contract.organization,
                    user=user,
                    defaults={'role': 'member'},
                )
            except Exception:
                pass

            # Enroll user under contract (seat availability enforced)
            enrollment = InstitutionalBillingService.enroll_student(
                contract_id=match.contract.id,
                user_id=user.id,
                enrollment_type='domain_auto_enrolled',
                created_by=None,
            )
            return enrollment
        except Exception:
            return None

    @staticmethod
    def process_overdue_invoices():
        """
        Process overdue invoices and send reminders.

        Returns:
            Dictionary with processing results
        """
        overdue_invoices = InstitutionalBilling.objects.filter(
            status='sent',
            due_date__lt=date.today()
        )

        results = {
            'processed': 0,
            'reminders_sent': 0,
            'errors': []
        }

        for invoice in overdue_invoices:
            try:
                # Update status to overdue
                invoice.status = 'overdue'
                invoice.save()
                results['processed'] += 1

                # Send reminder email (implement based on days overdue)
                if invoice.days_overdue in [7, 14, 30]:
                    if InstitutionalBillingService._send_overdue_reminder(invoice):
                        results['reminders_sent'] += 1

            except Exception as e:
                results['errors'].append(f"Invoice {invoice.invoice_number}: {str(e)}")
                logger.error(f"Error processing overdue invoice {invoice.invoice_number}: {str(e)}")

        return results

    @staticmethod
    def _send_overdue_reminder(invoice):
        """Send overdue payment reminder"""
        try:
            context = {
                'invoice': invoice,
                'contract': invoice.contract,
                'organization': invoice.contract.organization,
                'days_overdue': invoice.days_overdue,
                'payment_url': f"{settings.FRONTEND_URL}/institutional/payment/{invoice.id}"
            }

            subject = f"OVERDUE: Invoice {invoice.invoice_number} - {invoice.days_overdue} days past due"
            html_content = render_to_string('organizations/emails/overdue_reminder.html', context)

            send_mail(
                subject=subject,
                message=f"Invoice {invoice.invoice_number} is {invoice.days_overdue} days overdue. Please remit payment immediately.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[invoice.contract.billing_contact_email],
                html_message=html_content,
                fail_silently=False
            )

            return True

        except Exception as e:
            logger.error(f"Failed to send overdue reminder for {invoice.invoice_number}: {str(e)}")
            return False

    @staticmethod
    def generate_contract_renewal_quote(contract_id, new_seat_count=None, new_billing_cycle=None):
        """
        Generate renewal quote for expiring contract.

        Args:
            contract_id: Contract UUID
            new_seat_count: Proposed new seat count
            new_billing_cycle: Proposed new billing cycle

        Returns:
            Dictionary with renewal quote details
        """
        try:
            contract = InstitutionalContract.objects.get(id=contract_id)

            if not contract.is_renewable:
                raise ValueError(f"Contract {contract.contract_number} is not eligible for renewal")

            # Use current values if not specified
            proposed_seats = (
                contract.pending_renewal_seat_count
                or new_seat_count
                or contract.student_seat_count
            )
            proposed_cycle = (
                contract.pending_renewal_billing_cycle
                or new_billing_cycle
                or contract.billing_cycle
            )

            # Calculate new pricing
            if proposed_seats <= 50:
                new_rate = Decimal('15.00')
            elif proposed_seats <= 200:
                new_rate = Decimal('12.00')
            elif proposed_seats <= 500:
                new_rate = Decimal('9.00')
            else:
                new_rate = Decimal('7.00')

            # Apply market adjustment 0-5% (configurable) at renewal time.
            try:
                adj = Decimal(str(getattr(settings, 'INSTITUTION_RENEWAL_ADJUSTMENT_PERCENT', '0')))
            except Exception:
                adj = Decimal('0')
            if adj < 0:
                adj = Decimal('0')
            if adj > 5:
                adj = Decimal('5')
            new_rate = (new_rate * (Decimal('1') + (adj / Decimal('100')))).quantize(Decimal('0.01'))

            monthly_amount = proposed_seats * new_rate
            annual_amount = monthly_amount * 12

            # Apply annual discount if applicable
            if proposed_cycle == 'annual' and contract.annual_payment_discount > 0:
                annual_discount = annual_amount * (contract.annual_payment_discount / 100)
                annual_amount -= annual_discount

            quote = {
                'contract_number': contract.contract_number,
                'organization': contract.organization.name,
                'current_seats': contract.student_seat_count,
                'current_rate': float(contract.per_student_rate),
                'current_monthly': float(contract.monthly_amount),
                'current_annual': float(contract.annual_amount),
                'proposed_seats': proposed_seats,
                'proposed_rate': float(new_rate),
                'market_adjustment_percent': float(adj),
                'proposed_monthly': float(monthly_amount),
                'proposed_annual': float(annual_amount),
                'proposed_cycle': proposed_cycle,
                'renewal_start_date': contract.end_date + timedelta(days=1),
                'renewal_end_date': contract.end_date + relativedelta(years=1),
                'savings_vs_current': float(contract.annual_amount - annual_amount) if proposed_cycle == 'annual' else 0,
                'generated_at': timezone.now().isoformat()
            }

            return quote

        except InstitutionalContract.DoesNotExist:
            raise ValueError(f"Contract {contract_id} not found")

    @staticmethod
    def request_early_termination(contract_id, notice_date=None, requested_termination_date=None, requested_by=None):
        """
        Record an early termination notice (requires 60 days notice).
        Optionally specify a requested termination effective date (must be >= notice_date + 60 days).
        """
        from datetime import date as date_cls

        if notice_date is None:
            notice_date = date_cls.today()
        if isinstance(notice_date, str):
            notice_date = date_cls.fromisoformat(notice_date)

        term_date = None
        if requested_termination_date:
            if isinstance(requested_termination_date, str):
                term_date = date_cls.fromisoformat(requested_termination_date)
            else:
                term_date = requested_termination_date

        contract = InstitutionalContract.objects.get(id=contract_id)
        if contract.status != 'active':
            raise ValueError("Contract must be active to request termination")

        min_effective = notice_date + timedelta(days=60)
        if term_date and term_date < min_effective:
            raise ValueError("Termination effective date must be at least 60 days after notice")

        contract.early_termination_notice_date = notice_date
        contract.save(update_fields=['early_termination_notice_date', 'updated_at'])

        return {
            'contract_id': str(contract.id),
            'contract_number': contract.contract_number,
            'notice_date': notice_date.isoformat(),
            'earliest_termination_date': min_effective.isoformat(),
            'requested_termination_date': term_date.isoformat() if term_date else None,
        }

    @staticmethod
    def terminate_contract_early(contract_id, termination_date=None, payment_method=None, payment_reference=None):
        """
        Terminate a contract before end_date.
        Requires early_termination_notice_date and at least 60 days elapsed since notice.
        Generates a final net-30 invoice for service through termination_date.
        """
        from datetime import date as date_cls

        if termination_date is None:
            termination_date = date_cls.today() + timedelta(days=60)
        if isinstance(termination_date, str):
            termination_date = date_cls.fromisoformat(termination_date)

        contract = InstitutionalContract.objects.get(id=contract_id)
        if contract.status != 'active':
            raise ValueError("Contract is not active")
        if not contract.early_termination_notice_date:
            raise ValueError("Early termination notice is required")
        notice_ok = (date_cls.today() - contract.early_termination_notice_date).days >= 60
        if not notice_ok:
            raise ValueError("60-day notice period has not elapsed")
        if termination_date > contract.end_date:
            termination_date = contract.end_date

        today = date_cls.today()
        if termination_date <= today:
            raise ValueError("Termination date must be in the future")

        # Prorate remaining service from today until termination date (daily proration).
        # We use a 30-day month for simplicity and consistency across billing cycles.
        daily_amount = (contract.monthly_amount / Decimal('30')).quantize(Decimal('0.01'))
        days = (termination_date - today).days
        final_amount = (daily_amount * Decimal(days)).quantize(Decimal('0.01'))

        with transaction.atomic():
            invoice = InstitutionalBilling.objects.create(
                contract=contract,
                billing_period_start=today,
                billing_period_end=termination_date,
                billing_cycle='monthly',
                base_seat_count=contract.student_seat_count,
                active_seat_count=contract.student_seat_count,
                base_amount=final_amount,
                adjustment_amount=Decimal('0.00'),
                discount_amount=Decimal('0.00'),
                tax_amount=Decimal('0.00'),
                total_amount=final_amount,
                status='sent',
                invoice_date=today,
                due_date=today + timedelta(days=30),
                payment_method=payment_method or '',
                payment_reference=payment_reference or '',
                seat_adjustments=[],
            )
            invoice.generate_line_items()
            invoice.save(update_fields=['line_items', 'updated_at'])

            # Mark contract terminated and shorten end_date to termination_date.
            contract.status = 'terminated'
            contract.end_date = termination_date
            contract.save(update_fields=['status', 'end_date', 'updated_at'])

        return {
            'contract_number': contract.contract_number,
            'termination_date': termination_date.isoformat(),
            'final_invoice_number': invoice.invoice_number,
            'final_invoice_total': float(invoice.total_amount),
        }

    @staticmethod
    def get_contract_analytics(contract_id):
        """
        Get analytics for a specific contract.

        Args:
            contract_id: Contract UUID

        Returns:
            Dictionary with contract analytics
        """
        try:
            contract = InstitutionalContract.objects.get(id=contract_id)

            # Get billing history
            invoices = contract.billing_records.all()
            total_invoiced = sum(inv.total_amount for inv in invoices)
            total_paid = sum(inv.total_amount for inv in invoices if inv.status == 'paid')
            overdue_amount = sum(inv.total_amount for inv in invoices if inv.is_overdue)

            # Get student enrollment stats
            students = contract.enrolled_students.all()
            active_students = students.filter(is_active=True).count()
            total_enrolled = students.count()

            # Calculate utilization
            seat_utilization = (active_students / contract.student_seat_count * 100) if contract.student_seat_count > 0 else 0

            analytics = {
                'contract_info': {
                    'contract_number': contract.contract_number,
                    'organization': contract.organization.name,
                    'status': contract.status,
                    'start_date': contract.start_date.isoformat(),
                    'end_date': contract.end_date.isoformat(),
                    'days_remaining': contract.days_until_expiry
                },
                'financial': {
                    'total_invoiced': float(total_invoiced),
                    'total_paid': float(total_paid),
                    'outstanding_amount': float(total_invoiced - total_paid),
                    'overdue_amount': float(overdue_amount),
                    'monthly_recurring_revenue': float(contract.monthly_amount),
                    'annual_contract_value': float(contract.annual_amount)
                },
                'students': {
                    'licensed_seats': contract.student_seat_count,
                    'active_students': active_students,
                    'total_enrolled': total_enrolled,
                    'seat_utilization': round(seat_utilization, 2),
                    'available_seats': contract.student_seat_count - active_students
                },
                'billing': {
                    'billing_cycle': contract.billing_cycle,
                    'per_student_rate': float(contract.per_student_rate),
                    'total_invoices': invoices.count(),
                    'paid_invoices': invoices.filter(status='paid').count(),
                    'overdue_invoices': invoices.filter(status='overdue').count()
                }
            }

            return analytics

        except InstitutionalContract.DoesNotExist:
            raise ValueError(f"Contract {contract_id} not found")
