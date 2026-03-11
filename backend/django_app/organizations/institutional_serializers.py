"""
Institutional Billing Serializers - DRF serializers for institutional billing models.
"""
from rest_framework import serializers
from decimal import Decimal
from .institutional_models import (
    InstitutionalContract,
    InstitutionalBilling,
    InstitutionalSeatAdjustment,
    InstitutionalStudent,
    InstitutionalBillingSchedule
)
from .models import Organization
from users.models import User


class InstitutionalContractSerializer(serializers.ModelSerializer):
    """Serializer for InstitutionalContract model"""
    
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    monthly_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    annual_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True)
    is_renewable = serializers.BooleanField(read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    signed_by_name = serializers.CharField(source='signed_by.get_full_name', read_only=True)
    
    class Meta:
        model = InstitutionalContract
        fields = [
            'id', 'contract_number', 'organization', 'organization_name',
            'status', 'start_date', 'end_date', 'student_seat_count',
            'per_student_rate', 'billing_cycle', 'monthly_amount', 'annual_amount',
            'auto_renew', 'renewal_notice_days', 'early_termination_notice_date',
            'annual_payment_discount', 'custom_discount',
            'billing_contact_name', 'billing_contact_email', 'billing_contact_phone',
            'billing_address', 'purchase_order_required',
            'days_until_expiry', 'is_renewable',
            'created_by', 'created_by_name', 'signed_by', 'signed_by_name',
            'signed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'contract_number', 'per_student_rate', 'monthly_amount',
            'annual_amount', 'days_until_expiry', 'is_renewable',
            'created_by', 'signed_by', 'signed_at', 'created_at', 'updated_at'
        ]
    
    def validate_student_seat_count(self, value):
        """Validate seat count is positive"""
        if value < 1:
            raise serializers.ValidationError("Seat count must be at least 1")
        return value
    
    def validate_custom_discount(self, value):
        """Validate custom discount is within reasonable range"""
        if value < 0 or value > 50:
            raise serializers.ValidationError("Custom discount must be between 0% and 50%")
        return value
    
    def validate(self, data):
        """Validate contract dates"""
        if 'start_date' in data and 'end_date' in data:
            if data['end_date'] <= data['start_date']:
                raise serializers.ValidationError("End date must be after start date")
        return data


class InstitutionalSeatAdjustmentSerializer(serializers.ModelSerializer):
    """Serializer for InstitutionalSeatAdjustment model"""
    
    contract_number = serializers.CharField(source='contract.contract_number', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = InstitutionalSeatAdjustment
        fields = [
            'id', 'contract', 'contract_number', 'adjustment_type',
            'previous_seat_count', 'new_seat_count', 'adjustment_amount',
            'effective_date', 'prorated_amount', 'days_in_billing_period',
            'days_remaining', 'reason', 'created_by', 'created_by_name',
            'created_at'
        ]
        read_only_fields = [
            'id', 'prorated_amount', 'created_by', 'created_at'
        ]


class InstitutionalBillingSerializer(serializers.ModelSerializer):
    """Serializer for InstitutionalBilling model"""
    
    contract_number = serializers.CharField(source='contract.contract_number', read_only=True)
    organization_name = serializers.CharField(source='contract.organization.name', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    days_overdue = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = InstitutionalBilling
        fields = [
            'id', 'invoice_number', 'contract', 'contract_number', 'organization_name',
            'billing_period_start', 'billing_period_end', 'billing_cycle',
            'base_seat_count', 'active_seat_count', 'seat_adjustments',
            'base_amount', 'adjustment_amount', 'discount_amount', 'tax_amount',
            'total_amount', 'currency', 'status', 'invoice_date', 'due_date',
            'is_overdue', 'days_overdue', 'sent_at', 'paid_at',
            'payment_method', 'payment_reference', 'purchase_order_number',
            'line_items', 'pdf_generated', 'pdf_url', 'email_sent',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'invoice_number', 'is_overdue', 'days_overdue',
            'pdf_generated', 'email_sent', 'created_at', 'updated_at'
        ]


class InstitutionalStudentSerializer(serializers.ModelSerializer):
    """Serializer for InstitutionalStudent model"""
    
    contract_number = serializers.CharField(source='contract.contract_number', read_only=True)
    organization_name = serializers.CharField(source='contract.organization.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = InstitutionalStudent
        fields = [
            'id', 'contract', 'contract_number', 'organization_name',
            'user', 'user_email', 'user_name', 'enrolled_at', 'enrollment_type',
            'is_active', 'deactivated_at', 'deactivation_reason',
            'last_billed_period', 'total_billed_amount',
            'created_by', 'created_by_name'
        ]
        read_only_fields = [
            'id', 'enrolled_at', 'total_billed_amount', 'created_by'
        ]


class InstitutionalBillingScheduleSerializer(serializers.ModelSerializer):
    """Serializer for InstitutionalBillingSchedule model"""
    
    contract_number = serializers.CharField(source='contract.contract_number', read_only=True)
    organization_name = serializers.CharField(source='contract.organization.name', read_only=True)
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    
    class Meta:
        model = InstitutionalBillingSchedule
        fields = [
            'id', 'contract', 'contract_number', 'organization_name',
            'next_billing_date', 'billing_period_start', 'billing_period_end',
            'is_processed', 'processed_at', 'invoice', 'invoice_number',
            'processing_attempts', 'last_error', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'is_processed', 'processed_at', 'invoice',
            'processing_attempts', 'last_error', 'created_at', 'updated_at'
        ]


class ContractCreateSerializer(serializers.Serializer):
    """Serializer for creating new institutional contracts"""
    
    organization_id = serializers.IntegerField()
    student_seat_count = serializers.IntegerField(min_value=1)
    billing_cycle = serializers.ChoiceField(
        choices=['monthly', 'quarterly', 'annual'],
        default='monthly'
    )
    billing_contact_name = serializers.CharField(max_length=255)
    billing_contact_email = serializers.EmailField()
    billing_contact_phone = serializers.CharField(max_length=50, required=False, allow_blank=True)
    billing_address = serializers.CharField(required=False, allow_blank=True)
    purchase_order_required = serializers.BooleanField(default=False)
    custom_discount = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=0, max_value=50, default=0
    )
    start_date = serializers.DateField(required=False)
    
    def validate_organization_id(self, value):
        """Validate organization exists"""
        try:
            Organization.objects.get(id=value)
        except Organization.DoesNotExist:
            raise serializers.ValidationError("Organization not found")
        return value


class SeatAdjustmentSerializer(serializers.Serializer):
    """Serializer for seat count adjustments"""
    
    new_seat_count = serializers.IntegerField(min_value=1)
    effective_date = serializers.DateField(required=False)
    reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate_new_seat_count(self, value):
        """Validate new seat count is different from current"""
        if hasattr(self, 'context') and 'contract' in self.context:
            contract = self.context['contract']
            if value == contract.student_seat_count:
                raise serializers.ValidationError("New seat count must be different from current count")
        return value


class StudentEnrollmentSerializer(serializers.Serializer):
    """Serializer for enrolling students in contracts"""
    
    user_id = serializers.IntegerField()
    enrollment_type = serializers.ChoiceField(
        choices=['director_enrolled', 'self_enrolled', 'bulk_import'],
        default='director_enrolled'
    )
    
    def validate_user_id(self, value):
        """Validate user exists"""
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
        return value


class PaymentMarkSerializer(serializers.Serializer):
    """Serializer for marking invoices as paid"""
    
    payment_method = serializers.CharField(max_length=50, required=False, allow_blank=True)
    payment_reference = serializers.CharField(max_length=255, required=False, allow_blank=True)
    payment_date = serializers.DateTimeField(required=False)


class ContractAnalyticsSerializer(serializers.Serializer):
    """Serializer for contract analytics data"""
    
    contract_info = serializers.DictField()
    financial = serializers.DictField()
    students = serializers.DictField()
    billing = serializers.DictField()


class RenewalQuoteSerializer(serializers.Serializer):
    """Serializer for contract renewal quotes"""
    
    contract_number = serializers.CharField()
    organization = serializers.CharField()
    current_seats = serializers.IntegerField()
    current_rate = serializers.DecimalField(max_digits=10, decimal_places=2)
    current_monthly = serializers.DecimalField(max_digits=12, decimal_places=2)
    current_annual = serializers.DecimalField(max_digits=12, decimal_places=2)
    proposed_seats = serializers.IntegerField()
    proposed_rate = serializers.DecimalField(max_digits=10, decimal_places=2)
    proposed_monthly = serializers.DecimalField(max_digits=12, decimal_places=2)
    proposed_annual = serializers.DecimalField(max_digits=12, decimal_places=2)
    proposed_cycle = serializers.CharField()
    renewal_start_date = serializers.DateField()
    renewal_end_date = serializers.DateField()
    savings_vs_current = serializers.DecimalField(max_digits=12, decimal_places=2)
    generated_at = serializers.DateTimeField()


class InstitutionalAnalyticsSerializer(serializers.Serializer):
    """Serializer for institutional billing analytics"""
    
    period = serializers.DictField()
    contracts = serializers.DictField()
    revenue = serializers.DictField()
    students = serializers.DictField()
    top_organizations = serializers.ListField()


class BulkStudentEnrollmentSerializer(serializers.Serializer):
    """Serializer for bulk student enrollment"""
    
    contract_id = serializers.UUIDField()
    student_emails = serializers.ListField(
        child=serializers.EmailField(),
        min_length=1,
        max_length=100
    )
    enrollment_type = serializers.ChoiceField(
        choices=['director_enrolled', 'bulk_import'],
        default='bulk_import'
    )
    create_users_if_not_exist = serializers.BooleanField(default=True)
    send_welcome_emails = serializers.BooleanField(default=True)
    
    def validate_contract_id(self, value):
        """Validate contract exists and is active"""
        try:
            contract = InstitutionalContract.objects.get(id=value)
            if contract.status != 'active':
                raise serializers.ValidationError("Contract must be active for enrollment")
        except InstitutionalContract.DoesNotExist:
            raise serializers.ValidationError("Contract not found")
        return value


class ContractRenewalSerializer(serializers.Serializer):
    """Serializer for contract renewals"""
    
    new_seat_count = serializers.IntegerField(min_value=1, required=False)
    new_billing_cycle = serializers.ChoiceField(
        choices=['monthly', 'quarterly', 'annual'],
        required=False
    )
    custom_discount = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=0, max_value=50, required=False
    )
    billing_contact_name = serializers.CharField(max_length=255, required=False)
    billing_contact_email = serializers.EmailField(required=False)
    billing_contact_phone = serializers.CharField(max_length=50, required=False)
    notes = serializers.CharField(required=False, allow_blank=True)