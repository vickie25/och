# Cohort one-time fee + enrollment window (Stream D / financial spec)

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0017_create_certificate_table'),
    ]

    operations = [
        migrations.AddField(
            model_name='cohort',
            name='enrollment_fee',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='One-time cohort fee (USD). If 0, paid checkout uses the program default_price when set.',
                max_digits=10,
                validators=[django.core.validators.MinValueValidator(0)],
            ),
        ),
        migrations.AddField(
            model_name='cohort',
            name='enrollment_opens_at',
            field=models.DateTimeField(
                blank=True,
                help_text='If set, self-serve enrollment cannot begin before this instant (UTC).',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='cohort',
            name='enrollment_closes_at',
            field=models.DateTimeField(
                blank=True,
                help_text='If set, self-serve enrollment cannot continue after this instant (UTC).',
                null=True,
            ),
        ),
    ]
