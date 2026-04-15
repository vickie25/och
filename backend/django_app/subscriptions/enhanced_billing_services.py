"""
Enhanced Billing Services - Academic Discounts and Promotional Pricing
"""
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .billing_engine import EnhancedSubscription
from .promotional_models import (
    AcademicDiscount,
    EnhancedTrialConfiguration,
    GracePeriodTracking,
    PromotionalCode,
    PromotionalCodeRedemption,
)
from django.db.models import Avg, Count, Sum


class AcademicDiscountService:
    """Service for managing academic discounts."""

    @staticmethod
    def _academic_domain_allowed(domain: str) -> bool:
        try:
            allowed = getattr(settings, 'ACADEMIC_ALLOWED_DOMAINS', None)
            if allowed:
                allowed_set = {str(d).strip().lower() for d in allowed if str(d).strip()}
                return domain.strip().lower() in allowed_set
        except Exception:
            pass
        return True

    @staticmethod
    def _is_plan_eligible_for_academic_discount(plan_id: str | None, billing_cycle: str) -> bool:
        """
        Academic discount applies only to:
          - Pro (plan_id == "pro") monthly + annual
          - Premium (plan_id == "premium") monthly only
        """
        pid = (plan_id or '').strip().lower()
        cycle = (billing_cycle or 'monthly').strip().lower()
        if pid == 'pro' and cycle in ['monthly', 'annual']:
            return True
        if pid == 'premium' and cycle == 'monthly':
            return True
        return False

    @staticmethod
    def verify_edu_email(user, edu_email):
        """Verify educational email and create discount."""
        try:
            # Auto-verify .edu domains
            domain = (edu_email.split('@')[1] if '@' in (edu_email or '') else '').strip().lower()
            if edu_email.endswith('.edu') and domain and AcademicDiscountService._academic_domain_allowed(domain):
                discount = AcademicDiscount.auto_verify_edu_email(user, edu_email)
                if discount:
                    AcademicDiscountService._send_verification_email(discount)
                    return discount, "Educational email verified successfully!"

            # For non-.edu emails, create pending verification
            discount, created = AcademicDiscount.objects.get_or_create(
                user=user,
                defaults={
                    'verification_method': 'manual_upload',
                    'student_email': edu_email,
                    'status': 'pending'
                }
            )

            if created:
                return discount, "Please upload verification documents to complete the process."
            else:
                return discount, "Academic discount application already exists."

        except Exception as e:
            raise ValidationError(f"Failed to verify educational email: {str(e)}")

    @staticmethod
    def upload_verification_document(user, document, document_type, institution_name):
        """Upload verification document for manual review."""
        try:
            discount = AcademicDiscount.objects.get(user=user)
            discount.uploaded_document = document
            discount.document_type = document_type
            discount.institution_name = institution_name
            discount.status = 'pending'
            discount.save()

            # Notify admin team for review
            AcademicDiscountService._notify_admin_for_review(discount)

            return discount, "Document uploaded successfully. Review typically takes 1-2 business days."

        except AcademicDiscount.DoesNotExist:
            raise ValidationError("No academic discount application found. Please start the verification process.")

    @staticmethod
    def admin_review_discount(discount_id, approved, reviewer, notes=""):
        """Admin review of academic discount application."""
        try:
            discount = AcademicDiscount.objects.get(id=discount_id)

            if approved:
                discount.verify_discount(verified_by=reviewer)
                AcademicDiscountService._send_approval_email(discount)
                message = "Academic discount approved and activated."
            else:
                discount.status = 'rejected'
                discount.review_notes = notes
                discount.reviewed_by = reviewer
                discount.save()
                AcademicDiscountService._send_rejection_email(discount)
                message = "Academic discount application rejected."

            return discount, message

        except AcademicDiscount.DoesNotExist:
            raise ValidationError("Academic discount application not found.")

    @staticmethod
    def calculate_academic_price(original_price, user, plan_id: str | None = None, billing_cycle: str = 'monthly'):
        """Calculate price with academic discount applied."""
        if not AcademicDiscountService._is_plan_eligible_for_academic_discount(plan_id, billing_cycle):
            return {
                'original_price': original_price,
                'discount_rate': Decimal('0.00'),
                'discount_amount': Decimal('0.00'),
                'final_price': original_price,
                'has_discount': False
            }
        try:
            discount = AcademicDiscount.objects.get(user=user)
            if discount.is_valid:
                discount_amount = original_price * (discount.discount_rate / 100)
                discounted_price = original_price - discount_amount
                return {
                    'original_price': original_price,
                    'discount_rate': discount.discount_rate,
                    'discount_amount': discount_amount,
                    'final_price': discounted_price,
                    'has_discount': True
                }
        except AcademicDiscount.DoesNotExist:
            pass

        return {
            'original_price': original_price,
            'discount_rate': Decimal('0.00'),
            'discount_amount': Decimal('0.00'),
            'final_price': original_price,
            'has_discount': False
        }

    @staticmethod
    def check_expiring_discounts():
        """Check for discounts expiring in 30 days and send reminders."""
        expiring_soon = AcademicDiscount.objects.filter(
            status='verified',
            expires_at__lte=timezone.now() + timedelta(days=30),
            expires_at__gt=timezone.now(),
            last_reverification_sent__isnull=True
        )

        for discount in expiring_soon:
            discount.send_reverification_reminder()
            AcademicDiscountService._send_reverification_email(discount)

    @staticmethod
    def _send_verification_email(discount):
        """Send verification confirmation email."""
        subject = "Academic Discount Verified - 30% Off OCH Subscription"
        message = f"""
        Congratulations! Your academic discount has been verified.

        You now receive 30% off all OCH subscription plans.

        Institution: {discount.institution_domain}
        Discount Rate: {discount.discount_rate}%
        Valid Until: {discount.expires_at.strftime('%B %d, %Y')}

        Start your discounted subscription today!
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[discount.user.email],
            fail_silently=True
        )

    @staticmethod
    def _send_approval_email(discount):
        """Send approval email for manual verification."""
        subject = "Academic Discount Approved - 30% Off OCH Subscription"
        message = f"""
        Great news! Your academic discount application has been approved.

        Institution: {discount.institution_name}
        Discount Rate: {discount.discount_rate}%
        Valid Until: {discount.expires_at.strftime('%B %d, %Y')}

        You can now enjoy 30% off all OCH subscription plans.
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[discount.user.email],
            fail_silently=True
        )

    @staticmethod
    def _send_rejection_email(discount):
        """Send rejection email."""
        subject = "Academic Discount Application Update"
        message = f"""
        Thank you for your academic discount application.

        Unfortunately, we were unable to verify your student status with the provided documentation.

        Reason: {discount.review_notes}

        If you are currently receiving an academic discount, your subscription will revert to standard pricing when your academic discount expires.

        You can reapply with additional documentation or contact support for assistance.
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[discount.user.email],
            fail_silently=True
        )

    @staticmethod
    def _send_reverification_email(discount):
        """Send reverification reminder email."""
        subject = "Academic Discount Renewal Required"
        message = f"""
        Your academic discount expires in {discount.days_until_expiry} days.

        To continue receiving 30% off your OCH subscription, please verify your current student status.

        Current Discount: {discount.discount_rate}%
        Expires: {discount.expires_at.strftime('%B %d, %Y')}

        Important: if you don't re-verify, your subscription will revert to standard pricing on the expiry date.

        Renew your academic discount today to avoid a rate increase.
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[discount.user.email],
            fail_silently=True
        )

    @staticmethod
    def _notify_admin_for_review(discount):
        """Notify admin team of pending review."""
        subject = f"Academic Discount Review Required - {discount.user.email}"
        message = f"""
        New academic discount application requires review:

        User: {discount.user.email}
        Institution: {discount.institution_name}
        Document Type: {discount.get_document_type_display()}
        Submitted: {discount.created_at.strftime('%B %d, %Y at %I:%M %p')}

        Please review in the admin dashboard.
        """

        # Send to admin team
        admin_emails = ['admin@och.com']  # Configure admin emails
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            fail_silently=True
        )


class PromotionalCodeService:
    """Service for managing promotional codes."""

    @staticmethod
    def validate_and_apply_code(code_str, user, plan_id=None, original_amount=None):
        """Validate promotional code and calculate discount."""
        try:
            code = PromotionalCode.objects.get(code=code_str.upper())

            # Check if code can be used
            can_use, message = code.can_be_used_by(user, plan_id)
            if not can_use:
                return None, message

            # Calculate discount
            discount_amount = Decimal('0.00')
            if original_amount and code.discount_type in ['percentage', 'fixed_amount']:
                discount_amount = code.calculate_discount(original_amount)

            return {
                'code': code,
                'discount_amount': discount_amount,
                'discount_type': code.discount_type,
                'discount_value': code.discount_value,
                'extended_trial_days': code.extended_trial_days,
                'bonus_credits': code.bonus_credits,
                'final_amount': max(Decimal('0.00'), original_amount - discount_amount) if original_amount else None,
                'can_stack_academic': code.stackable_with_academic
            }, "Promotional code is valid!"

        except PromotionalCode.DoesNotExist:
            return None, "Invalid promotional code."

    @staticmethod
    def apply_code_to_subscription(code_str, user, subscription=None):
        """Apply promotional code to subscription."""
        try:
            with transaction.atomic():
                code = PromotionalCode.objects.get(code=code_str.upper())

                # Validate code
                can_use, message = code.can_be_used_by(user, subscription.plan_version.plan_id if subscription else None)
                if not can_use:
                    raise ValidationError(message)

                # Prevent stacking: only one promo code per subscription
                if subscription and PromotionalCodeRedemption.objects.filter(subscription=subscription).exists():
                    raise ValidationError("A promotional code has already been applied to this subscription")

                # Calculate discount amount
                original_amount = Decimal('0.00')
                if subscription:
                    original_amount = (
                        subscription.plan_version.price_annual if subscription.billing_cycle == 'annual'
                        else subscription.plan_version.price_monthly
                    )

                discount_amount = code.calculate_discount(original_amount)

                # Create redemption record
                redemption = code.redeem(user, subscription)
                redemption.original_amount = original_amount
                redemption.discount_amount = discount_amount
                redemption.final_amount = max(Decimal('0.00'), original_amount - discount_amount)

                # Apply extended trial if applicable
                if code.discount_type == 'extended_trial' and subscription and subscription.status == 'TRIAL':
                    new_trial_end = subscription.trial_end + timedelta(days=code.extended_trial_days)
                    subscription.trial_end = new_trial_end
                    subscription.current_period_end = new_trial_end
                    subscription.save()
                    redemption.extended_trial_days_applied = code.extended_trial_days

                # Apply bonus credits if applicable
                if code.discount_type == 'bonus_credits':
                    # Add bonus credits to user account (implement based on your credit system)
                    redemption.bonus_credits_applied = code.bonus_credits

                redemption.save()

                return redemption, f"Promotional code '{code.code}' applied successfully!"

        except PromotionalCode.DoesNotExist:
            raise ValidationError("Invalid promotional code.")

    @staticmethod
    def calculate_combined_discount(user, plan_version, billing_cycle, promo_code=None):
        """Calculate combined academic + promotional discount."""
        original_price = (
            plan_version.price_annual if billing_cycle == 'annual'
            else plan_version.price_monthly
        )

        result = {
            'original_price': original_price,
            'academic_discount': Decimal('0.00'),
            'promo_discount': Decimal('0.00'),
            'total_discount': Decimal('0.00'),
            'final_price': original_price,
            'has_academic': False,
            'has_promo': False,
            'promo_details': None
        }

        # Apply academic discount
        academic_pricing = AcademicDiscountService.calculate_academic_price(
            original_price,
            user,
            plan_id=getattr(plan_version, 'plan_id', None),
            billing_cycle=billing_cycle,
        )
        if academic_pricing['has_discount']:
            result['academic_discount'] = academic_pricing['discount_amount']
            result['has_academic'] = True
            result['final_price'] = academic_pricing['final_price']

        # Apply promotional discount
        if promo_code:
            promo_result, message = PromotionalCodeService.validate_and_apply_code(
                promo_code, user, plan_version.plan_id, result['final_price']
            )

            if promo_result:
                # Check if can stack with academic
                if result['has_academic'] and not promo_result['can_stack_academic']:
                    # Choose better discount
                    if promo_result['discount_amount'] > result['academic_discount']:
                        result['academic_discount'] = Decimal('0.00')
                        result['has_academic'] = False
                        result['promo_discount'] = promo_result['discount_amount']
                        result['final_price'] = promo_result['final_amount']
                    # Keep academic discount if it's better
                else:
                    # Stack discounts
                    result['promo_discount'] = promo_result['discount_amount']
                    result['final_price'] = max(Decimal('0.00'), result['final_price'] - promo_result['discount_amount'])

                result['has_promo'] = True
                result['promo_details'] = promo_result

        result['total_discount'] = result['academic_discount'] + result['promo_discount']

        return result

    @staticmethod
    def get_active_codes_for_admin():
        """Get active promotional codes for admin dashboard."""
        return PromotionalCode.objects.filter(
            status='active',
            valid_until__gt=timezone.now()
        ).order_by('-created_at')

    @staticmethod
    def get_code_analytics(code_id):
        """Get analytics for a promotional code."""
        try:
            code = PromotionalCode.objects.get(id=code_id)
            redemptions = code.redemptions.all()

            totals = redemptions.aggregate(
                total_discount=Sum('discount_amount'),
                total_original=Sum('original_amount'),
                avg_discount=Avg('discount_amount'),
                redemptions=Count('id'),
            )
            total_discount = totals['total_discount'] or Decimal('0.00')
            total_original = totals['total_original'] or Decimal('0.00')
            avg_discount = totals['avg_discount'] or Decimal('0.00')
            redemption_count = totals['redemptions'] or 0

            by_plan = (
                redemptions
                .exclude(subscription__isnull=True)
                .values('subscription__plan_version__plan_id', 'subscription__plan_version__name')
                .annotate(redemptions=Count('id'), total_discount=Sum('discount_amount'))
                .order_by('-redemptions')
            )

            converted = redemptions.exclude(subscription__isnull=True).filter(subscription__status='ACTIVE')
            converted_count = converted.count()
            conversion_rate = (Decimal(converted_count) / Decimal(redemption_count) * 100) if redemption_count > 0 else Decimal('0.00')

            conversions_by_plan = (
                converted
                .values('subscription__plan_version__plan_id', 'subscription__plan_version__name')
                .annotate(conversions=Count('id'))
                .order_by('-conversions')
            )

            return {
                'code': code,
                'total_redemptions': code.current_redemptions,
                'redemptions_remaining': code.redemptions_remaining,
                'usage_percentage': code.usage_percentage,
                'total_discount_given': total_discount,
                'average_discount': avg_discount,
                'revenue_impact': {
                    'total_original': total_original,
                    'total_discount': total_discount,
                    'discount_rate': (total_discount / total_original * 100) if total_original > 0 else Decimal('0.00'),
                    'net_revenue': (total_original - total_discount),
                    'redemption_count': redemption_count,
                },
                'conversion': {
                    'converted_count': converted_count,
                    'conversion_rate': conversion_rate,
                    'conversions_by_plan': [
                        {
                            'plan_id': row['subscription__plan_version__plan_id'],
                            'plan_name': row['subscription__plan_version__name'],
                            'conversions': row['conversions'],
                        }
                        for row in conversions_by_plan
                    ]
                },
                'plan_breakdown': [
                    {
                        'plan_id': row['subscription__plan_version__plan_id'],
                        'plan_name': row['subscription__plan_version__name'],
                        'redemptions': row['redemptions'],
                        'total_discount': row['total_discount'] or Decimal('0.00'),
                    }
                    for row in by_plan
                ],
                'redemption_timeline': [
                    {
                        'date': r.redeemed_at.date(),
                        'user': r.user.email,
                        'discount': float(r.discount_amount)
                    }
                    for r in redemptions.order_by('-redeemed_at')[:50]
                ]
            }
        except PromotionalCode.DoesNotExist:
            raise ValidationError("Promotional code not found.")


class EnhancedTrialService:
    """Service for managing enhanced trial periods."""

    @staticmethod
    def get_trial_configuration(plan_version):
        """Get trial configuration for plan."""
        try:
            return plan_version.trial_config
        except EnhancedTrialConfiguration.DoesNotExist:
            # Create default configuration
            return EnhancedTrialConfiguration.objects.create(
                plan_version=plan_version,
                trial_days=14 if plan_version.plan_id != 'premium' else 7,
                requires_payment_method=plan_version.plan_id == 'premium',
                grace_period_days=3 if plan_version.plan_id != 'premium' else 7
            )

    @staticmethod
    def create_enhanced_trial(user, plan_version, billing_cycle='monthly', promo_code=None, payment_method_ref=None, payment_gateway=None):
        """Create trial with enhanced configuration."""
        trial_config = EnhancedTrialService.get_trial_configuration(plan_version)

        # Calculate trial period
        trial_days = trial_config.trial_days

        # Enforce card-on-file requirement for trials (e.g., Premium)
        if trial_config.requires_payment_method and not payment_method_ref:
            raise ValidationError("Payment method is required to start a trial for this plan")

        # Apply promotional extension if applicable
        if promo_code:
            promo_result, _ = PromotionalCodeService.validate_and_apply_code(
                promo_code, user, plan_version.plan_id
            )
            if promo_result and promo_result['extended_trial_days'] > 0:
                trial_days += promo_result['extended_trial_days']

        # Create subscription
        trial_start = timezone.now()
        trial_end = trial_start + timedelta(days=trial_days)

        subscription = EnhancedSubscription.objects.create(
            user=user,
            plan_version=plan_version,
            status='TRIAL',
            billing_cycle=billing_cycle,
            cycle_anchor_day=trial_end.day,
            current_period_start=trial_start,
            current_period_end=trial_end,
            trial_start=trial_start,
            trial_end=trial_end,
            payment_method_ref=payment_method_ref,
            payment_gateway=payment_gateway,
            payment_method_added_at=timezone.now() if payment_method_ref else None,
        )

        # Apply promotional code if provided
        if promo_code:
            try:
                PromotionalCodeService.apply_code_to_subscription(promo_code, user, subscription)
            except ValidationError:
                pass  # Continue even if promo code fails

        return subscription

    @staticmethod
    def send_trial_reminders():
        """Send trial expiration reminders."""
        # Get trials expiring in 7, 3, and 1 days
        for days in [7, 3, 1]:
            expiring_trials = EnhancedSubscription.objects.filter(
                status='TRIAL',
                trial_end__date=timezone.now().date() + timedelta(days=days)
            )

            for subscription in expiring_trials:
                EnhancedTrialService._send_trial_reminder(subscription, days)

    @staticmethod
    def _send_trial_reminder(subscription, days_remaining):
        """Send trial reminder email."""
        subject = f"Your OCH Trial Expires in {days_remaining} Day{'s' if days_remaining > 1 else ''}"

        message = f"""
        Hi {subscription.user.first_name or subscription.user.email},

        Your {subscription.plan_version.name} trial expires in {days_remaining} day{'s' if days_remaining > 1 else ''}.

        Don't lose access to:
        • {', '.join(subscription.plan_version.tier_access)} tier content
        • {subscription.plan_version.mentorship_credits} mentorship credits per month
        • All premium features

        Convert to a paid plan now to continue your learning journey.
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[subscription.user.email],
            fail_silently=True
        )


class GracePeriodService:
    """Service for managing grace periods."""

    @staticmethod
    def initiate_grace_period(subscription, billing_period):
        """Start grace period for failed payment."""
        trial_config = EnhancedTrialService.get_trial_configuration(subscription.plan_version)
        grace_days = trial_config.grace_period_days

        grace_period = GracePeriodTracking.objects.create(
            subscription=subscription,
            billing_period=billing_period,
            ends_at=timezone.now() + timedelta(days=grace_days),
            grace_days=grace_days
        )

        # Send grace period notification
        GracePeriodService._send_grace_period_notification(grace_period)

        return grace_period

    @staticmethod
    def check_expiring_grace_periods():
        """Check for expiring grace periods and send final warnings."""
        expiring_today = GracePeriodTracking.objects.filter(
            is_active=True,
            ends_at__date=timezone.now().date()
        )

        for grace_period in expiring_today:
            GracePeriodService._send_final_warning(grace_period)

    @staticmethod
    def _send_grace_period_notification(grace_period):
        """Send grace period start notification."""
        subject = "Payment Failed - Grace Period Active"

        message = f"""
        Your recent payment failed, but don't worry - your access continues.

        Grace Period: {grace_period.grace_days} days
        Expires: {grace_period.ends_at.strftime('%B %d, %Y at %I:%M %p')}

        Please update your payment method to avoid service interruption.
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[grace_period.subscription.user.email],
            fail_silently=True
        )

    @staticmethod
    def _send_final_warning(grace_period):
        """Send final warning before suspension."""
        subject = "URGENT: Account Suspension in 24 Hours"

        message = f"""
        FINAL NOTICE: Your grace period expires in 24 hours.

        Your account will be suspended if payment is not received by:
        {grace_period.ends_at.strftime('%B %d, %Y at %I:%M %p')}

        Update your payment method immediately to avoid losing access.
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[grace_period.subscription.user.email],
            fail_silently=True
        )
