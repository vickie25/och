import os
import paramiko

def test_fastapi_direct():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    # Test 1: NextJS -> FastAPI
    cmd1 = 'docker exec hub_prod_nextjs curl -s -X POST http://fastapi:8001/api/v1/profiling/session/start -H "Content-Type: application/json" -d "{}"'
    stdin, stdout, stderr = client.exec_command(cmd1)
    print("--- NextJS -> FastAPI ---")
    print(stdout.read().decode())
    print(stderr.read().decode())

    # Test 2: Django -> FastAPI
    cmd2 = 'docker exec hub_prod_django curl -s -X POST http://fastapi:8001/api/v1/profiling/session/start -H "Content-Type: application/json" -d "{}"'
    stdin, stdout, stderr = client.exec_command(cmd2)
    print("--- Django -> FastAPI ---")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    test_fastapi_direct()
