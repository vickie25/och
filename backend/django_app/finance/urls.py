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

router = DefaultRouter()
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'credits', CreditViewSet, basename='credit')
router.register(r'contracts', ContractViewSet, basename='contract')
router.register(r'tax-rates', TaxRateViewSet, basename='taxrate')
router.register(r'mentor-payouts', MentorPayoutViewSet, basename='mentorpayout')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = [
    path('api/finance/', include(router.urls)),
    path('api/finance/dashboard/', FinancialDashboardView.as_view(), name='financial-dashboard'),
]