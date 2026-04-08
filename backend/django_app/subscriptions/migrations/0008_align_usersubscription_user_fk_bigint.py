# Align UserSubscription.user FK with local/dev PostgreSQL schema where user_id references users.id (bigint).
# Some environments use users.uuid_id; this migration restores the Django state to match the actual DB here.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("subscriptions", "0007_ensure_promotional_codes_eligible_plans_m2m"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name="usersubscription",
                    name="user",
                    field=models.OneToOneField(
                        db_column="user_id",
                        db_index=True,
                        help_text="FK column stores users.id (bigint) in local/dev DB.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subscription",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]

