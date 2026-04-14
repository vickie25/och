"""
Financial Dashboard Serializers - Complete Implementation
Serializers for all financial dashboard components
"""

from rest_framework import serializers

from .dashboard_models import *
from .models import *


class FinancialDashboardSerializer(serializers.ModelSerializer):
    """Serializer for financial dashboard configuration"""

    class Meta:
        model = FinancialDashboard
        fields = [
            'id', 'dashboard_type', 'configuration', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class RevenueMetricsSerializer(serializers.ModelSerializer):
    """Serializer for revenue metrics"""

    class Meta:
        model = RevenueMetrics
        fields = [
            'id', 'metric_type', 'revenue_stream', 'value', 'currency',
            'period_start', 'period_end', 'calculated_at'
        ]
        read_only_fields = ['id', 'calculated_at']

class FinancialKPISerializer(serializers.ModelSerializer):
    """Serializer for financial KPIs"""
    growth_rate = serializers.ReadOnlyField()
    target_achievement = serializers.ReadOnlyField()

    class Meta:
        model = FinancialKPI
        fields = [
            'id', 'name', 'category', 'current_value', 'target_value',
            'previous_value', 'unit', 'period', 'growth_rate',
            'target_achievement', 'last_updated'
        ]
        read_only_fields = ['id', 'growth_rate', 'target_achievement', 'last_updated']

class FinancialAlertSerializer(serializers.ModelSerializer):
    """Serializer for financial alerts"""
    assigned_to_email = serializers.CharField(source='assigned_to.email', read_only=True)
    acknowledged_by_email = serializers.CharField(source='acknowledged_by.email', read_only=True)
    resolved_by_email = serializers.CharField(source='resolved_by.email', read_only=True)

    class Meta:
        model = FinancialAlert
        fields = [
            'id', 'alert_type', 'severity', 'title', 'description', 'data',
            'status', 'assigned_to', 'assigned_to_email', 'acknowledged_by',
            'acknowledged_by_email', 'resolved_by', 'resolved_by_email',
            'created_at', 'acknowledged_at', 'resolved_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'acknowledged_at', 'resolved_at',
            'assigned_to_email', 'acknowledged_by_email', 'resolved_by_email'
        ]

class CashFlowProjectionSerializer(serializers.ModelSerializer):
    """Serializer for cash flow projections"""

    class Meta:
        model = CashFlowProjection
        fields = [
            'id', 'projection_type', 'period_start', 'period_end',
            'subscription_revenue', 'institution_revenue', 'employer_revenue',
            'cohort_revenue', 'total_revenue', 'mentor_payouts',
            'operational_costs', 'marketing_costs', 'total_expenses',
            'net_cash_flow', 'confidence_score', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'total_revenue', 'total_expenses', 'net_cash_flow',
            'created_at', 'updated_at'
        ]

class FinancialReportSerializer(serializers.ModelSerializer):
    """Serializer for financial reports"""
    generated_by_email = serializers.CharField(source='generated_by.email', read_only=True)

    class Meta:
        model = FinancialReport
        fields = [
            'id', 'report_type', 'title', 'description', 'period_start',
            'period_end', 'filters', 'format', 'status', 'file_url',
            'file_size', 'generated_by', 'generated_by_email', 'is_public',
            'expires_at', 'created_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'status', 'file_url', 'file_size', 'generated_by_email',
            'created_at', 'completed_at'
        ]

class ComplianceRecordSerializer(serializers.ModelSerializer):
    """Serializer for compliance records"""
    reviewed_by_email = serializers.CharField(source='reviewed_by.email', read_only=True)

    class Meta:
        model = ComplianceRecord
        fields = [
            'id', 'compliance_type', 'title', 'description', 'regulation',
            'requirement', 'status', 'evidence_files', 'documentation',
            'reviewed_by', 'reviewed_by_email', 'remediation_plan',
            'remediation_deadline', 'compliance_date', 'next_review_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'reviewed_by_email', 'created_at', 'updated_at'
        ]

class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for audit logs"""
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_email', 'action_type', 'resource_type',
            'resource_id', 'old_values', 'new_values', 'changes_summary',
            'ip_address', 'user_agent', 'session_id', 'metadata', 'created_at'
        ]
        read_only_fields = [
            'id', 'user_email', 'created_at'
        ]

class WalletSerializer(serializers.ModelSerializer):
    """Serializer for user wallets"""

    class Meta:
        model = Wallet
        fields = [
            'id', 'balance', 'currency', 'last_transaction_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'last_transaction_at', 'created_at', 'updated_at'
        ]

class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for wallet transactions"""

    class Meta:
        model = Transaction
        fields = [
            'id', 'type', 'amount', 'description', 'reference_type',
            'reference_id', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class CreditSerializer(serializers.ModelSerializer):
    """Serializer for credits"""

    class Meta:
        model = Credit
        fields = [
            'id', 'type', 'amount', 'remaining', 'expires_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ContractSerializer(serializers.ModelSerializer):
    """Serializer for contracts"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    is_active = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()

    class Meta:
        model = Contract
        fields = [
            'id', 'organization', 'organization_name', 'type', 'start_date',
            'end_date', 'status', 'total_value', 'payment_terms',
            'auto_renew', 'renewal_notice_days', 'is_active',
            'days_until_expiry', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'organization_name', 'is_active', 'days_until_expiry',
            'created_at', 'updated_at'
        ]

class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for invoices"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'user', 'user_email', 'organization', 'organization_name',
            'contract', 'type', 'amount', 'tax', 'total', 'status',
            'due_date', 'paid_date', 'invoice_number', 'pdf_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_email', 'organization_name', 'total',
            'invoice_number', 'pdf_url', 'created_at', 'updated_at'
        ]

class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for payments"""
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'invoice', 'invoice_number', 'amount', 'currency',
            'status', 'paystack_reference', 'payment_method',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'invoice_number', 'created_at', 'updated_at'
        ]

class MentorPayoutSerializer(serializers.ModelSerializer):
    """Serializer for mentor payouts"""
    mentor_email = serializers.CharField(source='mentor.email', read_only=True)

    class Meta:
        model = MentorPayout
        fields = [
            'id', 'mentor', 'mentor_email', 'amount', 'period_start',
            'period_end', 'status', 'payout_method', 'paystack_transfer_id',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'mentor_email', 'created_at', 'updated_at'
        ]

class TaxRateSerializer(serializers.ModelSerializer):
    """Serializer for tax rates"""

    class Meta:
        model = TaxRate
        fields = [
            'id', 'country', 'region', 'rate', 'type', 'is_active',
            'effective_date', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

# Dashboard-specific serializers for complex data structures

class AdminDashboardSerializer(serializers.Serializer):
    """Serializer for admin dashboard data"""
    revenue_metrics = serializers.DictField()
    kpis = serializers.ListField()
    alerts = serializers.ListField()
    cash_flow = serializers.DictField(allow_null=True)
    last_updated = serializers.DateTimeField()

class StudentDashboardSerializer(serializers.Serializer):
    """Serializer for student dashboard data"""
    subscription = serializers.DictField(allow_null=True)
    wallet = serializers.DictField(allow_null=True)
    enrollments = serializers.ListField()
    payment_history = serializers.ListField()

class InstitutionDashboardSerializer(serializers.Serializer):
    """Serializer for institution dashboard data"""
    organization = serializers.DictField()
    contracts = serializers.ListField()
    enrollment_metrics = serializers.DictField()
    recent_invoices = serializers.ListField()

class EmployerDashboardSerializer(serializers.Serializer):
    """Serializer for employer dashboard data"""
    employer = serializers.DictField()
    job_postings = serializers.ListField()
    recent_interactions = serializers.ListField()

class RevenueAnalyticsSerializer(serializers.Serializer):
    """Serializer for revenue analytics data"""
    revenue_breakdown = serializers.DictField()
    key_metrics = serializers.DictField()
    period = serializers.DictField()

class KPIDashboardSerializer(serializers.Serializer):
    """Serializer for KPI dashboard data"""
    kpis_by_category = serializers.DictField()
    last_updated = serializers.DateTimeField()

class ComplianceStatusSerializer(serializers.Serializer):
    """Serializer for compliance status data"""
    compliance_overview = serializers.DictField()
    recent_records = serializers.ListField()

class AuditLogsResponseSerializer(serializers.Serializer):
    """Serializer for audit logs response"""
    logs = serializers.ListField()
    total_count = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
