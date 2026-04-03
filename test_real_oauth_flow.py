#!/usr/bin/env python3
"""
Test Real Google OAuth Flow
"""
import os
import sys
import requests
import json

# Add the backend directory to Python path
sys.path.append('/Users/airm1/Projects/och/backend/django_app')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

def test_real_oauth_flow():
    """Test the complete Google OAuth flow as it would happen in production"""
    print("=== Testing Real Google OAuth Flow ===\n")
    
    # Step 1: Initiate OAuth flow
    print("1. Testing OAuth Initiation...")
    try:
        initiate_response = requests.get(
            "http://localhost/api/v1/auth/google/initiate",
            params={"role": "student", "mode": "login"}
        )
        
        if initiate_response.status_code == 200:
            initiate_data = initiate_response.json()
            auth_url = initiate_data.get('auth_url')
            state = initiate_data.get('state')
            
            print(f"   ✅ Initiation successful")
            print(f"   Auth URL: {auth_url[:100]}...")
            print(f"   State: {state}")
            
            # Extract redirect URI from auth URL
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(auth_url)
            redirect_uri = parse_qs(parsed_url.query)['redirect_uri'][0]
            print(f"   Redirect URI: {redirect_uri}")
            
        else:
            print(f"   ❌ Initiation failed: {initiate_response.status_code}")
            print(f"   Response: {initiate_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Initiation exception: {e}")
        return False
    
    # Step 2: Test callback with fake code
    print("\n2. Testing OAuth Callback...")
    try:
        callback_data = {
            "code": "fake_test_code_12345",
            "state": state,
            "device_fingerprint": "test_device",
            "device_name": "Test Device"
        }
        
        callback_response = requests.post(
            "http://localhost/api/v1/auth/google/callback",
            json=callback_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status: {callback_response.status_code}")
        
        if callback_response.status_code == 400:
            try:
                error_data = callback_response.json()
                detail = error_data.get('detail', 'No detail')
                print(f"   Response: {detail}")
                
                # Check if it's the expected "invalid_grant" error
                if "invalid_grant" in detail:
                    print("   ✅ This is expected - fake code should give 'invalid_grant'")
                    print("   ✅ Client credentials are working correctly")
                    return True
                elif "unauthorized_client" in detail:
                    print("   ❌ This is the actual problem - 'unauthorized_client'")
                    print("   🔍 Let's analyze the exact error...")
                    
                    # Extract the Google error details
                    if "Failed to exchange authorization code:" in detail:
                        google_error_part = detail.split("Failed to exchange authorization code:")[1].strip()
                        print(f"   Google Error: {google_error_part}")
                        
                        if "unauthorized_client" in google_error_part:
                            print("   🔍 This suggests the redirect URI is not configured in Google Console")
                            print("   🔍 OR there's a mismatch in client credentials")
                            
                    return False
                else:
                    print(f"   ❌ Unexpected error: {detail}")
                    return False
                    
            except json.JSONDecodeError:
                print(f"   ❌ Could not parse JSON response: {callback_response.text}")
                return False
                
        else:
            print(f"   ❌ Unexpected status code: {callback_response.status_code}")
            print(f"   Response: {callback_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Callback exception: {e}")
        return False

def check_environment():
    """Check the current environment configuration"""
    print("=== Environment Check ===\n")
    
    client_id = os.getenv('GOOGLE_CLIENT_ID') or os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    
    print(f"Client ID: {client_id[:20] if client_id else 'NOT_SET'}...")
    print(f"Client Secret: {'SET' if client_secret else 'NOT_SET'}")
    print(f"Frontend URL: {frontend_url}")
    
    # Check if we can access the backend
    try:
        response = requests.get("http://localhost/api/v1/health/", timeout=5)
        print(f"Backend Health: {'✅ OK' if response.status_code == 200 else '❌ FAILED'}")
    except:
        print("Backend Health: ❌ FAILED (connection error)")
        return False
    
    return True

if __name__ == "__main__":
    if check_environment():
        test_real_oauth_flow()
