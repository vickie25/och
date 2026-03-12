"""
Financial Dashboard URLs - Complete Implementation
URL patterns for all financial dashboard endpoints
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import dashboard_views

# Create router for viewsets
router = DefaultRouter()
router.register(r'dashboards', dashboard_views.FinancialDashboardViewSet, basename='financial-dashboards')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Dashboard endpoints
    path('dashboard/admin/', dashboard_views.FinancialDashboardViewSet.as_view({'get': 'admin_dashboard'}), name='admin-dashboard'),
    path('dashboard/student/', dashboard_views.FinancialDashboardViewSet.as_view({'get': 'student_dashboard'}), name='student-dashboard'),
    path('dashboard/institution/', dashboard_views.FinancialDashboardViewSet.as_view({'get': 'institution_dashboard'}), name='institution-dashboard'),
    path('dashboard/employer/', dashboard_views.FinancialDashboardViewSet.as_view({'get': 'employer_dashboard'}), name='employer-dashboard'),
    
    # Analytics endpoints
    path('analytics/revenue/', dashboard_views.revenue_analytics, name='revenue-analytics'),
    path('analytics/kpis/', dashboard_views.kpi_dashboard, name='kpi-dashboard'),
    path('analytics/kpis/update/', dashboard_views.update_kpis, name='update-kpis'),
    
    # Reporting endpoints
    path('reports/generate/', dashboard_views.generate_report, name='generate-report'),
    
    # Cash flow endpoints
    path('cash-flow/projections/', dashboard_views.cash_flow_projections, name='cash-flow-projections'),
    path('cash-flow/update/', dashboard_views.update_cash_flow_projections, name='update-cash-flow-projections'),
    
    # Alert endpoints
    path('alerts/', dashboard_views.financial_alerts, name='financial-alerts'),
    path('alerts/<uuid:alert_id>/acknowledge/', dashboard_views.acknowledge_alert, name='acknowledge-alert'),
    path('alerts/<uuid:alert_id>/resolve/', dashboard_views.resolve_alert, name='resolve-alert'),
    path('alerts/run-checks/', dashboard_views.run_financial_checks, name='run-financial-checks'),
    
    # Compliance endpoints
    path('compliance/status/', dashboard_views.compliance_status, name='compliance-status'),
    path('compliance/audit-logs/', dashboard_views.audit_logs, name='audit-logs'),
]