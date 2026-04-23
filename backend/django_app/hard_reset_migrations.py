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
        
    print("\n2. Faking core migrations in correct dependency order...")
    # These apps already have tables in the database
    CORE_APPS = [
        "contenttypes",
        "users",
        "auth",
        "admin",
        "sessions",
    ]
    
    for app in CORE_APPS:
        try:
            print(f"Faking migrations for {app}...")
            call_command('migrate', app, '--fake', verbosity=0)
        except Exception as e:
            print(f"   (Failed for {app}: {e})")

    print("\n3. Running actual migrations for all other apps...")
    try:
        # Now run normal migrate for everything else. 
        # Django will see that others have no records in django_migrations and no tables,
        # so it will create them.
        call_command('migrate', verbosity=1)
        print("\nSUCCESS: Database is fully synced!")
    except Exception as e:
        import traceback
        print(f"\n[ERROR] Migration failed: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    reset_and_fix()
