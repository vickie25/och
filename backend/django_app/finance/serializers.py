"""
Finance serializers for API responses.
"""
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from organizations.models import Organization
from .models import (
    Wallet, Transaction, Credit, Contract, TaxRate, 
    MentorPayout, Invoice, Payment
)


class WalletSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Wallet
        fields = [
            'id', 'user_email', 'balance', 'currency', 
            'last_transaction_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_transaction_at']


class TransactionSerializer(serializers.ModelSerializer):
    wallet_user = serializers.CharField(source='wallet.user.email', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'wallet_user', 'type', 'amount', 'description',
            'reference_type', 'reference_id', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CreditSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    is_expired = serializers.SerializerMethodField()
    cohort = serializers.UUIDField(source='cohort_id', read_only=True, allow_null=True)

    class Meta:
        model = Credit
        fields = [
            'id', 'user_email', 'type', 'amount', 'remaining',
            'cohort',
            'expires_at', 'is_expired', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_is_expired(self, obj):
        from django.utils import timezone
        return obj.expires_at and timezone.now() > obj.expires_at


class ContractSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(),
        required=False,
        allow_null=True,
    )
    is_active = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    email_sent = serializers.SerializerMethodField()
    
    class Meta:
        model = Contract
        fields = [
            'id', 'organization', 'organization_name', 'type', 'start_date', 'end_date',
            'status', 'total_value', 'payment_terms', 'auto_renew',
            'renewal_notice_days', 'is_active', 'days_until_expiry', 'email_sent',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'total_value': {'required': False},
            'payment_terms': {'required': False},
        }

    def validate(self, attrs):
        if self.instance is None and not attrs.get('organization'):
            raise serializers.ValidationError(
                {'organization': 'This field is required when creating a contract.'}
            )
        return attrs

    def get_email_sent(self, obj):
        # Contract creation requires org contact email for both employer/institution flows.
        return bool(getattr(obj.organization, 'contact_email', None))


class TaxRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxRate
        fields = [
            'id', 'country', 'region', 'rate', 'type',
            'is_active', 'effective_date', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class MentorPayoutSerializer(serializers.ModelSerializer):
    mentor_email = serializers.CharField(source='mentor.email', read_only=True)
    mentor_name = serializers.CharField(source='mentor.get_full_name', read_only=True)
    mentor_id = serializers.IntegerField(source='mentor.id', read_only=True)
    mentor_user_id = serializers.IntegerField(write_only=True, required=False)
    cohort_id = serializers.UUIDField(required=False, allow_null=True)
    cohort_name = serializers.CharField(source='cohort.name', read_only=True, allow_null=True)

    class Meta:
        model = MentorPayout
        fields = [
            'id', 'mentor_id', 'mentor_user_id', 'mentor_email', 'mentor_name',
            'cohort_id', 'cohort_name',
            'compensation_mode', 'allocation_notes', 'cohort_budget_share_percent',
            'amount',
            'period_start', 'period_end', 'status', 'payout_method',
            'paystack_transfer_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'mentor_email', 'mentor_name', 'cohort_name', 'mentor_id']

    def validate(self, attrs):
        mode = attrs.get('compensation_mode')
        if mode is None and self.instance:
            mode = self.instance.compensation_mode
        if mode is None:
            mode = 'paid'
        amount = attrs.get('amount')
        if amount is None and self.instance:
            amount = self.instance.amount
        if mode == 'volunteer' and amount is not None and amount > 0:
            raise serializers.ValidationError('Volunteer payouts must have amount 0.')
        if mode == 'volunteer':
            attrs['amount'] = attrs.get('amount', 0) or 0
            attrs['payout_method'] = attrs.get('payout_method') or 'not_applicable'
        return attrs

    def create(self, validated_data):
        from programs.models import Cohort
        from django.contrib.auth import get_user_model
        User = get_user_model()
        mentor_id = validated_data.pop('mentor_user_id', None)
        cohort_id = validated_data.pop('cohort_id', None)
        request = self.context.get('request')
        if not request or not request.user.is_staff:
            raise PermissionDenied('Only staff can create mentor payout records.')
        if mentor_id is None:
            raise serializers.ValidationError({'mentor_user_id': 'Required for staff-created payouts.'})
        validated_data['mentor'] = User.objects.get(pk=mentor_id)
        if cohort_id:
            validated_data['cohort'] = Cohort.objects.get(pk=cohort_id)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        from programs.models import Cohort
        validated_data.pop('mentor_user_id', None)
        cohort_id = validated_data.pop('cohort_id', None)
        if cohort_id is not None:
            validated_data['cohort'] = Cohort.objects.get(pk=cohort_id) if cohort_id else None
        return super().update(instance, validated_data)


class InvoiceSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    contract_id = serializers.CharField(source='contract.id', read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'user_email', 'organization_name', 'contract_id',
            'type', 'amount', 'tax', 'total', 'status', 'due_date',
            'paid_date', 'invoice_number', 'pdf_url', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'invoice_number', 'created_at', 'updated_at']


class PaymentSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'invoice_number', 'amount', 'currency', 'status',
            'paystack_reference', 'payment_method', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WalletTopUpSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=1)
    description = serializers.CharField(max_length=255, required=False, default="Wallet top-up")


class CreditPurchaseSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=1)
    type = serializers.ChoiceField(choices=Credit.TYPE_CHOICES, default='purchased')
    expires_days = serializers.IntegerField(min_value=1, required=False)