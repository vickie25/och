"""
Institution license invoicing: per-student tier × seat_cap × billing cycle.
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError
from django.utils import timezone

from .models import Contract, Invoice
from .services import DynamicPricingService

# USD per student / month by volume tier (2.2.2) - LEGACY FALLBACK
PER_STUDENT_MONTHLY_USD = {
    'tier_1_50': Decimal('15'),
    'tier_51_200': Decimal('12'),
    'tier_201_500': Decimal('9'),
    'tier_500_plus': Decimal('7'),
}


def _invoice_amount_for_period(contract: Contract) -> Decimal | None:
    """
    Calculate invoice amount using dynamic pricing service.
    Falls back to hardcoded rates if no dynamic pricing configured.
    """
    tier = contract.institution_pricing_tier
    cycle = contract.billing_cycle
    seats = int(contract.seat_cap or 0)

    if not tier or not cycle or seats < 1:
        return None

    # Use dynamic pricing service first
    amount = DynamicPricingService.calculate_institution_invoice(contract, cycle)

    if amount is not None:
        return amount

    # Fallback to legacy hardcoded calculation
    rate = PER_STUDENT_MONTHLY_USD.get(tier)
    if rate is None:
        return None

    monthly = rate * seats
    if cycle == 'monthly':
        return monthly
    if cycle == 'quarterly':
        return monthly * Decimal('3')
    if cycle == 'annual':
        # ~2% annual discount (2.2.3)
        return (monthly * Decimal('12') * Decimal('0.98')).quantize(Decimal('0.01'))
    return None


def ensure_institution_contract_invoice(contract: Contract) -> Invoice | None:
    """
    Create or update unpaid invoice when institution tier + billing + seats are set.
    """
    if contract.type != 'institution':
        return None
    amount = _invoice_amount_for_period(contract)
    if amount is None or amount <= 0:
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
        _maybe_pending_payments(contract)
        return unpaid

    org = contract.organization
    due = timezone.now() + timedelta(days=30)
    inv = Invoice(
        organization=org,
        contract=contract,
        type='institution',
        amount=amount,
        tax=Decimal('0'),
        total=amount,
        status='sent',
        due_date=due,
    )
    inv.save()
    _maybe_pending_payments(contract)
    return inv


def _maybe_pending_payments(contract: Contract) -> None:
    st = Contract.objects.filter(pk=contract.pk).values_list('status', flat=True).first()
    if st in ('proposal', 'negotiation', 'signed'):
        try:
            Contract.objects.filter(pk=contract.pk).exclude(
                status__in=['active', 'terminated'],
            ).update(status='pending_payments')
        except IntegrityError:
            # Older DBs may still enforce a CHECK that excludes pending_payments.
            # Keep contract in signed state to avoid 500 until DB constraint is updated.
            Contract.objects.filter(pk=contract.pk).exclude(
                status__in=['active', 'terminated'],
            ).update(status='signed')
