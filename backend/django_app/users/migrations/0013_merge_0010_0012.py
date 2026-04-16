"""
Merge migration for users app.

This resolves multiple leaf nodes in the migration graph:
- 0010_align_device_trust_and_mfa_user_fk_uuid
- 0012_force_device_trust_user_id_uuid
"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0010_align_device_trust_and_mfa_user_fk_uuid"),
        ("users", "0012_force_device_trust_user_id_uuid"),
    ]

    operations = []

