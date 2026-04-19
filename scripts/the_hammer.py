import subprocess
import sys

def run(cmd):
    return subprocess.check_output(cmd, shell=True).decode().strip()

print("The Hammer: Deep Cleanup Starting...")

# 1. Find all containers related to ongoza or the project
all_containers = run("docker ps -a --format '{{.ID}}|{{.Names}}'")
to_kill = []
for line in all_containers.split('\n'):
    if not line: continue
    cid, name = line.split('|')
    if 'ongoza' in name.lower() or 'och' in name.lower():
        to_kill.append(cid)

if not to_kill:
    print("No conflicting containers found.")
else:
    print(f"Targeting {len(to_kill)} containers: {to_kill}")
    for cid in to_kill:
        print(f"Killing {cid}...")
        try:
            subprocess.run(f"docker stop {cid}", shell=True, timeout=10)
            subprocess.run(f"docker rm -f {cid}", shell=True, timeout=5)
        except:
            print(f"Failed to kill {cid}, moving on.")

print("Cleanup complete.")
