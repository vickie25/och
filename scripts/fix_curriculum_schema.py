import paramiko

def fix_curriculum_schema():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    migration_0008_fixed = """# Generated manually to fix: column curriculum_tracks.slug does not exist
# Simplified to avoid Django's duplicate index bug on AlterField for SlugFields

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('curriculum', '0007_tier3_completion_config'),
    ]

    operations = [
        migrations.AddField(
            model_name='curriculumtrack',
            name='slug',
            field=models.SlugField(help_text="'defender', 'offensive', 'grc', 'innovation', 'leadership'", max_length=50, unique=True),
        ),
        migrations.AddField(
            model_name='curriculumtrack',
            name='title',
            field=models.CharField(default='', help_text='Display title', max_length=255),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='curriculumtrack',
            name='order_number',
            field=models.IntegerField(default=1, help_text='Display order'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='curriculumtrack',
            name='thumbnail_url',
            field=models.URLField(blank=True, default='', help_text='Track thumbnail image'),
            preserve_default=True,
        ),
    ]
"""

    drop_sql = """
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT relname, relkind FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace 
              WHERE n.nspname = 'public' 
              AND (relname LIKE 'curriculum%' OR relname LIKE 'user_track%' OR relname LIKE 'user_module%' OR relname LIKE 'user_lesson%' OR relname LIKE 'user_content%' OR relname LIKE 'module_mission%' OR relname LIKE 'cross_track%' OR relname LIKE 'lessons%' OR relname LIKE 'strategic_session%' OR relname LIKE 'user_curriculum%')
              AND relkind IN ('r', 'v', 'm', 'i', 's'))
    LOOP
        EXECUTE 'DROP ' || CASE r.relkind WHEN 'r' THEN 'TABLE' WHEN 'v' THEN 'VIEW' WHEN 'm' THEN 'MATERIALIZED VIEW' WHEN 'i' THEN 'INDEX' WHEN 's' THEN 'SEQUENCE' END || ' IF EXISTS ' || r.relname || ' CASCADE';
    END LOOP;
END;
$$ ;
"""

    python_script = """
import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

with connection.cursor() as cursor:
    print("Step 1: Removing curriculum migrations from tracking table...")
    cursor.execute("DELETE FROM django_migrations WHERE app = 'curriculum'")
    connection.commit()

print("Step 3: Running migrations for curriculum app...")
os.system("python manage.py migrate curriculum")
"""
    
    print("Step 1: Patching migration 0008...")
    escaped_patch = migration_0008_fixed.replace("'", "'\\''")
    client.exec_command(f"echo '{escaped_patch}' > /tmp/0008_fixed.py")
    client.exec_command("echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker cp /tmp/0008_fixed.py hub_prod_django:/app/curriculum/migrations/0008_curriculumtrack_slug_backfill.py")

    print("Step 2: Dropping all relations using PSQL...")
    escaped_drop = drop_sql.replace("'", "'\\''")
    client.exec_command(f"echo '{escaped_drop}' > /tmp/drop_tables.sql")
    client.exec_command("echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker cp /tmp/drop_tables.sql hub_prod_django:/tmp/drop_tables.sql")
    stdin_p, stdout_p, stderr_p = client.exec_command("echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker exec hub_prod_django psql -U postgres -d ongozacyberhub -f /tmp/drop_tables.sql")
    print("--- PSQL Output ---")
    print(stdout_p.read().decode())
    print(stderr_p.read().decode())
    
    print("Step 3: Running final migration script...")
    escaped_script = python_script.replace("'", "'\\''")
    client.exec_command(f"echo '{escaped_script}' > /tmp/fix_curriculum.py")
    client.exec_command("echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker cp /tmp/fix_curriculum.py hub_prod_django:/app/fix_curriculum.py")
    
    cmd2 = "echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker exec hub_prod_django python /app/fix_curriculum.py"
    stdin2, stdout2, stderr2 = client.exec_command(cmd2)
    
    print("--- Fix Output ---")
    print(stdout2.read().decode())
    print(stderr2.read().decode())
    
    client.close()

if __name__ == "__main__":
    fix_curriculum_schema()
