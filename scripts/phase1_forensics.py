import paramiko
import time

def phase1_forensics_and_kill():
    """Phase 1: Find the malware, understand how it respawns, kill it permanently."""
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(host, username=user, password=password, timeout=120, auth_timeout=120, banner_timeout=120)
        print("Connected.\n")

        def run(cmd, label=""):
            if label:
                print(f"\n{'='*60}")
                print(f"  {label}")
                print(f"{'='*60}")
            stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
            raw = stdout.read()
            out = raw.decode('ascii', 'ignore').strip()
            if out:
                print(out)
            return out

        sudo = f"printf '%s\\n' '{password}' | sudo -S -p ''"

        # ============================================================
        # FORENSIC STEP 1: IDENTIFY THE LIVE MALWARE PROCESS
        # ============================================================
        run(f"{sudo} ps aux | grep -E '\\.config\\.json|\\.sys-ca|xmrig|kdevtmpfsi|kinsing' | grep -v grep",
            "STEP 1: ACTIVE MALWARE PROCESSES")

        # Get the PID of the miner
        result = run(f"{sudo} pgrep -f '.config.json' 2>/dev/null || echo 'none'")
        miner_pid = result.strip().split('\n')[0] if result.strip() != 'none' else None

        if miner_pid and miner_pid.isdigit():
            print(f"\n  Miner PID: {miner_pid}")

            # FORENSIC STEP 2: FIND THE ACTUAL BINARY
            run(f"{sudo} ls -la /proc/{miner_pid}/exe 2>/dev/null",
                "STEP 2: MALWARE BINARY LOCATION")
            run(f"{sudo} cat /proc/{miner_pid}/cmdline 2>/dev/null | tr '\\0' ' '",
                "STEP 2b: FULL COMMAND LINE")
            run(f"{sudo} cat /proc/{miner_pid}/cwd 2>/dev/null || {sudo} ls -la /proc/{miner_pid}/cwd 2>/dev/null",
                "STEP 2c: WORKING DIRECTORY")

            # FORENSIC STEP 3: FIND PARENT PROCESS (what restarts it)
            run(f"{sudo} cat /proc/{miner_pid}/status | grep -E 'PPid|Name|Uid'",
                "STEP 3: PARENT PROCESS INFO")
            ppid_line = run(f"{sudo} cat /proc/{miner_pid}/status | grep PPid | awk '{{print $2}}'")
            ppid = ppid_line.strip().split('\n')[-1].strip() if ppid_line else None

            if ppid and ppid.isdigit():
                print(f"\n  Parent PID: {ppid}")
                run(f"{sudo} ps -p {ppid} -o pid,ppid,user,args 2>/dev/null",
                    "STEP 3b: PARENT PROCESS DETAILS")
                run(f"{sudo} ls -la /proc/{ppid}/exe 2>/dev/null",
                    "STEP 3c: PARENT BINARY")
        else:
            print("  Miner process not found - may be dead from last kill")

        # FORENSIC STEP 4: CHECK ALL PERSISTENCE MECHANISMS
        run(f"{sudo} find /etc/systemd/system/ -name '*.service' -newer /etc/hostname 2>/dev/null | head -10",
            "STEP 4a: CUSTOM SYSTEMD SERVICES")
        run(f"{sudo} find /etc/systemd/system/ -name '*.timer' 2>/dev/null | head -10",
            "STEP 4b: SYSTEMD TIMERS")
        run(f"{sudo} cat /etc/rc.local 2>/dev/null || echo 'No rc.local'",
            "STEP 4c: RC.LOCAL (boot script)")
        run(f"{sudo} ls -la /etc/init.d/ | grep -v -E 'README|skeleton|ssh|cron|docker|udev|procps|kmod|apparmor|rsyslog|dbus|unattended|sysstat|hwclock|x11-common|console-setup|keyboard-setup'",
            "STEP 4d: CUSTOM INIT.D SCRIPTS")
        run(f"cat /home/administrator/.bashrc | grep -v '^#' | grep -v '^$'",
            "STEP 4e: BASHRC (login hooks)")
        run(f"cat /home/administrator/.profile | grep -v '^#' | grep -v '^$'",
            "STEP 4f: PROFILE (login hooks)")
        run(f"{sudo} cat /root/.bashrc | grep -v '^#' | grep -v '^$' 2>/dev/null",
            "STEP 4g: ROOT BASHRC")

        # FORENSIC STEP 5: FIND ALL MALWARE FILES
        run(f"{sudo} find / -name '.sys-ca' -o -name '.config.json' -o -name 'free_proc.sh' -o -name 'kdevtmpfsi' -o -name 'kinsing' 2>/dev/null | grep -v '/proc/'",
            "STEP 5: ALL MALWARE FILES ON DISK")

        # FORENSIC STEP 6: CHECK FILE TIMESTAMPS (when was malware installed)
        run(f"{sudo} stat /usr/local/bin/.config.json 2>/dev/null",
            "STEP 6: MALWARE CONFIG FILE TIMESTAMP")

        # FORENSIC STEP 7: CHECK AUTH LOGS (how did attacker get in)
        run(f"{sudo} grep 'Accepted' /var/log/auth.log 2>/dev/null | tail -20",
            "STEP 7a: SUCCESSFUL SSH LOGINS (last 20)")
        run(f"{sudo} grep 'Failed' /var/log/auth.log 2>/dev/null | tail -10",
            "STEP 7b: FAILED SSH ATTEMPTS (last 10)")
        run(f"{sudo} last -20 2>/dev/null",
            "STEP 7c: RECENT LOGIN HISTORY")

        # ============================================================
        # NOW KILL IT PERMANENTLY
        # ============================================================
        print(f"\n{'='*60}")
        print("  KILLING MALWARE PERMANENTLY")
        print(f"{'='*60}")

        # Kill the miner and parent
        if miner_pid and miner_pid.isdigit():
            if ppid and ppid.isdigit() and ppid != '1':
                run(f"{sudo} kill -9 {ppid} 2>/dev/null; echo 'Killed parent PID {ppid}'")
            run(f"{sudo} kill -9 {miner_pid} 2>/dev/null; echo 'Killed miner PID {miner_pid}'")

        # Kill ALL processes matching the pattern
        run(f"{sudo} pkill -9 -f '.config.json' 2>/dev/null; echo 'pkill .config.json done'")
        run(f"{sudo} pkill -9 -f '.sys-ca' 2>/dev/null; echo 'pkill .sys-ca done'")

        # DELETE the malware binary and config
        run(f"{sudo} rm -f /usr/local/bin/.config.json 2>/dev/null; echo 'Deleted /usr/local/bin/.config.json'")
        run(f"{sudo} find / -name '.sys-ca' -not -path '/proc/*' -delete 2>/dev/null; echo 'Deleted all .sys-ca files'")
        run(f"{sudo} find / -name 'free_proc.sh' -not -path '/proc/*' -delete 2>/dev/null; echo 'Deleted all free_proc.sh files'")

        # Lock the directories so malware can't recreate
        run(f"{sudo} chattr -i /home/administrator/.sys-cache 2>/dev/null; {sudo} chattr -i /home/administrator/.sys-cache/free_proc.sh 2>/dev/null; {sudo} rm -rf /home/administrator/.sys-cache; {sudo} mkdir -p /home/administrator/.sys-cache; {sudo} touch /home/administrator/.sys-cache/free_proc.sh; {sudo} chmod 000 /home/administrator/.sys-cache /home/administrator/.sys-cache/free_proc.sh; {sudo} chattr +i /home/administrator/.sys-cache/free_proc.sh 2>/dev/null; {sudo} chattr +i /home/administrator/.sys-cache 2>/dev/null; echo 'Locked .sys-cache'")

        # Place a dummy .config.json that's immutable so miner can't recreate it
        run(f"{sudo} echo 'blocked' > /usr/local/bin/.config.json; {sudo} chmod 000 /usr/local/bin/.config.json; {sudo} chattr +i /usr/local/bin/.config.json 2>/dev/null; echo 'Locked .config.json'")

        # Ensure iptables blocks are in place
        run(f"{sudo} iptables -C OUTPUT -d 136.243.75.233 -j DROP 2>/dev/null && echo 'Mining pool already blocked' || ({sudo} iptables -A OUTPUT -d 136.243.75.233 -j DROP; echo 'Blocked mining pool')")
        run(f"{sudo} iptables -C OUTPUT -p tcp --dport 8029 -j DROP 2>/dev/null && echo 'Port 8029 already blocked' || ({sudo} iptables -A OUTPUT -p tcp --dport 8029 -j DROP; echo 'Blocked port 8029')")

        # Wait and verify it's dead
        time.sleep(5)
        result = run(f"{sudo} pgrep -f '.config.json' 2>/dev/null || echo 'MALWARE IS DEAD'",
                     "VERIFICATION: IS MALWARE DEAD?")

        if 'MALWARE IS DEAD' in result:
            print("\n  SUCCESS: THE MALWARE HAS BEEN PERMANENTLY KILLED.")
        else:
            print(f"\n  WARNING: Malware respawned! New PID: {result}")
            print("  Attempting to find and kill the respawn mechanism...")
            # Get new PID parent
            new_pid = result.strip()
            run(f"{sudo} cat /proc/{new_pid}/status 2>/dev/null | grep PPid")
            # Nuclear option: find the actual binary from /proc
            binary_path = run(f"{sudo} readlink /proc/{new_pid}/exe 2>/dev/null")
            if binary_path:
                print(f"  Actual binary: {binary_path}")
                run(f"{sudo} kill -9 {new_pid}; {sudo} rm -f {binary_path}; {sudo} touch {binary_path}; {sudo} chmod 000 {binary_path}; {sudo} chattr +i {binary_path} 2>/dev/null; echo 'Binary deleted and locked'")

        run("uptime", "CPU AFTER CLEANUP")

        client.close()
        print("\n  Phase 1 complete. Run phase2_restore.py next.")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    phase1_forensics_and_kill()
