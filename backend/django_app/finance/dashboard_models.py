"""
Financial Dashboard Models - Complete Implementation
Supports admin, student, institution, employer, and cohort manager dashboards
"""

import uuid

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

User = get_user_model()

class FinancialDashboard(models.Model):
    """Base dashboard configuration for different user types"""
    DASHBOARD_TYPE_CHOICES = [
        ('admin', 'Admin Dashboard'),
        ('student', 'Student Dashboard'),
        ('institution', 'Institution Dashboard'),
        ('employer', 'Employer Dashboard'),
        ('cohort_manager', 'Cohort Manager Dashboard'),
        ('mentor', 'Mentor Dashboard'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='financial_dashboards')
    dashboard_type = models.CharField(max_length=20, choices=DASHBOARD_TYPE_CHOICES)
    configuration = models.JSONField(
        default=dict,
        help_text='Dashboard widget configuration and preferences'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'financial_dashboards'
        unique_together = ['user', 'dashboard_type']
        indexes = [
            models.Index(fields=['user', 'dashboard_type']),
            models.Index(fields=['dashboard_type', 'is_active'])
        ]

    def __str__(self):
        return f"{self.user.email} - {self.get_dashboard_type_display()}"

class RevenueMetrics(models.Model):
    """Revenue metrics tracking for analytics"""
    METRIC_TYPE_CHOICES = [
        ('mrr', 'Monthly Recurring Revenue'),
        ('arr', 'Annual Recurring Revenue'),
        ('churn_rate', 'Churn Rate'),
        ('ltv', 'Lifetime Value'),
        ('cac', 'Customer Acquisition Cost'),
        ('arpu', 'Average Revenue Per User'),
        ('conversion_rate', 'Trial Conversion Rate'),
    ]

    REVENUE_STREAM_CHOICES = [
        ('subscriptions', 'Student Subscriptions'),
        ('institutions', 'Institution Contracts'),
        ('employers', 'Employer Contracts'),
        ('cohorts', 'Cohort Programs'),
        ('total', 'Total Revenue'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPE_CHOICES)
    revenue_stream = models.CharField(max_length=20, choices=REVENUE_STREAM_CHOICES)
    value = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    period_start = models.DateField()
    period_end = models.DateField()
    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'revenue_metrics'
        unique_together = ['metric_type', 'revenue_stream', 'period_start', 'period_end']
        indexes = [
            models.Index(fields=['metric_type', 'revenue_stream']),
            models.Index(fields=['period_start', 'period_end']),
            models.Index(fields=['calculated_at'])
        ]

    def __str__(self):
        return f"{self.get_metric_type_display()} - {self.get_revenue_stream_display()}: {self.value}"

class FinancialKPI(models.Model):
    """Key Performance Indicators tracking"""
    KPI_CATEGORY_CHOICES = [
        ('revenue', 'Revenue KPIs'),
        ('growth', 'Growth KPIs'),
        ('retention', 'Retention KPIs'),
        ('efficiency', 'Efficiency KPIs'),
        ('profitability', 'Profitability KPIs'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=KPI_CATEGORY_CHOICES)
    current_value = models.DecimalField(max_digits=15, decimal_places=2)
    target_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    previous_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=20, default='currency')  # currency, percentage, count
    period = models.CharField(max_length=20, default='monthly')  # daily, weekly, monthly, quarterly, annual
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'financial_kpis'
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['last_updated'])
        ]

    @property
    def growth_rate(self):
        """Calculate growth rate from previous period"""
        if self.previous_value and self.previous_value > 0:
            return ((self.current_value - self.previous_value) / self.previous_value) * 100
        return 0

    @property
    def target_achievement(self):
        """Calculate target achievement percentage"""
        if self.target_value and self.target_value > 0:
            return (self.current_value / self.target_value) * 100
        return 0

    def __str__(self):
        return f"{self.name}: {self.current_value} {self.unit}"

class FinancialAlert(models.Model):
    """Financial alerts and notifications"""
    ALERT_TYPE_CHOICES = [
        ('revenue_drop', 'Revenue Drop'),
        ('churn_spike', 'Churn Rate Spike'),
        ('payment_failure', 'Payment Failure'),
        ('low_cash_flow', 'Low Cash Flow'),
        ('target_missed', 'Target Missed'),
        ('anomaly_detected', 'Anomaly Detected'),
    ]

    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    data = models.JSONField(default=dict, help_text='Alert-specific data and context')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # Assignment and resolution
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_financial_alerts'
    )
    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_financial_alerts'
    )
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_financial_alerts'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'financial_alerts'
        indexes = [
            models.Index(fields=['alert_type', 'severity']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['assigned_to', 'status'])
        ]

    def __str__(self):
        return f"{self.get_severity_display()} Alert: {self.title}"

class CashFlowProjection(models.Model):
    """Cash flow projections and forecasting"""
    PROJECTION_TYPE_CHOICES = [
        ('weekly', 'Weekly Projection'),
        ('monthly', 'Monthly Projection'),
        ('quarterly', 'Quarterly Projection'),
        ('annual', 'Annual Projection'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    projection_type = models.CharField(max_length=20, choices=PROJECTION_TYPE_CHOICES)
    period_start = models.DateField()
    period_end = models.DateField()

    # Revenue projections by stream
    subscription_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    institution_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    employer_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cohort_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Expense projections
    mentor_payouts = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    operational_costs = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    marketing_costs = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Net cash flow
    net_cash_flow = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Confidence and accuracy
    confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Confidence score 0-100%'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cash_flow_projections'
        unique_together = ['projection_type', 'period_start', 'period_end']
        indexes = [
            models.Index(fields=['projection_type']),
            models.Index(fields=['period_start', 'period_end'])
        ]

    def save(self, *args, **kwargs):
        # Auto-calculate totals
        self.total_revenue = (
            self.subscription_revenue +
            self.institution_revenue +
            self.employer_revenue +
            self.cohort_revenue
        )
        self.total_expenses = (
            self.mentor_payouts +
            self.operational_costs +
            self.marketing_costs
        )
        self.net_cash_flow = self.total_revenue - self.total_expenses
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_projection_type_display()}: {self.period_start} - {self.period_end}"

class FinancialReport(models.Model):
    """Generated financial reports"""
    REPORT_TYPE_CHOICES = [
        ('revenue_summary', 'Revenue Summary'),
        ('subscription_analytics', 'Subscription Analytics'),
        ('cohort_financials', 'Cohort Financials'),
        ('mentor_compensation', 'Mentor Compensation'),
        ('cash_flow', 'Cash Flow Report'),
        ('tax_report', 'Tax Report'),
        ('audit_report', 'Audit Report'),
    ]

    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
    ]

    STATUS_CHOICES = [
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Report parameters
    period_start = models.DateField()
    period_end = models.DateField()
    filters = models.JSONField(default=dict, help_text='Report filters and parameters')

    # Generation details
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='generating')
    file_url = models.URLField(blank=True, help_text='URL to generated report file')
    file_size = models.BigIntegerField(null=True, blank=True, help_text='File size in bytes')

    # Access control
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_reports')
    is_public = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'financial_reports'
        indexes = [
            models.Index(fields=['report_type', 'status']),
            models.Index(fields=['generated_by', 'created_at']),
            models.Index(fields=['period_start', 'period_end'])
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

class ComplianceRecord(models.Model):
    """Compliance and audit records"""
    COMPLIANCE_TYPE_CHOICES = [
        ('tax_filing', 'Tax Filing'),
        ('audit_trail', 'Audit Trail'),
        ('data_retention', 'Data Retention'),
        ('privacy_compliance', 'Privacy Compliance'),
        ('financial_regulation', 'Financial Regulation'),
        ('payment_compliance', 'Payment Compliance'),
    ]

    STATUS_CHOICES = [
        ('compliant', 'Compliant'),
        ('non_compliant', 'Non-Compliant'),
        ('pending_review', 'Pending Review'),
        ('remediation_required', 'Remediation Required'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    compliance_type = models.CharField(max_length=30, choices=COMPLIANCE_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()

    # Compliance details
    regulation = models.CharField(max_length=100, help_text='Regulation or standard name')
    requirement = models.TextField(help_text='Specific requirement being tracked')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES)

    # Evidence and documentation
    evidence_files = models.JSONField(default=list, help_text='List of evidence file URLs')
    documentation = models.TextField(blank=True)

    # Review and remediation
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_compliance_records'
    )
    remediation_plan = models.TextField(blank=True)
    remediation_deadline = models.DateField(null=True, blank=True)

    # Timestamps
    compliance_date = models.DateField()
    next_review_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'compliance_records'
        indexes = [
            models.Index(fields=['compliance_type', 'status']),
            models.Index(fields=['next_review_date']),
            models.Index(fields=['remediation_deadline'])
        ]

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

class AuditLog(models.Model):
    """Comprehensive audit logging for financial operations"""
    ACTION_TYPE_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('subscription_change', 'Subscription Change'),
        ('invoice_generation', 'Invoice Generation'),
        ('report_generation', 'Report Generation'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=30, choices=ACTION_TYPE_CHOICES)
    resource_type = models.CharField(max_length=50, help_text='Model name or resource type')
    resource_id = models.UUIDField(help_text='ID of the affected resource')

    # Change details
    old_values = models.JSONField(default=dict, help_text='Previous values before change')
    new_values = models.JSONField(default=dict, help_text='New values after change')
    changes_summary = models.TextField(help_text='Human-readable summary of changes')

    # Context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=100, blank=True)

    # Metadata
    metadata = models.JSONField(default=dict, help_text='Additional context and metadata')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'financial_audit_logs'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action_type', 'created_at']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['created_at'])
        ]

    def __str__(self):
        user_str = self.user.email if self.user else 'System'
        return f"{user_str} - {self.get_action_type_display()} {self.resource_type}"
