import subprocess
import os
import sys

def run_migrate():
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    
    print("Running migrations...")
    process = subprocess.Popen(
        [sys.executable, "manage.py", "migrate"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8'
    )
    
    for line in process.stdout:
        print(line, end='')
    
    process.wait()
    if process.returncode == 0:
        print("\nMigrations completed successfully!")
    else:
        print(f"\nMigrations failed with exit code {process.returncode}")

if __name__ == '__main__':
    run_migrate()
