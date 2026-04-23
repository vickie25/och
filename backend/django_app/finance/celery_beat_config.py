from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "expire-finance-credits-daily-utc": {
        "task": "finance.tasks.expire_credits",
        "schedule": crontab(hour=0, minute=30),
        "options": {"queue": "billing"},
    },
}
