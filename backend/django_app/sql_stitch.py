
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
        migrations_to_stitch = [
            '0008_curriculumtrack_slug_backfill',
            '0009_curriculummodule_fields',
            '0010_curriculummodule_supporting_recipes_slug_lock'
        ]
        
        for name in migrations_to_stitch:
            cursor.execute("SELECT name FROM django_migrations WHERE app='curriculum' AND name=%s;", [name])
            if not cursor.fetchone():
                print(f"Injecting migration record: curriculum.{name}")
                cursor.execute("INSERT INTO django_migrations (app, name, applied) VALUES ('curriculum', %s, now())", [name])
            else:
                print(f"Migration record {name} already exists.")

if __name__ == "__main__":
    stitch_history()
