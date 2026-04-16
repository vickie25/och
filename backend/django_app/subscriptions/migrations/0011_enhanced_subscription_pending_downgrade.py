from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('subscriptions', '0010_usersubscription_payment_method_fields'),
    ]

    # No-op: EnhancedSubscription is not part of this app's migration state here.
    operations = []

