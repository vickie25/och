from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('marketplace', '0005_employer_matching_queue_and_waitlist'),
    ]

    operations = [
        migrations.AddField(
            model_name='employercontract',
            name='exclusivity_started_at',
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='employercontract',
            name='exclusivity_ends_at',
            field=models.DateField(null=True, blank=True, db_index=True),
        ),
        migrations.AddField(
            model_name='employercontract',
            name='exclusivity_scope',
            field=models.CharField(default='global', max_length=64, help_text='Exclusivity scope key (allows non-competing employers to have exclusivity in different scopes)'),
        ),
        migrations.AddField(
            model_name='replacementguarantee',
            name='departure_type',
            field=models.CharField(
                default='candidate_initiated',
                max_length=30,
                choices=[
                    ('candidate_initiated', 'Candidate-initiated departure'),
                    ('employer_performance', 'Employer terminated for performance'),
                    ('other', 'Other'),
                ],
                help_text='Used to enforce guarantee exclusions',
            ),
        ),
    ]

