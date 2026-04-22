import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from django.db import connection

def fix_migration_state():
    with connection.cursor() as cursor:
        # Check current state
        cursor.execute("SELECT app, name FROM django_migrations WHERE app = 'dashboard' ORDER BY name;")
        current = cursor.fetchall()
        print("Current dashboard migrations in database:")
        for _app, name in current:
            print(f"  - {name}")

        # Remove the incorrectly applied 0004 migration record
        print("\nRemoving incorrectly applied 0004_merge_20260209_1202 migration record from history...")
        cursor.execute("DELETE FROM django_migrations WHERE app = 'dashboard' AND name = '0004_merge_20260209_1202';")
        affected = cursor.rowcount
        print(f"Removed {affected} migration record(s)")

if __name__ == '__main__':
    try:
        fix_migration_state()
        print("\nDone! You can now run migrations normally.")
    except Exception as e:
        print(f"Error: {e}")
