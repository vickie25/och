"""
Finance models for the Ongoza CyberHub platform.
Implements wallet, credits, contracts, and tax management.
"""
import uuid
from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from users.models import User


class Wallet(models.Model):
    """Wallet entity for storing user credit balance."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='wallet',
        db_index=True
    )
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Current credit balance'
    )
    currency = models.CharField(max_length=3, default='USD', help_text='Currency code')
    last_transaction_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wallets'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['balance']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.balance} {self.currency}"

    def add_balance(self, amount, description="Credit added"):
        """Add balance to wallet and create transaction record."""
        self.balance += amount
        self.last_transaction_at = timezone.now()
        self.save()

        Transaction.objects.create(
            wallet=self,
            type='credit',
            amount=amount,
            description=description,
            reference_type='manual',
            reference_id=str(uuid.uuid4())
        )

    def deduct_balance(self, amount, description="Credit used"):
        """Deduct balance from wallet and create transaction record."""
        if self.balance < amount:
            raise ValueError("Insufficient balance")

        self.balance -= amount
        self.last_transaction_at = timezone.now()
        self.save()

        Transaction.objects.create(
            wallet=self,
            type='debit',
            amount=amount,
            description=description,
            reference_type='usage',
            reference_id=str(uuid.uuid4())
        )


class Transaction(models.Model):
    """Transaction entity recording wallet transactions."""
    TYPE_CHOICES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]

    REFERENCE_TYPE_CHOICES = [
        ('subscription', 'Subscription'),
        ('cohort', 'Cohort'),
        ('promotion', 'Promotion'),
        ('refund', 'Refund'),
        ('manual', 'Manual'),
        ('usage', 'Usage'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='transactions',
        db_index=True
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    description = models.TextField()
    reference_type = models.CharField(max_length=20, choices=REFERENCE_TYPE_CHOICES)
    reference_id = models.UUIDField(help_text='Reference to source transaction')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wallet_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', 'type']),
            models.Index(fields=['reference_type', 'reference_id']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.wallet.user.email} - {self.type} {self.amount}"


class Credit(models.Model):
    """Credit entity for tracking promotional and scholarship credits."""
    TYPE_CHOICES = [
        ('purchased', 'Purchased'),
        ('promotional', 'Promotional'),
        ('referral', 'Referral'),
        ('scholarship', 'Scholarship'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='credits',
        db_index=True
    )
    cohort = models.ForeignKey(
        'programs.Cohort',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scholarship_credits',
        help_text='When type is scholarship, optional cohort this credit applies to',
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Original credit amount'
    )
    remaining = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Unused credit amount'
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'credits'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'type']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['cohort', 'type']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.type} {self.remaining}/{self.amount}"

    def use_credit(self, amount):
        """Use credit amount and return actual amount used."""
        if self.remaining <= 0:
            return 0

        if self.expires_at and timezone.now() > self.expires_at:
            return 0

        used_amount = min(amount, self.remaining)
        self.remaining -= used_amount
        self.save()
        return used_amount


class Contract(models.Model):
    """Contract entity for institution and employer agreements."""
    TYPE_CHOICES = [
        ('institution', 'Institution'),
        ('employer', 'Employer'),
    ]

    STATUS_CHOICES = [
        ('proposal', 'Proposal'),
        ('negotiation', 'Negotiation'),
        ('signed', 'Signed'),
        ('pending_payments', 'Pending payments'),
        ('active', 'Active'),
        ('renewal', 'Renewal'),
        ('terminated', 'Terminated'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='contracts',
        db_index=True
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='proposal',
        help_text='Current contract lifecycle status.',
    )
    total_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Contract value in USD'
    )
    payment_terms = models.CharField(
        max_length=100,
        default='Net 30',
        help_text='Payment terms (e.g., Net 30)'
    )
    auto_renew = models.BooleanField(default=False)
    renewal_notice_days = models.IntegerField(
        default=60,
        validators=[MinValueValidator(1)],
        help_text='Days notice required for renewal'
    )
    seat_cap = models.PositiveIntegerField(
        default=0,
        help_text='Allocated seat cap: max students (institution) or placements/pipeline slots (employer) under this contract.',
    )
    EMPLOYER_PLAN_CHOICES = [
        ('starter', 'Starter'),
        ('growth', 'Growth'),
        ('enterprise', 'Enterprise'),
        ('custom', 'Custom'),
    ]
    employer_plan = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=EMPLOYER_PLAN_CHOICES,
        help_text='Employer-selected commercial tier during proposal/negotiation.',
    )
    INSTITUTION_PRICING_TIER_CHOICES = [
        ('tier_1_50', '1–50 students ($15/student/mo)'),
        ('tier_51_200', '51–200 students ($12/student/mo)'),
        ('tier_201_500', '201–500 students ($9/student/mo)'),
        ('tier_500_plus', '500+ students ($7/student/mo)'),
    ]
    institution_pricing_tier = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        choices=INSTITUTION_PRICING_TIER_CHOICES,
        help_text='Volume tier for per-student licensing (institution contracts).',
    )
    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
    ]
    billing_cycle = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=BILLING_CYCLE_CHOICES,
        help_text='Institution billing cadence.',
    )
    institution_curriculum = models.JSONField(
        blank=True,
        null=True,
        help_text='Blueprint: mandated tracks, modules, cohort label — visible to director.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'contracts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['type', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.organization.name} - {self.type} - {self.total_value}"

    @property
    def is_active(self):
        """True when within date range, not terminated, and paid (or legacy active with no invoices)."""
        now = timezone.now().date()
        if self.status == 'terminated':
            return False
        if not (self.start_date <= now <= self.end_date):
            return False
        if self.invoices.filter(status='paid').exists():
            return True
        # Legacy rows marked active before invoice workflow
        if self.status == 'active' and not self.invoices.exists():
            return True
        return False

    @property
    def days_until_expiry(self):
        """Calculate days until contract expires."""
        if not self.end_date:
            return None
        delta = self.end_date - timezone.now().date()
        return delta.days if delta.days > 0 else 0


class TaxRate(models.Model):
    """TaxRate entity for multi-region tax management."""
    TYPE_CHOICES = [
        ('VAT', 'VAT'),
        ('GST', 'GST'),
        ('sales_tax', 'Sales Tax'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    country = models.CharField(
        max_length=2,
        help_text='ISO 3166-1 alpha-2 country code'
    )
    region = models.CharField(
        max_length=100,
        blank=True,
        help_text='State/province'
    )
    rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Tax rate as percentage'
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    effective_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tax_rates'
        unique_together = ['country', 'region', 'type']
        indexes = [
            models.Index(fields=['country', 'is_active']),
            models.Index(fields=['effective_date']),
        ]

    def __str__(self):
        region_str = f", {self.region}" if self.region else ""
        return f"{self.country}{region_str} - {self.type} {self.rate}%"

    @classmethod
    def get_tax_rate(cls, country, region=None, tax_type='VAT'):
        """Get applicable tax rate for a location."""
        try:
            return cls.objects.get(
                country=country,
                region=region or '',
                type=tax_type,
                is_active=True
            ).rate
        except cls.DoesNotExist:
            return Decimal('0.00')


class MentorPayout(models.Model):
    """MentorPayout entity for tracking mentor payments."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected'),
    ]

    PAYOUT_METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('paypal', 'PayPal'),
        ('not_applicable', 'Not applicable (volunteer)'),
    ]

    COMPENSATION_MODE_CHOICES = [
        ('paid', 'Paid'),
        ('volunteer', 'Volunteer'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mentor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='mentor_payouts',
        limit_choices_to={'is_mentor': True},
        db_index=True
    )
    cohort = models.ForeignKey(
        'programs.Cohort',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mentor_payouts',
        help_text='Cohort this payout allocation relates to (optional)',
    )
    compensation_mode = models.CharField(
        max_length=20,
        choices=COMPENSATION_MODE_CHOICES,
        default='paid',
        db_index=True,
    )
    allocation_notes = models.TextField(
        blank=True,
        help_text='Cohort-specific allocation notes (hours, stipend rules, etc.)',
    )
    cohort_budget_share_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Share of cohort mentor budget allocated to this line (0–100)',
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    period_start = models.DateField()
    period_end = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payout_method = models.CharField(max_length=20, choices=PAYOUT_METHOD_CHOICES)
    paystack_transfer_id = models.CharField(
        max_length=255,
        blank=True,
        help_text='Paystack transfer ID'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mentor_payouts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['mentor', 'status']),
            models.Index(fields=['period_start', 'period_end']),
            models.Index(fields=['status']),
            models.Index(fields=['cohort', 'compensation_mode']),
        ]

    def __str__(self):
        return f"{self.mentor.email} - {self.amount} ({self.status})"


class ReconciliationRun(models.Model):
    """Snapshot of a book vs bank reconciliation for a period."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    period_start = models.DateField()
    period_end = models.DateField()
    book_total = models.DecimalField(max_digits=15, decimal_places=2)
    bank_total = models.DecimalField(max_digits=15, decimal_places=2)
    difference = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    payment_count = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reconciliation_runs',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reconciliation_runs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['period_start', 'period_end']),
        ]

    def __str__(self):
        return f"Reconciliation {self.period_start}–{self.period_end} (Δ {self.difference})"


class Invoice(models.Model):
    """Enhanced Invoice entity representing billing documents."""
    TYPE_CHOICES = [
        ('subscription', 'Subscription'),
        ('institution', 'Institution'),
        ('employer', 'Employer'),
        ('cohort', 'Cohort'),
        ('contract', 'Contract'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('void', 'Void'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='invoices',
        null=True,
        blank=True,
        help_text='User for individual invoices'
    )
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='invoices',
        null=True,
        blank=True,
        help_text='Organization for institutional invoices'
    )
    contract = models.ForeignKey(
        Contract,
        on_delete=models.SET_NULL,
        related_name='invoices',
        null=True,
        blank=True
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    currency = models.CharField(max_length=3, default='KES')
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Base amount before tax'
    )
    tax = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Amount + tax'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    due_date = models.DateTimeField()
    paid_date = models.DateTimeField(null=True, blank=True)
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        help_text='Formatted invoice number'
    )
    pdf_url = models.URLField(
        blank=True,
        help_text='S3 link to generated PDF'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_invoices'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['type', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['invoice_number']),
        ]

    def __str__(self):
        client = self.organization.name if self.organization else (
            self.user.email if self.user else 'Unknown'
        )
        return f"{self.invoice_number} - {client} - {self.total}"

    def save(self, *args, **kwargs):
        old_status = None
        if self.pk:
            try:
                old_status = (
                    Invoice.objects.filter(pk=self.pk).values_list('status', flat=True).first()
                )
            except Exception:
                old_status = None
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        if not self.total:
            self.total = self.amount + self.tax
        super().save(*args, **kwargs)
        if (
            self.status == 'paid'
            and old_status != 'paid'
            and self.contract_id
        ):
            Contract.objects.filter(
                pk=self.contract_id,
                status__in=['pending_payments', 'proposal', 'negotiation', 'signed'],
            ).update(status='active', updated_at=timezone.now())

    @staticmethod
    def generate_invoice_number():
        """Generate unique invoice number."""
        from datetime import datetime
        year = datetime.now().year
        last_invoice = Invoice.objects.filter(
            invoice_number__startswith=f'INV-{year}-'
        ).order_by('-invoice_number').first()

        if last_invoice:
            last_num = int(last_invoice.invoice_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f'INV-{year}-{new_num:06d}'


class Payment(models.Model):
    """Payment entity recording all payment transactions."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('card', 'Card'),
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Bank Transfer'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    paystack_reference = models.CharField(
        max_length=255,
        blank=True,
        help_text='Paystack transaction ID'
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invoice', 'status']),
            models.Index(fields=['paystack_reference']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Payment {self.amount} for {self.invoice.invoice_number}"


class PricingTier(models.Model):
    """
    Dynamic pricing configuration for institution and employer tiers.
    Allows admin to update pricing without code changes.
    """
    TIER_TYPE_CHOICES = [
        ('institution', 'Institution'),
        ('employer', 'Employer'),
    ]

    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('KES', 'Kenyan Shilling'),
        ('EUR', 'Euro'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=50,
        help_text='Tier identifier (e.g., tier_1_50, starter)'
    )
    display_name = models.CharField(
        max_length=100,
        help_text='Human-readable name for admin interface'
    )
    tier_type = models.CharField(
        max_length=20,
        choices=TIER_TYPE_CHOICES,
        help_text='Whether this is for institution or employer pricing'
    )
    min_quantity = models.PositiveIntegerField(
        default=0,
        help_text='Minimum quantity (students for institution, placements for employer)'
    )
    max_quantity = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Maximum quantity (null for unlimited)'
    )
    price_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Price per unit per month in selected currency'
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='USD',
        help_text='Currency for this pricing tier'
    )
    billing_frequency = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('annual', 'Annual'),
        ],
        default='monthly',
        help_text='Billing frequency for this tier'
    )
    annual_discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Discount percentage for annual billing'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this pricing tier is currently active'
    )
    effective_date = models.DateTimeField(
        default=timezone.now,
        help_text='When this pricing becomes effective'
    )
    expiry_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When this pricing expires (null for no expiry)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pricing_tiers'
        ordering = ['tier_type', 'min_quantity']
        unique_together = [
            ['name', 'tier_type', 'currency'],
        ]
        indexes = [
            models.Index(fields=['tier_type', 'is_active']),
            models.Index(fields=['effective_date', 'expiry_date']),
        ]

    def __str__(self):
        return f"{self.display_name} ({self.tier_type}): {self.price_per_unit} {self.currency}/{self.billing_frequency}"

    @classmethod
    def get_active_tiers(cls, tier_type, currency='USD'):
        """Get all active pricing tiers for a specific type and currency."""
        return cls.objects.filter(
            tier_type=tier_type,
            currency=currency,
            is_active=True,
            effective_date__lte=timezone.now()
        ).filter(
            models.Q(expiry_date__isnull=True) | models.Q(expiry_date__gt=timezone.now())
        ).order_by('min_quantity')

    def calculate_price(self, quantity, billing_frequency='monthly'):
        """Calculate total price for given quantity and billing frequency."""
        base_price = self.price_per_unit * quantity

        if billing_frequency == 'quarterly':
            return base_price * 3
        elif billing_frequency == 'annual':
            annual_price = base_price * 12
            discount = annual_price * (self.annual_discount_percent / 100)
            return annual_price - discount
        else:
            return base_price

    def is_quantity_in_range(self, quantity):
        """Check if quantity falls within this tier's range."""
        if quantity < self.min_quantity:
            return False
        if self.max_quantity is not None and quantity > self.max_quantity:
            return False
        return True


class PricingHistory(models.Model):
    """
    Track pricing changes for audit and historical billing purposes.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pricing_tier = models.ForeignKey(
        PricingTier,
        on_delete=models.CASCADE,
        related_name='history'
    )
    old_price_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    new_price_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    old_annual_discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    new_annual_discount = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )
    change_reason = models.TextField(
        blank=True,
        help_text='Reason for pricing change'
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='pricing_changes'
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pricing_history'
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['pricing_tier', 'changed_at']),
        ]

    def __str__(self):
        return f"Price change for {self.pricing_tier.name} at {self.changed_at}"
