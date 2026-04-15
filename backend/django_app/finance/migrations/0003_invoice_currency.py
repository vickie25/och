from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('finance', '0002_pricing_tiers'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='currency',
            field=models.CharField(default='KES', max_length=3),
        ),
    ]

