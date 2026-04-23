import paramiko
import time

def phase1_cleanup():
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("[PHASE 1] Starting Deep Cleanup on 69.30.235.220...")
    try:
        client.connect(host, username=user, password=password, timeout=60, banner_timeout=60)
        print("Connected to server.")
    except Exception as e:
        print(f"Connection Failed: {e}")
        return

    def run_remote(cmd, label):
        print(f"\n--- {label} ---")
        full_cmd = f"printf '%s\\n' '{password}' | sudo -S -p '' {cmd}"
        stdin, stdout, stderr = client.exec_command(full_cmd, get_pty=True)
        # Wait for completion
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode()
        print(output)
        return exit_status, output

    # 1. Kill everything - handle cases where no containers exist
    print("Purging stale containers...")
    run_remote("docker stop $(docker ps -aq) 2>/dev/null || true", "Stopping Containers")
    run_remote("docker rm -f $(docker ps -aq) 2>/dev/null || true", "Removing Containers")
    run_remote("docker network prune -f", "Pruning Networks")
    
    # 2. Free Disk Space - This is the long one
    print("Freeing disk space (pruning images/volumes/build cache)...")
    run_remote("docker system prune -af --volumes", "Full System Prune")
    
    print("\nPhase 1 Complete: Server is now a clean state.")
    client.close()

if __name__ == "__main__":
    phase1_cleanup()
