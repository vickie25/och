"""
Enhanced Billing URLs - Complete API Endpoints
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import enhanced_views

# Create router for viewsets
router = DefaultRouter()
router.register(r'promo-codes', enhanced_views.PromotionalCodeViewSet, basename='promotional-codes')

urlpatterns = [
    # Include router URLs
    path('admin/', include(router.urls)),

    # Academic Discount Endpoints
    path('academic-discount/', enhanced_views.academic_discount_view, name='academic-discount'),
    path('academic-discount/<uuid:user_id>/', enhanced_views.academic_discount_view, name='academic-discount-user'),
    path('academic-discount/verify/<uuid:discount_id>/', enhanced_views.verify_academic_discount, name='verify-academic-discount'),

    # Promotional Code Endpoints
    path('validate-promo-code/', enhanced_views.validate_promo_code, name='validate-promo-code'),

    # Subscription Management Endpoints
    path('subscription/', enhanced_views.subscription_status, name='subscription-status'),
    path('subscription/<int:user_id>/', enhanced_views.subscription_status, name='subscription-status-user'),
    path('plans/', enhanced_views.available_plans, name='available-plans'),
    path('create-subscription/', enhanced_views.create_subscription, name='create-subscription'),
    path('change-plan/', enhanced_views.change_plan, name='change-plan'),
    path('convert-trial/', enhanced_views.convert_trial, name='convert-trial'),

    # Billing History and Analytics
    path('billing-history/', enhanced_views.billing_history, name='billing-history'),
    path('billing-history/<int:user_id>/', enhanced_views.billing_history, name='billing-history-user'),
    path('analytics/', enhanced_views.billing_analytics, name='billing-analytics'),
]
