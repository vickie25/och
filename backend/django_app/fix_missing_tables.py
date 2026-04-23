import os
import django
from django.db import connection
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from django.apps import apps

def fix_missing_tables():
    with connection.cursor() as cursor:
        # Get all existing tables
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        existing_tables = {row[0] for row in cursor.fetchall()}
        
    print(f"Found {len(existing_tables)} existing tables.")
    
    apps_to_unfake = set()
    
    # Iterate over all models and check if their table exists
    for model in apps.get_models():
        table_name = model._meta.db_table
        if table_name not in existing_tables:
            app_label = model._meta.app_label
            if app_label not in ['admin', 'auth', 'contenttypes', 'sessions', 'messages', 'staticfiles']:
                apps_to_unfake.add(app_label)
                print(f"Table '{table_name}' for model '{model.__name__}' in app '{app_label}' is MISSING.")

    if not apps_to_unfake:
        print("No missing tables found for installed apps.")
        return

    print(f"\nClearing migration records for: {', '.join(apps_to_unfake)}")
    
    with connection.cursor() as cursor:
        for app in apps_to_unfake:
            cursor.execute("DELETE FROM django_migrations WHERE app = %s", [app])
    
    print("\nRunning migrations for affected apps...")
    for app in sorted(apps_to_unfake):
        print(f"Migrating {app}...")
        try:
            call_command('migrate', app, verbosity=1)
        except Exception as e:
            print(f"Error migrating {app}: {e}")

if __name__ == '__main__':
    fix_missing_tables()
