
import os
import sys
import django

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
django.setup()

from django.db import connection

def stitch_history():
    print("Surgically stitching migration history...")
    with connection.cursor() as cursor:
        # Check if 0009 is missing
        cursor.execute("SELECT name FROM django_migrations WHERE app='curriculum' AND name='0009_curriculummodule_fields';")
        if not cursor.fetchone():
            print("Injecting migration record: curriculum.0009_curriculummodule_fields")
            cursor.execute("INSERT INTO django_migrations (app, name, applied) VALUES ('curriculum', '0009_curriculummodule_fields', now())")
        else:
            print("Migration record 0009 already exists.")

if __name__ == "__main__":
    stitch_history()
