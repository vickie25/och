"""
Coaching OS URL configuration.
"""
from django.urls import path

from .recommendation_views import generate_recommendation
from .usage_views import ai_coach_usage
from .views import (
    ai_coach_chat,
    ai_coach_history,
    ai_coach_message,
    coaching_metrics,
    coaching_sessions_api,
    community_activity,
    goal_detail,
    goals_list,
    habit_detail,
    habit_logs,
    habits_list,
    log_habit,
    mentorship_sessions,
    reflection_detail,
    reflections_list,
    student_analytics,
    user_mission_progress,
    user_recipe_progress,
    user_track_progress,
)
from .welcome_views import generate_welcome_message

urlpatterns = [
    # Habits
    path('habits', habits_list, name='coaching-habits-list'),
    path('habits/<uuid:habit_id>', habit_detail, name='coaching-habit-detail'),
    path('habits/log', log_habit, name='coaching-habit-log'),
    path('habits/<uuid:habit_id>/logs', habit_logs, name='coaching-habit-logs'),

    # Goals
    path('goals', goals_list, name='coaching-goals-list'),
    path('goals/<uuid:goal_id>', goal_detail, name='coaching-goal-detail'),

    # Reflections
    path('reflections', reflections_list, name='coaching-reflections-list'),
    path('reflections/<uuid:reflection_id>', reflection_detail, name='coaching-reflection-detail'),

    # AI Coach
    path('ai-coach/message', ai_coach_message, name='coaching-ai-coach-message'),
    path('ai-coach/chat', ai_coach_chat, name='coaching-ai-coach-chat'),
    path('ai-coach/history', ai_coach_history, name='coaching-ai-coach-history'),
    path('ai-coach/usage', ai_coach_usage, name='coaching-ai-coach-usage'),
    path('ai-coach/welcome', generate_welcome_message, name='coaching-ai-coach-welcome'),
    path('ai-coach/recommendation', generate_recommendation, name='coaching-ai-coach-recommendation'),

    # Metrics
    path('metrics', coaching_metrics, name='coaching-metrics'),

    # Student Analytics (PostgreSQL replacement for Supabase)
    path('student-analytics', student_analytics, name='coaching-student-analytics'),

    # Recipe Progress
    path('recipe-progress', user_recipe_progress, name='coaching-recipe-progress'),

    # Track Progress
    path('track-progress', user_track_progress, name='coaching-track-progress'),

    # Mission Progress
    path('mission-progress', user_mission_progress, name='coaching-mission-progress'),

    # Community Activity
    path('community-activity', community_activity, name='coaching-community-activity'),

    # Mentorship Sessions
    path('mentorship-sessions', mentorship_sessions, name='coaching-mentorship-sessions'),

    # Coaching Sessions
    path('sessions', coaching_sessions_api, name='coaching-sessions'),
]
