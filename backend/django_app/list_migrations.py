import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

with connection.cursor() as cursor:
    cursor.execute("SELECT app, name FROM django_migrations ORDER BY app, name")
    migrations = cursor.fetchall()
    print("Applied Migrations:")
    for app, name in migrations:
        print(f"- {app}: {name}")
