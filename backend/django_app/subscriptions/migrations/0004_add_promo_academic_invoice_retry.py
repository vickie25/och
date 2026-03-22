# Generated migration for new subscription features

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
import uuid
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0002_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        # Promotional Codes
        migrations.CreateModel(
            name='PromotionalCode',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('code', models.CharField(db_index=True, help_text='Promo code (e.g., CYBER2026)', max_length=50, unique=True)),
                ('discount_type', models.CharField(choices=[('percentage', 'Percentage Discount'), ('fixed', 'Fixed Amount Discount'), ('trial_extension', 'Trial Extension'), ('bonus_credits', 'Bonus Credits')], default='percentage', max_length=20)),
                ('discount_value', models.DecimalField(decimal_places=2, help_text='Percentage (e.g., 50 for 50%) or fixed amount in KES', max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('valid_from', models.DateTimeField(help_text='Code becomes active from this date')),
                ('valid_until', models.DateTimeField(help_text='Code expires after this date')),
                ('max_redemptions', models.IntegerField(blank=True, help_text='Maximum total redemptions (NULL = unlimited)', null=True, validators=[django.core.validators.MinValueValidator(1)])),
                ('usage_limit_per_user', models.IntegerField(default=1, help_text='How many times each user can use this code', validators=[django.core.validators.MinValueValidator(1)])),
                ('is_active', models.BooleanField(default=True, help_text='Manually disable code')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_promo_codes', to='users.user')),
                ('eligible_plans', models.ManyToManyField(blank=True, help_text='Leave empty for all plans', related_name='promo_codes', to='subscriptions.subscriptionplan')),
            ],
            options={
                'verbose_name': 'Promotional Code',
                'verbose_name_plural': 'Promotional Codes',
                'db_table': 'promotional_codes',
            },
        ),
        
        # Promo Code Redemptions
        migrations.CreateModel(
            name='PromoCodeRedemption',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('discount_applied', models.DecimalField(decimal_places=2, help_text='Actual discount amount in KES', max_digits=10)),
                ('original_amount', models.DecimalField(decimal_places=2, help_text='Original price before discount', max_digits=10)),
                ('final_amount', models.DecimalField(decimal_places=2, help_text='Final price after discount', max_digits=10)),
                ('redeemed_at', models.DateTimeField(auto_now_add=True)),
                ('code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='redemptions', to='subscriptions.promotionalcode')),
                ('subscription', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='promo_redemptions', to='subscriptions.usersubscription')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='promo_redemptions', to='users.user')),
            ],
            options={
                'verbose_name': 'Promo Code Redemption',
                'verbose_name_plural': 'Promo Code Redemptions',
                'db_table': 'promo_code_redemptions',
            },
        ),
        
        # Academic Discounts
        migrations.CreateModel(
            name='AcademicDiscount',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('verification_method', models.CharField(choices=[('edu_email', '.edu Email'), ('document', 'Document Upload'), ('manual', 'Manual Verification')], max_length=20)),
                ('verification_status', models.CharField(choices=[('pending', 'Pending Verification'), ('verified', 'Verified'), ('rejected', 'Rejected'), ('expired', 'Expired')], db_index=True, default='pending', max_length=20)),
                ('edu_email', models.EmailField(blank=True, help_text='Verified .edu email address', max_length=254, null=True)),
                ('institution_name', models.CharField(blank=True, max_length=255)),
                ('document_url', models.URLField(blank=True, help_text='URL to uploaded verification document', null=True)),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('expires_at', models.DateTimeField(blank=True, help_text='Annual re-verification required', null=True)),
                ('rejection_reason', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='academic_discount', to='users.user')),
                ('verified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='verified_academic_discounts', to='users.user')),
            ],
            options={
                'verbose_name': 'Academic Discount',
                'verbose_name_plural': 'Academic Discounts',
                'db_table': 'academic_discounts',
            },
        ),
        
        # Subscription Invoices
        migrations.CreateModel(
            name='SubscriptionInvoice',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('invoice_number', models.CharField(db_index=True, help_text='e.g., INV-2026-001234', max_length=50, unique=True)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('sent', 'Sent'), ('paid', 'Paid'), ('overdue', 'Overdue'), ('void', 'Void')], db_index=True, default='draft', max_length=20)),
                ('subtotal', models.DecimalField(decimal_places=2, max_digits=10)),
                ('discount_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('tax_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(default='KES', max_length=3)),
                ('invoice_date', models.DateTimeField(default=timezone.now)),
                ('due_date', models.DateTimeField()),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('line_items', models.JSONField(default=list, help_text='List of invoice line items')),
                ('notes', models.TextField(blank=True)),
                ('pdf_url', models.URLField(blank=True, help_text='URL to generated PDF', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('subscription', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invoices', to='subscriptions.usersubscription')),
                ('transaction', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invoice', to='subscriptions.paymenttransaction')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscription_invoices', to='users.user')),
            ],
            options={
                'verbose_name': 'Subscription Invoice',
                'verbose_name_plural': 'Subscription Invoices',
                'db_table': 'subscription_invoices',
                'ordering': ['-invoice_date'],
            },
        ),
        
        # Payment Retry Attempts
        migrations.CreateModel(
            name='PaymentRetryAttempt',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('attempt_number', models.IntegerField(help_text='Retry attempt number (1, 2, 3, etc.)', validators=[django.core.validators.MinValueValidator(1)])),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('success', 'Success'), ('failed', 'Failed')], db_index=True, default='pending', max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(default='KES', max_length=3)),
                ('scheduled_at', models.DateTimeField(help_text='When retry is scheduled')),
                ('attempted_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('gateway_response', models.JSONField(blank=True, default=dict)),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('subscription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='retry_attempts', to='subscriptions.usersubscription')),
            ],
            options={
                'verbose_name': 'Payment Retry Attempt',
                'verbose_name_plural': 'Payment Retry Attempts',
                'db_table': 'payment_retry_attempts',
                'ordering': ['scheduled_at'],
            },
        ),
        
        # Indexes
        migrations.AddIndex(
            model_name='promotionalcode',
            index=models.Index(fields=['code', 'is_active'], name='promotional_code_active_idx'),
        ),
        migrations.AddIndex(
            model_name='promotionalcode',
            index=models.Index(fields=['valid_from', 'valid_until'], name='promotional_validity_idx'),
        ),
        migrations.AddIndex(
            model_name='promocoderedemption',
            index=models.Index(fields=['user', 'redeemed_at'], name='promo_redemption_user_idx'),
        ),
        migrations.AddIndex(
            model_name='promocoderedemption',
            index=models.Index(fields=['code', 'redeemed_at'], name='promo_redemption_code_idx'),
        ),
        migrations.AddIndex(
            model_name='academicdiscount',
            index=models.Index(fields=['user', 'verification_status'], name='academic_user_status_idx'),
        ),
        migrations.AddIndex(
            model_name='academicdiscount',
            index=models.Index(fields=['expires_at'], name='academic_expires_idx'),
        ),
        migrations.AddIndex(
            model_name='subscriptioninvoice',
            index=models.Index(fields=['user', 'status'], name='invoice_user_status_idx'),
        ),
        migrations.AddIndex(
            model_name='subscriptioninvoice',
            index=models.Index(fields=['invoice_date'], name='invoice_date_idx'),
        ),
        migrations.AddIndex(
            model_name='subscriptioninvoice',
            index=models.Index(fields=['due_date'], name='invoice_due_date_idx'),
        ),
        migrations.AddIndex(
            model_name='paymentretryattempt',
            index=models.Index(fields=['subscription', 'status'], name='retry_sub_status_idx'),
        ),
        migrations.AddIndex(
            model_name='paymentretryattempt',
            index=models.Index(fields=['scheduled_at', 'status'], name='retry_scheduled_idx'),
        ),
    ]
