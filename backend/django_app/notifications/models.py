from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('lesson_completed', 'Lesson Completed'),
        ('module_completed', 'Module Completed'),
        ('mission_submitted', 'Mission Submitted'),
        ('mission_reviewed', 'Mission Reviewed'),
        ('mentor_assigned', 'Mentor Assigned'),
        ('mentor_feedback', 'Mentor Feedback'),
        ('achievement_unlocked', 'Achievement Unlocked'),
        ('subscription_changed', 'Subscription Changed'),
        ('system_announcement', 'System Announcement'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='medium')
    action_url = models.CharField(max_length=500, blank=True, null=True)
    action_label = models.CharField(max_length=100, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    send_email = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class NotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    enable_in_system = models.BooleanField(default=True)
    enable_email = models.BooleanField(default=True)
    email_mission_reviewed = models.BooleanField(default=True)
    email_mentor_feedback = models.BooleanField(default=True)
    email_achievements = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'notification_preferences'
