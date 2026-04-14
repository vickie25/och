"""
URL configuration for mentorship endpoints.
"""
from django.urls import path

from .views import get_chat_messages, get_mentor_presence, send_chat_message

app_name = 'mentorship'

urlpatterns = [
    path('mentorships/<uuid:mentee_id>/chat', get_chat_messages, name='chat-list'),
    path('mentorships/<uuid:mentee_id>/chat', send_chat_message, name='chat-create'),
    path('mentorships/<uuid:mentee_id>/presence', get_mentor_presence, name='presence'),
]

