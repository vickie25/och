"""
Finance serializers for API responses.
"""
from rest_framework import serializers
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
    
    class Meta:
        model = Credit
        fields = [
            'id', 'user_email', 'type', 'amount', 'remaining',
            'expires_at', 'is_expired', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_is_expired(self, obj):
        from django.utils import timezone
        return obj.expires_at and timezone.now() > obj.expires_at


class ContractSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    is_active = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    
    class Meta:
        model = Contract
        fields = [
            'id', 'organization_name', 'type', 'start_date', 'end_date',
            'status', 'total_value', 'payment_terms', 'auto_renew',
            'renewal_notice_days', 'is_active', 'days_until_expiry',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


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
    
    class Meta:
        model = MentorPayout
        fields = [
            'id', 'mentor_email', 'mentor_name', 'amount',
            'period_start', 'period_end', 'status', 'payout_method',
            'paystack_transfer_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


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