"""
Cohort-related Celery tasks
"""
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from programs.models import Cohort, Enrollment
from cohorts.services.enhanced_cohort_service import enhanced_cohort_service
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_daily_reminders():
    """
    Send daily reminders to cohort students about upcoming activities
    """
    try:
        today = timezone.now().date()
        active_cohorts = Cohort.objects.filter(
            status__in=['active', 'running'],
            start_date__lte=today,
            end_date__gte=today
        )
        
        reminder_count = 0
        for cohort in active_cohorts:
            # Get upcoming events for this cohort
            upcoming_events = cohort.calendar_events.filter(
                start_ts__date=today + timezone.timedelta(days=1),
                status='scheduled'
            )
            
            if upcoming_events.exists():
                # Send reminders to all enrolled students
                enrollments = cohort.enrollments.filter(status='active')
                for enrollment in enrollments:
                    send_cohort_reminder_email.delay(
                        enrollment.id, 
                        list(upcoming_events.values('title', 'start_ts', 'location', 'link'))
                    )
                    reminder_count += 1
        
        logger.info(f"Sent {reminder_count} cohort reminders")
        return f"Sent {reminder_count} reminders"
        
    except Exception as exc:
        logger.error(f"Daily reminders task failed: {exc}")
        raise exc

@shared_task(bind=True, max_retries=3)
def send_cohort_reminder_email(self, enrollment_id, events_data):
    """
    Send reminder email to individual student
    """
    try:
        enrollment = Enrollment.objects.select_related('user', 'cohort').get(id=enrollment_id)
        user = enrollment.user
        cohort = enrollment.cohort
        
        # Format events for email
        events_text = ""
        for event in events_data:
            events_text += f"""
            • {event['title']}
              Time: {event['start_ts']}
              Location: {event.get('location', 'Virtual')}
              {f"Link: {event['link']}" if event.get('link') else ""}
            """
        
        subject = f"Tomorrow's Activities - {cohort.name}"
        message = f"""
        Hi {user.first_name},
        
        Here are your upcoming activities for tomorrow in {cohort.name}:
        
        {events_text}
        
        Don't forget to prepare and join on time!
        
        Best regards,
        OCH Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        logger.info(f"Cohort reminder sent to {user.email}")
        return f"Reminder sent to {user.email}"
        
    except Enrollment.DoesNotExist:
        logger.error(f"Enrollment {enrollment_id} not found")
        return f"Enrollment {enrollment_id} not found"
    except Exception as exc:
        logger.error(f"Failed to send cohort reminder: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@shared_task
def update_cohort_analytics():
    """
    Update analytics for all active cohorts
    """
    try:
        active_cohorts = Cohort.objects.filter(
            status__in=['active', 'running']
        )
        
        updated_count = 0
        for cohort in active_cohorts:
            # Generate analytics (this could be heavy computation)
            analytics = enhanced_cohort_service.get_cohort_analytics(cohort)
            
            # Store or cache analytics results
            # You could save to a CohortAnalytics model or cache
            logger.info(f"Updated analytics for cohort {cohort.name}")
            updated_count += 1
        
        logger.info(f"Updated analytics for {updated_count} cohorts")
        return f"Updated {updated_count} cohort analytics"
        
    except Exception as exc:
        logger.error(f"Cohort analytics update failed: {exc}")
        raise exc

@shared_task
def process_cohort_completions():
    """
    Process cohort completions and issue certificates
    """
    try:
        # Find cohorts that have ended
        ended_cohorts = Cohort.objects.filter(
            status='running',
            end_date__lt=timezone.now().date()
        )
        
        processed_count = 0
        for cohort in ended_cohorts:
            # Update cohort status
            cohort.status = 'closing'
            cohort.save()
            
            # Process completions for each enrollment
            enrollments = cohort.enrollments.filter(status='active')
            for enrollment in enrollments:
                process_student_completion.delay(enrollment.id)
            
            processed_count += 1
        
        logger.info(f"Processed {processed_count} cohort completions")
        return f"Processed {processed_count} completions"
        
    except Exception as exc:
        logger.error(f"Cohort completion processing failed: {exc}")
        raise exc

@shared_task(bind=True, max_retries=2)
def process_student_completion(self, enrollment_id):
    """
    Process individual student completion and certificate generation
    """
    try:
        enrollment = Enrollment.objects.select_related('user', 'cohort').get(id=enrollment_id)
        
        # Check completion criteria (this would use your business logic)
        # For now, we'll assume completion based on progress
        
        # Update enrollment status
        enrollment.status = 'completed'
        enrollment.completed_at = timezone.now()
        enrollment.save()
        
        # Generate certificate (placeholder)
        generate_certificate.delay(enrollment.id)
        
        # Send completion email
        send_completion_email.delay(enrollment.id)
        
        logger.info(f"Processed completion for {enrollment.user.email}")
        return f"Processed completion for {enrollment.user.email}"
        
    except Enrollment.DoesNotExist:
        logger.error(f"Enrollment {enrollment_id} not found")
        return f"Enrollment {enrollment_id} not found"
    except Exception as exc:
        logger.error(f"Failed to process completion: {exc}")
        raise self.retry(exc=exc, countdown=120)

@shared_task
def generate_certificate(enrollment_id):
    """
    Generate certificate for completed student
    """
    try:
        enrollment = Enrollment.objects.select_related('user', 'cohort').get(id=enrollment_id)
        
        # Certificate generation logic would go here
        # This could involve PDF generation, template rendering, etc.
        
        logger.info(f"Generated certificate for {enrollment.user.email}")
        return f"Certificate generated for {enrollment.user.email}"
        
    except Exception as exc:
        logger.error(f"Certificate generation failed: {exc}")
        raise exc

@shared_task(bind=True, max_retries=2)
def send_completion_email(self, enrollment_id):
    """
    Send completion congratulations email
    """
    try:
        enrollment = Enrollment.objects.select_related('user', 'cohort').get(id=enrollment_id)
        user = enrollment.user
        cohort = enrollment.cohort
        
        subject = f"Congratulations! You've Completed {cohort.name}"
        message = f"""
        Hi {user.first_name},
        
        Congratulations on successfully completing {cohort.name}!
        
        Your certificate will be available in your dashboard shortly.
        
        We're proud of your achievement and look forward to seeing your continued growth.
        
        Best regards,
        OCH Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        logger.info(f"Completion email sent to {user.email}")
        return f"Completion email sent to {user.email}"
        
    except Exception as exc:
        logger.error(f"Failed to send completion email: {exc}")
        raise self.retry(exc=exc, countdown=120)