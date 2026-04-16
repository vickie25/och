from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('marketplace', '0003_successfulplacement_probation_fields'),
    ]

    # See note in 0003_successfulplacement_probation_fields: these contract models
    # are not part of the marketplace app's registered models in this codebase.
    operations = []

