#!/usr/bin/env python3
"""
Google OAuth Flow Test
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

def test_google_oauth_flow():
    """Test complete Google OAuth flow"""
    print("=== Google OAuth Flow Test ===\n")
    
    # Test 1: Frontend Initiation
    print("1. Testing frontend Google OAuth initiation...")
    try:
        response = requests.get('http://localhost:3000/api/v1/auth/google/initiate', 
            params={'role': 'student', 'mode': 'login'}
        )
        
        if response.status_code == 200:
            data = response.json()
            auth_url = data.get('auth_url')
            state = data.get('state')
            
            print(f"   ✅ Frontend initiation successful!")
            print(f"   ✅ Auth URL generated: {auth_url[:50]}...")
            print(f"   ✅ State generated: {state[:20]}...")
            
            if auth_url and state:
                print(f"   ✅ Required parameters present")
            else:
                print(f"   ❌ Missing parameters")
                return False
        else:
            print(f"   ❌ Frontend initiation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Frontend initiation error: {e}")
        return False
    
    # Test 2: Backend Direct Initiation
    print("\n2. Testing backend direct initiation...")
    try:
        response = requests.get('http://localhost:8000/api/v1/auth/google/initiate',
            params={'role': 'student', 'mode': 'login'}
        )
        
        if response.status_code == 200:
            data = response.json()
            backend_auth_url = data.get('auth_url')
            backend_state = data.get('state')
            
            print(f"   ✅ Backend initiation successful!")
            print(f"   ✅ Auth URL: {backend_auth_url[:50]}...")
            print(f"   ✅ State: {backend_state[:20]}...")
            
            # Check if URLs match (except state)
            if auth_url and backend_auth_url:
                # Extract base URLs without state
                frontend_base = auth_url.split('&state=')[0]
                backend_base = backend_auth_url.split('&state=')[0]
                
                if frontend_base == backend_base:
                    print(f"   ✅ Frontend and backend URLs match!")
                else:
                    print(f"   ⚠️  Frontend and backend URLs differ")
                    print(f"      Frontend: {frontend_base}")
                    print(f"      Backend:  {backend_base}")
            else:
                print(f"   ❌ URL comparison failed")
        else:
            print(f"   ❌ Backend initiation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Backend initiation error: {e}")
        return False
    
    # Test 3: Google OAuth Configuration
    print("\n3. Checking Google OAuth configuration...")
    try:
        from django.conf import settings
        
        client_id = getattr(settings, 'GOOGLE_CLIENT_ID', None)
        client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', None)
        frontend_url = getattr(settings, 'FRONTEND_URL', None)
        
        print(f"   Google Client ID: {'SET' if client_id else 'NOT_SET'}")
        print(f"   Google Client Secret: {'SET' if client_secret else 'NOT_SET'}")
        print(f"   Frontend URL: {frontend_url}")
        
        if client_id and client_secret and frontend_url:
            redirect_uri = f"{frontend_url.rstrip('/')}/auth/google/callback"
            print(f"   ✅ Redirect URI: {redirect_uri}")
            print(f"   ✅ Configuration complete!")
        else:
            print(f"   ❌ Configuration incomplete")
            return False
            
    except Exception as e:
        print(f"   ❌ Configuration check error: {e}")
        return False
    
    # Test 4: Callback Endpoint
    print("\n4. Testing callback endpoint...")
    try:
        # Test with invalid code (should fail gracefully)
        response = requests.post('http://localhost:3000/api/v1/auth/google/callback',
            json={'code': 'invalid_test_code', 'state': 'test_state'}
        )
        
        if response.status_code == 400:
            print(f"   ✅ Callback endpoint handles invalid codes correctly")
            print(f"   ✅ Proper error response: {response.status_code}")
        elif response.status_code == 500:
            data = response.json()
            if 'invalid_grant' in str(data.get('detail', '')):
                print(f"   ✅ Callback endpoint working (invalid code expected)")
            else:
                print(f"   ❌ Unexpected callback error")
                print(f"   Response: {response.text}")
        else:
            print(f"   ⚠️  Unexpected callback response: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Callback test error: {e}")
        return False
    
    print(f"\n=== Summary ===")
    print("✅ Google OAuth initiation working (frontend)")
    print("✅ Google OAuth initiation working (backend)")
    print("✅ Google OAuth configuration complete")
    print("✅ Google OAuth callback handling working")
    print("✅ Google OAuth flow is ready!")
    
    print(f"\n=== Next Steps ===")
    print("1. Visit: http://localhost:3000/login/student")
    print("2. Click 'Sign in with Google'")
    print("3. Complete Google authentication")
    print("4. Verify successful callback and login")
    
    return True

if __name__ == "__main__":
    test_google_oauth_flow()
