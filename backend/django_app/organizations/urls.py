"""
URL configuration for organizations app.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .institutional_management_views import (
    InstitutionalBulkImportViewSet,
    InstitutionalSeatPoolViewSet,
    available_cohorts,
    available_tracks,
    bulk_enroll_students,
    export_student_data,
    institutional_dashboard,
    invite_student,
    manage_cohort_enrollments,
    onboard_student,
    recycle_seats,
    student_progress_report,
    user_portal_access,
)
from .views import OrganizationMemberViewSet, OrganizationViewSet

router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'organization-members', OrganizationMemberViewSet, basename='organization-member')
router.register(r'institutional/seat-pools', InstitutionalSeatPoolViewSet, basename='institutional-seat-pool')
router.register(r'institutional/bulk-imports', InstitutionalBulkImportViewSet, basename='institutional-bulk-import')

urlpatterns = [
    path('', include(router.urls)),
    # Institutional management endpoints
    path('institutional/onboard-student/', onboard_student, name='institutional-onboard-student'),
    path('institutional/invite-student/', invite_student, name='institutional-invite-student'),
    path('institutional/cohorts/<uuid:cohort_id>/enrollments/', manage_cohort_enrollments, name='institutional-cohort-enrollments'),
    path('institutional/bulk-enroll/', bulk_enroll_students, name='institutional-bulk-enroll'),
    path('institutional/available-cohorts/', available_cohorts, name='institutional-available-cohorts'),
    path('institutional/available-tracks/', available_tracks, name='institutional-available-tracks'),
    path('institutional/dashboard/', institutional_dashboard, name='institutional-dashboard'),
    path('institutional/student-progress/', student_progress_report, name='institutional-student-progress'),
    path('institutional/recycle-seats/', recycle_seats, name='institutional-recycle-seats'),
    path('institutional/export-students/', export_student_data, name='institutional-export-students'),
    path('institutional/portal-access/', user_portal_access, name='institutional-portal-access'),
]


