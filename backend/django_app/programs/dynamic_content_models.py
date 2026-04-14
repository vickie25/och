"""
Dynamic Content Selection Models for Cohorts
"""
import uuid

from django.core.validators import MinValueValidator
from django.db import models

from .models import Cohort, Milestone, Module


class CohortContent(models.Model):
    """Dynamic content selection for cohorts - allows directors to pick specific content"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE, related_name='selected_content')
    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE, related_name='cohort_assignments')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='cohort_assignments')

    # Customization options
    is_required = models.BooleanField(default=True, help_text='Whether this content is required for completion')
    custom_order = models.IntegerField(default=0, help_text='Custom ordering within cohort')
    custom_duration_hours = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        help_text='Override default duration for this cohort'
    )
    custom_description = models.TextField(blank=True, help_text='Cohort-specific description override')

    # Scheduling
    scheduled_start_date = models.DateField(null=True, blank=True)
    scheduled_end_date = models.DateField(null=True, blank=True)

    # Tracking
    added_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='added_cohort_content'
    )
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cohort_content'
        unique_together = ['cohort', 'milestone', 'module']
        ordering = ['custom_order', 'milestone__order', 'module__order']
        indexes = [
            models.Index(fields=['cohort', 'custom_order']),
            models.Index(fields=['cohort', 'is_required']),
        ]

    def __str__(self):
        return f"{self.cohort.name} - {self.module.name}"


class CohortContentTemplate(models.Model):
    """Reusable content templates for cohorts"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    track = models.ForeignKey('programs.Track', on_delete=models.CASCADE, related_name='content_templates')

    # Template configuration
    content_selection = models.JSONField(
        default=list,
        help_text='List of selected milestone/module combinations with settings'
    )

    # Metadata
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_content_templates'
    )
    is_default = models.BooleanField(default=False)
    usage_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cohort_content_templates'
        ordering = ['-usage_count', 'name']

    def __str__(self):
        return f"{self.name} ({self.track.name})"


class PaymentSuccessRateTracking(models.Model):
    """Track payment success rates for financial module compliance"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Time period
    date = models.DateField(db_index=True)
    hour = models.IntegerField(null=True, blank=True, help_text='Hour of day for hourly tracking')

    # Metrics
    total_attempts = models.IntegerField(default=0)
    successful_payments = models.IntegerField(default=0)
    failed_payments = models.IntegerField(default=0)
    success_rate_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    # Gateway breakdown
    gateway_breakdown = models.JSONField(
        default=dict,
        help_text='Success rates by payment gateway: {stripe: {success: 10, failed: 1}, paystack: {...}}'
    )

    # Alerts
    below_threshold_alert_sent = models.BooleanField(default=False)
    threshold_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=95.00)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payment_success_rate_tracking'
        unique_together = ['date', 'hour']
        ordering = ['-date', '-hour']
        indexes = [
            models.Index(fields=['date', 'success_rate_percentage']),
            models.Index(fields=['success_rate_percentage']),
        ]

    def __str__(self):
        period = f"{self.date}"
        if self.hour is not None:
            period += f" {self.hour}:00"
        return f"Payment Success Rate {period}: {self.success_rate_percentage}%"


class InvoiceDeliveryTracking(models.Model):
    """Track invoice delivery times for 5-minute SLA compliance"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Invoice reference
    invoice = models.OneToOneField(
        'subscriptions.SubscriptionInvoice',
        on_delete=models.CASCADE,
        related_name='delivery_tracking'
    )

    # Timing
    transaction_completed_at = models.DateTimeField()
    invoice_generated_at = models.DateTimeField()
    invoice_sent_at = models.DateTimeField(null=True, blank=True)

    # Calculated metrics
    generation_time_seconds = models.IntegerField(help_text='Time from transaction to invoice generation')
    delivery_time_seconds = models.IntegerField(null=True, blank=True, help_text='Time from generation to delivery')
    total_time_seconds = models.IntegerField(null=True, blank=True, help_text='Total time from transaction to delivery')

    # SLA compliance
    meets_5min_sla = models.BooleanField(default=False)
    sla_breach_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'invoice_delivery_tracking'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['meets_5min_sla']),
            models.Index(fields=['total_time_seconds']),
            models.Index(fields=['transaction_completed_at']),
        ]

    def __str__(self):
        return f"Invoice {self.invoice.invoice_number} - {self.total_time_seconds}s"


class DunningRecoveryTracking(models.Model):
    """Track dunning management recovery rates for 80% target compliance"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Subscription reference
    subscription = models.ForeignKey(
        'subscriptions.UserSubscription',
        on_delete=models.CASCADE,
        related_name='dunning_tracking'
    )

    # Dunning cycle
    cycle_start_date = models.DateTimeField()
    cycle_end_date = models.DateTimeField(null=True, blank=True)

    # Recovery attempts
    total_attempts = models.IntegerField(default=0)
    email_reminders_sent = models.IntegerField(default=0)
    payment_retries = models.IntegerField(default=0)

    # Outcome
    STATUS_CHOICES = [
        ('active', 'Active Dunning'),
        ('recovered', 'Payment Recovered'),
        ('failed', 'Recovery Failed'),
        ('cancelled', 'Subscription Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    recovered_at = models.DateTimeField(null=True, blank=True)
    recovery_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Timeline tracking
    timeline = models.JSONField(
        default=list,
        help_text='Timeline of dunning actions: [{date, action, result}, ...]'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dunning_recovery_tracking'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['cycle_start_date']),
            models.Index(fields=['recovered_at']),
        ]

    def __str__(self):
        return f"Dunning {self.subscription.user.email} - {self.status}"


class AuditRetentionPolicy(models.Model):
    """7-year audit trail retention policy management"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Policy configuration
    table_name = models.CharField(max_length=100, db_index=True)
    retention_years = models.IntegerField(default=7)

    # Archival settings
    archive_after_years = models.IntegerField(default=3, help_text='Move to cold storage after X years')
    delete_after_years = models.IntegerField(default=7, help_text='Permanently delete after X years')

    # Status tracking
    last_cleanup_date = models.DateTimeField(null=True, blank=True)
    records_archived = models.IntegerField(default=0)
    records_deleted = models.IntegerField(default=0)

    # Compliance
    is_active = models.BooleanField(default=True)
    compliance_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'audit_retention_policies'
        unique_together = ['table_name']
        ordering = ['table_name']

    def __str__(self):
        return f"Retention Policy: {self.table_name} ({self.retention_years} years)"


class PCIComplianceMonitoring(models.Model):
    """PCI compliance violation monitoring"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Violation details
    VIOLATION_TYPES = [
        ('data_storage', 'Unauthorized Card Data Storage'),
        ('transmission', 'Insecure Data Transmission'),
        ('access_control', 'Access Control Violation'),
        ('logging', 'Insufficient Logging'),
        ('encryption', 'Encryption Failure'),
        ('network_security', 'Network Security Issue'),
    ]
    violation_type = models.CharField(max_length=50, choices=VIOLATION_TYPES)
    severity = models.CharField(
        max_length=20,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')],
        default='medium'
    )

    # Detection
    detected_at = models.DateTimeField(auto_now_add=True)
    detection_method = models.CharField(max_length=100, help_text='How violation was detected')

    # Details
    description = models.TextField()
    affected_systems = models.JSONField(default=list)
    potential_impact = models.TextField()

    # Resolution
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('false_positive', 'False Positive'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)

    # Compliance tracking
    reported_to_compliance = models.BooleanField(default=False)
    compliance_ticket_id = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pci_compliance_monitoring'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['status', 'severity']),
            models.Index(fields=['violation_type']),
            models.Index(fields=['detected_at']),
        ]

    def __str__(self):
        return f"PCI Violation: {self.get_violation_type_display()} - {self.severity}"
