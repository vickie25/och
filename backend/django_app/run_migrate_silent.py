import os
import sys
import io
from django.core.management import execute_from_command_line

def run_migrate_silent():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
    
    # Redirect stdout and stderr to a string buffer to avoid encoding issues on terminal
    buf = io.StringIO()
    sys.stdout = buf
    sys.stderr = buf
    
    try:
        execute_from_command_line(['manage.py', 'migrate'])
    except Exception as e:
        sys.__stdout__.write(f"Migration failed: {str(e)}\n")
    finally:
        # Restore stdout/stderr
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        
        # Save output to a file
        with open('migrate_silent_output.txt', 'w', encoding='utf-8') as f:
            f.write(buf.getvalue())
        
        print("Migration process finished. Check migrate_silent_output.txt for details.")

if __name__ == '__main__':
    run_migrate_silent()
