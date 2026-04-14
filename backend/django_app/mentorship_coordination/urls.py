"""
URL configuration for Mentorship Coordination Engine.
"""
from django.urls import path

from .sse_views import mentor_dashboard_stream
from .views import (
    create_flag,
    create_session,
    director_mentor_available,
    director_mentor_conversations,
    director_mentor_message_read,
    director_mentor_messages,
    get_mentor_assignments,
    get_mentorship_assignment,
    get_notifications,
    get_session_feedback,
    get_student_mentor,
    get_student_mentorship_assignments,
    mark_message_read,
    mentee_cockpit,
    mentee_sessions,
    mentor_assigned_cohorts,
    mentor_assignments_list,
    mentor_capstones,
    mentor_cohort_missions,
    mentor_dashboard,
    mentor_feedback_summary,
    mentor_flags,
    mentor_influence_index,
    mentor_mentee_talentscope,
    mentor_mentees,
    mentor_mission_submissions,
    mentor_reviews_list,
    mentor_sessions,
    mentor_workqueue,
    mentorship_registry,
    messages_endpoint,
    request_session,
    review_mission,
    send_notification,
    submit_session_feedback,
    update_group_session,
)

app_name = 'mentorship_coordination'

urlpatterns = [
    # CRITICAL: More specific patterns MUST come first to avoid conflicts
    # The order matters - Django matches patterns in order
    path('mentor-assignments/', mentor_assignments_list, name='mentor-assignments-list'),
    path('mentors/<int:mentor_id>/capstones', mentor_capstones, name='mentor-capstones'),
    path('mentors/<int:mentor_id>/cohorts', mentor_assigned_cohorts, name='mentor-assigned-cohorts'),
    path('mentors/<int:mentor_id>/mentees/<int:mentee_id>/talentscope/', mentor_mentee_talentscope, name='mentor-mentee-talentscope'),
    path('mentors/<int:mentor_id>/mentees/<int:mentee_id>/talentscope', mentor_mentee_talentscope, name='mentor-mentee-talentscope-no-slash'),
    path('mentors/<int:mentor_id>/missions/cohorts', mentor_cohort_missions, name='mentor-cohort-missions'),
    path('mentors/<int:mentor_id>/missions/submissions', mentor_mission_submissions, name='mentor-mission-submissions'),
    path('mentors/<int:mentor_id>/influence', mentor_influence_index, name='mentor-influence'),
    path('mentors/<int:mentor_id>/flags/', mentor_flags, name='mentor-flags-slash'),
    path('mentors/<int:mentor_id>/flags', mentor_flags, name='mentor-flags'),
    path('mentors/<int:mentor_id>/sessions', mentor_sessions, name='mentor-sessions'),
    path('mentors/<int:mentor_id>/mentees', mentor_mentees, name='mentor-mentees'),
    path('mentor/dashboard/stream', mentor_dashboard_stream, name='dashboard-stream'),
    path('mentor/dashboard', mentor_dashboard, name='dashboard'),
    path('mentor/workqueue', mentor_workqueue, name='workqueue'),
    path('mentor/mentees/<int:mentee_id>/cockpit', mentee_cockpit, name='mentee-cockpit'),
    path('mentor/sessions', create_session, name='create-session'),
    path('mentorship/registry', mentorship_registry, name='mentorship-registry'),
    path('mentorship/sessions/request', request_session, name='request-session'),
    path('mentorship/sessions', mentee_sessions, name='mentee-sessions'),
    path('mentors/sessions/<uuid:session_id>', update_group_session, name='update-group-session'),
    path('sessions/<uuid:session_id>/feedback', get_session_feedback, name='get-session-feedback'),  # GET
    path('sessions/<uuid:session_id>/feedback', submit_session_feedback, name='submit-session-feedback'),  # POST (same URL, different method)
    path('mentorship/mentor-reviews', mentor_reviews_list, name='mentor-reviews-list'),
    path('mentors/<int:mentor_id>/feedback-summary', mentor_feedback_summary, name='mentor-feedback-summary'),
    path('mentor/missions/<uuid:submission_id>/review', review_mission, name='review-mission'),
    # Keep old endpoint for backward compatibility
    path('mentor/flags', create_flag, name='create-flag-legacy'),
    # Student mentor endpoints
    path('mentorship/mentees/<int:mentee_id>/mentor', get_student_mentor, name='get-student-mentor'),
    # Support both with and without trailing slash for assignments
    path('mentorship/mentees/<int:mentee_id>/assignments', get_student_mentorship_assignments, name='get-student-assignments'),
    path('mentorship/mentees/<int:mentee_id>/assignments/', get_student_mentorship_assignments, name='get-student-assignments-slash'),
    # Get mentorship assignment
    path('mentorship/assignment', get_mentorship_assignment, name='get-mentorship-assignment'),
    # Get all assignments for a mentor
    path('mentorship/mentors/<int:mentor_id>/assignments', get_mentor_assignments, name='get-mentor-assignments'),
    # Messaging endpoints
    path('mentorship/assignments/<uuid:assignment_id>/messages', messages_endpoint, name='messages-endpoint'),
    path('mentorship/messages/<uuid:message_id>/read', mark_message_read, name='mark-message-read'),
    # Director-mentor messaging
    path('mentorship/director-mentor/conversations', director_mentor_conversations, name='director-mentor-conversations'),
    path('mentorship/director-mentor/available', director_mentor_available, name='director-mentor-available'),
    path('mentorship/director-mentor/messages', director_mentor_messages, name='director-mentor-messages'),
    path('mentorship/director-mentor/messages/<uuid:message_id>/read', director_mentor_message_read, name='director-mentor-message-read'),
    # Notifications endpoints
    path('mentorship/notifications', send_notification, name='send-notification'),
    path('mentorship/users/<int:user_id>/notifications', get_notifications, name='get-notifications'),
]

