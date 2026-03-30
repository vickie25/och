from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0010_align_device_trust_and_mfa_user_fk_uuid"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mfacode",
            name="code",
            field=models.CharField(max_length=64, db_index=True),
        ),
    ]
