"""
Enhanced Cohort URLs - Complete routing for cohort management.
"""
from django.urls import path
from cohorts.views import (
    materials_views,
    module_management_views,
    enhanced_cohort_views,
    grades_views,
    collaboration_views,
    payment_views
)

urlpatterns = [
    # Student cohort dashboard and status
    path('my-status/', enhanced_cohort_views.get_user_cohort_status, name='user_cohort_status'),
    path('available/', enhanced_cohort_views.get_available_cohorts, name='available_cohorts'),
    path('check-eligibility/', enhanced_cohort_views.check_cohort_eligibility, name='check_cohort_eligibility'),
    path('enroll/', enhanced_cohort_views.enroll_in_cohort, name='enroll_in_cohort'),
    path('dashboard/<uuid:enrollment_id>/', enhanced_cohort_views.get_cohort_dashboard, name='cohort_dashboard'),
    
    # Cohort analytics and management
    path('<uuid:cohort_id>/analytics/', enhanced_cohort_views.get_cohort_analytics, name='cohort_analytics'),
    path('<uuid:cohort_id>/pricing/', enhanced_cohort_views.update_cohort_pricing, name='update_cohort_pricing'),
    
    # Module management (Director/Coordinator)
    path('<uuid:cohort_id>/modules/', module_management_views.cohort_modules_list, name='cohort_modules_list'),
    path('<uuid:cohort_id>/modules/<uuid:module_id>/', module_management_views.cohort_modules_detail, name='cohort_modules_detail'),
    path('<uuid:cohort_id>/modules/reorder/', module_management_views.reorder_cohort_modules, name='reorder_cohort_modules'),
    path('<uuid:cohort_id>/modules/import-track/', module_management_views.import_track_modules, name='import_track_modules'),
    
    # Student materials and progress
    path('materials/', materials_views.get_cohort_materials, name='get_cohort_materials'),
    path('materials/by-day/', materials_views.get_materials_by_day, name='get_materials_by_day'),
    path('materials/start/', materials_views.start_material, name='start_material'),
    path('materials/complete/', materials_views.complete_material, name='complete_material'),
    path('materials/progress/', materials_views.get_progress_summary, name='get_progress_summary'),
    
    # Grades and assessments
    # Student-facing grade endpoints implemented in grades_views
    path('grades/', grades_views.get_student_grades, name='get_student_grades'),
    path('grades/recalculate/', grades_views.recalculate_grades, name='recalculate_grades'),
    path('grades/rankings/', grades_views.get_cohort_rankings, name='get_cohort_rankings'),
    
    # Collaboration and messaging
    path('messages/peers/', collaboration_views.peer_messages, name='peer_messages'),
    path('messages/mentors/', collaboration_views.mentor_messages, name='mentor_messages'),
    path('peers/', collaboration_views.get_cohort_peers, name='get_cohort_peers'),
    
    # Payment processing
    path('payment/initiate/', payment_views.initiate_cohort_payment, name='initiate_cohort_payment'),
    path('payment/verify/', payment_views.verify_cohort_payment, name='verify_cohort_payment'),
    path('payment/status/', payment_views.get_payment_status, name='get_payment_status'),
]