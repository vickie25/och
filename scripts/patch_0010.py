import os
import paramiko

def patch_0010():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))

    patch = """# Generated manually to fix: duplicate column error
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('curriculum', '0009_curriculummodule_fields'),
    ]
    operations = []
"""
    escaped_patch = patch.replace("'", "'\\''")
    client.exec_command(f"echo '{escaped_patch}' > /tmp/0010_patch.py")
    client.exec_command("echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker cp /tmp/0010_patch.py hub_prod_django:/app/curriculum/migrations/0010_curriculummodule_supporting_recipes_slug_lock.py")
    client.close()

if __name__ == "__main__":
    patch_0010()
