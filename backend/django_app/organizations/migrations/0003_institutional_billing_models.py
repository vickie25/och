import uuid
from datetime import date
from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('organizations', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='InstitutionalContract',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, serialize=False, editable=False)),
                ('contract_number', models.CharField(max_length=50, unique=True, db_index=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('student_seat_count', models.IntegerField(validators=[django.core.validators.MinValueValidator(1)], help_text='Total licensed student seats')),
                ('per_student_rate', models.DecimalField(max_digits=10, decimal_places=2, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], help_text='Monthly rate per student based on volume tier')),
                ('billing_cycle', models.CharField(max_length=20, default='monthly', choices=[('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('annual', 'Annual')])),
                ('status', models.CharField(max_length=20, default='draft', choices=[('draft', 'Draft'), ('active', 'Active'), ('expired', 'Expired'), ('terminated', 'Terminated'), ('pending_renewal', 'Pending Renewal')])),
                ('auto_renew', models.BooleanField(default=True, help_text='Auto-renew for additional 12-month terms')),
                ('renewal_notice_days', models.IntegerField(default=60, help_text='Days notice required for non-renewal')),
                ('early_termination_notice_date', models.DateField(null=True, blank=True, help_text='Date when early termination notice was given')),
                ('annual_payment_discount', models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('2.50'), validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)], help_text='Percentage discount for annual payment')),
                ('custom_discount', models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(50)], help_text='Additional custom discount percentage')),
                ('billing_contact_name', models.CharField(max_length=255)),
                ('billing_contact_email', models.EmailField(max_length=254)),
                ('billing_contact_phone', models.CharField(max_length=50, blank=True)),
                ('billing_address', models.TextField(blank=True)),
                ('purchase_order_required', models.BooleanField(default=False)),
                ('signed_at', models.DateTimeField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_institutional_contracts', to=settings.AUTH_USER_MODEL)),
                ('signed_by', models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name='signed_institutional_contracts', to=settings.AUTH_USER_MODEL)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='institutional_contracts', to='organizations.organization')),
            ],
            options={
                'db_table': 'institutional_contracts',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='InstitutionalSeatAdjustment',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, serialize=False, editable=False)),
                ('adjustment_type', models.CharField(max_length=20, choices=[('increase', 'Seat Increase'), ('decrease', 'Seat Decrease'), ('correction', 'Correction')])),
                ('previous_seat_count', models.IntegerField()),
                ('new_seat_count', models.IntegerField()),
                ('adjustment_amount', models.IntegerField()),
                ('effective_date', models.DateField()),
                ('prorated_amount', models.DecimalField(max_digits=10, decimal_places=2, help_text='Prorated charge/credit for the adjustment')),
                ('days_in_billing_period', models.IntegerField()),
                ('days_remaining', models.IntegerField()),
                ('reason', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seat_adjustments', to='organizations.institutionalcontract')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'institutional_seat_adjustments',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='InstitutionalBilling',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, serialize=False, editable=False)),
                ('invoice_number', models.CharField(max_length=50, unique=True, db_index=True)),
                ('billing_period_start', models.DateField()),
                ('billing_period_end', models.DateField()),
                ('billing_cycle', models.CharField(max_length=20, choices=[('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('annual', 'Annual')])),
                ('base_seat_count', models.IntegerField()),
                ('active_seat_count', models.IntegerField()),
                ('seat_adjustments', models.JSONField(default=list, help_text='List of seat adjustments applied to this billing period')),
                ('base_amount', models.DecimalField(max_digits=12, decimal_places=2)),
                ('adjustment_amount', models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))),
                ('discount_amount', models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))),
                ('tax_amount', models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))),
                ('total_amount', models.DecimalField(max_digits=12, decimal_places=2)),
                ('currency', models.CharField(max_length=3, default='USD')),
                ('status', models.CharField(max_length=20, default='draft', choices=[('draft', 'Draft'), ('pending', 'Pending'), ('sent', 'Sent'), ('paid', 'Paid'), ('overdue', 'Overdue'), ('cancelled', 'Cancelled')])),
                ('invoice_date', models.DateField(default=date.today)),
                ('due_date', models.DateField()),
                ('sent_at', models.DateTimeField(null=True, blank=True)),
                ('paid_at', models.DateTimeField(null=True, blank=True)),
                ('payment_method', models.CharField(max_length=50, blank=True)),
                ('payment_reference', models.CharField(max_length=255, blank=True)),
                ('purchase_order_number', models.CharField(max_length=100, blank=True)),
                ('line_items', models.JSONField(default=list, help_text='Detailed breakdown of charges')),
                ('pdf_generated', models.BooleanField(default=False)),
                ('pdf_url', models.URLField(blank=True)),
                ('email_sent', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='billing_records', to='organizations.institutionalcontract')),
            ],
            options={
                'db_table': 'institutional_billing',
                'ordering': ['-invoice_date'],
            },
        ),
        migrations.CreateModel(
            name='InstitutionalStudent',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, serialize=False, editable=False)),
                ('enrollment_type', models.CharField(max_length=30, default='self_enrolled', choices=[('self_enrolled', 'Self Enrolled'), ('director_enrolled', 'Director Enrolled'), ('bulk_imported', 'Bulk Imported')])),
                ('is_active', models.BooleanField(default=True)),
                ('enrolled_at', models.DateTimeField(auto_now_add=True)),
                ('unenrolled_at', models.DateTimeField(null=True, blank=True)),
                ('department', models.CharField(max_length=255, blank=True)),
                ('student_id', models.CharField(max_length=100, blank=True)),
                ('metadata', models.JSONField(default=dict)),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrolled_students', to='organizations.institutionalcontract')),
                ('enrolled_by', models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name='institutional_enrollments_created', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='institutional_enrollments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'institutional_students',
                'indexes': [
                    models.Index(fields=['contract', 'is_active'], name='inst_student_active_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='InstitutionalBillingSchedule',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, serialize=False, editable=False)),
                ('next_billing_date', models.DateField()),
                ('billing_period_start', models.DateField()),
                ('billing_period_end', models.DateField()),
                ('is_processed', models.BooleanField(default=False)),
                ('processed_at', models.DateTimeField(null=True, blank=True)),
                ('processing_attempts', models.IntegerField(default=0)),
                ('last_error', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='billing_schedules', to='organizations.institutionalcontract')),
                ('invoice', models.OneToOneField(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name='schedule', to='organizations.institutionalbilling')),
            ],
            options={
                'db_table': 'institutional_billing_schedules',
                'ordering': ['next_billing_date'],
            },
        ),
        migrations.AddIndex(
            model_name='institutionalcontract',
            index=models.Index(fields=['organization', 'status'], name='inst_contract_org_status_idx'),
        ),
        migrations.AddIndex(
            model_name='institutionalcontract',
            index=models.Index(fields=['start_date', 'end_date'], name='inst_contract_dates_idx'),
        ),
        migrations.AddIndex(
            model_name='institutionalcontract',
            index=models.Index(fields=['status', 'end_date'], name='inst_contract_status_end_idx'),
        ),
        migrations.AddIndex(
            model_name='institutionalbilling',
            index=models.Index(fields=['contract', 'status'], name='inst_bill_contract_status_idx'),
        ),
        migrations.AddIndex(
            model_name='institutionalbilling',
            index=models.Index(fields=['invoice_date', 'due_date'], name='inst_bill_dates_idx'),
        ),
        migrations.AddIndex(
            model_name='institutionalbilling',
            index=models.Index(fields=['status', 'due_date'], name='inst_bill_status_due_idx'),
        ),
    ]

