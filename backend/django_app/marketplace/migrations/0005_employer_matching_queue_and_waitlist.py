import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('marketplace', '0004_employer_contract_currency_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmployerMatchingQueueItem',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('priority_score', models.IntegerField(default=0, db_index=True)),
                ('status', models.CharField(max_length=20, choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed'), ('cancelled', 'Cancelled')], default='pending', db_index=True)),
                ('attempts', models.IntegerField(default=0)),
                ('last_error', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('processed_at', models.DateTimeField(null=True, blank=True)),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='matching_queue', to='marketplace.employercontract', db_index=True)),
                ('requirement', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='matching_queue_item', to='marketplace.candidaterequirement')),
            ],
            options={'db_table': 'employer_matching_queue'},
        ),
        migrations.CreateModel(
            name='EmployerCandidateWaitlist',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('reason', models.CharField(max_length=20, choices=[('exclusive', 'Exclusive to another employer'), ('other', 'Other')], default='exclusive')),
                ('status', models.CharField(max_length=20, choices=[('waiting', 'Waiting'), ('ready', 'Ready'), ('presented', 'Presented'), ('expired', 'Expired'), ('cancelled', 'Cancelled')], default='waiting', db_index=True)),
                ('exclusive_until', models.DateTimeField(null=True, blank=True, db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('candidate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employer_waitlist_entries', to='users.user', db_index=True)),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='candidate_waitlist', to='marketplace.employercontract', db_index=True)),
                ('requirement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='candidate_waitlist', to='marketplace.candidaterequirement', db_index=True)),
            ],
            options={
                'db_table': 'employer_candidate_waitlist',
                'unique_together': {('contract', 'requirement', 'candidate')},
            },
        ),
        migrations.AddIndex(
            model_name='employermatchingqueueitem',
            index=models.Index(fields=['status', 'priority_score', 'created_at'], name='emp_match_queue_status_prio_created_idx'),
        ),
        migrations.AddIndex(
            model_name='employermatchingqueueitem',
            index=models.Index(fields=['contract', 'status'], name='emp_match_queue_contract_status_idx'),
        ),
        migrations.AddIndex(
            model_name='employercandidatewaitlist',
            index=models.Index(fields=['status', 'exclusive_until'], name='emp_waitlist_status_excl_until_idx'),
        ),
        migrations.AddIndex(
            model_name='employercandidatewaitlist',
            index=models.Index(fields=['contract', 'status'], name='emp_waitlist_contract_status_idx'),
        ),
    ]

