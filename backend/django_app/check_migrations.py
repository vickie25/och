from django.db import connection
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

with connection.cursor() as cursor:
    cursor.execute("SELECT app, name, applied FROM django_migrations ORDER BY applied DESC")
    migrations = cursor.fetchall()
    print(f"{'App':<20} {'Migration':<50} {'Applied'}")
    print("-" * 100)
    for app, name, applied in migrations:
        print(f"{app:<20} {name:<50} {applied}")
