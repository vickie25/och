from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0009_enhanced_subscription_payment_method_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersubscription',
            name='payment_gateway',
            field=models.CharField(
                blank=True,
                choices=[('stripe', 'Stripe'), ('paystack', 'Paystack')],
                db_index=True,
                help_text='Gateway holding the default payment method',
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='usersubscription',
            name='payment_method_ref',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='Gateway payment method reference (e.g. Stripe pm_...)',
                max_length=255,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='usersubscription',
            name='payment_method_added_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

