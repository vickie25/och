from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0009_add_gender_and_onboarded_email_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mfacode",
            name="code",
            field=models.CharField(max_length=64, db_index=True),
        ),
    ]
