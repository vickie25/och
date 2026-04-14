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

            # Calculate adjustment details
            previous_count = contract.student_seat_count
            adjustment_amount = new_seat_count - previous_count
            adjustment_type = 'increase' if adjustment_amount > 0 else 'decrease'

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
                    adjustment_amount=adjustment_amount,
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
                # Calculate billing amounts
                base_amount = InstitutionalBillingService._calculate_base_amount(
                    contract, schedule.billing_period_start, schedule.billing_period_end
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
                    active_seat_count=contract.student_seat_count,
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
        if contract.billing_cycle == 'monthly':
            return contract.monthly_amount
        elif contract.billing_cycle == 'quarterly':
            return contract.monthly_amount * 3
        else:  # annual
            return contract.annual_amount

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
            proposed_seats = new_seat_count or contract.student_seat_count
            proposed_cycle = new_billing_cycle or contract.billing_cycle

            # Calculate new pricing
            if proposed_seats <= 50:
                new_rate = Decimal('15.00')
            elif proposed_seats <= 200:
                new_rate = Decimal('12.00')
            elif proposed_seats <= 500:
                new_rate = Decimal('9.00')
            else:
                new_rate = Decimal('7.00')

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
