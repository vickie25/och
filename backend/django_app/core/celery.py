"""
Celery configuration for OCH Platform
"""
import os

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.base')

app = Celery('och_platform')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    # Subscription management
    'check-subscription-renewals': {
        'task': 'subscriptions.tasks.check_subscription_renewals',
        'schedule': 60.0 * 60,  # Every hour
    },
    'process-grace-period-expiry': {
        'task': 'subscriptions.tasks.process_grace_period_expiry',
        'schedule': 60.0 * 60 * 6,  # Every 6 hours
    },

    # Cohort management
    'send-cohort-daily-reminders': {
        'task': 'cohorts.tasks.send_daily_reminders',
        'schedule': 60.0 * 60 * 24,  # Daily
    },
    'update-cohort-analytics': {
        'task': 'cohorts.tasks.update_cohort_analytics',
        'schedule': 60.0 * 60 * 2,  # Every 2 hours
    },

    # Email processing
    'process-email-queue': {
        'task': 'notifications.tasks.process_email_queue',
        'schedule': 60.0 * 5,  # Every 5 minutes
    },

    # Mentorship
    'send-mentorship-reminders': {
        'task': 'mentorship.tasks.send_session_reminders',
        'schedule': 60.0 * 60,  # Every hour
    },

    # Analytics and reporting
    'generate-daily-reports': {
        'task': 'director_dashboard.tasks.generate_daily_reports',
        'schedule': 60.0 * 60 * 24,  # Daily
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
