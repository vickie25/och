import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from django.db import connection
from django.core.management import call_command

def reset_and_fix():
    print("1. Clearing ALL migration history to resolve deep graph conflicts...")
    with connection.cursor() as cursor:
        cursor.execute("TRUNCATE django_migrations;")
        print("Emptied the django_migrations table.")
        
    print("\n2. Re-faking the migration history ...")
    APPS = [
        "contenttypes", "auth", "admin", "sessions",
        "organizations", "users", "subscriptions", "programs", "missions", "progress",
        "student_dashboard", "mentorship", "mentorship_coordination", "profiler",
        "coaching", "talentscope", "sponsor_dashboard", "director_dashboard",
        "dashboard", "community", "recipes", "curriculum"
    ]
    
    for app in APPS:
        try:
            print(f"Faking migrations for {app}...")
            call_command('migrate', app, '--fake', verbosity=0)
        except Exception as e:
            print(f"   (Failed or skipped for {app}: {e})")

    print("\n3. Running final actual migrations to update any missing tables...")
    try:
        call_command('migrate', verbosity=1)
        print("\nSUCCESS: Database is fully synced!")
    except Exception as e:
        import traceback
        with open('migration_error_log.txt', 'a') as f:
            f.write(traceback.format_exc())
            f.write(f"\nERROR: {e}\n")
        print("\n[ERROR] Final migration step failed. Error saved to migration_error_log.txt")

if __name__ == '__main__':
    reset_and_fix()
