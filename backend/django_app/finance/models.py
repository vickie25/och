"""
Finance models for the Ongoza CyberHub platform.
Implements wallet, credits, contracts, and tax management.
"""
import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='proposal')
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
        """Check if contract is currently active."""
        now = timezone.now().date()
        return (
            self.status == 'active' and
            self.start_date <= now <= self.end_date
        )

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
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mentor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='mentor_payouts',
        limit_choices_to={'is_mentor': True},
        db_index=True
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
        ]

    def __str__(self):
        return f"{self.mentor.email} - {self.amount} ({self.status})"


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
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        if not self.total:
            self.total = self.amount + self.tax
        super().save(*args, **kwargs)

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