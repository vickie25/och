import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

with connection.cursor() as cursor:
    print("Checking for django_session table...")
    cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'django_session')")
    exists = cursor.fetchone()[0]
    print(f"django_session exists: {exists}")
    
    if not exists:
        print("Table missing. Deleting sessions migrations from django_migrations to re-run them...")
        cursor.execute("DELETE FROM django_migrations WHERE app = 'sessions'")
        print("Deleted. Now you should run 'python manage.py migrate sessions'")
