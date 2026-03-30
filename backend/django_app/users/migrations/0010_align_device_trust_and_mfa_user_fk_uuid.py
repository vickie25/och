# Generated manually to align migration state with DB schema.
#
# Background:
# - Some environments have a DB dump where the `users.uuid_id` column exists (added via SQL)
#   but the Django migration graph does not include an AddField for it.
# - Other tables (device_trust, mfa_codes) were migrated to reference users.uuid_id.
#
# This migration updates Django's *state* only (no DB operations) so ORM queries don't try to
# compare UUID columns to integer IDs.

import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0009_add_gender_and_onboarded_email_status"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name="user",
                    name="uuid_id",
                    field=models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        unique=True,
                        db_index=True,
                    ),
                ),
                migrations.AlterField(
                    model_name="devicetrust",
                    name="user",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="trusted_devices",
                        to=settings.AUTH_USER_MODEL,
                        to_field="uuid_id",
                    ),
                ),
                migrations.AlterField(
                    model_name="mfacode",
                    name="user",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="mfa_codes",
                        to=settings.AUTH_USER_MODEL,
                        to_field="uuid_id",
                    ),
                ),
            ],
        ),
    ]
