import os
import paramiko
import sys

def scan_logs_utf8():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    stdin, stdout, stderr = client.exec_command('docker logs --since 2m hub_prod_nextjs')
    
    # Read as bytes and decode as utf-8
    logs_bytes = stdout.read()
    try:
        logs_str = logs_bytes.decode('utf-8')
    except UnicodeDecodeError:
        logs_str = logs_bytes.decode('latin-1')
        
    # Print to stdout with utf-8 encoding
    sys.stdout.buffer.write(logs_str.encode('utf-8'))
    
    client.close()

if __name__ == "__main__":
    scan_logs_utf8()
