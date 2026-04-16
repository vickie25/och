import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
        ('organizations', '0001_initial'),
    ]

    operations = [
        # Tables were created outside migrations in some environments.
        # Keep DB operations as a no-op, but provide migration state so other
        # apps can reference programs.Cohort during migration planning.
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL("SELECT 1;", reverse_sql="SELECT 1;"),
            ],
            state_operations=[
                migrations.CreateModel(
                    name='Program',
                    fields=[
                        ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                    ],
                    options={
                        'db_table': 'programs',
                        'managed': False,
                    },
                ),
                migrations.CreateModel(
                    name='Track',
                    fields=[
                        ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                    ],
                    options={
                        'db_table': 'tracks',
                        'managed': False,
                    },
                ),
                migrations.CreateModel(
                    name='Cohort',
                    fields=[
                        ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                    ],
                    options={
                        'db_table': 'cohorts',
                        'managed': False,
                    },
                ),
                migrations.CreateModel(
                    name='Enrollment',
                    fields=[
                        ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                    ],
                    options={
                        'db_table': 'enrollments',
                        'managed': False,
                    },
                ),
            ],
        ),
    ]