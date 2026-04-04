# Model had module_id without a matching migration (ORM expected column on missions table).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('missions', '0005_add_mastery_enhancements'),
    ]

    operations = [
        migrations.AddField(
            model_name='mission',
            name='module_id',
            field=models.UUIDField(
                blank=True,
                help_text='UUID of curriculum module',
                null=True,
            ),
        ),
    ]
