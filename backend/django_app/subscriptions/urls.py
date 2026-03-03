"""
URL configuration for Subscription Engine.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    subscription_status, upgrade_subscription, stripe_webhook, billing_history,
    list_plans, list_plans_public, simulate_payment, cancel_subscription, list_user_subscriptions,
    paystack_config, paystack_initialize, paystack_verify, paystack_webhook,
)
from .admin_views import (
    SubscriptionPlanViewSet, UserSubscriptionAdminViewSet,
    PaymentGatewayViewSet, PaymentTransactionViewSet,
    SubscriptionRuleViewSet, PaymentSettingsViewSet
)

app_name = 'subscriptions'

# Admin router
admin_router = DefaultRouter()
admin_router.register(r'admin/plans', SubscriptionPlanViewSet, basename='admin-plan')
admin_router.register(r'admin/subscriptions', UserSubscriptionAdminViewSet, basename='admin-subscription')
admin_router.register(r'admin/gateways', PaymentGatewayViewSet, basename='admin-gateway')
admin_router.register(r'admin/transactions', PaymentTransactionViewSet, basename='admin-transaction')
admin_router.register(r'admin/rules', SubscriptionRuleViewSet, basename='admin-rule')
admin_router.register(r'admin/settings', PaymentSettingsViewSet, basename='admin-setting')

urlpatterns = [
    # ── User-facing subscription endpoints ──────────────────────────────────
    path('subscription/status/', subscription_status, name='status'),
    path('subscription/status', subscription_status, name='status-no-slash'),
    path('subscription/plans/', list_plans, name='plans'),
    path('subscription/plans', list_plans, name='plans-no-slash'),
    path('subscription/plans/public/', list_plans_public, name='plans-public'),
    path('subscription/plans/public', list_plans_public, name='plans-public-no-slash'),
    path('subscription/users/', list_user_subscriptions, name='user-subscriptions'),
    path('subscription/users', list_user_subscriptions, name='user-subscriptions-no-slash'),
    path('subscription/upgrade/', upgrade_subscription, name='upgrade'),
    path('subscription/upgrade', upgrade_subscription, name='upgrade-no-slash'),
    path('subscription/simulate-payment/', simulate_payment, name='simulate-payment'),
    path('subscription/simulate-payment', simulate_payment, name='simulate-payment-no-slash'),
    path('subscription/cancel/', cancel_subscription, name='cancel'),
    path('subscription/cancel', cancel_subscription, name='cancel-no-slash'),
    path('subscription/billing-history/', billing_history, name='billing-history'),
    path('subscription/billing-history', billing_history, name='billing-history-no-slash'),
    path('subscription/webhooks/stripe/', stripe_webhook, name='stripe-webhook'),
    path('subscription/webhooks/stripe', stripe_webhook, name='stripe-webhook-no-slash'),
    path('subscription/webhooks/paystack/', paystack_webhook, name='paystack-webhook'),
    path('subscription/webhooks/paystack', paystack_webhook, name='paystack-webhook-no-slash'),
    path('subscription/paystack/config/', paystack_config, name='paystack-config'),
    path('subscription/paystack/config', paystack_config, name='paystack-config-no-slash'),
    path('subscription/paystack/initialize/', paystack_initialize, name='paystack-initialize'),
    path('subscription/paystack/initialize', paystack_initialize, name='paystack-initialize-no-slash'),
    path('subscription/paystack/verify/', paystack_verify, name='paystack-verify'),
    path('subscription/paystack/verify', paystack_verify, name='paystack-verify-no-slash'),
    # ── Admin endpoints ──────────────────────────────────────────────────────
    path('', include(admin_router.urls)),
]

