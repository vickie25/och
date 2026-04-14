from curriculum.models import UserLessonProgress
from django.db.models.signals import post_save
from django.dispatch import receiver
from missions.models_mxp import MissionProgress

from .services import notify_lesson_completed, notify_mission_reviewed


@receiver(post_save, sender=UserLessonProgress)
def lesson_completed_notification(sender, instance, created, **kwargs):
    if instance.status == 'completed' and instance.lesson:
        notify_lesson_completed(
            user=instance.user,
            lesson_title=instance.lesson.title,
            module_title=instance.lesson.module.title if instance.lesson.module else 'Module'
        )


@receiver(post_save, sender=MissionProgress)
def mission_reviewed_notification(sender, instance, created, **kwargs):
    if instance.status == 'approved' and instance.mentor_reviewed_at:
        notify_mission_reviewed(
            user=instance.user,
            mission_title=instance.mission.title if hasattr(instance, 'mission') else 'Mission',
            grade=instance.final_status or 'pass',
            feedback_url=f'/dashboard/student/missions/{instance.mission_id}'
        )
