from decimal import Decimal

from django.core.management.base import BaseCommand
from django.conf import settings

from marketplace.employer_contracts import EmployerContractTier


class Command(BaseCommand):
    help = "Seed Stream C employer contract tiers (KES)."

    def handle(self, *args, **options):
        fx = Decimal(str(getattr(settings, 'EMPLOYER_PRICING_USD_TO_KES', 160.0)))

        def usd_to_kes(usd: Decimal) -> Decimal:
            return (usd * fx).quantize(Decimal('0.01'))

        tiers = [
            {
                'tier_name': 'starter',
                'display_name': 'Starter',
                'monthly_retainer': usd_to_kes(Decimal('500')),
                'candidates_per_quarter': 5,
                'placement_fee': usd_to_kes(Decimal('2000')),
                'placement_fee_cap_multiplier': Decimal('2.0'),
                'dedicated_account_manager': False,
                'priority_matching': False,
                'custom_reports': False,
                'exclusive_pipeline_access': False,
                'currency': 'KES',
            },
            {
                'tier_name': 'growth',
                'display_name': 'Growth',
                'monthly_retainer': usd_to_kes(Decimal('1500')),
                'candidates_per_quarter': 15,
                'placement_fee': usd_to_kes(Decimal('1500')),
                'placement_fee_cap_multiplier': Decimal('2.0'),
                'dedicated_account_manager': True,
                'priority_matching': True,
                'custom_reports': False,
                'exclusive_pipeline_access': False,
                'currency': 'KES',
            },
            {
                'tier_name': 'enterprise',
                'display_name': 'Enterprise',
                'monthly_retainer': usd_to_kes(Decimal('3500')),
                'candidates_per_quarter': None,  # unlimited
                'placement_fee': usd_to_kes(Decimal('1000')),
                'placement_fee_cap_multiplier': Decimal('2.0'),
                'dedicated_account_manager': True,
                'priority_matching': True,
                'custom_reports': True,
                'exclusive_pipeline_access': True,
                'currency': 'KES',
            },
        ]

        for t in tiers:
            EmployerContractTier.objects.update_or_create(
                tier_name=t['tier_name'],
                defaults=t,
            )

        self.stdout.write(self.style.SUCCESS("Seeded employer contract tiers (KES)."))

