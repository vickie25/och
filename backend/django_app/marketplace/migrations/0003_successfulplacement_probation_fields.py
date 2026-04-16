from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('marketplace', '0002_jobapplication'),
    ]

    # NOTE:
    # This migration originally attempted to add fields to a `SuccessfulPlacement`
    # model that is not part of the marketplace app's registered models
    # (it is defined outside `marketplace/models.py` and is not imported by the app).
    # That breaks Django's migration state and prevents the entire migration graph
    # from applying. Keep this as a no-op to allow the platform to migrate.
    operations = []

