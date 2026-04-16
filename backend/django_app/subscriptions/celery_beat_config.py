"""
Celery Beat Schedule for Enhanced Billing Engine
Add this to your Django settings.py or celery configuration
"""

from celery.schedules import crontab

# Enhanced Billing Engine Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    # §3.1.3: Midnight UTC boundary — reconcile ended cycles (then renewals run later same day)
    'enforce-subscription-cycle-boundary-utc': {
        'task': 'subscriptions.billing_tasks.enforce_subscription_cycle_boundary_utc',
        'schedule': crontab(hour=0, minute=5),
        'options': {'queue': 'billing'}
    },
    # §3.1.3: Renewal charge attempt 1 calendar day before cycle end (UTC date match)
    'process-subscription-renewals': {
        'task': 'subscriptions.billing_tasks.process_subscription_renewals',
        'schedule': crontab(hour=2, minute=0),
        'options': {'queue': 'billing'}
    },

    # Process dunning retries every 4 hours
    'process-dunning-retries': {
        'task': 'subscriptions.billing_tasks.process_dunning_retries',
        'schedule': crontab(minute=0, hour='*/4'),
        'options': {'queue': 'billing'}
    },

    # Expire trial subscriptions daily at 3 AM UTC
    'expire-trial-subscriptions': {
        'task': 'subscriptions.billing_tasks.expire_trial_subscriptions',
        'schedule': crontab(hour=3, minute=0),
        'options': {'queue': 'billing'}
    },

    # Suspend past due subscriptions daily at 4 AM UTC
    'suspend-past-due-subscriptions': {
        'task': 'subscriptions.billing_tasks.suspend_past_due_subscriptions',
        'schedule': crontab(hour=4, minute=0),
        'options': {'queue': 'billing'}
    },

    # Expire suspended subscriptions daily at 5 AM UTC
    'expire-suspended-subscriptions': {
        'task': 'subscriptions.billing_tasks.expire_suspended_subscriptions',
        'schedule': crontab(hour=5, minute=0),
        'options': {'queue': 'billing'}
    },

    # Suspended account reactivation reminders (days 10, 20, 25 of window)
    'send-suspended-reactivation-reminders': {
        'task': 'subscriptions.billing_tasks.send_suspended_reactivation_reminder_emails',
        'schedule': crontab(hour=11, minute=0),
        'options': {'queue': 'notifications'}
    },

    # Send dunning notifications every 2 hours during business hours
    'send-dunning-notifications': {
        'task': 'subscriptions.billing_tasks.send_dunning_notifications',
        'schedule': crontab(minute=0, hour='8-20/2'),  # Every 2 hours from 8 AM to 8 PM
        'options': {'queue': 'notifications'}
    },

    # Generate monthly billing report on the 1st of each month at 6 AM UTC
    'generate-monthly-billing-report': {
        'task': 'subscriptions.billing_tasks.generate_monthly_billing_report',
        'schedule': crontab(hour=6, minute=0, day_of_month=1),
        'options': {'queue': 'reports'}
    },

    # Academic discount expiry check (enhanced model): daily at 03:30 UTC
    'check-enhanced-academic-discount-expiry': {
        'task': 'subscriptions.billing_tasks.check_enhanced_academic_discount_expiry',
        'schedule': crontab(hour=3, minute=30),
        'options': {'queue': 'notifications'}
    },
}

# Celery Queue Configuration
CELERY_TASK_ROUTES = {
    'subscriptions.billing_tasks.*': {'queue': 'billing'},
    'subscriptions.billing_tasks.send_dunning_notifications': {'queue': 'notifications'},
    'subscriptions.billing_tasks.send_suspended_reactivation_reminder_emails': {'queue': 'notifications'},
    'subscriptions.billing_tasks.generate_monthly_billing_report': {'queue': 'reports'},
}

# Celery Task Settings
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True

# Task retry settings
CELERY_TASK_ANNOTATIONS = {
    'subscriptions.billing_tasks.process_subscription_renewals': {
        'rate_limit': '10/m',
        'max_retries': 3,
        'default_retry_delay': 60
    },
    'subscriptions.billing_tasks.process_dunning_retries': {
        'rate_limit': '20/m',
        'max_retries': 3,
        'default_retry_delay': 60
    },
    'subscriptions.billing_tasks.send_dunning_notifications': {
        'rate_limit': '50/m',
        'max_retries': 2,
        'default_retry_delay': 30
    },
}
