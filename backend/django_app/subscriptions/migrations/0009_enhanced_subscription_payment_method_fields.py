from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0008_align_usersubscription_user_fk_bigint'),
    ]

    # NOTE:
    # This migration references an `EnhancedSubscription` model that is not part of the
    # subscriptions app's registered migration state in this repo (it was introduced
    # in an experimental billing engine module). Keep as a no-op so the overall
    # migration graph can apply for local dev.
    operations = []

