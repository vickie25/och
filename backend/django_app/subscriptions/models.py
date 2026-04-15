"""
Subscription Engine models - Tier management and Stripe integration.
"""
import uuid

from django.core.validators import MinValueValidator
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

from users.models import User

# Subscription Tier Constants
TIER_FREE = 'free'
TIER_STARTER = 'starter'
TIER_PREMIUM = 'premium'


class SubscriptionPlan(models.Model):
    """Subscription plan definition. Student Stream A plans are driven by `catalog` + admin-editable fields."""
    TIER_CHOICES = [
        (TIER_FREE, 'Free Tier'),
        (TIER_STARTER, 'Starter / Pro (monthly or annual SKUs)'),
        (TIER_PREMIUM, 'Premium Tier'),
    ]

    STREAM_STUDENT = 'student'
    STREAM_CHOICES = [
        (STREAM_STUDENT, 'Student (Stream A)'),
    ]

    BILLING_NONE = 'none'
    BILLING_MONTHLY = 'monthly'
    BILLING_ANNUAL = 'annual'
    BILLING_INTERVAL_CHOICES = [
        (BILLING_NONE, 'No billing (free)'),
        (BILLING_MONTHLY, 'Monthly'),
        (BILLING_ANNUAL, 'Annual'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='e.g., "free", "starter", "premium"'
    )
    tier = models.CharField(
        max_length=20,
        choices=TIER_CHOICES,
        db_index=True,
        help_text='Subscription tier level'
    )
    price_monthly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text='Monthly price (NULL for free tier)'
    )
    features = models.JSONField(
        default=list,
        blank=True,
        help_text='Feature flags: ["curriculum_read", "profiler_full", "missions", "ai_coach", "portfolio", "talentscope", "mentorship", "marketplace"]'
    )
    # Feature-specific limits
    ai_coach_daily_limit = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text='AI Coach interactions per day (NULL = unlimited)'
    )
    portfolio_item_limit = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text='Portfolio items limit (NULL = unlimited)'
    )
    missions_access_type = models.CharField(
        max_length=50,
        choices=[
            ('none', 'No Missions'),
            ('ai_only', 'AI-Only Missions'),
            ('full', 'Full Missions (including Capstones and Labs)'),
        ],
        default='none',
        help_text='Type of mission access'
    )
    mentorship_access = models.BooleanField(
        default=False,
        help_text='Full mentorship access (group sessions, recordings, reviews)'
    )
    talentscope_access = models.CharField(
        max_length=50,
        choices=[
            ('none', 'No Access'),
            ('basic', 'Basic TalentScope'),
            ('preview', 'Preview Mode'),
            ('full', 'Full Analytics (readiness, CV scoring, Mentor Influence Index)'),
        ],
        default='none',
        help_text='TalentScope access level'
    )
    marketplace_contact = models.BooleanField(
        default=False,
        help_text='Enable employer contact via Marketplace'
    )
    enhanced_access_days = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text='Enhanced access period in days (e.g., 180 for Starter tier)'
    )
    stream = models.CharField(
        max_length=32,
        choices=STREAM_CHOICES,
        default=STREAM_STUDENT,
        db_index=True,
        help_text='Revenue stream (e.g. student vs future B2B)',
    )
    billing_interval = models.CharField(
        max_length=16,
        choices=BILLING_INTERVAL_CHOICES,
        default=BILLING_MONTHLY,
        db_index=True,
        help_text='How this SKU is billed (free tier = none)',
    )
    price_annual = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text='Annual price in primary ledger currency (KES) when billing_interval is annual',
    )
    sort_order = models.PositiveSmallIntegerField(
        default=0,
        help_text='Display order (lower first)',
    )
    is_listed = models.BooleanField(
        default=True,
        db_index=True,
        help_text='Show on student pricing pages; admin can hide SKUs without deleting',
    )
    catalog = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            'Stream A metadata: tier_rank, usd_monthly, usd_annual, tier_range {min,max}, '
            'mentorship_credits_per_month (null = unlimited), trial_days, '
            'trial_requires_payment_method, features {tier_2_6_access, tier_7_9_access, '
            'priority_support, certification_prep}, annual_savings_percent, display_name, marketing_notes'
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscription_plans'
        indexes = [
            models.Index(fields=['tier']),
        ]

    def __str__(self):
        price_str = f"${self.price_monthly}/mo" if self.price_monthly else "Free"
        return f"{self.get_tier_display()} - {price_str}"


class UserSubscription(models.Model):
    """User subscription record."""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('trial', 'Trial'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='subscription',
        db_column='user_id',
        db_index=True,
        help_text='FK column stores users.id (bigint) in local/dev DB.',
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='user_subscriptions',
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='trial',
        db_index=True
    )
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    enhanced_access_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text='180 days for starter_enhanced'
    )
    stripe_subscription_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        db_index=True
    )
    payment_gateway = models.CharField(
        max_length=20,
        choices=[('stripe', 'Stripe'), ('paystack', 'Paystack')],
        null=True,
        blank=True,
        db_index=True,
        help_text='Gateway holding the default payment method'
    )
    payment_method_ref = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text='Gateway payment method reference (e.g. Stripe pm_...)'
    )
    payment_method_added_at = models.DateTimeField(null=True, blank=True)
    billing_interval = models.CharField(
        max_length=16,
        choices=SubscriptionPlan.BILLING_INTERVAL_CHOICES,
        default=SubscriptionPlan.BILLING_MONTHLY,
        db_index=True,
        help_text='Active cycle for this subscription (monthly vs annual)',
    )
    trial_end = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text='When trial ends (if applicable)',
    )
    cancel_at_period_end = models.BooleanField(
        default=False,
        help_text='Cancellation scheduled for end of current period',
    )
    grace_period_end = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text='Access continues until this time after a failed renewal',
    )
    pending_downgrade_plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pending_downgrades',
        help_text='If set, user moves to this plan at current_period_end',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_subscriptions'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'current_period_end']),
        ]

    def __str__(self):
        return f"Subscription: {self.user.email} - {self.plan.name} ({self.status})"

    @property
    def days_enhanced_left(self):
        """Calculate days remaining for enhanced access."""
        if not self.enhanced_access_expires_at:
            return None
        delta = self.enhanced_access_expires_at - timezone.now()
        return max(0, delta.days)


class PaymentGateway(models.Model):
    """Payment gateway configuration for admin management."""
    GATEWAY_CHOICES = [
        ('stripe', 'Stripe'),
        ('paystack', 'Paystack'),
        ('flutterwave', 'Flutterwave'),
        ('mpesa', 'M-Pesa'),
        ('orange_money', 'Orange Money'),
        ('airtel_money', 'Airtel Money'),
        ('visa_mastercard', 'Visa/Mastercard'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, choices=GATEWAY_CHOICES, unique=True, db_index=True)
    enabled = models.BooleanField(default=False, help_text='Enable this payment gateway')
    api_key = models.CharField(max_length=255, blank=True, help_text='Public/API key')
    secret_key = models.CharField(max_length=255, blank=True, help_text='Secret key (encrypted)')
    webhook_secret = models.CharField(max_length=255, blank=True, help_text='Webhook signing secret')
    webhook_url = models.URLField(blank=True, help_text='Webhook endpoint URL')
    test_mode = models.BooleanField(default=True, help_text='Use test/sandbox mode')
    metadata = models.JSONField(default=dict, blank=True, help_text='Additional gateway-specific settings')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payment_gateways'
        verbose_name = 'Payment Gateway'
        verbose_name_plural = 'Payment Gateways'

    def __str__(self):
        return f"{self.get_name_display()} ({'Enabled' if self.enabled else 'Disabled'})"


class PaymentTransaction(models.Model):
    """Payment transaction record."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('canceled', 'Canceled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_transactions', db_index=True)
    gateway = models.ForeignKey(PaymentGateway, on_delete=models.PROTECT, related_name='transactions', null=True, blank=True)
    subscription = models.ForeignKey(UserSubscription, on_delete=models.SET_NULL, related_name='payments', null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    gateway_transaction_id = models.CharField(max_length=255, blank=True, db_index=True, help_text='External gateway transaction ID')
    gateway_response = models.JSONField(default=dict, blank=True, help_text='Raw gateway response')
    failure_reason = models.TextField(blank=True, help_text='Reason for failure if status is failed')
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payment_transactions'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['gateway_transaction_id']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Payment: {self.user.email} - {self.amount} {self.currency} ({self.status})"


class SubscriptionRule(models.Model):
    """Admin-configurable subscription rules and settings."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule_name = models.CharField(max_length=100, unique=True, db_index=True, help_text='e.g., "upgrade_instant", "downgrade_end_cycle"')
    rule_type = models.CharField(
        max_length=50,
        choices=[
            ('upgrade', 'Upgrade Rule'),
            ('downgrade', 'Downgrade Rule'),
            ('grace_period', 'Grace Period'),
            ('enhanced_access', 'Enhanced Access Period'),
        ],
        db_index=True
    )
    enabled = models.BooleanField(default=True)
    value = models.JSONField(default=dict, help_text='Rule configuration (e.g., {"days": 7, "action": "downgrade"})')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscription_rules'
        verbose_name = 'Subscription Rule'
        verbose_name_plural = 'Subscription Rules'

    def __str__(self):
        return f"{self.rule_name} ({self.get_rule_type_display()})"


class PaymentSettings(models.Model):
    """Global payment and subscription settings for admin configuration."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    setting_key = models.CharField(max_length=100, unique=True, db_index=True)
    setting_value = models.JSONField(default=dict)
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_settings_updates')

    class Meta:
        db_table = 'payment_settings'
        verbose_name = 'Payment Setting'
        verbose_name_plural = 'Payment Settings'

    def __str__(self):
        return f"{self.setting_key}"


class PromotionalCode(models.Model):
    """Promotional discount codes for marketing campaigns."""
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage Discount'),
        ('fixed', 'Fixed Amount Discount'),
        ('trial_extension', 'Trial Extension'),
        ('bonus_credits', 'Bonus Credits'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, db_index=True, help_text='Promo code (e.g., CYBER2026)')
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Percentage (e.g., 50 for 50%) or fixed amount in KES'
    )
    valid_from = models.DateTimeField(help_text='Code becomes active from this date')
    valid_until = models.DateTimeField(help_text='Code expires after this date')
    max_redemptions = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text='Maximum total redemptions (NULL = unlimited)'
    )
    usage_limit_per_user = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text='How many times each user can use this code'
    )
    eligible_plans = models.ManyToManyField(
        SubscriptionPlan,
        blank=True,
        related_name='promo_codes',
        help_text='Leave empty for all plans'
    )
    is_active = models.BooleanField(default=True, help_text='Manually disable code')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_promo_codes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'promotional_codes'
        verbose_name = 'Promotional Code'
        verbose_name_plural = 'Promotional Codes'
        indexes = [
            models.Index(fields=['code', 'is_active']),
            models.Index(fields=['valid_from', 'valid_until']),
        ]

    def __str__(self):
        return f"{self.code} ({self.get_discount_type_display()})"

    def clean(self):
        if self.code:
            self.code = self.code.upper().strip()
            # Keep it simple for marketing/share links
            for ch in self.code:
                if not ('A' <= ch <= 'Z' or '0' <= ch <= '9'):
                    raise ValidationError("Promo code must contain only letters A-Z and numbers 0-9")

        if self.valid_until and self.valid_from and self.valid_until <= self.valid_from:
            raise ValidationError("valid_until must be after valid_from")

        now = timezone.now()
        if self.pk:
            prior = PromotionalCode.objects.filter(pk=self.pk).values('valid_until', 'is_active').first()
            if prior:
                prior_valid_until = prior.get('valid_until')
                # If the code was already expired, it can never be reactivated or extended.
                if prior_valid_until and prior_valid_until < now:
                    if self.is_active:
                        raise ValidationError("Expired promo codes cannot be reactivated")
                    if self.valid_until and self.valid_until > prior_valid_until:
                        raise ValidationError("Expired promo codes cannot have their expiration extended")

        # Auto-expire: after valid_until, force-disable.
        if self.valid_until and self.valid_until < now:
            self.is_active = False

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    def is_valid(self):
        """Check if code is currently valid."""
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_until and
            (self.max_redemptions is None or self.redemptions.count() < self.max_redemptions)
        )

    def can_user_redeem(self, user):
        """Check if user can redeem this code."""
        if not self.is_valid():
            return False, "Code is not valid or has expired"

        user_redemptions = self.redemptions.filter(user=user).count()
        if user_redemptions >= self.usage_limit_per_user:
            return False, f"You have already used this code {self.usage_limit_per_user} time(s)"

        return True, "Code is valid"

    def calculate_discount(self, base_amount):
        """Calculate discount amount based on type."""
        if self.discount_type == 'percentage':
            return base_amount * (self.discount_value / 100)
        elif self.discount_type == 'fixed':
            return min(self.discount_value, base_amount)  # Don't exceed base amount
        return 0


class PromoCodeRedemption(models.Model):
    """Track promotional code redemptions."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.ForeignKey(
        PromotionalCode,
        on_delete=models.CASCADE,
        related_name='redemptions'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='promo_redemptions'
    )
    subscription = models.ForeignKey(
        UserSubscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='promo_redemptions'
    )
    discount_applied = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Actual discount amount in KES'
    )
    original_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Original price before discount'
    )
    final_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Final price after discount'
    )
    redeemed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'promo_code_redemptions'
        verbose_name = 'Promo Code Redemption'
        verbose_name_plural = 'Promo Code Redemptions'
        indexes = [
            models.Index(fields=['user', 'redeemed_at']),
            models.Index(fields=['code', 'redeemed_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.code.code} - {self.discount_applied} KES off"


class AcademicDiscount(models.Model):
    """Academic discount verification for students."""
    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]

    VERIFICATION_METHOD_CHOICES = [
        ('edu_email', '.edu Email'),
        ('document', 'Document Upload'),
        ('manual', 'Manual Verification'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='academic_discount'
    )
    verification_method = models.CharField(max_length=20, choices=VERIFICATION_METHOD_CHOICES)
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    edu_email = models.EmailField(
        null=True,
        blank=True,
        help_text='Verified .edu email address'
    )
    institution_name = models.CharField(max_length=255, blank=True)
    document_url = models.URLField(
        null=True,
        blank=True,
        help_text='URL to uploaded verification document'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Annual re-verification required'
    )
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_academic_discounts'
    )
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'academic_discounts'
        verbose_name = 'Academic Discount'
        verbose_name_plural = 'Academic Discounts'
        indexes = [
            models.Index(fields=['user', 'verification_status']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.get_verification_status_display()}"

    def is_active(self):
        """Check if discount is currently active."""
        if self.verification_status != 'verified':
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

    def get_discount_percentage(self):
        """Return discount percentage (30% for academic)."""
        return 30 if self.is_active() else 0

    def calculate_discounted_price(self, base_price):
        """Calculate price after academic discount."""
        if not self.is_active():
            return base_price
        discount = base_price * (self.get_discount_percentage() / 100)
        return base_price - discount


class SubscriptionInvoice(models.Model):
    """Invoice records for subscription payments."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('void', 'Void'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='e.g., INV-2026-001234'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscription_invoices'
    )
    subscription = models.ForeignKey(
        UserSubscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices'
    )
    transaction = models.OneToOneField(
        PaymentTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)

    # Amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='KES')

    # Dates
    invoice_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField()
    paid_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    # Invoice details
    line_items = models.JSONField(
        default=list,
        help_text='List of invoice line items'
    )
    notes = models.TextField(blank=True)
    pdf_url = models.URLField(null=True, blank=True, help_text='URL to generated PDF')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscription_invoices'
        verbose_name = 'Subscription Invoice'
        verbose_name_plural = 'Subscription Invoices'
        ordering = ['-invoice_date']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['invoice_date']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.user.email} - {self.total_amount} {self.currency}"

    def mark_as_paid(self):
        """Mark invoice as paid."""
        self.status = 'paid'
        self.paid_at = timezone.now()
        self.save(update_fields=['status', 'paid_at', 'updated_at'])

    def mark_as_sent(self):
        """Mark invoice as sent."""
        if self.status == 'draft':
            self.status = 'sent'
            self.sent_at = timezone.now()
            self.save(update_fields=['status', 'sent_at', 'updated_at'])

    @staticmethod
    def generate_invoice_number():
        """Generate unique invoice number."""
        from datetime import datetime
        year = datetime.now().year
        # Get last invoice number for this year
        last_invoice = SubscriptionInvoice.objects.filter(
            invoice_number__startswith=f'INV-{year}-'
        ).order_by('-invoice_number').first()

        if last_invoice:
            last_num = int(last_invoice.invoice_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f'INV-{year}-{new_num:06d}'


class PaymentRetryAttempt(models.Model):
    """Track payment retry attempts for failed renewals."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(
        UserSubscription,
        on_delete=models.CASCADE,
        related_name='retry_attempts'
    )
    attempt_number = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text='Retry attempt number (1, 2, 3, etc.)'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='KES')

    scheduled_at = models.DateTimeField(help_text='When retry is scheduled')
    attempted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    gateway_response = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payment_retry_attempts'
        verbose_name = 'Payment Retry Attempt'
        verbose_name_plural = 'Payment Retry Attempts'
        ordering = ['scheduled_at']
        indexes = [
            models.Index(fields=['subscription', 'status']),
            models.Index(fields=['scheduled_at', 'status']),
        ]

    def __str__(self):
        return f"Retry #{self.attempt_number} for {self.subscription.user.email} - {self.status}"
