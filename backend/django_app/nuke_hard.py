import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

def nuke_hard():
    print("WARNING: This will DROP and RECREATE the public schema!")
    with connection.cursor() as cursor:
        cursor.execute("DROP SCHEMA public CASCADE;")
        cursor.execute("CREATE SCHEMA public;")
        cursor.execute("GRANT ALL ON SCHEMA public TO public;")
        # Set permissions for the current user (the one in .env)
        from django.conf import settings
        db_user = settings.DATABASES['default']['USER']
        cursor.execute(f"GRANT ALL ON SCHEMA public TO {db_user};")
        print("Public schema dropped and recreated.")

if __name__ == '__main__':
    nuke_hard()
