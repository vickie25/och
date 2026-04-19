
import os
import sys
import django
import json
from datetime import datetime

# Setup Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

try:
    django.setup()
except Exception as e:
    print(json.dumps({"status": "ASD_FAIL", "error": f"Django setup failed: {str(e)}"}))
    sys.exit(1)

from django.db import connection, transaction
from django.core.management import call_command
from curriculum.models import CurriculumTrack
from foundations.models import FoundationsProgress

def run_asd():
    results = {
        "status": "ASD_PASS",
        "timestamp": datetime.now().isoformat(),
        "audit": [],
        "heals": [],
        "verifications": {}
    }

    try:
        with transaction.atomic():
            # 1. Audit Table Schema
            with connection.cursor() as cursor:
                if connection.vendor == 'postgresql':
                    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'curriculum_tracks' AND column_name = 'slug';")
                else:
                    # SQLite fallback
                    cursor.execute("PRAGMA table_info(curriculum_tracks);")
                    columns = [row[1] for row in cursor.fetchall()]
                    has_slug = 'slug' in columns
                
                if (connection.vendor == 'postgresql' and cursor.fetchone()) or (connection.vendor != 'postgresql' and has_slug):
                    results["audit"].append("Found 'slug' column in curriculum_tracks.")
                    # Fake curriculum 0005 because slug already exists
                    # Check migration history
                    if connection.vendor == 'postgresql':
                        cursor.execute("SELECT name FROM django_migrations WHERE app = 'curriculum' AND name = '0005_curriculumtrack_slug_title_order_thumbnail';")
                        migration_found = cursor.fetchone()
                    else:
                        cursor.execute("SELECT name FROM django_migrations WHERE app = 'curriculum' AND name = '0005_curriculumtrack_slug_title_order_thumbnail';")
                        migration_found = cursor.fetchone()

                    if not migration_found:
                        results["heals"].append("Faking migration 0005_curriculumtrack_slug_title_order_thumbnail")
                        call_command('migrate', 'curriculum', '0005_curriculumtrack_slug_title_order_thumbnail', '--fake', interactive=False)
                
                # Check for Users migration drift
                cursor.execute("SELECT name FROM django_migrations WHERE app = 'users' AND name = '0013_merge_0010_0012';")
                if not cursor.fetchone():
                    results["heals"].append("Attempting to run/fake user migrations to heal auth drift")
                    call_command('migrate', 'users', interactive=False)

            # 2. Run all pending migrations
            results["audit"].append("Running all pending migrations...")
            call_command('migrate', interactive=False)

            # 3. Verify Foundations -> Tier 2 Logic
            results["verifications"]["track_count"] = CurriculumTrack.objects.count()
            foundation_track = CurriculumTrack.objects.filter(tier=2).first()
            if foundation_track:
                results["verifications"]["foundation_check"] = "SUCCESS: Found Tier 2 track for student orientation."
            else:
                results["verifications"]["foundation_check"] = "WARNING: No Tier 2 track found. Please check Curriculum admin."

            # 4. Check for Ghost processes (via DB connection count)
            with connection.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE datname = %s;", [connection.settings_dict['NAME']])
                conn_count = cursor.fetchone()[0]
                results["verifications"]["db_connections"] = conn_count
                if conn_count > 20: 
                    results["audit"].append(f"HIGH CONNECTION COUNT: {conn_count}. Ghost servers likely active.")

    except Exception as e:
        results["status"] = "ASD_FAIL"
        results["error"] = str(e)

    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    run_asd()
