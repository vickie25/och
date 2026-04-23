import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

with connection.cursor() as cursor:
    cursor.execute("SELECT name, display_name FROM roles")
    roles = cursor.fetchall()
    print("Available Roles:")
    for name, display in roles:
        print(f"- {name} ({display})")
