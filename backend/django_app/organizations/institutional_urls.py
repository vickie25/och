"""
URL patterns for institutional billing system.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .institutional_views import (
    InstitutionalContractViewSet,
    InstitutionalBillingViewSet,
    InstitutionalStudentViewSet,
    institutional_analytics,
    process_scheduled_billing,
)
from .institutional_management_views import (
    InstitutionalBulkImportViewSet,
    InstitutionalSeatPoolViewSet,
    export_student_data,
    institutional_dashboard,
    recycle_seats,
    student_progress_report,
    user_portal_access,
)
from .institutional_additional_urls import additional_urlpatterns

# Create router for viewsets
router = DefaultRouter()
router.register(r'contracts', InstitutionalContractViewSet, basename='institutional-contracts')
router.register(r'billing', InstitutionalBillingViewSet, basename='institutional-billing')
router.register(r'students', InstitutionalStudentViewSet, basename='institutional-students')

management_router = DefaultRouter()
management_router.register(r'seat-pools', InstitutionalSeatPoolViewSet, basename='institutional-seat-pools')
management_router.register(r'bulk-imports', InstitutionalBulkImportViewSet, basename='institutional-bulk-imports')

# Mounted at /api/v1/institutional/ (see api/urls.py)
urlpatterns = [
    path('', include(router.urls)),
    path('', include(management_router.urls)),
    path('analytics/', institutional_analytics, name='institutional-analytics'),
    path('process-billing/', process_scheduled_billing, name='process-scheduled-billing'),
    path('dashboard/', institutional_dashboard, name='institutional-management-dashboard'),
    path('student-progress/', student_progress_report, name='institutional-student-progress'),
    path('recycle-seats/', recycle_seats, name='institutional-recycle-seats'),
    path('export-students/', export_student_data, name='institutional-export-students'),
    path('portal-access/', user_portal_access, name='institutional-portal-access'),
] + additional_urlpatterns