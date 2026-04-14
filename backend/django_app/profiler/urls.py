"""
URL configuration for Profiler Engine.
"""
from django.urls import path

from .analytics_views import (
    get_role_mapping_accuracy,
    get_track_acceptance_analytics,
)
from .views import (
    accept_profiler_result,
    admin_adjust_scores,
    admin_reset_profiler,
    approve_retake_request,
    autosave_response,
    check_profiling_required,
    check_tier0_completion,
    complete_profiling,
    complete_section,
    generate_future_you,
    get_cohort_profiler_analytics,
    get_enterprise_profiler_analytics,
    get_future_you_by_mentee,
    get_future_you_insights,
    get_mentee_profiler_results,
    get_profiling_results,
    get_retake_request_status,
    get_value_statement,
    list_retake_requests,
    profiler_status,
    reject_retake_request,
    request_profiler_retake,
    reset_profiling,
    start_profiler,
    submit_answers,
    sync_fastapi_profiling,
    update_section_progress,
)

app_name = 'profiler'

urlpatterns = [
    path('profiler/tier0-status', check_tier0_completion, name='tier0-status'),
    path('profiler/check-required', check_profiling_required, name='check-required'),
    path('profiler/start', start_profiler, name='start'),
    path('profiler/autosave', autosave_response, name='autosave'),
    path('profiler/update-progress', update_section_progress, name='update-progress'),
    path('profiler/complete-section', complete_section, name='complete-section'),
    path('profiler/complete', complete_profiling, name='complete'),
    path('profiler/results', get_profiling_results, name='results'),
    path('profiler/answers', submit_answers, name='answers'),
    path('profiler/future-you', generate_future_you, name='future-you'),
    path('profiler/future-you/insights', get_future_you_insights, name='future-you-insights'),
    path('profiler/status', profiler_status, name='status'),
    path('profiler/mentees/<int:mentee_id>/future-you', get_future_you_by_mentee, name='future-you-by-mentee'),
    path('profiler/mentees/<int:mentee_id>/results', get_mentee_profiler_results, name='mentee-profiler-results'),
    path('profiler/sessions/<uuid:session_id>/accept-result', accept_profiler_result, name='accept-profiler-result'),
    path('profiler/value-statement', get_value_statement, name='value-statement'),
    path('profiler/sync-fastapi', sync_fastapi_profiling, name='sync-fastapi'),
    path('profiler/reset', reset_profiling, name='reset'),

    # Retake request endpoints
    path('profiler/retake-request', request_profiler_retake, name='retake-request'),
    path('profiler/retake-request/status', get_retake_request_status, name='retake-request-status'),

    # Admin retake management endpoints
    path('profiler/admin/retake-requests', list_retake_requests, name='admin-retake-requests'),
    path('profiler/admin/retake-requests/<uuid:request_id>/approve', approve_retake_request, name='approve-retake-request'),
    path('profiler/admin/retake-requests/<uuid:request_id>/reject', reject_retake_request, name='reject-retake-request'),

    # Admin analytics endpoints
    path('profiler/admin/cohorts/<uuid:cohort_id>/analytics', get_cohort_profiler_analytics, name='cohort-profiler-analytics'),
    path('profiler/admin/enterprise/analytics', get_enterprise_profiler_analytics, name='enterprise-profiler-analytics'),

    # Success metrics analytics endpoints
    path('profiler/admin/analytics/acceptance-rate', get_track_acceptance_analytics, name='track-acceptance-analytics'),
    path('profiler/admin/analytics/role-mapping-accuracy', get_role_mapping_accuracy, name='role-mapping-accuracy'),

    # Admin management endpoints
    path('profiler/admin/users/<int:user_id>/reset', admin_reset_profiler, name='admin-reset-profiler'),
    path('profiler/admin/sessions/<uuid:session_id>/adjust-scores', admin_adjust_scores, name='admin-adjust-scores'),
]

