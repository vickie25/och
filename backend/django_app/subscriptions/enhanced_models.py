# Enhanced Billing Models with Academic Discounts and Promotional Codes

import uuid

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class AcademicDiscount(models.Model):
    """Academic discount eligibility and verification"""
    VERIFICATION_METHODS = [
        ('edu_email', 'Educational Email Domain'),
        ('manual', 'Manual Verification'),
        ('student_id', 'Student ID Upload'),
        ('faculty_id', 'Faculty ID Upload')
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='academic_discount')
    verification_method = models.CharField(max_length=20, choices=VERIFICATION_METHODS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Verification details
    email_domain = models.CharField(max_length=255, blank=True)
    institution_name = models.CharField(max_length=255, blank=True)
    student_id = models.CharField(max_length=100, blank=True)
    verification_document = models.FileField(upload_to='academic_verification/', blank=True)

    # Discount details
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2, default=30.00)  # 30%
    verified_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    # Verification tracking
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_academic_discounts')
    rejection_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'academic_discounts'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['email_domain']),
            models.Index(fields=['expires_at'])
        ]

    def is_valid(self):
        """Check if academic discount is currently valid"""
        return (
            self.status == 'verified' and
            (self.expires_at is None or self.expires_at > timezone.now())
        )

    def __str__(self):
        return f"Academic Discount - {self.user.email} ({self.status})"

class PromotionalCode(models.Model):
    """Promotional codes for discounts"""
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage Discount'),
        ('fixed', 'Fixed Amount Discount'),
        ('free_trial', 'Extended Free Trial'),
        ('free_months', 'Free Months')
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('expired', 'Expired'),
        ('exhausted', 'Exhausted')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Discount configuration
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)

    # Validity period
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()

    # Usage limits
    max_redemptions = models.IntegerField(null=True, blank=True)  # None = unlimited
    max_redemptions_per_user = models.IntegerField(default=1)
    current_redemptions = models.IntegerField(default=0)

    # Plan restrictions
    applicable_plans = models.ManyToManyField('SubscriptionPlan', blank=True)
    minimum_plan_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # User restrictions
    new_users_only = models.BooleanField(default=False)
    academic_users_only = models.BooleanField(default=False)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'promotional_codes'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['status']),
            models.Index(fields=['valid_from', 'valid_until']),
            models.Index(fields=['discount_type'])
        ]

    def is_valid(self):
        """Check if promotional code is currently valid"""
        now = timezone.now()
        return (
            self.status == 'active' and
            self.valid_from <= now <= self.valid_until and
            (self.max_redemptions is None or self.current_redemptions < self.max_redemptions)
        )

    def can_be_used_by_user(self, user):
        """Check if user can use this promotional code"""
        if not self.is_valid():
            return False, "Promotional code is not valid"

        # Check user-specific restrictions
        if self.new_users_only:
            # Check if user has any previous subscriptions
            if user.subscriptions.exists():
                return False, "This code is only for new users"

        if self.academic_users_only:
            # Check if user has verified academic discount
            if not hasattr(user, 'academic_discount') or not user.academic_discount.is_valid():
                return False, "This code is only for verified academic users"

        # Check per-user redemption limit
        user_redemptions = self.redemptions.filter(user=user).count()
        if user_redemptions >= self.max_redemptions_per_user:
            return False, f"You have already used this code {self.max_redemptions_per_user} time(s)"

        return True, "Code can be used"

    def __str__(self):
        return f"{self.code} - {self.name}"

class PromoCodeRedemption(models.Model):
    """Track promotional code redemptions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    promo_code = models.ForeignKey(PromotionalCode, on_delete=models.CASCADE, related_name='redemptions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='promo_redemptions')
    subscription = models.ForeignKey('Subscription', on_delete=models.CASCADE, null=True, blank=True)

    # Redemption details
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2)
    original_amount = models.DecimalField(max_digits=10, decimal_places=2)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)

    redeemed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'promo_code_redemptions'
        unique_together = ['promo_code', 'user', 'subscription']
        indexes = [
            models.Index(fields=['promo_code']),
            models.Index(fields=['user']),
            models.Index(fields=['redeemed_at'])
        ]

    def __str__(self):
        return f"{self.promo_code.code} redeemed by {self.user.email}"

class EnhancedSubscriptionPlan(models.Model):
    """Enhanced subscription plan with trial configurations"""
    BILLING_CYCLES = [
        ('monthly', 'Monthly'),
        ('annual', 'Annual'),
        ('quarterly', 'Quarterly')
    ]

    PLAN_TYPES = [
        ('basic', 'Basic'),
        ('pro', 'Pro'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    description = models.TextField(blank=True)

    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLES)

    # Trial configuration
    trial_days = models.IntegerField(default=0)
    requires_credit_card = models.BooleanField(default=False)

    # Grace period configuration
    grace_period_days = models.IntegerField(default=3)  # Default for monthly

    # Features
    features = models.JSONField(default=list)
    feature_limits = models.JSONField(default=dict)

    # Plan status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'enhanced_subscription_plans'
        ordering = ['sort_order', 'price']
        indexes = [
            models.Index(fields=['plan_type']),
            models.Index(fields=['billing_cycle']),
            models.Index(fields=['is_active']),
            models.Index(fields=['sort_order'])
        ]

    def get_trial_config(self):
        """Get trial configuration based on plan type"""
        trial_configs = {
            'basic': {'days': 7, 'requires_card': False},
            'pro': {'days': 14, 'requires_card': False},
            'premium': {'days': 7, 'requires_card': True},
            'enterprise': {'days': 30, 'requires_card': True}
        }
        return trial_configs.get(self.plan_type, {'days': self.trial_days, 'requires_card': self.requires_credit_card})

    def get_grace_period_days(self):
        """Get grace period based on billing cycle"""
        if self.billing_cycle == 'annual':
            return 7
        elif self.billing_cycle == 'quarterly':
            return 5
        else:  # monthly
            return 3

    def calculate_price_with_discounts(self, user=None, promo_code=None):
        """Calculate final price with all applicable discounts"""
        base_price = self.price
        discounts_applied = []

        # Apply academic discount
        if user and hasattr(user, 'academic_discount') and user.academic_discount.is_valid():
            academic_discount = user.academic_discount.discount_rate
            base_price = base_price * (1 - academic_discount / 100)
            discounts_applied.append(f"Academic discount: {academic_discount}%")

        # Apply promotional code
        if promo_code and promo_code.is_valid():
            if promo_code.discount_type == 'percentage':
                promo_discount = base_price * (promo_code.discount_value / 100)
                base_price = base_price - promo_discount
                discounts_applied.append(f"Promo code: {promo_code.discount_value}%")
            elif promo_code.discount_type == 'fixed':
                base_price = max(0, base_price - promo_code.discount_value)
                discounts_applied.append(f"Promo code: ${promo_code.discount_value}")

        return {
            'final_price': base_price,
            'original_price': self.price,
            'discounts_applied': discounts_applied,
            'total_savings': self.price - base_price
        }

    def __str__(self):
        return f"{self.name} - ${self.price}/{self.billing_cycle}"

# Enhanced Subscription model with trial and grace period support
class EnhancedSubscription(models.Model):
    """Enhanced subscription with comprehensive trial and grace period support"""
    STATUS_CHOICES = [
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('suspended', 'Suspended'),
        ('canceled', 'Canceled'),
        ('expired', 'Expired')
    ]

    DUNNING_STATUS_CHOICES = [
        ('none', 'None'),
        ('soft_decline', 'Soft Decline'),
        ('hard_decline', 'Hard Decline'),
        ('final_notice', 'Final Notice')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enhanced_subscriptions')
    plan = models.ForeignKey(EnhancedSubscriptionPlan, on_delete=models.PROTECT)

    # Subscription status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    dunning_status = models.CharField(max_length=20, choices=DUNNING_STATUS_CHOICES, default='none')

    # Billing periods
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    next_billing_date = models.DateTimeField()

    # Trial period
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    trial_converted_at = models.DateTimeField(null=True, blank=True)

    # Grace period
    grace_period_start = models.DateTimeField(null=True, blank=True)
    grace_period_end = models.DateTimeField(null=True, blank=True)

    # Pricing and discounts
    base_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')

    # Applied discounts
    academic_discount_applied = models.BooleanField(default=False)
    promo_code_applied = models.ForeignKey(PromotionalCode, on_delete=models.SET_NULL, null=True, blank=True)

    # Billing tracking
    amount_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_payment_attempt = models.DateTimeField(null=True, blank=True)
    payment_retry_count = models.IntegerField(default=0)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    canceled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'enhanced_subscriptions'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['next_billing_date']),
            models.Index(fields=['trial_end']),
            models.Index(fields=['grace_period_end']),
            models.Index(fields=['dunning_status'])
        ]

    def is_in_trial(self):
        """Check if subscription is currently in trial period"""
        if not self.trial_start or not self.trial_end:
            return False
        now = timezone.now()
        return self.trial_start <= now <= self.trial_end and self.status == 'trial'

    def is_in_grace_period(self):
        """Check if subscription is in grace period"""
        if not self.grace_period_start or not self.grace_period_end:
            return False
        now = timezone.now()
        return self.grace_period_start <= now <= self.grace_period_end

    def days_until_trial_end(self):
        """Get days remaining in trial"""
        if not self.is_in_trial():
            return 0
        return (self.trial_end - timezone.now()).days

    def days_until_grace_period_end(self):
        """Get days remaining in grace period"""
        if not self.is_in_grace_period():
            return 0
        return (self.grace_period_end - timezone.now()).days

    def __str__(self):
        return f"{self.user.email} - {self.plan.name} ({self.status})"
