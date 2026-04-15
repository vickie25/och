from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [
        ('marketplace', '0002_jobapplication'),
    ]

    operations = [
        migrations.AddField(
            model_name='successfulplacement',
            name='probation_days',
            field=models.IntegerField(
                default=90,
                validators=[django.core.validators.MinValueValidator(1)],
            ),
        ),
        migrations.AddField(
            model_name='successfulplacement',
            name='probation_end_date',
            field=models.DateField(null=True, blank=True, db_index=True),
        ),
        migrations.AddField(
            model_name='successfulplacement',
            name='confirmed_at',
            field=models.DateTimeField(null=True, blank=True, db_index=True),
        ),
    ]

