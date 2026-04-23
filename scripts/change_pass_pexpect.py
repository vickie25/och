import pexpect
import sys

try:
    print("Connecting via SSH...")
    child = pexpect.spawn('ssh administrator@69.30.235.220', timeout=20)
    
    # Handle possible new host key warning
    idx = child.expect(['Are you sure you want to continue connecting', 'password:'])
    if idx == 0:
        child.sendline('yes')
        child.expect('password:')
        
    child.sendline('Ongoza@#1')
    child.expect(r'\$')
    
    print("Logged in. Changing password...")
    child.sendline('passwd')
    
    # It might ask for current password or directly for new password
    idx = child.expect(['Current password:', 'New password:'])
    if idx == 0:
        child.sendline('Ongoza@#1')
        child.expect('New password:')
        
    child.sendline('0ngoz@_Cyber_2026_Secure!')
    child.expect('Retype new password:')
    child.sendline('0ngoz@_Cyber_2026_Secure!')
    
    child.expect(r'password updated successfully')
    print("Password successfully updated via pexpect!")
    
except Exception as e:
    print(f"Failed: {e}")
    if 'child' in locals():
        print("Before output:\n", child.before.decode('utf-8', 'ignore') if child.before else '')

