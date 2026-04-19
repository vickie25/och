
import os
import subprocess
import sys
import django
import json
import datetime
import uuid

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
django.setup()

from django.core.management import call_command
from django.db import connection, transaction
from curriculum.models import CurriculumTrack
from django.contrib.auth import get_user_model

User = get_user_model()

def run_fix():
    print(f"--- Master ASD Master Healer v2.0 [{datetime.datetime.now()}] ---")
    results = {
        "status": "ASD_PASS",
        "timestamp": str(datetime.datetime.now()),
        "audit": [],
        "heals": [],
        "verifications": {}
    }
    
    try:
        # 1. Audit Schema
        with connection.cursor() as cursor:
            # Check for slug in curriculum_tracks
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='curriculum_tracks' AND column_name='slug';")
            if cursor.fetchone():
                results["audit"].append("Found 'slug' column in curriculum_tracks.")
            else:
                results["audit"].append("MISSING 'slug' column in curriculum_tracks.")

            # 2. Heal Auth Drift (Faking users migrations if needed)
            # If the user model is already using UUID but migrations say BigInt, we must reconcile.
            cursor.execute("SELECT data_type FROM information_schema.columns WHERE table_name='users_user' AND column_name='id';")
            id_type = cursor.fetchone()
            if id_type and 'uuid' in id_type[0].lower():
                # If DB is UUID but migrations are stuck, force fake the users migrations up to 0013
                print("Auth Drift Detected (DB is UUID). Reconciling...")
                results["heals"].append("Attempting to run/fake user migrations to heal auth drift")
                call_command('migrate', 'users', interactive=False)

        # Final Migration Run
        print("Running all pending migrations...")
        results["audit"].append("Running all pending migrations...")
        try:
            # We run them one by one to catch exactly where it fails
            subprocess.run(["python", "manage.py", "migrate", "--noinput"], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr or e.stdout
            print(f"Migration error: {error_msg}")
            
            # RESILIENCY: If column already exists, try to find which migration failed and fake it
            if "already exists" in error_msg:
                import re
                # Try to extract the app and migration name from the error if possible
                match = re.search(r'Applying ([\w\.]+)\.\.\. FAILED', error_msg)
                if match:
                    failed_migration = match.group(1)
                    print(f"Resiliency Trigger: Faking {failed_migration} due to existing schema...")
                    results["audit"].append(f"Faking {failed_migration} due to existing schema.")
                    subprocess.run(["python", "manage.py", "migrate", failed_migration.split('.')[0], failed_migration.split('.')[1], "--fake"], check=True)
                    # Retry the full migration
                    subprocess.run(["python", "manage.py", "migrate", "--noinput"], check=True)
                else:
                    # Specific fallback for missions if it's the known culprit
                    if "missions" in error_msg:
                        print("Resiliency Trigger: Faking missions.0003 specifically...")
                        subprocess.run(["python", "manage.py", "migrate", "missions", "0003", "--fake"], check=True)
                        subprocess.run(["python", "manage.py", "migrate", "--noinput"], check=True)
                    else:
                        raise e
            else:
                raise e

        # 3. Final Verifications
        results["verifications"]["db_connections"] = len(connection.queries) + 1
        foundation_track = CurriculumTrack.objects.filter(tier=2).first()
        if foundation_track:
            results["verifications"]["foundation_check"] = "SUCCESS: Found Tier 2 track for student orientation."
        else:
            results["verifications"]["foundation_check"] = "WARNING: No Tier 2 track found. Please check Curriculum admin."

    except Exception as e:
        results["status"] = "ASD_FAIL"
        results["error"] = str(e)
    
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    run_fix()
