from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('subscriptions', '0010_usersubscription_payment_method_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='enhancedsubscription',
            name='pending_downgrade_plan_version',
            field=models.ForeignKey(
                blank=True,
                help_text='If set, downgrade will apply at period boundary',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='pending_downgrade_subscriptions',
                to='subscriptions.subscriptionplanversion',
            ),
        ),
        migrations.AddField(
            model_name='enhancedsubscription',
            name='pending_downgrade_effective_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

