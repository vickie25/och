"""
Periodic finance tasks (Celery).
"""
import logging

from django.db import transaction
from django.utils import timezone

try:
    from celery import shared_task
except ImportError:  # pragma: no cover
    def shared_task(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

from .audit import log_financial_action
from .models import Credit

logger = logging.getLogger(__name__)


@shared_task(name="finance.expire_credits")
def expire_credits():
    """
    Zero out `remaining` on credits past `expires_at` (daily).
    Does not alter wallet cash balance; promotional credit buckets are separate.
    """
    now = timezone.now()
    qs = Credit.objects.filter(expires_at__isnull=False, expires_at__lt=now, remaining__gt=0)
    updated = 0
    for credit in qs.iterator():
        with transaction.atomic():
            old = credit.remaining
            credit.remaining = 0
            credit.save(update_fields=["remaining", "updated_at"])
            updated += 1
            try:
                log_financial_action(
                    user=None,
                    action="update",
                    entity_type="credit",
                    entity_id=credit.id,
                    description="Credit expired (remaining zeroed by scheduled task)",
                    old_values={"remaining": str(old)},
                    new_values={"remaining": "0"},
                )
            except Exception as ex:  # pragma: no cover - audit must not break task
                logger.warning("Credit expiry audit log failed: %s", ex)
    return {"credits_zeroed": updated, "at": now.isoformat()}
