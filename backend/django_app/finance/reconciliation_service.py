"""Book balance computation for reconciliation (payments recorded in Django)."""
from datetime import date
from decimal import Decimal

from cohorts.models import CohortPayment
from django.db.models import Sum

from .models import Payment, ReconciliationRun


def compute_book_total_for_period(
    period_start: date,
    period_end: date,
    currency: str = 'USD',
) -> tuple[Decimal, int]:
    """
    Sum successful finance Payments and completed cohort payments in [period_start, period_end].
    Uses Payment.created_at and CohortPayment.completed_at date parts.
    """
    ps = Payment.objects.filter(
        status='success',
        currency=currency,
        created_at__date__gte=period_start,
        created_at__date__lte=period_end,
    ).aggregate(t=Sum('amount'))['t'] or Decimal('0')

    cp = CohortPayment.objects.filter(
        status='completed',
        currency=currency,
        completed_at__date__gte=period_start,
        completed_at__date__lte=period_end,
    ).aggregate(t=Sum('amount'))['t'] or Decimal('0')

    count = (
        Payment.objects.filter(
            status='success',
            currency=currency,
            created_at__date__gte=period_start,
            created_at__date__lte=period_end,
        ).count()
        + CohortPayment.objects.filter(
            status='completed',
            currency=currency,
            completed_at__date__gte=period_start,
            completed_at__date__lte=period_end,
        ).count()
    )

    return (ps + cp).quantize(Decimal('0.01')), count


def run_reconciliation(
    *,
    period_start: date,
    period_end: date,
    bank_total: Decimal,
    currency: str,
    user,
    notes: str = '',
) -> ReconciliationRun:
    book_total, payment_count = compute_book_total_for_period(
        period_start, period_end, currency=currency
    )
    diff = (book_total - bank_total).quantize(Decimal('0.01'))
    return ReconciliationRun.objects.create(
        period_start=period_start,
        period_end=period_end,
        book_total=book_total,
        bank_total=bank_total,
        difference=diff,
        currency=currency,
        payment_count=payment_count,
        notes=notes,
        created_by=user if user.is_authenticated else None,
    )
