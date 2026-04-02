#!/usr/bin/env python3
"""
Admin User Confirmation Test
"""
import os
import sys
import requests

# Add the backend directory to Python path
sys.path.append('/Users/airm1/Projects/och/backend/django_app')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from users.models import User, UserRole

def test_admin_user():
    """Test admin user creation and functionality"""
    print("=== Admin User Confirmation Test ===\n")
    
    # Test 1: User exists and has admin role
    print("1. Checking admin user exists...")
    try:
        user = User.objects.get(email='nelsonochieng516@gmail.com')
        roles = UserRole.objects.filter(user=user)
        role_names = [ur.role.name for ur in roles]
        
        print(f"   ✅ User found: {user.email}")
        print(f"   ✅ Active: {user.is_active}")
        print(f"   ✅ Email Verified: {user.email_verified}")
        print(f"   ✅ Account Status: {user.account_status}")
        print(f"   ✅ Roles: {role_names}")
        
        if 'admin' in role_names:
            print("   ✅ Admin role confirmed!")
        else:
            print("   ❌ Admin role missing!")
            return False
            
    except User.DoesNotExist:
        print("   ❌ User not found!")
        return False
    
    # Test 2: API Login
    print("\n2. Testing API login...")
    try:
        response = requests.post('http://localhost:3000/api/auth/login', 
            json={
                'email': 'nelsonochieng516@gmail.com',
                'password': 'Admin123!'
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            user_data = data.get('user', {})
            
            print(f"   ✅ Login successful!")
            print(f"   ✅ User ID: {user_data.get('id')}")
            print(f"   ✅ Email: {user_data.get('email')}")
            print(f"   ✅ Account Status: {user_data.get('account_status')}")
            print(f"   ✅ Token received: {'Yes' if token else 'No'}")
            
            # Test 3: Authenticated API access
            if token:
                print("\n3. Testing authenticated API access...")
                auth_response = requests.get('http://localhost:8000/api/v1/auth/me',
                    headers={'Authorization': f'Bearer {token}'}
                )
                
                if auth_response.status_code == 200:
                    auth_data = auth_response.json()
                    auth_roles = [r.get('role') for r in auth_data.get('roles', [])]
                    
                    print(f"   ✅ Authenticated access successful!")
                    print(f"   ✅ API Roles: {auth_roles}")
                    
                    if 'admin' in auth_roles:
                        print("   ✅ Admin access confirmed via API!")
                    else:
                        print("   ❌ Admin access not confirmed via API!")
                        return False
                else:
                    print(f"   ❌ Authenticated access failed: {auth_response.status_code}")
                    return False
        else:
            print(f"   ❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ API test error: {e}")
        return False
    
    print(f"\n=== Summary ===")
    print("✅ Admin user created successfully")
    print("✅ Admin has correct role and permissions")
    print("✅ Login authentication working")
    print("✅ API access with admin privileges confirmed")
    print("✅ Admin user is fully functional!")
    
    print(f"\n=== Login Credentials ===")
    print(f"Email: nelsonochieng516@gmail.com")
    print(f"Password: Admin123!")
    print(f"Role: admin")
    print(f"Status: Active and Ready")
    
    return True

if __name__ == "__main__":
    test_admin_user()
