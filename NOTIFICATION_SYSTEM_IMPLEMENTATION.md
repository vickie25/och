# Notification System Implementation

## Overview
Full-stack notification system for in-system and out-system notifications with automatic triggers.

## Backend (Django)

### Files Created:
1. `backend/django_app/notifications/models.py` - Notification & NotificationPreference models
2. `backend/django_app/notifications/views.py` - REST API endpoints
3. `backend/django_app/notifications/serializers.py` - Data serializers
4. `backend/django_app/notifications/urls.py` - URL routing
5. `backend/django_app/notifications/services.py` - Notification creation utilities
6. `backend/django_app/notifications/signals.py` - Auto-trigger on activities
7. `backend/django_app/notifications/apps.py` - App configuration

### API Endpoints:
- `GET /api/v1/notifications/` - List all notifications
- `GET /api/v1/notifications/unread_count` - Get unread count
- `POST /api/v1/notifications/{id}/mark_read/` - Mark as read
- `POST /api/v1/notifications/mark_all_read/` - Mark all as read
- `GET /api/v1/notifications/preferences` - Get user preferences
- `PUT /api/v1/notifications/update_preferences/` - Update preferences

### Auto-Triggers:
- Lesson completed → Notification created
- Mission reviewed → Notification created
- Mentor feedback → Notification created

## Frontend (Next.js)

### Files Created:
1. `frontend/nextjs_app/components/notifications/NotificationBell.tsx` - Bell icon with badge
2. `frontend/nextjs_app/components/notifications/NotificationPanel.tsx` - Dropdown panel
3. `frontend/nextjs_app/services/notificationService.ts` - API client

### Files Modified:
1. `frontend/nextjs_app/components/navigation/Notifications.tsx` - Replaced dummy with real system

### Features:
- Real-time unread count badge
- Dropdown notification panel
- Mark as read (individual & all)
- Click to navigate to action URL
- Priority-based styling (high/medium/low)
- Auto-refresh every 30 seconds

## Setup Instructions

### 1. Add to Django settings:
```python
INSTALLED_APPS = [
    ...
    'notifications',
]
```

### 2. Add to main urls.py:
```python
urlpatterns = [
    ...
    path('api/v1/notifications/', include('notifications.urls')),
]
```

### 3. Run migrations:
```bash
cd backend/django_app
python manage.py makemigrations notifications
python manage.py migrate
```

### 4. Test the system:
```bash
# Backend should be running on port 8000
# Frontend should be running on port 3000
# Navigate to http://localhost:3000/dashboard/student
# Bell icon appears in header with notification count
```

## Usage Examples

### Create notification manually:
```python
from notifications.services import create_notification

create_notification(
    user=user,
    notification_type='system_announcement',
    title='System Maintenance',
    message='Scheduled maintenance on Sunday',
    priority='high',
    action_url='/dashboard/student/support',
    action_label='Learn More'
)
```

### Notifications auto-created on:
- Completing a lesson
- Mission being reviewed
- Mentor leaving feedback
- Achievement unlocked
- Subscription changes

## Database Schema

### notifications table:
- id (UUID)
- user_id (FK)
- notification_type (VARCHAR)
- title (VARCHAR)
- message (TEXT)
- priority (VARCHAR)
- action_url (VARCHAR)
- action_label (VARCHAR)
- metadata (JSON)
- is_read (BOOLEAN)
- read_at (TIMESTAMP)
- send_email (BOOLEAN)
- email_sent (BOOLEAN)
- created_at (TIMESTAMP)

### notification_preferences table:
- user_id (FK)
- enable_in_system (BOOLEAN)
- enable_email (BOOLEAN)
- email_mission_reviewed (BOOLEAN)
- email_mentor_feedback (BOOLEAN)
- email_achievements (BOOLEAN)

## Next Steps (Optional Enhancements)

1. **Email delivery**: Integrate with email service for out-system notifications
2. **WebSocket**: Real-time push instead of polling
3. **Push notifications**: Browser push API integration
4. **Notification categories**: Filter by type
5. **Notification history**: Archive and search
6. **Digest emails**: Daily/weekly summaries
