# Generated manually to align DB schema with users.models.User

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0006_sqlite_compatible"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        'ALTER TABLE "users" '
                        'ADD COLUMN IF NOT EXISTS "gender" varchar(20) NULL;'
                    ),
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    sql=(
                        'ALTER TABLE "users" '
                        'ADD COLUMN IF NOT EXISTS "onboarded_email_status" varchar(20) NULL;'
                    ),
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    sql=(
                        'CREATE INDEX IF NOT EXISTS "users_onboarded_email_status_idx" '
                        'ON "users" ("onboarded_email_status");'
                    ),
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="user",
                    name="gender",
                    field=models.CharField(
                        blank=True,
                        choices=[
                            ("male", "Male"),
                            ("female", "Female"),
                            ("other", "Other"),
                            ("prefer_not_to_say", "Prefer not to say"),
                        ],
                        help_text="User gender (optional)",
                        max_length=20,
                        null=True,
                    ),
                ),
                migrations.AddField(
                    model_name="user",
                    name="onboarded_email_status",
                    field=models.CharField(
                        blank=True,
                        choices=[("sent", "Sent"), ("sent_and_seen", "Sent & Seen")],
                        db_index=True,
                        help_text=(
                            "Status of onboarding email: null (not sent), sent (sent but not opened), "
                            "sent_and_seen (sent and opened)"
                        ),
                        max_length=20,
                        null=True,
                    ),
                ),
            ],
        ),
    ]
