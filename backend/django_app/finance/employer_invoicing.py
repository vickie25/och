"""
Employer contract: retainer invoice when a commercial plan is selected.
"""
from __future__ import annotations

from decimal import Decimal
from datetime import timedelta
from typing import Optional

from django.db import IntegrityError
from django.utils import timezone

from .models import Contract, Invoice


# Monthly retainer (USD) — aligned with employer commercial catalog
EMPLOYER_RETAINER_USD = {
    'starter': Decimal('500'),
    'growth': Decimal('1500'),
    'enterprise': Decimal('3500'),
}


def ensure_employer_plan_retainer_invoice(contract: Contract) -> Optional[Invoice]:
    """
    Create or update a sent invoice for the monthly retainer when employer_plan is set/changed.
    If an unpaid invoice exists for this contract, its amounts are updated to match the new plan.
    """
    if contract.type != 'employer' or not contract.employer_plan:
        return None

    plan = contract.employer_plan
    if plan == 'custom':
        amount = contract.total_value or Decimal('0')
        if amount <= 0:
            return None
    else:
        amount = EMPLOYER_RETAINER_USD.get(plan)
        if amount is None:
            return None

    unpaid = (
        Invoice.objects.filter(
            contract=contract,
            status__in=['draft', 'sent', 'overdue'],
        )
        .order_by('-created_at')
        .first()
    )
    if unpaid:
        unpaid.amount = amount
        tax = unpaid.tax or Decimal('0')
        unpaid.tax = tax
        unpaid.total = amount + tax
        unpaid.save(update_fields=['amount', 'tax', 'total', 'updated_at'])
        _maybe_set_pending_payments(contract)
        return unpaid

    org = contract.organization
    due = timezone.now() + timedelta(days=14)
    inv = Invoice(
        organization=org,
        contract=contract,
        type='employer',
        amount=amount,
        tax=Decimal('0'),
        total=amount,
        status='sent',
        due_date=due,
    )
    inv.save()
    _maybe_set_pending_payments(contract)
    return inv


def _maybe_set_pending_payments(contract: Contract) -> None:
    if contract.status in ('proposal', 'negotiation', 'signed'):
        try:
            Contract.objects.filter(pk=contract.pk).exclude(
                status__in=['active', 'terminated'],
            ).update(status='pending_payments')
        except IntegrityError:
            # Backward-compatible fallback for DBs whose CHECK still excludes pending_payments.
            Contract.objects.filter(pk=contract.pk).exclude(
                status__in=['active', 'terminated'],
            ).update(status='signed')
