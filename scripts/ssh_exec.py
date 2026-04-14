import paramiko
import sys
import time

def execute_stream(command):
    host = "69.30.235.220"
    user = "administrator"
    password = "Ongoza@#1"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        print(f"Executing: {command}")
        transport = client.get_transport()
        channel = transport.open_session()
        channel.get_pty()
        channel.exec_command(command)
        
        while not channel.exit_status_ready():
            if channel.recv_ready():
                print(channel.recv(1024).decode(errors='replace'), end="")
            time.sleep(0.1)
        
        # Print remaining output
        while channel.recv_ready():
            print(channel.recv(1024).decode(errors='replace'), end="")
            
        print(f"\nCommand exited with status: {channel.recv_exit_status()}")
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        execute_stream(sys.argv[1])
    else:
        print("No command provided.")
