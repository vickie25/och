from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('marketplace', '0003_successfulplacement_probation_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='employercontracttier',
            name='currency',
            field=models.CharField(default='KES', max_length=3),
        ),
        migrations.AddField(
            model_name='employercontract',
            name='currency',
            field=models.CharField(default='KES', max_length=3),
        ),
    ]

