import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

def check_table():
    with connection.cursor() as cursor:
        cursor.execute("SELECT n.nspname as schema, c.relname as relation, c.relkind FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'public'")
        relations = cursor.fetchall()
        print(f"Relations in public schema: {relations}")
        
        # Check if the specific offending index exists
        cursor.execute("SELECT count(*) FROM pg_class WHERE relname = 'curriculum_tracks_slug_869ab9cd_like'")
        count = cursor.fetchone()[0]
        print(f"Offending index 'curriculum_tracks_slug_869ab9cd_like' exists: {count > 0}")

if __name__ == '__main__':
    check_table()
