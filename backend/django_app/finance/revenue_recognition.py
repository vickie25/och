"""Create RevenueStream rows from paid invoices (idempotent by invoice id)."""
import uuid as uuid_lib
from datetime import date

from .models import Invoice
from .analytics import RevenueStream

STREAM_BY_INVOICE_TYPE = {
    'subscription': 'subscription',
    'institution': 'institution',
    'employer': 'employer',
    'cohort': 'cohort',
    'contract': 'employer',
}


def _customer_uuid_for_invoice(inv: Invoice):
    if inv.user_id and getattr(inv.user, 'uuid_id', None):
        return inv.user.uuid_id
    if inv.organization_id:
        return uuid_lib.uuid5(
            uuid_lib.NAMESPACE_OID,
            f'org:{inv.organization_id}',
        )
    return None


def recognize_revenue_for_period(
    period_start: date,
    period_end: date,
    currency: str = 'USD',
) -> dict:
    """
    For each paid Invoice with paid_date in range, ensure a RevenueStream exists
    with source_type='finance_invoice' and source_id=invoice.id.
    """
    qs = Invoice.objects.filter(
        status='paid',
        paid_date__isnull=False,
        paid_date__date__gte=period_start,
        paid_date__date__lte=period_end,
    )

    created = 0
    skipped = 0
    for inv in qs:
        exists = RevenueStream.objects.filter(
            source_id=inv.id,
            source_type='finance_invoice',
        ).exists()
        if exists:
            skipped += 1
            continue
        st = STREAM_BY_INVOICE_TYPE.get(inv.type, 'subscription')
        cust_id = _customer_uuid_for_invoice(inv)
        cust_type = 'user' if inv.user_id else ('organization' if inv.organization_id else '')

        RevenueStream.objects.create(
            stream_type=st,
            amount=inv.total,
            currency=currency,
            source_id=inv.id,
            source_type='finance_invoice',
            customer_id=cust_id,
            customer_type=cust_type,
            recognized_date=inv.paid_date.date(),
            payment_date=inv.paid_date.date(),
        )
        created += 1

    return {
        'created': created,
        'skipped_existing': skipped,
        'period_start': period_start.isoformat(),
        'period_end': period_end.isoformat(),
    }
