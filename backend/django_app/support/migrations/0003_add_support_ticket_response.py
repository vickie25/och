# Generated for SupportTicketResponse (conversation thread on tickets).
# If support_ticket_responses was already created via setup_support_permissions.sql, run:
#   python manage.py migrate support 0002 --fake
# then: python manage.py migrate support

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0002_seed_default_problem_codes'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SupportTicketResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('is_staff', models.BooleanField(default=False)),
                ('created_by_name', models.CharField(db_column='created_by_name', max_length=255, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='support_ticket_responses',
                    to=settings.AUTH_USER_MODEL,
                    db_column='created_by_id',
                )),
                ('ticket', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='responses',
                    to='support.supportticket',
                    db_column='ticket_id',
                )),
            ],
            options={
                'db_table': 'support_ticket_responses',
                'ordering': ['created_at'],
            },
        ),
    ]
