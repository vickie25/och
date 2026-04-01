"""
Add dynamic pricing tiers and history tracking
"""
from django.db import migrations, models
import django.db.models.deletion
import uuid
from django.utils import timezone
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        ('finance', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PricingTier',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('name', models.CharField(help_text='Tier identifier (e.g., tier_1_50, starter)', max_length=50)),
                ('display_name', models.CharField(help_text='Human-readable name for admin interface', max_length=100)),
                ('tier_type', models.CharField(choices=[('institution', 'Institution'), ('employer', 'Employer')], help_text='Whether this is for institution or employer pricing', max_length=20)),
                ('min_quantity', models.PositiveIntegerField(default=0, help_text='Minimum quantity (students for institution, placements for employer)')),
                ('max_quantity', models.PositiveIntegerField(blank=True, help_text='Maximum quantity (null for unlimited)', null=True)),
                ('price_per_unit', models.DecimalField(decimal_places=2, help_text='Price per unit per month in selected currency', max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('currency', models.CharField(choices=[('USD', 'US Dollar'), ('KES', 'Kenyan Shilling'), ('EUR', 'Euro')], default='USD', help_text='Currency for this pricing tier', max_length=3)),
                ('billing_frequency', models.CharField(choices=[('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('annual', 'Annual')], default='monthly', help_text='Billing frequency for this tier', max_length=20)),
                ('annual_discount_percent', models.DecimalField(decimal_places=2, default=Decimal('0'), help_text='Discount percentage for annual billing', max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('is_active', models.BooleanField(default=True, help_text='Whether this pricing tier is currently active')),
                ('effective_date', models.DateTimeField(default=timezone.now, help_text='When this pricing becomes effective')),
                ('expiry_date', models.DateTimeField(blank=True, help_text='When this pricing expires (null for no expiry)', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'pricing_tiers',
                'ordering': ['tier_type', 'min_quantity'],
                'indexes': [
                    models.Index(fields=['tier_type', 'is_active'], name='finance_pricin_tier_type_2f3f8a_idx'),
                    models.Index(fields=['effective_date', 'expiry_date'], name='finance_pricin_effective_8c4f3b_idx'),
                ],
            },
        ),
        
        migrations.CreateModel(
            name='PricingHistory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('old_price_per_unit', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('new_price_per_unit', models.DecimalField(decimal_places=2, max_digits=10)),
                ('old_annual_discount', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('new_annual_discount', models.DecimalField(decimal_places=2, max_digits=5)),
                ('change_reason', models.TextField(blank=True, help_text='Reason for pricing change')),
                ('changed_at', models.DateTimeField(auto_now_add=True)),
                ('pricing_tier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history', to='finance.pricingtier')),
                ('changed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pricing_changes', to='users.user')),
            ],
            options={
                'db_table': 'pricing_history',
                'ordering': ['-changed_at'],
                'indexes': [
                    models.Index(fields=['pricing_tier', 'changed_at'], name='finance_pricin_pricing_t_6a7f2c_idx'),
                ],
            },
        ),
        
        migrations.AlterUniqueTogether(
            name='pricingtier',
            unique_together={('name', 'tier_type', 'currency')},
        ),
    ]
