import uuid
from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('organizations', '0004_institutional_management_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='institutionalcontract',
            name='pending_renewal_seat_count',
            field=models.IntegerField(
                blank=True,
                null=True,
                help_text='If set, seat reductions apply at next renewal (no mid-contract refunds).',
                validators=[django.core.validators.MinValueValidator(1)],
            ),
        ),
        migrations.AddField(
            model_name='institutionalcontract',
            name='pending_renewal_billing_cycle',
            field=models.CharField(
                blank=True,
                null=True,
                choices=[('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('annual', 'Annual')],
                max_length=20,
                help_text='If set, billing cycle changes apply at next renewal.',
            ),
        ),
        migrations.AlterField(
            model_name='institutionalcontract',
            name='renewal_notice_days',
            field=models.IntegerField(default=90, help_text='Days notice required for non-renewal'),
        ),
        migrations.CreateModel(
            name='InstitutionalContractAmendment',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, serialize=False, editable=False)),
                ('amendment_type', models.CharField(max_length=50, choices=[
                    ('seat_increase', 'Seat increase'),
                    ('seat_reduction_scheduled', 'Seat reduction scheduled'),
                    ('billing_cycle_scheduled', 'Billing cycle scheduled'),
                    ('termination_notice', 'Termination notice'),
                    ('termination', 'Termination executed'),
                    ('renewal_quote_sent', 'Renewal quote sent'),
                ])),
                ('previous_terms', models.JSONField(default=dict)),
                ('new_terms', models.JSONField(default=dict)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='amendments', to='organizations.institutionalcontract')),
                ('requested_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='institutional_contract_amendments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'institutional_contract_amendments',
            },
        ),
        migrations.AddIndex(
            model_name='institutionalcontractamendment',
            index=models.Index(fields=['contract', 'created_at'], name='inst_amend_contract_created_idx'),
        ),
        migrations.AddIndex(
            model_name='institutionalcontractamendment',
            index=models.Index(fields=['amendment_type', 'created_at'], name='inst_amend_type_created_idx'),
        ),
    ]

