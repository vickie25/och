import os
import paramiko

def manual_fix():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))

    # 1. Clear migrations and drop tables on remote DB
    print("Step 1 & 2: Cleaning remote DB...")
    tables = [
        'curriculum_activities', 'curriculummodules', 'curriculum_tracks', 
        'lessons', 'module_missions', 'curriculum_recipe_recommendations', 
        'user_lesson_progress', 'user_curriculum_mission_progress', 
        'user_module_progress', 'user_track_progress', 
        'cross_track_program_progress', 'cross_track_submissions', 
        'user_lesson_bookmarks', 'curriculum_mentor_feedback', 
        'curriculum_levels', 'curriculum_videos', 'curriculum_quizzes', 
        'strategic_sessions', 'user_track_enrollments', 'curriculum_content', 
        'user_content_progress', 'curriculum_track_mentor_assignments'
    ]
    
    drop_commands = [f"DROP TABLE IF EXISTS {t} CASCADE;" for t in tables]
    full_sql = "DELETE FROM django_migrations WHERE app = 'curriculum';" + " ".join(drop_commands)
    
    client.exec_command(f"echo '{full_sql}' > /tmp/drop_final.sql")
    client.exec_command("echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker cp /tmp/drop_final.sql hub_prod_postgres:/tmp/drop_final.sql")
    stdin_d, stdout_d, stderr_d = client.exec_command("echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker exec hub_prod_postgres psql -h 38.247.138.250 -U postgres -d ongozacyberhub -f /tmp/drop_final.sql")
    print('--- PSQL OUTPUT ---')
    print(stdout_d.read().decode())
    print(stderr_d.read().decode())

    # 2. Run migrations
    print("Step 3: Running migrations...")
    stdin, stdout, stderr = client.exec_command("echo os.environ.get('PRODUCTION_SSH_PASSWORD', '') | sudo -S docker exec hub_prod_django python manage.py migrate curriculum")
    
    print('--- MIGRATE STDOUT ---')
    print(stdout.read().decode())
    print('--- MIGRATE STDERR ---')
    print(stderr.read().decode())
    client.close()

if __name__ == "__main__":
    manual_fix()
