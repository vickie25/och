import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('organizations', '0005_contract_amendments_and_pending_renewal_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='institutionalacademiccalendar',
            name='summer_billing_mode',
            field=models.CharField(
                choices=[('full_rate', 'Full Rate'), ('reduced_rate', 'Reduced Rate'), ('pause', 'Pause Billing')],
                default='full_rate',
                help_text='How to handle billing during summer break months',
                max_length=20,
            ),
        ),
    ]

