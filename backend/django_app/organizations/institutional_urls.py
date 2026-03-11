"""
URL patterns for institutional billing system.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .institutional_views import (
    InstitutionalContractViewSet,
    InstitutionalBillingViewSet,
    institutional_analytics,
    process_scheduled_billing
)

# Create router for viewsets
router = DefaultRouter()
router.register(r'contracts', InstitutionalContractViewSet, basename='institutional-contracts')
router.register(r'billing', InstitutionalBillingViewSet, basename='institutional-billing')

# URL patterns
institutional_urlpatterns = [
    # ViewSet routes
    path('', include(router.urls)),
    
    # Analytics endpoints
    path('analytics/', institutional_analytics, name='institutional-analytics'),
    
    # Administrative endpoints
    path('process-billing/', process_scheduled_billing, name='process-scheduled-billing'),
]

# Add to main organizations URLs
urlpatterns = [
    # Existing organization URLs...
    path('institutional/', include(institutional_urlpatterns)),
]