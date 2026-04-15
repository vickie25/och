import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('organizations', '0006_academic_calendar_alignment_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='InstitutionalSCIMToken',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('token_hash', models.CharField(max_length=64, db_index=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_used_at', models.DateTimeField(null=True, blank=True)),
                ('contract', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='scim_token', to='organizations.institutionalcontract')),
            ],
            options={'db_table': 'institutional_scim_tokens'},
        ),
        migrations.CreateModel(
            name='InstitutionalSCIMUser',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('external_id', models.CharField(max_length=255, db_index=True)),
                ('is_active', models.BooleanField(default=True)),
                ('raw_profile', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scim_users', to='organizations.institutionalcontract')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='institutional_scim_mappings', to='users.user')),
            ],
            options={
                'db_table': 'institutional_scim_users',
                'unique_together': {('contract', 'external_id'), ('contract', 'user')},
            },
        ),
        migrations.CreateModel(
            name='InstitutionalSCIMEvent',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('external_id', models.CharField(max_length=255, blank=True, default='')),
                ('event_type', models.CharField(max_length=20, choices=[('create', 'Create'), ('update', 'Update'), ('deactivate', 'Deactivate'), ('reactivate', 'Reactivate')])),
                ('success', models.BooleanField(default=True)),
                ('error', models.TextField(blank=True, default='')),
                ('payload', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scim_events', to='organizations.institutionalcontract')),
            ],
            options={'db_table': 'institutional_scim_events'},
        ),
        migrations.AddIndex(
            model_name='institutionalscimuser',
            index=models.Index(fields=['contract', 'external_id'], name='inst_scim_u_contract_external_id_idx'),
        ),
        migrations.AddIndex(
            model_name='institutionalscimuser',
            index=models.Index(fields=['contract', 'is_active'], name='inst_scim_u_contract_is_active_idx'),
        ),
        migrations.AddIndex(
            model_name='institutionalscimevent',
            index=models.Index(fields=['contract', 'created_at'], name='inst_scim_e_contract_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='institutionalscimevent',
            index=models.Index(fields=['contract', 'event_type'], name='inst_scim_e_contract_event_type_idx'),
        ),
    ]

