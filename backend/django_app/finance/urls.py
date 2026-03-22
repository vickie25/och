"""
Finance URL patterns.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WalletViewSet, TransactionViewSet, CreditViewSet,
    ContractViewSet, TaxRateViewSet, MentorPayoutViewSet,
    InvoiceViewSet, PaymentViewSet, FinancialDashboardView
)
from .enhanced_views import AnalyticsViewSet, ComplianceViewSet
from .operations_views import (
    ReconciliationPreviewView,
    ReconciliationRunCreateView,
    ReconciliationRunListView,
    RevenueRecognitionRunView,
    CohortManagerFinanceView,
)

router = DefaultRouter()
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'credits', CreditViewSet, basename='credit')
router.register(r'contracts', ContractViewSet, basename='contract')
router.register(r'tax-rates', TaxRateViewSet, basename='taxrate')
router.register(r'mentor-payouts', MentorPayoutViewSet, basename='mentorpayout')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'analytics', AnalyticsViewSet, basename='finance-analytics')
router.register(r'compliance', ComplianceViewSet, basename='finance-compliance')

# NOTE:
# These URLs are intentionally defined WITHOUT the /api/v1 prefix.
# They are included under /api/v1/finance/ from backend/django_app/api/urls.py.
urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', FinancialDashboardView.as_view(), name='financial-dashboard'),
    path('reconciliation/preview/', ReconciliationPreviewView.as_view(), name='finance-reconciliation-preview'),
    path('reconciliation/run/', ReconciliationRunCreateView.as_view(), name='finance-reconciliation-run'),
    path('reconciliation/history/', ReconciliationRunListView.as_view(), name='finance-reconciliation-history'),
    path('revenue/recognize/', RevenueRecognitionRunView.as_view(), name='finance-revenue-recognize'),
    path('cohort-manager/dashboard/', CohortManagerFinanceView.as_view(), name='finance-cohort-manager-dashboard'),
]