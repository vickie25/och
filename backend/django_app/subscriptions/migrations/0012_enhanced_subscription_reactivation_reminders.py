from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0011_enhanced_subscription_pending_downgrade'),
    ]

    # No-op: EnhancedSubscription is not part of this app's migration state here.
    operations = []
