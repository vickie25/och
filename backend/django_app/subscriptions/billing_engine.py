"""
Complete Billing Engine Implementation
Implements all functional requirements from section 3.1 including:
- Subscription lifecycle state machine
- Billing cycle management with anchor dates
- Proration logic for mid-cycle changes
- Comprehensive dunning management
- Plan versioning and audit trails
"""
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

User = get_user_model()


class SubscriptionPlanVersion(models.Model):
    """Plan versioning system - when plans are modified, new versions are created."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan_id = models.CharField(max_length=50, db_index=True, help_text='Stable plan identifier')
    version = models.IntegerField(default=1, help_text='Version number, increments on changes')

    # Plan Configuration
    name = models.CharField(max_length=100, help_text='Plan display name')
    price_monthly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Monthly price in USD'
    )
    price_annual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text='Annual price in USD (optional)'
    )

    # Billing Configuration
    billing_cycles = models.JSONField(
        default=list,
        help_text='Supported billing cycles: ["monthly", "annual"]'
    )
    trial_days = models.IntegerField(
        default=14,
        validators=[MinValueValidator(0), MaxValueValidator(365)],
        help_text='Trial period length in days'
    )

    # Feature Configuration
    tier_access = models.JSONField(
        default=list,
        help_text='Accessible tiers: ["beginner", "intermediate", "advanced", "mastery"]'
    )
    track_access = models.JSONField(
        default=list,
        help_text='Accessible tracks: ["defender", "grc", "innovation", "leadership", "offensive"]'
    )
    feature_flags = models.JSONField(
        default=dict,
        help_text='Feature access: {"ai_coach": true, "mentorship": false, "portfolio": true}'
    )
    mentorship_credits = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Monthly mentorship credits allocated'
    )

    # Plan Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft - Not visible to users'),
            ('active', 'Active - Available for subscription'),
            ('deprecated', 'Deprecated - No new subscriptions'),
            ('archived', 'Archived - Completely disabled')
        ],
        default='draft',
        db_index=True
    )

    # Regional Pricing (Future)
    regional_pricing = models.JSONField(
        default=dict,
        blank=True,
        help_text='Regional pricing overrides: {"KE": {"monthly": 650}, "NG": {"monthly": 12000}}'
    )

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_plan_versions')
    created_at = models.DateTimeField(auto_now_add=True)
    effective_date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'subscription_plan_versions'
        unique_together = ['plan_id', 'version']
        indexes = [
            models.Index(fields=['plan_id', 'status']),
            models.Index(fields=['status', 'effective_date']),
        ]

    def __str__(self):
        return f"{self.name} v{self.version} ({self.status})"

    @classmethod
    def get_active_plan(cls, plan_id):
        """Get the active version of a plan."""
        return cls.objects.filter(
            plan_id=plan_id,
            status='active'
        ).order_by('-version').first()

    @classmethod
    def create_new_version(cls, plan_id, **plan_data):
        """Create a new version of an existing plan."""
        latest = cls.objects.filter(plan_id=plan_id).order_by('-version').first()
        new_version = latest.version + 1 if latest else 1

        return cls.objects.create(
            plan_id=plan_id,
            version=new_version,
            **plan_data
        )


class EnhancedSubscription(models.Model):
    """
    Enhanced subscription with complete lifecycle state machine.

    Accounting / compliance: subscription and billing history are retained for a minimum of
    seven (7) years after cancellation or expiry (do not hard-delete rows; archive exports only).
    """

    # Complete State Machine as per requirements
    STATUS_CHOICES = [
        ('TRIAL', 'Trial - 7-14 day free trial, no payment required'),
        ('ACTIVE', 'Active - Current billing period paid, full access granted'),
        ('PAST_DUE', 'Past Due - Payment failed, retry in progress'),
        ('SUSPENDED', 'Suspended - All payment retries failed, access restricted'),
        ('CANCELED', 'Canceled - User-initiated cancellation, access continues until period end'),
        ('EXPIRED', 'Expired - Billing period ended or reactivation window closed'),
    ]

    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('annual', 'Annual'),
    ]

    CANCELLATION_TYPE_CHOICES = [
        ('immediate', 'Immediate - Access revoked immediately'),
        ('end_of_period', 'End of Period - Access remains until period end'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='enhanced_subscription',
        db_index=True
    )
    plan_version = models.ForeignKey(
        SubscriptionPlanVersion,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        help_text='Locked to specific plan version'
    )

    # Subscription State
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TRIAL', db_index=True)
    billing_cycle = models.CharField(max_length=10, choices=BILLING_CYCLE_CHOICES, default='monthly')

    # Billing Cycle Management
    cycle_anchor_day = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text='Monthly: calendar day of month (UTC) from signup for renewals; annual: anchor day within month of anniversary'
    )
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()

    # Trial Management
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)

    # Cancellation Management
    canceled_at = models.DateTimeField(null=True, blank=True)
    cancellation_type = models.CharField(
        max_length=20,
        choices=CANCELLATION_TYPE_CHOICES,
        null=True,
        blank=True
    )
    cancel_at_period_end = models.BooleanField(default=False)

    # Scheduled Downgrade (applies at period boundary)
    pending_downgrade_plan_version = models.ForeignKey(
        SubscriptionPlanVersion,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='pending_downgrade_subscriptions',
        help_text='If set, downgrade will apply at period boundary'
    )
    pending_downgrade_effective_at = models.DateTimeField(null=True, blank=True)

    # Suspension and Reactivation
    suspended_at = models.DateTimeField(null=True, blank=True)
    reactivation_window_end = models.DateTimeField(
        null=True,
        blank=True,
        help_text='30-day reactivation window from suspension'
    )
    reactivation_reminder_last_milestone = models.IntegerField(
        default=0,
        help_text='Last reactivation reminder milestone sent (0, 10, 20, or 25 days after suspension)',
    )

    # Payment Gateway Integration
    stripe_subscription_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    paystack_subscription_code = models.CharField(max_length=255, unique=True, null=True, blank=True)

    # Payment Method (for trials that require card-on-file)
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

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'enhanced_subscriptions'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'current_period_end']),
            models.Index(fields=['cycle_anchor_day']),
            models.Index(fields=['reactivation_window_end']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.plan_version.name} ({self.status})"

    def calculate_next_billing_date(self):
        """
        Next cycle end from current_period_end (monthly: same anchor calendar day;
        annual: anniversary of current period end).
        """
        import calendar

        end = self.current_period_end
        if self.billing_cycle == 'monthly':
            y, m = end.year, end.month
            if m == 12:
                y, m = y + 1, 1
            else:
                m += 1
            last_day = calendar.monthrange(y, m)[1]
            return end.replace(year=y, month=m, day=min(self.cycle_anchor_day, last_day))
        try:
            return end.replace(year=end.year + 1)
        except ValueError:
            return end.replace(year=end.year + 1, month=2, day=28)

    def can_transition_to(self, new_status):
        """Check if transition to new status is valid."""
        valid_transitions = {
            'TRIAL': ['ACTIVE', 'EXPIRED'],
            'ACTIVE': ['PAST_DUE', 'CANCELED'],
            'PAST_DUE': ['ACTIVE', 'SUSPENDED'],
            'SUSPENDED': ['ACTIVE', 'EXPIRED'],
            'CANCELED': ['EXPIRED'],
            'EXPIRED': [],  # Terminal state
        }
        return new_status in valid_transitions.get(self.status, [])

    def transition_to(self, new_status, reason=None):
        """Safely transition to new status with validation."""
        if not self.can_transition_to(new_status):
            raise ValueError(f"Cannot transition from {self.status} to {new_status}")

        old_status = self.status
        self.status = new_status

        # Handle status-specific logic
        if new_status == 'SUSPENDED':
            self.suspended_at = timezone.now()
            self.reactivation_window_end = timezone.now() + timedelta(days=30)
            self.reactivation_reminder_last_milestone = 0
        elif new_status == 'ACTIVE' and old_status == 'SUSPENDED':
            self.reactivation_window_end = None
            self.suspended_at = None
            self.reactivation_reminder_last_milestone = 0
        elif new_status == 'CANCELED':
            self.canceled_at = timezone.now()

        self.save()

        # Audit record (reason must be a REASON_CHOICES value; narrative goes in description)
        detail = reason or f'Status changed from {old_status} to {new_status}'
        SubscriptionChange.objects.create(
            subscription=self,
            change_type='status_change',
            old_value=old_status,
            new_value=new_status,
            reason='system_initiated',
            description=detail[:2000] if detail else '',
            created_by=None,
        )

    def calculate_proration_credit(self, new_plan_version):
        """Calculate proration credit for plan changes."""
        if self.status != 'ACTIVE':
            return Decimal('0.00')

        # Calculate remaining days in current period
        now = timezone.now()
        if now >= self.current_period_end:
            return Decimal('0.00')

        total_days = (self.current_period_end - self.current_period_start).days
        remaining_days = (self.current_period_end - now).days

        # Calculate current plan daily cost
        current_price = (
            self.plan_version.price_annual if self.billing_cycle == 'annual'
            else self.plan_version.price_monthly
        )
        daily_cost = current_price / total_days

        # Calculate credit for unused days
        return daily_cost * remaining_days

    def calculate_proration_charge(self, new_plan_version, credit_amount):
        """Calculate proration charge for plan upgrade."""
        if self.status != 'ACTIVE':
            return Decimal('0.00')

        # Calculate remaining days in current period
        now = timezone.now()
        if now >= self.current_period_end:
            return Decimal('0.00')

        total_days = (self.current_period_end - self.current_period_start).days
        remaining_days = (self.current_period_end - now).days

        # Calculate new plan daily cost
        new_price = (
            new_plan_version.price_annual if self.billing_cycle == 'annual'
            else new_plan_version.price_monthly
        )
        new_daily_cost = new_price / total_days

        # Calculate charge for remaining days
        new_period_cost = new_daily_cost * remaining_days

        # Return net charge (new cost - credit)
        return max(Decimal('0.00'), new_period_cost - credit_amount)


class BillingPeriod(models.Model):
    """
    Audit record per billing cycle: period_start, period_end, status, invoice (FK exposes invoice_id).
    """

    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('current', 'Current'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(
        EnhancedSubscription,
        on_delete=models.CASCADE,
        related_name='billing_periods'
    )

    # Period Details
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')

    # Financial Details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')

    # Payment Processing
    payment_attempted_at = models.DateTimeField(null=True, blank=True)
    payment_completed_at = models.DateTimeField(null=True, blank=True)
    payment_failed_at = models.DateTimeField(null=True, blank=True)

    # Invoice Reference (DB column invoice_id — spec §3.1.3)
    invoice = models.ForeignKey(
        'EnhancedSubscriptionInvoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='billing_periods'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'billing_periods'
        indexes = [
            models.Index(fields=['subscription', 'status']),
            models.Index(fields=['period_start', 'period_end']),
            models.Index(fields=['payment_attempted_at']),
        ]

    def __str__(self):
        return f"Billing Period {self.period_start.date()} - {self.period_end.date()} ({self.status})"


class DunningSequence(models.Model):
    """Enhanced dunning management with automated retry sequence."""

    STATUS_CHOICES = [
        ('active', 'Active - Retries in progress'),
        ('paused', 'Paused - Temporarily stopped'),
        ('completed', 'Completed - Payment successful'),
        ('exhausted', 'Exhausted - All retries failed'),
        ('canceled', 'Canceled - Manually stopped'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(
        EnhancedSubscription,
        on_delete=models.CASCADE,
        related_name='dunning_sequences'
    )
    billing_period = models.ForeignKey(
        BillingPeriod,
        on_delete=models.CASCADE,
        related_name='dunning_sequences'
    )

    # Sequence Configuration
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    retry_schedule = models.JSONField(
        default=list,
        help_text='Offsets from first failure (documentation): [0, 3, 7] — immediate, day 3, day 7; next_retry_at is computed in code'
    )
    current_attempt = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)

    # Grace Period Logic
    grace_period_days = models.IntegerField(
        default=3,
        help_text='Grace period days (3 for monthly, 7 for annual)'
    )
    grace_period_end = models.DateTimeField()

    # Timeline
    started_at = models.DateTimeField(auto_now_add=True)
    next_retry_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

    # Notifications
    last_notification_sent = models.DateTimeField(null=True, blank=True)
    suspension_warning_sent = models.BooleanField(default=False)
    final_warning_sent = models.BooleanField(default=False)

    class Meta:
        db_table = 'dunning_sequences'
        indexes = [
            models.Index(fields=['subscription', 'status']),
            models.Index(fields=['next_retry_at', 'status']),
            models.Index(fields=['grace_period_end']),
        ]

    def __str__(self):
        return f"Dunning {self.subscription.user.email} - Attempt {self.current_attempt}/{self.max_attempts}"

    def schedule_next_retry(self):
        """
        §3.1.5: After initial failure, retries at Day 0 (immediate), Day 3, Day 7 from dunning start.
        `current_attempt` is count of completed failed attempts when scheduling the next run.
        """
        if self.current_attempt >= self.max_attempts:
            self.status = 'exhausted'
            self.save(update_fields=['status', 'updated_at'])
            return False

        start = self.started_at
        if self.current_attempt == 1:
            target = start + timedelta(days=3)
        elif self.current_attempt == 2:
            target = start + timedelta(days=7)
        else:
            self.status = 'exhausted'
            self.save(update_fields=['status', 'updated_at'])
            return False

        now = timezone.now()
        if target < now:
            target = now
        self.next_retry_at = target
        self.save(update_fields=['next_retry_at', 'updated_at'])
        return True

    def execute_retry(self):
        """Execute a scheduled retry attempt (§3.1.5). Suspension is enforced day 14 via Celery, not here."""
        from .email_service import SubscriptionEmailService

        self.current_attempt += 1

        success = self._process_payment_retry()

        if success:
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.subscription.transition_to('ACTIVE', 'Payment retry successful')
        else:
            try:
                next_days = None
                if self.current_attempt < self.max_attempts:
                    if self.current_attempt == 1:
                        next_days = 3
                    elif self.current_attempt == 2:
                        next_days = 7
                SubscriptionEmailService.send_payment_failed_notification(
                    self.subscription,
                    retry_attempt=self.current_attempt,
                    next_retry_days=next_days,
                )
            except Exception:
                pass

            if self.current_attempt >= self.max_attempts:
                self.status = 'exhausted'
            else:
                self.schedule_next_retry()

        self.save()
        return success

    def _process_payment_retry(self):
        """Process payment retry via gateway charge."""
        from .billing_services import PaymentProcessor, InvoiceGenerator

        # Create an invoice for the retry attempt (so funds are reflected if paid)
        period_start = timezone.now()
        period_end = self.subscription.calculate_next_billing_date()
        billing_period = BillingPeriod.objects.create(
            subscription=self.subscription,
            period_start=period_start,
            period_end=period_end,
            status='current',
            amount=self.subscription.plan_version.price_monthly if self.subscription.billing_cycle == 'monthly' else self.subscription.plan_version.price_annual,
            currency='USD',
        )
        invoice = InvoiceGenerator.create_subscription_invoice(billing_period)

        billing_period.payment_attempted_at = timezone.now()
        billing_period.save(update_fields=['payment_attempted_at', 'updated_at'])
        success, txn_id, error, _raw = PaymentProcessor.charge_subscription(
            self.subscription,
            amount=invoice.total_amount,
            currency=invoice.currency or 'usd',
            description=f'Dunning retry charge {invoice.invoice_number}',
        )
        if not success:
            billing_period.status = 'failed'
            billing_period.payment_failed_at = timezone.now()
            billing_period.save(update_fields=['status', 'payment_failed_at', 'updated_at'])
            return False

        billing_period.status = 'completed'
        billing_period.payment_completed_at = timezone.now()
        billing_period.save(update_fields=['status', 'payment_completed_at', 'updated_at'])
        invoice.mark_as_paid()
        InvoiceGenerator.send_invoice(invoice)
        return True


class SubscriptionChange(models.Model):
    """
    Audit trail for subscription and plan changes.

    Retention: keep records for at least seven (7) years for financial / compliance review (no hard-delete).
    """

    CHANGE_TYPE_CHOICES = [
        ('plan_change', 'Plan Change'),
        ('status_change', 'Status Change'),
        ('billing_cycle_change', 'Billing Cycle Change'),
        ('cancellation', 'Cancellation'),
        ('reactivation', 'Reactivation'),
        ('trial_conversion', 'Trial Conversion'),
        ('proration_adjustment', 'Proration Adjustment'),
    ]

    REASON_CHOICES = [
        ('user_initiated', 'User Initiated'),
        ('admin_initiated', 'Admin Initiated'),
        ('system_initiated', 'System Initiated'),
        ('payment_failure', 'Payment Failure'),
        ('trial_expiration', 'Trial Expiration'),
        ('dunning_exhausted', 'Dunning Exhausted'),
        ('trial_conversion', 'Trial Conversion'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(
        EnhancedSubscription,
        on_delete=models.CASCADE,
        related_name='change_history'
    )

    # Change Details
    change_type = models.CharField(max_length=30, choices=CHANGE_TYPE_CHOICES)
    old_value = models.TextField(blank=True, help_text='JSON representation of old value')
    new_value = models.TextField(blank=True, help_text='JSON representation of new value')

    # Proration Details (for plan changes)
    proration_credit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Credit amount for unused portion of old plan'
    )
    proration_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Charge amount for new plan prorated period'
    )
    net_proration = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Net amount charged (charge - credit)'
    )

    # Audit Information
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    description = models.TextField(help_text='Detailed description of the change')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscription_changes_made'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Additional Context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = 'subscription_changes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subscription', 'change_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['reason']),
        ]

    def __str__(self):
        return f"{self.subscription.user.email} - {self.get_change_type_display()} - {self.created_at.date()}"


class ProrationCredit(models.Model):
    """Track proration credits for plan changes."""

    STATUS_CHOICES = [
        ('pending', 'Pending Application'),
        ('applied', 'Applied to Invoice'),
        ('carried_forward', 'Carried Forward to Next Period'),
        ('refunded', 'Refunded to Customer'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(
        EnhancedSubscription,
        on_delete=models.CASCADE,
        related_name='proration_credits'
    )
    subscription_change = models.OneToOneField(
        SubscriptionChange,
        on_delete=models.CASCADE,
        related_name='proration_credit_record'
    )

    # Credit Details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Application Details
    applied_to_invoice = models.ForeignKey(
        'EnhancedSubscriptionInvoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applied_credits'
    )
    applied_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Credit expiration date (if applicable)'
    )

    class Meta:
        db_table = 'proration_credits'
        indexes = [
            models.Index(fields=['subscription', 'status']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"Credit ${self.amount} for {self.subscription.user.email} ({self.status})"


class EnhancedSubscriptionInvoice(models.Model):
    """Enhanced invoice model for subscription billing."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('void', 'Void'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(
        EnhancedSubscription,
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    billing_period = models.OneToOneField(
        BillingPeriod,
        on_delete=models.CASCADE,
        related_name='enhanced_invoice'
    )

    # Invoice Details
    invoice_number = models.CharField(max_length=50, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    credit_applied = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')

    # Dates
    invoice_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField()
    paid_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    # Line Items
    line_items = models.JSONField(default=list)

    # PDF Generation
    pdf_url = models.URLField(null=True, blank=True)
    pdf_generated_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'enhanced_subscription_invoices'
        ordering = ['-invoice_date']
        indexes = [
            models.Index(fields=['subscription', 'status']),
            models.Index(fields=['invoice_date']),
            models.Index(fields=['due_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.subscription.user.email} - ${self.total_amount}"

    def apply_proration_credits(self):
        """Apply available proration credits to this invoice."""
        available_credits = ProrationCredit.objects.filter(
            subscription=self.subscription,
            status='pending'
        ).order_by('created_at')

        remaining_amount = self.total_amount
        total_credit_applied = Decimal('0.00')

        for credit in available_credits:
            if remaining_amount <= 0:
                break

            credit_to_apply = min(credit.amount, remaining_amount)
            total_credit_applied += credit_to_apply
            remaining_amount -= credit_to_apply

            # Update credit status
            if credit_to_apply == credit.amount:
                credit.status = 'applied'
            else:
                # Partial application - create new credit for remainder
                ProrationCredit.objects.create(
                    subscription=self.subscription,
                    subscription_change=credit.subscription_change,
                    amount=credit.amount - credit_to_apply,
                    currency=credit.currency,
                    status='pending'
                )
                credit.amount = credit_to_apply
                credit.status = 'applied'

            credit.applied_to_invoice = self
            credit.applied_at = timezone.now()
            credit.save()

        # Update invoice with applied credits
        self.credit_applied = total_credit_applied
        self.total_amount = max(Decimal('0.00'), self.total_amount - total_credit_applied)
        self.save()

        return total_credit_applied

    def mark_as_paid(self):
        self.status = 'paid'
        self.paid_at = timezone.now()
        self.save(update_fields=['status', 'paid_at', 'updated_at'])

    def mark_as_sent(self):
        if self.status == 'draft':
            self.status = 'sent'
            self.sent_at = timezone.now()
            self.save(update_fields=['status', 'sent_at', 'updated_at'])

    @staticmethod
    def generate_invoice_number():
        """Generate unique invoice number."""
        year = datetime.now().year

        # Get last invoice number for this year
        last_invoice = EnhancedSubscriptionInvoice.objects.filter(
            invoice_number__startswith=f'SUB-{year}-'
        ).order_by('-invoice_number').first()

        if last_invoice:
            last_num = int(last_invoice.invoice_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f'SUB-{year}-{new_num:06d}'
