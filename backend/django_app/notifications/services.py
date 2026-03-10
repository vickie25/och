from .models import Notification, NotificationPreference


def create_notification(user, notification_type, title, message, **kwargs):
    """
    Create a notification for a user
    """
    prefs, _ = NotificationPreference.objects.get_or_create(user=user)
    
    if not prefs.enable_in_system:
        return None
    
    notification = Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        priority=kwargs.get('priority', 'medium'),
        action_url=kwargs.get('action_url'),
        action_label=kwargs.get('action_label'),
        metadata=kwargs.get('metadata', {}),
        send_email=kwargs.get('send_email', False) and prefs.enable_email,
    )
    
    return notification


def notify_lesson_completed(user, lesson_title, module_title):
    return create_notification(
        user=user,
        notification_type='lesson_completed',
        title='Lesson Completed!',
        message=f'You completed "{lesson_title}" in {module_title}',
        priority='low',
        action_url='/dashboard/student/curriculum',
        action_label='Continue Learning'
    )


def notify_mission_reviewed(user, mission_title, grade, feedback_url):
    return create_notification(
        user=user,
        notification_type='mission_reviewed',
        title='Mission Reviewed',
        message=f'Your mission "{mission_title}" has been reviewed. Grade: {grade}',
        priority='high',
        action_url=feedback_url,
        action_label='View Feedback',
        send_email=True
    )


def notify_mentor_feedback(user, mentor_name, feedback_url):
    return create_notification(
        user=user,
        notification_type='mentor_feedback',
        title='New Mentor Feedback',
        message=f'{mentor_name} left feedback on your work',
        priority='high',
        action_url=feedback_url,
        action_label='View Feedback',
        send_email=True
    )
