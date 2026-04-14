"""
Enhanced Billing Services - Complete Implementation
Includes academic discounts, promotional codes, enhanced trial periods, and grace period management
"""

import logging
import re
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)

class AcademicDiscountService:
    """Service for managing academic discounts"""

    ACADEMIC_DOMAINS = [
        r'\.edu$', r'\.ac\.uk$', r'\.edu\.au$', r'\.ac\.in$', r'\.edu\.sg$',
        r'\.ac\.jp$', r'\.edu\.cn$', r'\.uni-.*\.de$', r'\.university\..*$',
        r'\.college\..*$', r'\.school\..*$'
    ]

    @classmethod
    def is_academic_email(cls, email):
        """Check if email domain is academic"""
        email_lower = email.lower()
        return any(re.search(pattern, email_lower) for pattern in cls.ACADEMIC_DOMAINS)

    @classmethod
    def create_academic_discount(cls, user, verification_method='edu_email', institution_name='', student_id=''):
        """Create academic discount for user"""
        from .enhanced_models import AcademicDiscount

        # Check if user already has academic discount
        if hasattr(user, 'academic_discount'):
            return user.academic_discount

        discount_data = {
            'user': user,
            'verification_method': verification_method,
            'discount_rate': Decimal('30.00'),  # 30% discount
        }

        if verification_method == 'edu_email' and cls.is_academic_email(user.email):
            # Auto-verify for .edu emails
            discount_data.update({
                'status': 'verified',
                'email_domain': user.email.split('@')[1],
                'verified_at': timezone.now(),
                'expires_at': timezone.now() + timedelta(days=365)  # 1 year
            })
        else:
            # Manual verification required
            discount_data.update({
                'status': 'pending',
                'institution_name': institution_name,
                'student_id': student_id
            })

        return AcademicDiscount.objects.create(**discount_data)

    @classmethod
    def verify_academic_discount(cls, discount_id, verified_by_user, approved=True, rejection_reason=''):
        """Manually verify academic discount"""
        from .enhanced_models import AcademicDiscount

        try:
            discount = AcademicDiscount.objects.get(id=discount_id)

            if approved:
                discount.status = 'verified'
                discount.verified_by = verified_by_user
                discount.verified_at = timezone.now()
                discount.expires_at = timezone.now() + timedelta(days=365)
            else:
                discount.status = 'rejected'
                discount.rejection_reason = rejection_reason

            discount.save()
            return discount

        except AcademicDiscount.DoesNotExist:
            raise ValidationError("Academic discount not found")

class PromotionalCodeService:
    """Service for managing promotional codes"""

    @classmethod
    def validate_promo_code(cls, code, user, plan_id=None):
        """Validate promotional code for user and plan"""
        from .enhanced_models import PromotionalCode

        try:
            promo_code = PromotionalCode.objects.get(code=code.upper())
        except PromotionalCode.DoesNotExist:
            return {'valid': False, 'error': 'Invalid promotional code'}

        # Check if code is valid
        if not promo_code.is_valid():
            return {'valid': False, 'error': 'Promotional code has expired or is inactive'}

        # Check user eligibility
        can_use, message = promo_code.can_be_used_by_user(user)
        if not can_use:
            return {'valid': False, 'error': message}

        # Check plan restrictions
        if plan_id and promo_code.applicable_plans.exists():
            if not promo_code.applicable_plans.filter(id=plan_id).exists():
                return {'valid': False, 'error': 'This code is not valid for the selected plan'}

        return {
            'valid': True,
            'code': promo_code.code,
            'discount_type': promo_code.discount_type,
            'discount_value': float(promo_code.discount_value),
            'description': promo_code.description or f"{promo_code.discount_value}{'%' if promo_code.discount_type == 'percentage' else '$'} off"
        }

    @classmethod
    def apply_promo_code(cls, promo_code, user, subscription, original_amount):
        """Apply promotional code to subscription"""
        from .enhanced_models import PromoCodeRedemption

        if promo_code.discount_type == 'percentage':
            discount_amount = original_amount * (promo_code.discount_value / 100)
        elif promo_code.discount_type == 'fixed':
            discount_amount = min(promo_code.discount_value, original_amount)
        else:
            discount_amount = Decimal('0.00')

        final_amount = max(Decimal('0.00'), original_amount - discount_amount)

        # Create redemption record
        redemption = PromoCodeRedemption.objects.create(
            promo_code=promo_code,
            user=user,
            subscription=subscription,
            discount_applied=discount_amount,
            original_amount=original_amount,
            final_amount=final_amount
        )

        # Update promo code usage
        promo_code.current_redemptions += 1
        promo_code.save()

        return {
            'discount_amount': discount_amount,
            'final_amount': final_amount,
            'redemption': redemption
        }

class EnhancedTrialService:
    """Service for managing enhanced trial periods"""

    TRIAL_CONFIGURATIONS = {
        'basic': {'days': 7, 'requires_card': False},
        'pro': {'days': 14, 'requires_card': False},
        'premium': {'days': 7, 'requires_card': True},
        'enterprise': {'days': 30, 'requires_card': True}
    }

    @classmethod
    def get_trial_config(cls, plan_type):
        """Get trial configuration for plan type"""
        return cls.TRIAL_CONFIGURATIONS.get(plan_type.lower(), {'days': 7, 'requires_card': False})

    @classmethod
    def start_trial(cls, user, plan):
        """Start trial period for user and plan"""
        from .enhanced_models import EnhancedSubscription

        trial_config = cls.get_trial_config(plan.plan_type)
        now = timezone.now()

        trial_start = now
        trial_end = now + timedelta(days=trial_config['days'])

        subscription = EnhancedSubscription.objects.create(
            user=user,
            plan=plan,
            status='trial',
            current_period_start=trial_start,
            current_period_end=trial_end,
            next_billing_date=trial_end,
            trial_start=trial_start,
            trial_end=trial_end,
            base_amount=plan.price,
            final_amount=Decimal('0.00')  # Free during trial
        )

        logger.info(f"Started {trial_config['days']}-day trial for user {user.id} on plan {plan.name}")
        return subscription

    @classmethod
    def convert_trial(cls, subscription, payment_method=None, promo_code=None):
        """Convert trial to paid subscription"""
        if subscription.status != 'trial':
            raise ValidationError("Subscription is not in trial status")

        now = timezone.now()

        # Calculate pricing with discounts
        pricing = cls._calculate_subscription_pricing(
            subscription.user,
            subscription.plan,
            promo_code
        )

        # Update subscription
        subscription.status = 'active'
        subscription.trial_converted_at = now
        subscription.base_amount = pricing['base_amount']
        subscription.discount_amount = pricing['discount_amount']
        subscription.final_amount = pricing['final_amount']
        subscription.academic_discount_applied = pricing['academic_discount_applied']

        if promo_code:
            subscription.promo_code_applied = promo_code

        # Set next billing period
        if subscription.plan.billing_cycle == 'monthly':
            subscription.next_billing_date = now + timedelta(days=30)
            subscription.current_period_end = now + timedelta(days=30)
        elif subscription.plan.billing_cycle == 'annual':
            subscription.next_billing_date = now + timedelta(days=365)
            subscription.current_period_end = now + timedelta(days=365)

        subscription.save()

        logger.info(f"Converted trial to paid subscription for user {subscription.user.id}")
        return subscription

    @classmethod
    def _calculate_subscription_pricing(cls, user, plan, promo_code=None):
        """Calculate subscription pricing with all discounts"""
        base_amount = plan.price
        discount_amount = Decimal('0.00')
        academic_discount_applied = False

        # Apply academic discount
        if hasattr(user, 'academic_discount') and user.academic_discount.is_valid():
            academic_discount = base_amount * (user.academic_discount.discount_rate / 100)
            discount_amount += academic_discount
            academic_discount_applied = True

        # Apply promotional code
        if promo_code:
            if promo_code.discount_type == 'percentage':
                promo_discount = (base_amount - discount_amount) * (promo_code.discount_value / 100)
            else:
                promo_discount = min(promo_code.discount_value, base_amount - discount_amount)
            discount_amount += promo_discount

        final_amount = max(Decimal('0.00'), base_amount - discount_amount)

        return {
            'base_amount': base_amount,
            'discount_amount': discount_amount,
            'final_amount': final_amount,
            'academic_discount_applied': academic_discount_applied
        }

class GracePeriodService:
    """Service for managing grace periods"""

    GRACE_PERIODS = {
        'monthly': 3,    # 3 days for monthly plans
        'quarterly': 5,  # 5 days for quarterly plans
        'annual': 7      # 7 days for annual plans
    }

    @classmethod
    def get_grace_period_days(cls, billing_cycle):
        """Get grace period days for billing cycle"""
        return cls.GRACE_PERIODS.get(billing_cycle, 3)

    @classmethod
    def start_grace_period(cls, subscription):
        """Start grace period for subscription"""
        if subscription.status != 'past_due':
            raise ValidationError("Subscription must be past due to start grace period")

        grace_days = cls.get_grace_period_days(subscription.plan.billing_cycle)
        now = timezone.now()

        subscription.grace_period_start = now
        subscription.grace_period_end = now + timedelta(days=grace_days)
        subscription.save()

        logger.info(f"Started {grace_days}-day grace period for subscription {subscription.id}")
        return subscription

    @classmethod
    def check_grace_period_expiry(cls):
        """Check and handle expired grace periods"""
        from .enhanced_models import EnhancedSubscription

        expired_subscriptions = EnhancedSubscription.objects.filter(
            grace_period_end__lt=timezone.now(),
            status='past_due'
        )

        for subscription in expired_subscriptions:
            subscription.status = 'suspended'
            subscription.save()
            logger.info(f"Suspended subscription {subscription.id} after grace period expiry")

        return expired_subscriptions.count()

class EnhancedBillingService:
    """Main enhanced billing service"""

    @classmethod
    @transaction.atomic
    def create_subscription(cls, user, plan_id, payment_method=None, promo_code=None, start_trial=True):
        """Create new subscription with all enhancements"""
        from .enhanced_models import EnhancedSubscriptionPlan, PromotionalCode

        try:
            plan = EnhancedSubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except EnhancedSubscriptionPlan.DoesNotExist:
            raise ValidationError("Invalid or inactive plan")

        # Validate promo code if provided
        validated_promo = None
        if promo_code:
            validation_result = PromotionalCodeService.validate_promo_code(promo_code, user, plan_id)
            if not validation_result['valid']:
                raise ValidationError(validation_result['error'])
            validated_promo = PromotionalCode.objects.get(code=promo_code.upper())

        # Check if user should start with trial
        if start_trial and plan.trial_days > 0:
            subscription = EnhancedTrialService.start_trial(user, plan)

            # Apply promo code to trial conversion
            if validated_promo:
                subscription.promo_code_applied = validated_promo
                subscription.save()
        else:
            # Create active subscription directly
            pricing = EnhancedTrialService._calculate_subscription_pricing(user, plan, validated_promo)
            now = timezone.now()

            if plan.billing_cycle == 'monthly':
                period_end = now + timedelta(days=30)
            elif plan.billing_cycle == 'annual':
                period_end = now + timedelta(days=365)
            else:  # quarterly
                period_end = now + timedelta(days=90)

            subscription = EnhancedSubscription.objects.create(
                user=user,
                plan=plan,
                status='active',
                current_period_start=now,
                current_period_end=period_end,
                next_billing_date=period_end,
                base_amount=pricing['base_amount'],
                discount_amount=pricing['discount_amount'],
                final_amount=pricing['final_amount'],
                academic_discount_applied=pricing['academic_discount_applied'],
                promo_code_applied=validated_promo
            )

        # Apply promo code if provided
        if validated_promo:
            PromotionalCodeService.apply_promo_code(
                validated_promo,
                user,
                subscription,
                subscription.base_amount
            )

        logger.info(f"Created subscription {subscription.id} for user {user.id} on plan {plan.name}")
        return subscription

    @classmethod
    @transaction.atomic
    def change_plan(cls, subscription, new_plan_id, promo_code=None, prorate=True):
        """Change subscription plan with proration"""
        from .enhanced_models import EnhancedSubscriptionPlan, PromotionalCode

        try:
            new_plan = EnhancedSubscriptionPlan.objects.get(id=new_plan_id, is_active=True)
        except EnhancedSubscriptionPlan.DoesNotExist:
            raise ValidationError("Invalid or inactive plan")

        if subscription.plan.id == new_plan.id:
            raise ValidationError("User is already on this plan")

        # Validate promo code if provided
        validated_promo = None
        if promo_code:
            validation_result = PromotionalCodeService.validate_promo_code(promo_code, subscription.user, new_plan_id)
            if not validation_result['valid']:
                raise ValidationError(validation_result['error'])
            validated_promo = PromotionalCode.objects.get(code=promo_code.upper())

        # Calculate new pricing
        pricing = EnhancedTrialService._calculate_subscription_pricing(
            subscription.user,
            new_plan,
            validated_promo
        )

        # Handle proration if needed
        proration_credit = Decimal('0.00')
        if prorate and subscription.status == 'active':
            proration_credit = cls._calculate_proration_credit(subscription)

        # Update subscription
        old_plan_name = subscription.plan.name
        subscription.plan = new_plan
        subscription.base_amount = pricing['base_amount']
        subscription.discount_amount = pricing['discount_amount']
        subscription.final_amount = max(Decimal('0.00'), pricing['final_amount'] - proration_credit)
        subscription.academic_discount_applied = pricing['academic_discount_applied']
        subscription.promo_code_applied = validated_promo
        subscription.save()

        # Apply promo code if provided
        if validated_promo:
            PromotionalCodeService.apply_promo_code(
                validated_promo,
                subscription.user,
                subscription,
                subscription.base_amount
            )

        logger.info(f"Changed plan from {old_plan_name} to {new_plan.name} for subscription {subscription.id}")
        return subscription

    @classmethod
    def _calculate_proration_credit(cls, subscription):
        """Calculate proration credit for plan changes"""
        now = timezone.now()
        period_start = subscription.current_period_start
        period_end = subscription.current_period_end

        total_period_seconds = (period_end - period_start).total_seconds()
        remaining_seconds = (period_end - now).total_seconds()

        if remaining_seconds <= 0:
            return Decimal('0.00')

        usage_ratio = remaining_seconds / total_period_seconds
        return subscription.final_amount * Decimal(str(usage_ratio))

    @classmethod
    def process_dunning(cls, subscription):
        """Process dunning for failed payments"""
        if subscription.status != 'past_due':
            return subscription

        # Start grace period if not already started
        if not subscription.grace_period_start:
            GracePeriodService.start_grace_period(subscription)

        # Update dunning status based on retry count
        if subscription.payment_retry_count == 0:
            subscription.dunning_status = 'soft_decline'
        elif subscription.payment_retry_count <= 3:
            subscription.dunning_status = 'hard_decline'
        else:
            subscription.dunning_status = 'final_notice'

        subscription.payment_retry_count += 1
        subscription.last_payment_attempt = timezone.now()
        subscription.save()

        logger.info(f"Updated dunning status to {subscription.dunning_status} for subscription {subscription.id}")
        return subscription

    @classmethod
    def get_subscription_analytics(cls, user_id=None):
        """Get comprehensive subscription analytics"""
        from .enhanced_models import EnhancedSubscription

        queryset = EnhancedSubscription.objects.select_related('user', 'plan', 'promo_code_applied')

        if user_id:
            queryset = queryset.filter(user_id=user_id)

        analytics = {
            'total_subscriptions': queryset.count(),
            'active_subscriptions': queryset.filter(status='active').count(),
            'trial_subscriptions': queryset.filter(status='trial').count(),
            'past_due_subscriptions': queryset.filter(status='past_due').count(),
            'academic_discounts': queryset.filter(academic_discount_applied=True).count(),
            'promo_code_usage': queryset.exclude(promo_code_applied=None).count(),
            'total_revenue': sum(s.final_amount for s in queryset.filter(status='active')),
            'total_discounts': sum(s.discount_amount for s in queryset),
        }

        return analytics
