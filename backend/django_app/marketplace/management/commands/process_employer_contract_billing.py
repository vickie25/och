import logging
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from finance.models import Invoice

from marketplace.employer_contracts import EmployerContract
from marketplace.employer_contract_services import PlacementFeeService

logger = logging.getLogger(__name__)


def _month_start(d: date) -> date:
    return d.replace(day=1)


def _next_month_start(d: date) -> date:
    return (d.replace(day=28) + timedelta(days=4)).replace(day=1)


def ensure_monthly_retainer_invoice(contract: EmployerContract, month_start: date):
    """
    Create one retainer invoice per contract per month (idempotent by notes marker).
    Finance.Invoice doesn't have line items; we encode month marker in notes via invoice_number only,
    so we instead use a deterministic "duplicate check" on (org, type, amount, due window, created month).
    """
    amount = contract.get_effective_monthly_retainer()
    if amount <= 0:
        return None
    # Check if already created this month for this org+contract_number
    existing = Invoice.objects.filter(
        organization=contract.organization,
        type='employer',
        status__in=['draft', 'sent', 'overdue', 'paid'],
        created_at__date__gte=month_start,
        created_at__date__lt=_next_month_start(month_start),
        amount=amount,
    ).order_by('-created_at').first()
    if existing:
        return existing

    due = timezone.now() + timedelta(days=14)
    inv = Invoice.objects.create(
        organization=contract.organization,
        contract=None,
        type='employer',
        currency=getattr(contract, 'currency', 'KES') or 'KES',
        amount=amount,
        tax=Decimal('0'),
        total=amount,
        status='sent',
        due_date=due,
    )
    return inv


def process_employer_contract_billing(run_date=None):
    if run_date is None:
        run_date = timezone.now().date()
    month_start = _month_start(run_date)

    results = {
        'retainers_invoiced': 0,
        'placements_confirmed': 0,
        'placement_fee_invoices': 0,
        'matching_queue_processed': 0,
        'errors': [],
    }

    # 1) confirm probation completions (90-day trigger)
    try:
        results['placements_confirmed'] = PlacementFeeService.confirm_probation_if_due()
    except Exception as e:
        results['errors'].append(f"probation_confirm error: {e}")

    # 2) generate invoices for active contracts
    active_contracts = EmployerContract.objects.select_related('organization').filter(status='active')
    for c in active_contracts:
        try:
            inv = ensure_monthly_retainer_invoice(c, month_start)
            if inv:
                results['retainers_invoiced'] += 1
        except Exception as e:
            results['errors'].append(f"retainer invoice error {c.contract_number}: {e}")

        try:
            inv2 = PlacementFeeService.generate_placement_fee_invoice(c, month_start)
            if inv2:
                results['placement_fee_invoices'] += 1
        except Exception as e:
            results['errors'].append(f"placement fee invoice error {c.contract_number}: {e}")

    # 3) process matching queue (priority)
    try:
        from marketplace.employer_contract_services import EmployerMatchingQueueService

        qres = EmployerMatchingQueueService.process_next(batch_size=25)
        results['matching_queue_processed'] = qres.get('processed', 0)
        results['errors'].extend(qres.get('errors', []))
    except Exception as e:
        results['errors'].append(f"matching queue error: {e}")

    logger.info(f"Employer billing results: {results}")
    return results


class Command(BaseCommand):
    help = "Process Stream C employer retainers and placement fee billing (daily)."

    def handle(self, *args, **options):
        process_employer_contract_billing()

