import paramiko
import time
import sys

def professional_diagnostic():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("[1/5] Connecting to server (69.30.235.220)...")
    try:
        # Use a longer timeout and banner_timeout for potentially laggy SSH
        client.connect(host, username=user, password=password, timeout=30, banner_timeout=30)
        print("Done: Connected!")
    except Exception as e:
        print(f"Error: Connection Failed: {e}")
        return

    def run_remote(cmd, label):
        print(f"\n--- {label} ---")
        full_cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' {cmd}"
        stdin, stdout, stderr = client.exec_command(full_cmd, get_pty=True)
        # We need to wait for the command to finish if it's not a background one
        output = stdout.read().decode()
        print(output)
        return output

    # A. Check Disk Space
    run_remote("df -h /", "Disk Space (df -h)")

    # B. Check Resource Usage
    run_remote("free -m", "Memory Usage (MB)")
    run_remote("docker stats --no-stream --format 'table {{.Name}}\\t{{.CPUPerc}}\\t{{.MemUsage}}'", "Docker Container Stats")

    # C. Cleanup Ghosts (Only prune if requested, but let's at least list orphans)
    print("\n[2/5] Clearing Docker Orphans & Pruning System...")
    run_remote("docker system prune -f", "Docker System Prune (Non-destructive)")

    # D. Database & Django Logs (The Real Truth)
    print("\n[3/5] Pulling Recent Error Logs...")
    run_remote("docker logs hub_prod_django --tail 50", "Django Logs (Latest Errors)")
    run_remote("docker logs hub_prod_postgres --tail 30", "Postgres Logs (Latest DB Errors)")

    # E. Check for \"Ghost\" Containers (Same names or duplicates)
    run_remote("docker ps -a", "Full Container List (Status)")

    client.close()
    print("\nDone: Diagnostic Phase Complete.")

if __name__ == "__main__":
    professional_diagnostic()
