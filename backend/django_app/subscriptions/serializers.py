"""
Serializers for Subscription Engine.
"""
from decimal import Decimal

from rest_framework import serializers

from .models import SubscriptionPlan, UserSubscription

# Currency conversion rates: 1 KES = rate units of local currency
KES_TO_LOCAL = {
    'KE': 1, 'DZ': 0.12, 'AO': 6.5, 'BJ': 1.9, 'BW': 0.078, 'BF': 1.9, 'BI': 24,
    'CV': 0.65, 'CM': 0.52, 'CF': 0.52, 'TD': 0.52, 'KM': 2.1, 'CG': 0.52, 'CD': 27,
    'CI': 1.9, 'DJ': 1.8, 'EG': 0.19, 'GQ': 0.52, 'ER': 0.05, 'SZ': 0.14, 'ET': 1.5,
    'GA': 0.52, 'GM': 0.13, 'GH': 0.012, 'GN': 0.078, 'GW': 0.078, 'LS': 0.14,
    'LR': 0.006, 'LY': 0.002, 'MG': 0.032, 'MW': 0.11, 'ML': 1.9, 'MR': 0.36,
    'MU': 0.29, 'MA': 0.078, 'MZ': 0.52, 'NA': 0.14, 'NE': 1.9, 'NG': 0.009,
    'RW': 0.77, 'ST': 0.065, 'SN': 1.9, 'SC': 0.58, 'SL': 0.006, 'SO': 0.014,
    'ZA': 0.14, 'SS': 0.025, 'SD': 0.014, 'TZ': 17.8, 'TG': 1.9, 'TN': 0.024,
    'UG': 28.5, 'ZM': 0.12, 'ZW': 0.014,
}

CURRENCY_CODES = {
    'KE': 'KES', 'DZ': 'DZD', 'AO': 'AOA', 'BJ': 'XOF', 'BW': 'BWP', 'BF': 'XOF',
    'BI': 'BIF', 'CV': 'CVE', 'CM': 'XAF', 'CF': 'XAF', 'TD': 'XAF', 'KM': 'KMF',
    'CG': 'XAF', 'CD': 'CDF', 'CI': 'XOF', 'DJ': 'DJF', 'EG': 'EGP', 'GQ': 'XAF',
    'ER': 'ERN', 'SZ': 'SZL', 'ET': 'ETB', 'GA': 'XAF', 'GM': 'GMD', 'GH': 'GHS',
    'GN': 'GNF', 'GW': 'XOF', 'LS': 'LSL', 'LR': 'LRD', 'LY': 'LYD', 'MG': 'MGA',
    'MW': 'MWK', 'ML': 'XOF', 'MR': 'MRU', 'MU': 'MUR', 'MA': 'MAD', 'MZ': 'MZN',
    'NA': 'NAD', 'NE': 'XOF', 'NG': 'NGN', 'RW': 'RWF', 'ST': 'STN', 'SN': 'XOF',
    'SC': 'SCR', 'SL': 'SLE', 'SO': 'SOS', 'ZA': 'ZAR', 'SS': 'SSP', 'SD': 'SDG',
    'TZ': 'TZS', 'TG': 'XOF', 'TN': 'TND', 'UG': 'UGX', 'ZM': 'ZMW', 'ZW': 'ZWL',
}


def convert_kes_to_local(kes_amount, country_code):
    """Convert KES amount to user's local currency."""
    if not kes_amount or not country_code:
        return kes_amount
    code = country_code.upper()
    rate = KES_TO_LOCAL.get(code, 1)
    return round(float(kes_amount) * rate, 2)


def get_currency_code(country_code):
    """Get currency code for a country."""
    if not country_code:
        return 'KES'
    return CURRENCY_CODES.get(country_code.upper(), 'KES')


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serializer for subscription plans."""

    # Allow up to 4 decimal places from the client, then round to 2 for storage.
    price_monthly = serializers.DecimalField(
        max_digits=10,
        decimal_places=4,
        required=False,
        allow_null=True
    )
    price_monthly_local = serializers.SerializerMethodField()
    currency_code = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'tier', 'stream', 'billing_interval', 'sort_order', 'is_listed',
            'price_monthly', 'price_annual', 'price_monthly_local', 'currency_code',
            'catalog',
            'features', 'ai_coach_daily_limit', 'portfolio_item_limit',
            'missions_access_type', 'mentorship_access',
            'talentscope_access', 'marketplace_contact',
            'enhanced_access_days', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    price_annual = serializers.DecimalField(
        max_digits=12,
        decimal_places=4,
        required=False,
        allow_null=True,
    )

    def get_price_monthly_local(self, obj):
        """Convert price to user's local currency."""
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            country = getattr(request.user, 'country', None)
            if country and obj.price_monthly:
                return convert_kes_to_local(obj.price_monthly, country)
        return obj.price_monthly

    def get_currency_code(self, obj):
        """Get currency code for user's country."""
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            country = getattr(request.user, 'country', None)
            if country:
                return get_currency_code(country)
        return 'KES'

    def validate_price_monthly(self, value):
        """
        Accept finer-grained inputs (e.g. 0.0078) but store with 2 decimal places
        to match the underlying DecimalField (decimal_places=2).
        """
        if value is None:
            return None
        # Normalize to two decimal places using standard rounding.
        return value.quantize(Decimal('0.01'))

    def validate_price_annual(self, value):
        if value is None:
            return None
        return value.quantize(Decimal('0.01'))


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for user subscriptions."""
    plan = SubscriptionPlanSerializer(read_only=True)
    plan_id = serializers.UUIDField(write_only=True, required=False)
    user_id = serializers.IntegerField(write_only=True, required=False)
    days_enhanced_left = serializers.IntegerField(read_only=True)
    user = serializers.SerializerMethodField()
    stripe_subscription_id = serializers.CharField(read_only=True)
    price_monthly_local = serializers.SerializerMethodField()
    currency_code = serializers.SerializerMethodField()

    class Meta:
        model = UserSubscription
        fields = [
            'id', 'user', 'user_id', 'plan', 'plan_id', 'status', 'current_period_start',
            'current_period_end', 'enhanced_access_expires_at',
            'billing_interval', 'trial_end', 'cancel_at_period_end', 'grace_period_end',
            'pending_downgrade_plan',
            'days_enhanced_left', 'stripe_subscription_id', 'price_monthly_local',
            'currency_code', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_user(self, obj):
        """Include user details in the response."""
        return {
            'id': str(obj.user.id),
            'email': obj.user.email,
            'username': obj.user.username,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'country': getattr(obj.user, 'country', None),
        }

    def get_price_monthly_local(self, obj):
        """Get monthly price in user's local currency."""
        if obj.plan and obj.plan.price_monthly:
            country = getattr(obj.user, 'country', None)
            if country:
                return convert_kes_to_local(obj.plan.price_monthly, country)
            return float(obj.plan.price_monthly)
        return None

    def get_currency_code(self, obj):
        """Get currency code for user's country."""
        country = getattr(obj.user, 'country', None)
        if country:
            return get_currency_code(country)
        return 'KES'

    def create(self, validated_data):
        """Create subscription with user_id handling."""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user_id = validated_data.pop('user_id', None)
        plan_id = validated_data.pop('plan_id', None)

        if not user_id:
            raise serializers.ValidationError({'user_id': 'This field is required.'})

        if not plan_id:
            raise serializers.ValidationError({'plan_id': 'This field is required.'})

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError({'user_id': 'User not found.'})

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError({'plan_id': 'Plan not found.'})

        # Check if subscription already exists (OneToOneField constraint)
        if UserSubscription.objects.filter(user=user).exists():
            raise serializers.ValidationError({'user_id': 'User already has a subscription.'})

        validated_data['user'] = user
        validated_data['plan'] = plan

        return super().create(validated_data)


class SubscriptionStatusSerializer(serializers.Serializer):
    """Serializer for subscription status response."""
    tier = serializers.CharField()
    days_enhanced_left = serializers.IntegerField(required=False, allow_null=True)
    can_upgrade = serializers.BooleanField()
    features = serializers.ListField(child=serializers.CharField())
    next_payment = serializers.DateTimeField(required=False, allow_null=True)
    status = serializers.CharField()


class UpgradeSubscriptionSerializer(serializers.Serializer):
    """Serializer for upgrading subscription."""
    plan = serializers.CharField(required=True)
    stripe_session_id = serializers.CharField(required=False, allow_null=True)

