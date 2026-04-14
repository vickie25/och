"""Aggregated financial metrics for cohort managers (directors/coordinators)."""
from decimal import Decimal

from cohorts.models import CohortPayment
from django.db.models import Count, Sum
from programs.models import Cohort, Enrollment


def _user_has_finance_rbac(user) -> bool:
    ur = getattr(user, 'user_roles', None)
    if not ur:
        return False
    return ur.filter(role__name__in=['finance', 'finance_admin'], is_active=True).exists()


def user_can_view_cohort_finance(user, cohort: Cohort) -> bool:
    if getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False):
        return True
    if _user_has_finance_rbac(user):
        return True
    uid = getattr(user, 'uuid_id', None)
    if cohort.coordinator_id and uid and str(cohort.coordinator_id) == str(uid):
        return True
    if cohort.track_id and cohort.track.director_id and uid:
        if str(cohort.track.director_id) == str(uid):
            return True
    return False


def get_cohort_financial_summary(cohort_id) -> dict:
    cohort = Cohort.objects.select_related('track').get(pk=cohort_id)

    enrollments = Enrollment.objects.filter(cohort=cohort)
    total_enrolled = enrollments.count()
    by_seat = enrollments.values('seat_type').annotate(c=Count('id'))
    seat_breakdown = {row['seat_type']: row['c'] for row in by_seat}

    pay_qs = CohortPayment.objects.filter(
        enrollment__cohort=cohort,
        status='completed',
    )
    revenue_agg = pay_qs.aggregate(
        total=Sum('amount'),
        n=Count('id'),
    )
    revenue = revenue_agg['total'] or Decimal('0')
    pay_currency = (
        pay_qs.values_list('currency', flat=True).first() or 'USD'
    )

    pool = cohort.seat_pool or {}
    return {
        'cohort_id': str(cohort.id),
        'cohort_name': cohort.name,
        'status': cohort.status,
        'seat_cap': cohort.seat_cap,
        'seat_pool_config': pool,
        'enrollment_total': total_enrolled,
        'enrollment_by_seat_type': seat_breakdown,
        'cohort_payment_revenue': float(revenue),
        'cohort_payment_currency': pay_currency,
        'completed_payments_count': revenue_agg['n'] or 0,
    }
