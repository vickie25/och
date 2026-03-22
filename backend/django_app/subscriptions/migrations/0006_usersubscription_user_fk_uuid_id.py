# Align UserSubscription.user FK with PostgreSQL schema where user_id references users.uuid_id
# (see migrations_sql/FIX_USER_SUBSCRIPTIONS_USER_ID_UUID_PG.sql). No DDL: DB is already updated manually.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0005_student_stream_catalog_and_policy'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name='usersubscription',
                    name='user',
                    field=models.OneToOneField(
                        db_column='user_id',
                        db_index=True,
                        help_text='FK column stores users.uuid_id (see migrations_sql/FIX_USER_SUBSCRIPTIONS_USER_ID_UUID_PG.sql).',
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='subscription',
                        to=settings.AUTH_USER_MODEL,
                        to_field='uuid_id',
                    ),
                ),
            ],
        ),
    ]
