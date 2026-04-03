#!/usr/bin/env python3
"""
Google OAuth Configuration Test
"""
import os
import sys

# Add the backend directory to Python path
sys.path.append('/Users/airm1/Projects/och/backend/django_app')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

def test_google_oauth_config():
    """Test Google OAuth configuration"""
    print("=== Google OAuth Configuration Test ===\n")
    
    from django.conf import settings
    
    # Get configuration
    client_id = os.getenv('GOOGLE_CLIENT_ID') or os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    
    print("Current Configuration:")
    print(f"  - Client ID: {client_id[:20]}..." if client_id else "  - Client ID: NOT_SET")
    print(f"  - Client Secret: {'SET' if client_secret else 'NOT_SET'}")
    print(f"  - Frontend URL: {frontend_url}")
    
    # Calculate redirect URI
    redirect_uri = f"{frontend_url.rstrip('/')}/auth/google/callback"
    print(f"  - Redirect URI: {redirect_uri}")
    
    # Check if configuration is complete
    if not client_id or not client_secret:
        print("\n❌ ERROR: Google OAuth is not properly configured!")
        print("   Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env")
        return False
    
    print("\n✅ Google OAuth credentials are configured")
    
    # Test token exchange with current configuration
    import requests
    
    print(f"\n=== Testing Token Exchange ===")
    print("Note: This will fail with 'invalid_grant' since we're using a fake code")
    print("But we can check if the client credentials are accepted...")
    
    token_data = {
        'grant_type': 'authorization_code',
        'code': 'fake_test_code_12345',
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
    }
    
    try:
        print(f"Sending request to: https://oauth2.googleapis.com/token")
        print(f"Using redirect_uri: {redirect_uri}")
        
        response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 400:
            error_data = response.json()
            error = error_data.get('error', 'unknown')
            description = error_data.get('error_description', 'no description')
            
            print(f"Error: {error}")
            print(f"Description: {description}")
            
            if error == 'invalid_grant':
                print("✅ This is expected - we used a fake code")
                print("✅ Client credentials are accepted")
                return True
            elif error == 'unauthorized_client':
                print("❌ UNAUTHORIZED_CLIENT - This is the real issue!")
                print("\n🔧 SOLUTION:")
                print("1. Go to Google Cloud Console")
                print("2. Navigate to APIs & Services > Credentials")
                print("3. Find your OAuth 2.0 Client ID")
                print("4. Make sure the redirect URI is configured as:")
                print(f"   {redirect_uri}")
                print("5. Check that the client ID and secret match exactly")
                return False
            else:
                print(f"❌ Unexpected error: {error}")
                return False
        else:
            print(f"❌ Unexpected response status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    test_google_oauth_config()
