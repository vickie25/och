"""
Missions URL configuration
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MissionViewSet, get_sample_mission
from .views_capstone import (
    complete_capstone_phase,
    create_capstone_project,
    get_capstone_project,
    list_user_capstone_projects,
    submit_capstone_project,
    update_capstone_project,
)
from .views_mentorship_interaction import (
    complete_review_phase,
    create_mentorship_interaction,
    get_mentorship_interaction,
    list_mentorship_interactions,
    update_mentorship_interaction,
    upload_feedback_media,
)
from .views_mxp import (
    check_subtask_unlockable,
    enterprise_mission_analytics,
    get_mission_decisions,
    get_mission_hints,
    mission_completion_heatmap,
    mission_performance_analytics,
    record_decision,
    submit_reflection,
    track_time_stage,
    track_tool_usage,
)
from .views_student import (
    complete_subtask,
    get_mission_detail,
    get_mission_funnel,
    get_mission_progress,
    list_student_missions,
    save_mission_draft,
    start_mission_student,
    submit_for_mentor_review,
    submit_mission_for_ai,
    upload_mission_artifacts,
)

router = DefaultRouter()
router.register(r'missions', MissionViewSet, basename='mission')

urlpatterns = [
    # Sample mission for Foundations preview
    path('missions/sample', get_sample_mission, name='mission-sample'),

    # Student mission endpoints
    path('student/missions/', list_student_missions, name='student-missions-list'),
    path('student/missions/funnel/', get_mission_funnel, name='student-missions-funnel'),
    path('student/missions/<uuid:mission_id>/', get_mission_detail, name='student-mission-detail'),
    path('student/missions/<uuid:mission_id>/start/', start_mission_student, name='student-mission-start'),
    path('student/missions/<uuid:mission_id>/progress/', get_mission_progress, name='student-mission-progress'),
    path('student/missions/<uuid:mission_id>/submit-ai/', submit_mission_for_ai, name='student-mission-submit-ai'),
    path('student/missions/<uuid:mission_id>/save-draft/', save_mission_draft, name='student-mission-save-draft'),
    path('student/missions/<uuid:mission_id>/subtasks/<int:subtask_index>/complete/', complete_subtask, name='student-mission-complete-subtask'),
    path('student/submissions/<uuid:submission_id>/upload/', upload_mission_artifacts, name='student-mission-upload'),
    path('student/submissions/<uuid:submission_id>/submit-mentor/', submit_for_mentor_review, name='student-mission-submit-mentor'),

    # Mission hints and decision points
    path('missions/<uuid:mission_id>/hints/<int:subtask_id>/', get_mission_hints, name='mission-hints'),
    path('missions/<uuid:mission_id>/decisions/', get_mission_decisions, name='mission-decisions'),
    path('missions/<uuid:mission_id>/decisions/<str:decision_id>/choose/', record_decision, name='mission-record-decision'),

    # Mission progress tracking
    path('mission-progress/<uuid:progress_id>/subtasks/<int:subtask_id>/unlockable/', check_subtask_unlockable, name='mission-subtask-unlockable'),
    path('mission-progress/<uuid:progress_id>/track-time/', track_time_stage, name='mission-track-time'),
    path('mission-progress/<uuid:progress_id>/track-tools/', track_tool_usage, name='mission-track-tools'),
    path('mission-progress/<uuid:progress_id>/reflection/', submit_reflection, name='mission-submit-reflection'),

    # Mission analytics (admin only)
    path('missions/analytics/performance/', mission_performance_analytics, name='mission-performance-analytics'),
    path('missions/analytics/heatmap/', mission_completion_heatmap, name='mission-completion-heatmap'),
    path('missions/analytics/enterprise/', enterprise_mission_analytics, name='enterprise-mission-analytics'),
    path('missions/analytics/enterprise/<uuid:cohort_id>/', enterprise_mission_analytics, name='enterprise-mission-analytics-cohort'),

    # Capstone Project endpoints
    path('capstone-projects/', list_user_capstone_projects, name='capstone-projects-list'),
    path('capstone-projects/<uuid:capstone_id>/', get_capstone_project, name='capstone-project-detail'),
    path('capstone-projects/create/', create_capstone_project, name='capstone-project-create'),
    path('capstone-projects/<uuid:capstone_id>/update/', update_capstone_project, name='capstone-project-update'),
    path('capstone-projects/<uuid:capstone_id>/complete-phase/<str:phase>/', complete_capstone_phase, name='capstone-project-complete-phase'),
    path('capstone-projects/<uuid:capstone_id>/submit/', submit_capstone_project, name='capstone-project-submit'),

    # Mentorship Interaction endpoints
    path('mentorship-interactions/', list_mentorship_interactions, name='mentorship-interactions-list'),
    path('mentorship-interactions/<uuid:interaction_id>/', get_mentorship_interaction, name='mentorship-interaction-detail'),
    path('mentorship-interactions/create/', create_mentorship_interaction, name='mentorship-interaction-create'),
    path('mentorship-interactions/<uuid:interaction_id>/update/', update_mentorship_interaction, name='mentorship-interaction-update'),
    path('mentorship-interactions/<uuid:interaction_id>/complete-phase/', complete_review_phase, name='mentorship-interaction-complete-phase'),
    path('mentorship-interactions/<uuid:interaction_id>/upload-feedback/', upload_feedback_media, name='mentorship-interaction-upload-feedback'),

    # Admin mission management (MissionViewSet)
    path('', include(router.urls)),
]
