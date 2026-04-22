import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from django.db import connection

def fix_migration_state():
    with connection.cursor() as cursor:
        print("\nRemoving incorrectly applied 0015_trackmentorassignment migration record from history...")
        cursor.execute("DELETE FROM django_migrations WHERE app = 'programs' AND name = '0015_trackmentorassignment';")
        print(f"Removed {cursor.rowcount} migration record(s)")

if __name__ == '__main__':
    fix_migration_state()
