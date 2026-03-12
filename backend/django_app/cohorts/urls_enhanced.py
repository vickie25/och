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
    path('<uuid:cohort_id>/modules/', module_management_views.get_cohort_modules, name='get_cohort_modules'),
    path('<uuid:cohort_id>/modules/add/', module_management_views.add_cohort_module, name='add_cohort_module'),
    path('<uuid:cohort_id>/modules/<uuid:module_id>/update/', module_management_views.update_cohort_module, name='update_cohort_module'),
    path('<uuid:cohort_id>/modules/<uuid:module_id>/delete/', module_management_views.delete_cohort_module, name='delete_cohort_module'),
    path('<uuid:cohort_id>/modules/reorder/', module_management_views.reorder_cohort_modules, name='reorder_cohort_modules'),
    path('<uuid:cohort_id>/modules/import-track/', module_management_views.import_track_modules, name='import_track_modules'),
    
    # Student materials and progress
    path('materials/', materials_views.get_cohort_materials, name='get_cohort_materials'),
    path('materials/by-day/', materials_views.get_materials_by_day, name='get_materials_by_day'),
    path('materials/start/', materials_views.start_material, name='start_material'),
    path('materials/complete/', materials_views.complete_material, name='complete_material'),
    path('materials/progress/', materials_views.get_progress_summary, name='get_progress_summary'),
    
    # Grades and assessments
    path('grades/', grades_views.get_cohort_grades, name='get_cohort_grades'),
    path('grades/update/', grades_views.update_student_grade, name='update_student_grade'),
    path('exams/', grades_views.get_cohort_exams, name='get_cohort_exams'),
    path('exams/submit/', grades_views.submit_exam, name='submit_exam'),
    
    # Collaboration and messaging
    path('messages/peer/', collaboration_views.send_peer_message, name='send_peer_message'),
    path('messages/mentor/', collaboration_views.send_mentor_message, name='send_mentor_message'),
    path('messages/', collaboration_views.get_cohort_messages, name='get_cohort_messages'),
    
    # Payment processing
    path('payment/initiate/', payment_views.initiate_cohort_payment, name='initiate_cohort_payment'),
    path('payment/verify/', payment_views.verify_cohort_payment, name='verify_cohort_payment'),
    path('payment/status/', payment_views.get_payment_status, name='get_payment_status'),
]