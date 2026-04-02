#!/usr/bin/env python3
"""
Test script to verify Google OAuth configuration
"""
import os
import sys

# Add the backend directory to Python path
sys.path.append('/Users/airm1/Projects/och/backend/django_app')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.conf import settings

def test_google_oauth_config():
    """Test Google OAuth configuration"""
    print("=== Google OAuth Configuration Test ===\n")
    
    # Check required settings
    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', None)
    client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', None)
    frontend_url = getattr(settings, 'FRONTEND_URL', None)
    
    print(f"✅ GOOGLE_CLIENT_ID: {'SET' if client_id else 'NOT SET'}")
    print(f"✅ GOOGLE_CLIENT_SECRET: {'SET' if client_secret else 'NOT SET'}")
    print(f"✅ FRONTEND_URL: {frontend_url}")
    
    if not client_id:
        print("❌ GOOGLE_CLIENT_ID is not set")
        return False
        
    if not client_secret:
        print("❌ GOOGLE_CLIENT_SECRET is not set")
        return False
        
    if not frontend_url:
        print("❌ FRONTEND_URL is not set")
        return False
    
    # Calculate redirect URI
    redirect_uri = f"{frontend_url.rstrip('/')}/auth/google/callback"
    print(f"✅ Redirect URI: {redirect_uri}")
    
    print("\n=== Required Actions ===")
    print("1. Go to: https://console.cloud.google.com/apis/credentials")
    print("2. Find your OAuth 2.0 Client ID")
    print("3. Under 'Authorized redirect URIs', add:")
    print(f"   {redirect_uri}")
    print("4. Save the changes")
    print("\nFor production, also add:")
    print("   https://cybochengine.africa/auth/google/callback")
    
    return True

def test_initiate_endpoint():
    """Test Google OAuth initiate endpoint"""
    print("\n=== Testing Initiate Endpoint ===")
    
    try:
        import requests
        response = requests.get('http://localhost:8000/api/v1/auth/google/initiate')
        if response.status_code == 200:
            data = response.json()
            print("✅ Initiate endpoint working")
            print(f"✅ Auth URL generated: {data.get('auth_url', 'N/A')[:50]}...")
            print(f"✅ State generated: {data.get('state', 'N/A')[:20]}...")
            return True
        else:
            print(f"❌ Initiate endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing initiate endpoint: {e}")
        return False

if __name__ == "__main__":
    config_ok = test_google_oauth_config()
    endpoint_ok = test_initiate_endpoint()
    
    print(f"\n=== Summary ===")
    print(f"Configuration: {'✅ OK' if config_ok else '❌ FAILED'}")
    print(f"Initiate API: {'✅ OK' if endpoint_ok else '❌ FAILED'}")
    
    if config_ok and endpoint_ok:
        print("\n🎉 Google OAuth is properly configured!")
        print("📝 Just add the redirect URI to Google Console and you're ready to go!")
    else:
        print("\n⚠️  Fix the issues above before testing Google OAuth")
