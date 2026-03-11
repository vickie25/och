"""
Institutional Billing Models - Stream B Implementation
Contract-based billing for educational institutions with volume pricing.
"""
import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta, date
from dateutil.relativedelta import relativedelta
from users.models import User
from organizations.models import Organization


class InstitutionalContract(models.Model):
    """
    12-month minimum contracts for educational institutions.
    Supports volume-based per-student pricing with automatic renewals.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
        ('pending_renewal', 'Pending Renewal'),
    ]
    
    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract_number = models.CharField(max_length=50, unique=True, db_index=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='institutional_contracts'
    )
    
    # Contract terms
    start_date = models.DateField()
    end_date = models.DateField()  # Minimum 12 months from start
    student_seat_count = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text='Total licensed student seats'
    )
    per_student_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Monthly rate per student based on volume tier'
    )
    billing_cycle = models.CharField(
        max_length=20,
        choices=BILLING_CYCLE_CHOICES,
        default='monthly'
    )
    
    # Contract management
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    auto_renew = models.BooleanField(
        default=True,
        help_text='Auto-renew for additional 12-month terms'
    )
    renewal_notice_days = models.IntegerField(
        default=60,
        help_text='Days notice required for non-renewal'
    )
    early_termination_notice_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date when early termination notice was given'
    )
    
    # Pricing and discounts
    annual_payment_discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('2.50'),
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text='Percentage discount for annual payment'
    )
    custom_discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        help_text='Additional custom discount percentage'
    )
    
    # Contact and billing info
    billing_contact_name = models.CharField(max_length=255)
    billing_contact_email = models.EmailField()
    billing_contact_phone = models.CharField(max_length=50, blank=True)
    billing_address = models.TextField(blank=True)
    purchase_order_required = models.BooleanField(default=False)
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_institutional_contracts'
    )
    signed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='signed_institutional_contracts'
    )
    signed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'institutional_contracts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['status', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.contract_number} - {self.organization.name}"
    
    def save(self, *args, **kwargs):
        if not self.contract_number:
            self.contract_number = self.generate_contract_number()
        if not self.per_student_rate:
            self.per_student_rate = self.calculate_per_student_rate()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_contract_number():
        """Generate unique contract number: INST-2024-001"""
        year = timezone.now().year
        last_contract = InstitutionalContract.objects.filter(
            contract_number__startswith=f'INST-{year}-'
        ).order_by('-contract_number').first()
        
        if last_contract:
            last_num = int(last_contract.contract_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f'INST-{year}-{new_num:03d}'
    
    def calculate_per_student_rate(self):
        """Calculate per-student rate based on volume tiers"""
        if self.student_seat_count <= 50:
            return Decimal('15.00')
        elif self.student_seat_count <= 200:
            return Decimal('12.00')
        elif self.student_seat_count <= 500:
            return Decimal('9.00')
        else:
            return Decimal('7.00')
    
    @property
    def monthly_amount(self):
        """Calculate monthly contract amount"""
        base_amount = self.student_seat_count * self.per_student_rate
        if self.custom_discount > 0:
            discount = base_amount * (self.custom_discount / 100)
            base_amount -= discount
        return base_amount
    
    @property
    def annual_amount(self):
        """Calculate annual contract amount with discount"""
        monthly = self.monthly_amount
        annual = monthly * 12
        if self.billing_cycle == 'annual' and self.annual_payment_discount > 0:
            discount = annual * (self.annual_payment_discount / 100)
            annual -= discount
        return annual
    
    @property
    def is_renewable(self):
        """Check if contract is eligible for renewal"""
        return (
            self.status == 'active' and
            self.end_date - timezone.now().date() <= timedelta(days=self.renewal_notice_days)
        )
    
    @property
    def days_until_expiry(self):
        """Days until contract expires"""
        if self.end_date:
            return (self.end_date - timezone.now().date()).days
        return None
    
    def can_terminate_early(self):
        """Check if early termination is allowed"""
        if not self.early_termination_notice_date:
            return False
        notice_period = timezone.now().date() - self.early_termination_notice_date
        return notice_period.days >= 60
    
    def calculate_early_termination_amount(self):
        """Calculate remaining balance for early termination"""
        if self.status != 'active':
            return Decimal('0.00')
        
        remaining_months = (self.end_date.year - timezone.now().year) * 12 + \
                          (self.end_date.month - timezone.now().month)
        
        if remaining_months <= 0:
            return Decimal('0.00')
        
        return self.monthly_amount * remaining_months
    
    def renew_contract(self, new_seat_count=None, new_billing_cycle=None):
        """Create renewal contract"""
        if not self.is_renewable:
            raise ValueError("Contract is not eligible for renewal")
        
        new_contract = InstitutionalContract.objects.create(
            organization=self.organization,
            start_date=self.end_date + timedelta(days=1),
            end_date=self.end_date + relativedelta(years=1),
            student_seat_count=new_seat_count or self.student_seat_count,
            billing_cycle=new_billing_cycle or self.billing_cycle,
            billing_contact_name=self.billing_contact_name,
            billing_contact_email=self.billing_contact_email,
            billing_contact_phone=self.billing_contact_phone,
            billing_address=self.billing_address,
            purchase_order_required=self.purchase_order_required,
            created_by=self.created_by,
            status='pending_renewal'
        )
        
        return new_contract


class InstitutionalSeatAdjustment(models.Model):
    """
    Track seat count changes during contract period.
    Supports mid-cycle additions/removals with proration.
    """
    ADJUSTMENT_TYPE_CHOICES = [
        ('increase', 'Seat Increase'),
        ('decrease', 'Seat Decrease'),
        ('correction', 'Correction'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(
        InstitutionalContract,
        on_delete=models.CASCADE,
        related_name='seat_adjustments'
    )
    
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPE_CHOICES)
    previous_seat_count = models.IntegerField()
    new_seat_count = models.IntegerField()
    adjustment_amount = models.IntegerField()  # Can be negative
    effective_date = models.DateField()
    
    # Proration calculation
    prorated_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Prorated charge/credit for the adjustment'
    )
    days_in_billing_period = models.IntegerField()
    days_remaining = models.IntegerField()
    
    reason = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'institutional_seat_adjustments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.contract.contract_number} - {self.adjustment_type} ({self.adjustment_amount} seats)"
    
    def save(self, *args, **kwargs):
        if not self.prorated_amount:
            self.prorated_amount = self.calculate_proration()
        super().save(*args, **kwargs)
    
    def calculate_proration(self):
        """Calculate prorated amount for seat adjustment"""
        if not self.days_remaining or not self.days_in_billing_period:
            return Decimal('0.00')
        
        daily_rate = self.contract.per_student_rate / self.days_in_billing_period
        prorated_amount = abs(self.adjustment_amount) * daily_rate * self.days_remaining
        
        # Negative for decreases (credits)
        if self.adjustment_type == 'decrease':
            prorated_amount = -prorated_amount
        
        return prorated_amount


class InstitutionalBilling(models.Model):
    """
    Billing records for institutional contracts.
    Supports monthly, quarterly, and annual billing cycles.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=50, unique=True, db_index=True)
    contract = models.ForeignKey(
        InstitutionalContract,
        on_delete=models.CASCADE,
        related_name='billing_records'
    )
    
    # Billing period
    billing_period_start = models.DateField()
    billing_period_end = models.DateField()
    billing_cycle = models.CharField(max_length=20, choices=InstitutionalContract.BILLING_CYCLE_CHOICES)
    
    # Seat information
    base_seat_count = models.IntegerField()
    active_seat_count = models.IntegerField()  # After adjustments
    seat_adjustments = models.JSONField(
        default=list,
        help_text='List of seat adjustments applied to this billing period'
    )
    
    # Amounts
    base_amount = models.DecimalField(max_digits=12, decimal_places=2)
    adjustment_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Invoice details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    invoice_date = models.DateField(default=date.today)
    due_date = models.DateField()  # Net 30 days
    sent_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Payment information
    payment_method = models.CharField(max_length=50, blank=True)
    payment_reference = models.CharField(max_length=255, blank=True)
    purchase_order_number = models.CharField(max_length=100, blank=True)
    
    # Line items for detailed billing
    line_items = models.JSONField(
        default=list,
        help_text='Detailed breakdown of charges'
    )
    
    # PDF and delivery
    pdf_generated = models.BooleanField(default=False)
    pdf_url = models.URLField(blank=True)
    email_sent = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'institutional_billing'
        ordering = ['-invoice_date']
        indexes = [
            models.Index(fields=['contract', 'status']),
            models.Index(fields=['invoice_date', 'due_date']),
            models.Index(fields=['status', 'due_date']),
        ]
    
    def __str__(self):
        return f"{self.invoice_number} - {self.contract.organization.name}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        if not self.due_date:
            self.due_date = self.invoice_date + timedelta(days=30)
        if not self.total_amount:
            self.calculate_total()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_invoice_number():
        """Generate unique invoice number: INST-INV-2024-001"""
        year = timezone.now().year
        last_invoice = InstitutionalBilling.objects.filter(
            invoice_number__startswith=f'INST-INV-{year}-'
        ).order_by('-invoice_number').first()
        
        if last_invoice:
            last_num = int(last_invoice.invoice_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f'INST-INV-{year}-{new_num:04d}'
    
    def calculate_total(self):
        """Calculate total amount including adjustments, discounts, and tax"""
        self.total_amount = (
            self.base_amount + 
            self.adjustment_amount - 
            self.discount_amount + 
            self.tax_amount
        )
    
    def generate_line_items(self):
        """Generate detailed line items for the invoice"""
        items = []
        
        # Base subscription
        items.append({
            'description': f'Student Licenses ({self.billing_period_start} - {self.billing_period_end})',
            'quantity': self.base_seat_count,
            'unit_price': float(self.contract.per_student_rate),
            'amount': float(self.base_amount),
            'type': 'subscription'
        })
        
        # Seat adjustments
        for adjustment in self.seat_adjustments:
            if adjustment.get('amount', 0) != 0:
                items.append({
                    'description': f"Seat {adjustment['type']} - {adjustment['seats']} seats",
                    'quantity': adjustment['seats'],
                    'unit_price': float(adjustment.get('unit_price', 0)),
                    'amount': float(adjustment['amount']),
                    'type': 'adjustment'
                })
        
        # Discounts
        if self.discount_amount > 0:
            items.append({
                'description': 'Contract Discount',
                'quantity': 1,
                'unit_price': -float(self.discount_amount),
                'amount': -float(self.discount_amount),
                'type': 'discount'
            })
        
        # Tax
        if self.tax_amount > 0:
            items.append({
                'description': 'Tax',
                'quantity': 1,
                'unit_price': float(self.tax_amount),
                'amount': float(self.tax_amount),
                'type': 'tax'
            })
        
        self.line_items = items
        return items
    
    @property
    def is_overdue(self):
        """Check if invoice is overdue"""
        return (
            self.status in ['sent', 'pending'] and
            self.due_date < date.today()
        )
    
    @property
    def days_overdue(self):
        """Calculate days overdue"""
        if self.is_overdue:
            return (date.today() - self.due_date).days
        return 0
    
    def mark_as_paid(self, payment_method=None, payment_reference=None):
        """Mark invoice as paid"""
        self.status = 'paid'
        self.paid_at = timezone.now()
        if payment_method:
            self.payment_method = payment_method
        if payment_reference:
            self.payment_reference = payment_reference
        self.save()
    
    def send_invoice(self):
        """Mark invoice as sent"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.email_sent = True
        self.save()


class InstitutionalStudent(models.Model):
    """
    Track students enrolled under institutional contracts.
    Links individual students to institutional billing.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(
        InstitutionalContract,
        on_delete=models.CASCADE,
        related_name='enrolled_students'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='institutional_enrollments'
    )
    
    # Enrollment details
    enrolled_at = models.DateTimeField(auto_now_add=True)
    enrollment_type = models.CharField(
        max_length=20,
        choices=[
            ('director_enrolled', 'Director Enrolled'),
            ('self_enrolled', 'Self Enrolled'),
            ('bulk_import', 'Bulk Import'),
        ],
        default='director_enrolled'
    )
    
    # Status tracking
    is_active = models.BooleanField(default=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    deactivation_reason = models.TextField(blank=True)
    
    # Billing tracking
    last_billed_period = models.DateField(null=True, blank=True)
    total_billed_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_institutional_students'
    )
    
    class Meta:
        db_table = 'institutional_students'
        unique_together = ['contract', 'user']
        indexes = [
            models.Index(fields=['contract', 'is_active']),
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.contract.contract_number}"
    
    def deactivate(self, reason=""):
        """Deactivate student enrollment"""
        self.is_active = False
        self.deactivated_at = timezone.now()
        self.deactivation_reason = reason
        self.save()
    
    def reactivate(self):
        """Reactivate student enrollment"""
        self.is_active = True
        self.deactivated_at = None
        self.deactivation_reason = ""
        self.save()


class InstitutionalBillingSchedule(models.Model):
    """
    Automated billing schedule for institutional contracts.
    Manages when invoices should be generated.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(
        InstitutionalContract,
        on_delete=models.CASCADE,
        related_name='billing_schedules'
    )
    
    # Schedule details
    next_billing_date = models.DateField()
    billing_period_start = models.DateField()
    billing_period_end = models.DateField()
    
    # Processing status
    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    invoice = models.ForeignKey(
        InstitutionalBilling,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Error handling
    processing_attempts = models.IntegerField(default=0)
    last_error = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'institutional_billing_schedules'
        ordering = ['next_billing_date']
        indexes = [
            models.Index(fields=['next_billing_date', 'is_processed']),
            models.Index(fields=['contract', 'is_processed']),
        ]
    
    def __str__(self):
        return f"{self.contract.contract_number} - {self.next_billing_date}"
    
    @classmethod
    def generate_schedule_for_contract(cls, contract):
        """Generate billing schedule for a contract"""
        schedules = []
        current_date = contract.start_date
        
        while current_date < contract.end_date:
            if contract.billing_cycle == 'monthly':
                period_end = current_date + relativedelta(months=1) - timedelta(days=1)
            elif contract.billing_cycle == 'quarterly':
                period_end = current_date + relativedelta(months=3) - timedelta(days=1)
            else:  # annual
                period_end = current_date + relativedelta(years=1) - timedelta(days=1)
            
            # Don't exceed contract end date
            if period_end > contract.end_date:
                period_end = contract.end_date
            
            schedule = cls.objects.create(
                contract=contract,
                next_billing_date=current_date,
                billing_period_start=current_date,
                billing_period_end=period_end
            )
            schedules.append(schedule)
            
            # Move to next period
            if contract.billing_cycle == 'monthly':
                current_date = current_date + relativedelta(months=1)
            elif contract.billing_cycle == 'quarterly':
                current_date = current_date + relativedelta(months=3)
            else:  # annual
                current_date = current_date + relativedelta(years=1)
        
        return schedules