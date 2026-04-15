"""
URL configuration for Subscription Engine.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .admin_views import (
    PaymentGatewayViewSet,
    PaymentSettingsViewSet,
    PaymentTransactionViewSet,
    SubscriptionPlanViewSet,
    SubscriptionRuleViewSet,
    UserSubscriptionAdminViewSet,
)
from .views import (
    academic_discount_status,
    apply_academic_discount,
    billing_history,
    cancel_subscription,
    list_plans,
    list_plans_public,
    list_user_subscriptions,
    paystack_config,
    paystack_initialize,
    paystack_verify,
    paystack_webhook,
    promo_code_history,
    retry_attempts_status,
    simulate_payment,
    stripe_webhook,
    subscription_analytics,
    subscription_status,
    upgrade_subscription,
    update_legacy_trial_payment_method,
    schedule_downgrade,
    cancel_scheduled_downgrade,
    validate_promo_code,
)
from .enhanced_billing_views import (
    calculate_pricing_with_discounts as enhanced_calculate_pricing_with_discounts,
    create_enhanced_subscription as enhanced_create_enhanced_subscription,
    schedule_enhanced_downgrade as enhanced_schedule_enhanced_downgrade,
    cancel_enhanced_scheduled_downgrade as enhanced_cancel_enhanced_scheduled_downgrade,
    get_available_plans_with_pricing as enhanced_get_available_plans_with_pricing,
    get_academic_discount_status as enhanced_get_academic_discount_status,
    upload_academic_document as enhanced_upload_academic_document,
    validate_promo_code as enhanced_validate_promo_code,
    verify_academic_email as enhanced_verify_academic_email,
    update_trial_payment_method as enhanced_update_trial_payment_method,
    cancel_enhanced_subscription as enhanced_cancel_enhanced_subscription,
    reactivate_enhanced_subscription as enhanced_reactivate_enhanced_subscription,
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
    path('subscription/payment-method/', update_legacy_trial_payment_method, name='payment-method'),
    path('subscription/payment-method', update_legacy_trial_payment_method, name='payment-method-no-slash'),
    path('subscription/downgrade/', schedule_downgrade, name='downgrade'),
    path('subscription/downgrade', schedule_downgrade, name='downgrade-no-slash'),
    path('subscription/downgrade/cancel/', cancel_scheduled_downgrade, name='downgrade-cancel'),
    path('subscription/downgrade/cancel', cancel_scheduled_downgrade, name='downgrade-cancel-no-slash'),
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

    # ── Promotional Codes ───────────────────────────────────────────────────
    path('subscription/promo-code/validate/', validate_promo_code, name='validate-promo-code'),
    path('subscription/promo-code/validate', validate_promo_code, name='validate-promo-code-no-slash'),
    path('subscription/promo-code/history/', promo_code_history, name='promo-code-history'),
    path('subscription/promo-code/history', promo_code_history, name='promo-code-history-no-slash'),

    # ── Academic Discounts ──────────────────────────────────────────────────
    path('subscription/academic-discount/apply/', apply_academic_discount, name='apply-academic-discount'),
    path('subscription/academic-discount/apply', apply_academic_discount, name='apply-academic-discount-no-slash'),
    path('subscription/academic-discount/status/', academic_discount_status, name='academic-discount-status'),
    path('subscription/academic-discount/status', academic_discount_status, name='academic-discount-status-no-slash'),

    # ── Analytics ────────────────────────────────────────────────────────────
    path('subscription/analytics/', subscription_analytics, name='subscription-analytics'),
    path('subscription/analytics', subscription_analytics, name='subscription-analytics-no-slash'),
    path('subscription/retry-attempts/', retry_attempts_status, name='retry-attempts-status'),
    path('subscription/retry-attempts', retry_attempts_status, name='retry-attempts-status-no-slash'),
    # ── Admin endpoints ──────────────────────────────────────────────────────
    path('', include(admin_router.urls)),

    # ── Enhanced billing (plan-version engine) ───────────────────────────────
    path('enhanced-billing/academic/verify-email/', enhanced_verify_academic_email, name='enhanced-academic-verify-email'),
    path('enhanced-billing/academic/upload-document/', enhanced_upload_academic_document, name='enhanced-academic-upload-document'),
    path('enhanced-billing/academic/status/', enhanced_get_academic_discount_status, name='enhanced-academic-status'),
    path('enhanced-billing/promo/validate/', enhanced_validate_promo_code, name='enhanced-promo-validate'),
    path('enhanced-billing/pricing/calculate/', enhanced_calculate_pricing_with_discounts, name='enhanced-pricing-calculate'),
    path('enhanced-billing/plans/with-pricing/', enhanced_get_available_plans_with_pricing, name='enhanced-plans-with-pricing'),
    path('enhanced-billing/subscription/create-enhanced/', enhanced_create_enhanced_subscription, name='enhanced-subscription-create'),
    path('enhanced-billing/subscription/payment-method/', enhanced_update_trial_payment_method, name='enhanced-subscription-payment-method'),
    path('enhanced-billing/subscription/cancel/', enhanced_cancel_enhanced_subscription, name='enhanced-subscription-cancel'),
    path('enhanced-billing/subscription/reactivate/', enhanced_reactivate_enhanced_subscription, name='enhanced-subscription-reactivate'),
    path('enhanced-billing/subscription/downgrade/', enhanced_schedule_enhanced_downgrade, name='enhanced-subscription-downgrade'),
    path('enhanced-billing/subscription/downgrade/cancel/', enhanced_cancel_enhanced_scheduled_downgrade, name='enhanced-subscription-downgrade-cancel'),
]

