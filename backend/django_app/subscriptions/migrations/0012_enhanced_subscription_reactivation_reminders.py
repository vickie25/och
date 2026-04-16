from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0011_enhanced_subscription_pending_downgrade'),
    ]

    operations = [
        migrations.AddField(
            model_name='enhancedsubscription',
            name='reactivation_reminder_last_milestone',
            field=models.IntegerField(
                default=0,
                help_text='Last reactivation reminder milestone sent (0, 10, 20, or 25 days after suspension)',
            ),
        ),
    ]
