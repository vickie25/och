import paramiko

host = "69.30.235.220"
user = "administrator"
password = "Ongoza@#1"

try:
    print("Checking db.sqlite3 contents...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=60)
    
    def run_sudo(cmd):
        stdin, stdout, stderr = client.exec_command(f"printf '%s\\n' '{password}' | sudo -S -p '' {cmd}")
        return stdout.read().decode('utf-8', 'ignore').strip()

    # Check file size
    print(run_sudo("ls -lh /var/www/och/backend/django_app/db.sqlite3"))
    
    # Query SQLite directly using Python inside the container, or install sqlite3 locally
    sqlite_query = """
import sqlite3
import datetime
try:
    conn = sqlite3.connect('/var/www/och/backend/django_app/db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM api_user;")
    count = cursor.fetchone()[0]
    print(f"Users in SQLite: {count}")

    cursor.execute("SELECT email, role, is_active FROM api_user WHERE email LIKE '%kelvin%';")
    rows = cursor.fetchall()
    for r in rows:
        print(f"FOUND KELVIN: {r}")
        
    conn.close()
except Exception as e:
    print("Error:", e)
"""
    write_cmd = f"cat << 'EOF' > /tmp/check_sqlite.py\n{sqlite_query}\nEOF"
    client.exec_command(write_cmd)
    print("\nExecuting SQLite check...")
    print(run_sudo("python3 /tmp/check_sqlite.py"))

    client.close()
except Exception as e:
    print(f"Error: {e}")
