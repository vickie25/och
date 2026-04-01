"""
Finance serializers for API responses.
"""
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from organizations.models import Organization
from .models import (
    Wallet, Transaction, Credit, Contract, TaxRate, 
    MentorPayout, Invoice, Payment, PricingTier, PricingHistory
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
    seats_used = serializers.SerializerMethodField()
    
    class Meta:
        model = Contract
        fields = [
            'id', 'organization', 'organization_name', 'type', 'start_date', 'end_date',
            'status', 'total_value', 'payment_terms', 'auto_renew',
            'renewal_notice_days', 'seat_cap', 'seats_used', 'employer_plan',
            'institution_pricing_tier', 'billing_cycle', 'institution_curriculum',
            'is_active', 'days_until_expiry', 'email_sent',
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
        if self.instance is None:
            cap = attrs.get('seat_cap', 0)
            if not cap or int(cap) < 1:
                raise serializers.ValidationError(
                    {'seat_cap': 'Allocate at least one seat for this contract (institution students or employer placements).'}
                )
        return attrs

    def get_seats_used(self, obj):
        """Reserved for future enrollment/placement rollups; returns 0 until wired."""
        return 0

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
    amount_paid = serializers.SerializerMethodField()
    amount_remaining = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()
    payments_mapped = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'user_email', 'organization_name', 'contract_id',
            'type', 'amount', 'tax', 'total', 'status', 'due_date',
            'paid_date', 'invoice_number', 'pdf_url',
            'amount_paid', 'amount_remaining', 'payment_status', 'payments_mapped',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'invoice_number', 'created_at', 'updated_at']

    def _success_payments(self, obj):
        return obj.payments.filter(status='success').order_by('created_at', 'id')

    def get_amount_paid(self, obj):
        from decimal import Decimal
        total = Decimal('0')
        for payment in self._success_payments(obj):
            total += payment.amount
        return total

    def get_amount_remaining(self, obj):
        from decimal import Decimal
        paid = self.get_amount_paid(obj)
        remaining = obj.total - paid
        return remaining if remaining > 0 else Decimal('0')

    def get_payment_status(self, obj):
        paid = self.get_amount_paid(obj)
        if paid <= 0:
            return 'unpaid'
        if paid >= obj.total:
            return 'fully_paid'
        return 'partially_paid'

    def get_payments_mapped(self, obj):
        """
        Allocation view of invoice-linked transactions:
        - fully_allocated: entire payment amount consumed by this invoice
        - partially_allocated: part of payment consumed (invoice completed mid-payment)
        - not_allocated: failed/pending or nothing left to allocate
        """
        from decimal import Decimal
        outstanding = obj.total
        rows = []
        all_payments = obj.payments.order_by('created_at', 'id')
        for payment in all_payments:
            allocated = Decimal('0')
            allocation_status = 'not_allocated'
            if payment.status == 'success' and outstanding > 0:
                allocated = payment.amount if payment.amount <= outstanding else outstanding
                outstanding -= allocated
                if allocated == payment.amount and allocated > 0:
                    allocation_status = 'fully_allocated'
                elif allocated > 0:
                    allocation_status = 'partially_allocated'
            rows.append(
                {
                    'id': str(payment.id),
                    'amount': payment.amount,
                    'currency': payment.currency,
                    'status': payment.status,
                    'payment_method': payment.payment_method,
                    'paystack_reference': payment.paystack_reference,
                    'created_at': payment.created_at,
                    'allocated_amount': allocated,
                    'allocation_status': allocation_status,
                }
            )
        return rows


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


class PricingTierSerializer(serializers.ModelSerializer):
    """Serializer for dynamic pricing tiers"""
    
    class Meta:
        model = PricingTier
        fields = [
            'id', 'name', 'display_name', 'tier_type', 'min_quantity', 'max_quantity',
            'price_per_unit', 'currency', 'billing_frequency', 'annual_discount_percent',
            'is_active', 'effective_date', 'expiry_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate pricing tier configuration"""
        min_qty = data.get('min_quantity', 0)
        max_qty = data.get('max_quantity')
        
        if max_qty is not None and min_qty > max_qty:
            raise serializers.ValidationError(
                "min_quantity cannot be greater than max_quantity"
            )
        
        if data.get('annual_discount_percent', 0) < 0 or data.get('annual_discount_percent', 0) > 100:
            raise serializers.ValidationError(
                "annual_discount_percent must be between 0 and 100"
            )
        
        return data


class PricingHistorySerializer(serializers.ModelSerializer):
    """Serializer for pricing change history"""
    pricing_tier_name = serializers.CharField(source='pricing_tier.name', read_only=True)
    pricing_tier_display = serializers.CharField(source='pricing_tier.display_name', read_only=True)
    changed_by_email = serializers.CharField(source='changed_by.email', read_only=True)
    
    class Meta:
        model = PricingHistory
        fields = [
            'id', 'pricing_tier', 'pricing_tier_name', 'pricing_tier_display',
            'old_price_per_unit', 'new_price_per_unit',
            'old_annual_discount', 'new_annual_discount',
            'change_reason', 'changed_by', 'changed_by_email', 'changed_at'
        ]
        read_only_fields = ['id', 'pricing_tier', 'changed_by', 'changed_at']


class PricingUpdateSerializer(serializers.Serializer):
    """Serializer for pricing update requests"""
    price_per_unit = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    annual_discount_percent = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=0, max_value=100, required=False
    )
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_reason(self, value):
        if not value:
            return "Price updated without specific reason"
        return value