"""
Enhanced Billing Engine Serializers
"""
from rest_framework import serializers

from .billing_engine import (
    BillingPeriod,
    DunningSequence,
    EnhancedSubscription,
    ProrationCredit,
    SubscriptionChange,
    EnhancedSubscriptionInvoice,
    SubscriptionPlanVersion,
)


class SubscriptionPlanVersionSerializer(serializers.ModelSerializer):
    """Serializer for subscription plan versions."""

    class Meta:
        model = SubscriptionPlanVersion
        fields = [
            'id', 'plan_id', 'version', 'name', 'price_monthly', 'price_annual',
            'billing_cycles', 'trial_days', 'tier_access', 'track_access',
            'feature_flags', 'mentorship_credits', 'status', 'regional_pricing',
            'created_at', 'effective_date'
        ]
        read_only_fields = ['id', 'created_at']


class EnhancedSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for enhanced subscriptions."""

    plan_version = SubscriptionPlanVersionSerializer(read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    days_until_period_end = serializers.SerializerMethodField()
    can_reactivate = serializers.SerializerMethodField()

    class Meta:
        model = EnhancedSubscription
        fields = [
            'id', 'user_email', 'plan_version', 'status', 'billing_cycle',
            'cycle_anchor_day', 'current_period_start', 'current_period_end',
            'trial_start', 'trial_end', 'canceled_at', 'cancellation_type',
            'cancel_at_period_end', 'suspended_at', 'reactivation_window_end',
            'reactivation_reminder_last_milestone',
            'days_until_period_end', 'can_reactivate', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_days_until_period_end(self, obj):
        """Calculate days until current period ends."""
        if obj.current_period_end:
            from django.utils import timezone
            delta = obj.current_period_end - timezone.now()
            return max(0, delta.days)
        return None

    def get_can_reactivate(self, obj):
        """Check if subscription can be reactivated."""
        if obj.status != 'SUSPENDED':
            return False
        if not obj.reactivation_window_end:
            return False
        from django.utils import timezone
        return timezone.now() <= obj.reactivation_window_end


class BillingPeriodSerializer(serializers.ModelSerializer):
    """Serializer for billing periods."""

    class Meta:
        model = BillingPeriod
        fields = [
            'id', 'period_start', 'period_end', 'status', 'amount', 'currency',
            'payment_attempted_at', 'payment_completed_at', 'payment_failed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DunningSequenceSerializer(serializers.ModelSerializer):
    """Serializer for dunning sequences."""

    class Meta:
        model = DunningSequence
        fields = [
            'id', 'status', 'retry_schedule', 'current_attempt', 'max_attempts',
            'grace_period_days', 'grace_period_end', 'started_at', 'next_retry_at',
            'completed_at', 'last_notification_sent', 'suspension_warning_sent',
            'final_warning_sent'
        ]
        read_only_fields = ['id', 'started_at']


class SubscriptionChangeSerializer(serializers.ModelSerializer):
    """Serializer for subscription change audit records."""

    created_by_email = serializers.CharField(source='created_by.email', read_only=True)

    class Meta:
        model = SubscriptionChange
        fields = [
            'id', 'change_type', 'old_value', 'new_value', 'proration_credit',
            'proration_charge', 'net_proration', 'reason', 'description',
            'created_by_email', 'created_at', 'ip_address'
        ]
        read_only_fields = ['id', 'created_at']


class ProrationCreditSerializer(serializers.ModelSerializer):
    """Serializer for proration credits."""

    class Meta:
        model = ProrationCredit
        fields = [
            'id', 'amount', 'currency', 'status', 'applied_at',
            'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'created_at']


class SubscriptionInvoiceSerializer(serializers.ModelSerializer):
    """Serializer for subscription invoices."""

    class Meta:
        model = EnhancedSubscriptionInvoice
        fields = [
            'id', 'invoice_number', 'status', 'subtotal', 'discount_amount',
            'tax_amount', 'credit_applied', 'total_amount', 'currency',
            'invoice_date', 'due_date', 'paid_at', 'sent_at', 'line_items',
            'pdf_url', 'pdf_generated_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PlanChangePreviewSerializer(serializers.Serializer):
    """Serializer for plan change preview calculations."""

    new_plan_id = serializers.CharField()

    def validate_new_plan_id(self, value):
        """Validate that the new plan exists and is active."""
        plan = SubscriptionPlanVersion.get_active_plan(value)
        if not plan:
            raise serializers.ValidationError("Plan not found or not available.")
        return value


class CancellationSerializer(serializers.Serializer):
    """Serializer for subscription cancellation requests."""

    type = serializers.ChoiceField(
        choices=['immediate', 'end_of_period'],
        default='end_of_period'
    )
    reason = serializers.CharField(
        max_length=500,
        required=False,
        default='User requested cancellation'
    )


class ReactivationSerializer(serializers.Serializer):
    """Serializer for subscription reactivation requests."""

    payment_method = serializers.CharField(max_length=100)


class PaymentMethodUpdateSerializer(serializers.Serializer):
    """Serializer for payment method updates."""

    payment_method = serializers.CharField(max_length=100)
    gateway = serializers.ChoiceField(
        choices=['stripe', 'paystack'],
        default='stripe'
    )
