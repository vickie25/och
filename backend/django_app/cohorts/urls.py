"""
Cohorts URL Configuration.
"""
from django.urls import path

from .views import (
    complete_material,
    get_cohort_materials,
    get_cohort_peers,
    get_cohort_rankings,
    get_materials_by_day,
    get_payment_status,
    get_progress_summary,
    get_student_grades,
    initiate_cohort_payment,
    mentor_messages,
    paystack_webhook,
    peer_messages,
    recalculate_grades,
    start_material,
    verify_cohort_payment,
)

app_name = 'cohorts'

urlpatterns = [
    # Payment endpoints
    path('payment/initiate/', initiate_cohort_payment, name='payment-initiate'),
    path('payment/verify/', verify_cohort_payment, name='payment-verify'),
    path('payment/webhook/', paystack_webhook, name='payment-webhook'),
    path('payment/status/', get_payment_status, name='payment-status'),

    # Materials endpoints
    path('materials/', get_cohort_materials, name='materials-list'),
    path('materials/by-day/', get_materials_by_day, name='materials-by-day'),
    path('materials/start/', start_material, name='material-start'),
    path('materials/complete/', complete_material, name='material-complete'),
    path('materials/progress/', get_progress_summary, name='materials-progress'),

    # Grades endpoints
    path('grades/', get_student_grades, name='grades-detail'),
    path('grades/recalculate/', recalculate_grades, name='grades-recalculate'),
    path('grades/rankings/', get_cohort_rankings, name='grades-rankings'),

    # Collaboration endpoints
    path('messages/peers/', peer_messages, name='peer-messages'),
    path('messages/mentors/', mentor_messages, name='mentor-messages'),
    path('peers/', get_cohort_peers, name='cohort-peers'),
]
