import paramiko

def audit_curriculum():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    python_script = """
import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

tables = [
    'curriculum_tracks', 'curriculum_levels', 'curriculum_videos', 
    'curriculum_quizzes', 'curriculummodules', 'lessons', 
    'curriculum_content', 'user_content_progress', 'module_missions', 
    'curriculum_recipe_recommendations', 'user_track_progress'
]

results = {}
with connection.cursor() as cursor:
    for t in tables:
        try:
            cursor.execute(f'SELECT count(*) FROM {t}')
            results[t] = cursor.fetchone()[0]
        except Exception as e:
            results[t] = f"MISSING/ERROR: {str(e).splitlines()[0]}"
            connection.rollback()

print("AUDIT_RESULTS:", results)
"""
    
    print("Uploading audit script...")
    escaped_script = python_script.replace("'", "'\\''")
    remote_cmd = f"echo '{escaped_script}' > /tmp/audit_curriculum.py"
    client.exec_command(remote_cmd)
    
    print("Running audit script inside container...")
    cmd = "echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker cp /tmp/audit_curriculum.py hub_prod_django:/app/audit_curriculum.py"
    client.exec_command(cmd)
    
    cmd2 = "echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker exec hub_prod_django python /app/audit_curriculum.py"
    stdin2, stdout2, stderr2 = client.exec_command(cmd2)
    
    print("--- Audit Results ---")
    print(stdout2.read().decode())
    print(stderr2.read().decode())
    
    client.close()

if __name__ == "__main__":
    audit_curriculum()
