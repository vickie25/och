"""
Management command to initialize dynamic pricing tiers with current hardcoded values
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from finance.models import PricingTier


class Command(BaseCommand):
    help = 'Initialize dynamic pricing tiers with current hardcoded values'

    def handle(self, *args, **options):
        """Create pricing tiers based on current hardcoded values"""

        # Institution Tiers
        institution_tiers = [
            {
                'name': 'tier_1_50',
                'display_name': '1–50 students ($15/student/mo)',
                'tier_type': 'institution',
                'min_quantity': 1,
                'max_quantity': 50,
                'price_per_unit': Decimal('15.00'),
                'currency': 'USD',
                'annual_discount_percent': Decimal('2.0'),
            },
            {
                'name': 'tier_51_200',
                'display_name': '51–200 students ($12/student/mo)',
                'tier_type': 'institution',
                'min_quantity': 51,
                'max_quantity': 200,
                'price_per_unit': Decimal('12.00'),
                'currency': 'USD',
                'annual_discount_percent': Decimal('2.0'),
            },
            {
                'name': 'tier_201_500',
                'display_name': '201–500 students ($9/student/mo)',
                'tier_type': 'institution',
                'min_quantity': 201,
                'max_quantity': 500,
                'price_per_unit': Decimal('9.00'),
                'currency': 'USD',
                'annual_discount_percent': Decimal('2.0'),
            },
            {
                'name': 'tier_500_plus',
                'display_name': '500+ students ($7/student/mo)',
                'tier_type': 'institution',
                'min_quantity': 501,
                'max_quantity': None,
                'price_per_unit': Decimal('7.00'),
                'currency': 'USD',
                'annual_discount_percent': Decimal('2.0'),
            },
        ]

        # Employer Plans
        employer_tiers = [
            {
                'name': 'starter',
                'display_name': 'Starter Plan ($500/month)',
                'tier_type': 'employer',
                'min_quantity': 0,
                'max_quantity': None,
                'price_per_unit': Decimal('500.00'),
                'currency': 'USD',
                'annual_discount_percent': Decimal('0.0'),
            },
            {
                'name': 'growth',
                'display_name': 'Growth Plan ($1,500/month)',
                'tier_type': 'employer',
                'min_quantity': 0,
                'max_quantity': None,
                'price_per_unit': Decimal('1500.00'),
                'currency': 'USD',
                'annual_discount_percent': Decimal('0.0'),
            },
            {
                'name': 'enterprise',
                'display_name': 'Enterprise Plan ($3,500/month)',
                'tier_type': 'employer',
                'min_quantity': 0,
                'max_quantity': None,
                'price_per_unit': Decimal('3500.00'),
                'currency': 'USD',
                'annual_discount_percent': Decimal('0.0'),
            },
        ]

        all_tiers = institution_tiers + employer_tiers
        created_count = 0
        updated_count = 0

        for tier_data in all_tiers:
            tier, created = PricingTier.objects.update_or_create(
                name=tier_data['name'],
                tier_type=tier_data['tier_type'],
                currency=tier_data['currency'],
                defaults=tier_data
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Created pricing tier: {tier.display_name}")
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f"Updated pricing tier: {tier.display_name}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nPricing setup complete!\n"
                f"Created: {created_count} tiers\n"
                f"Updated: {updated_count} tiers\n"
                f"Total: {len(all_tiers)} tiers configured"
            )
        )
