#!/usr/bin/env python3
"""
Debug Google OAuth Redirect URI Issue
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

def debug_google_oauth_redirect():
    """Debug Google OAuth redirect URI configuration"""
    print("=== Google OAuth Redirect URI Debug ===\n")
    
    from django.conf import settings
    
    # Get configuration
    client_id = os.getenv('GOOGLE_CLIENT_ID') or os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    
    # Calculate redirect URI
    redirect_uri = f"{frontend_url.rstrip('/')}/auth/google/callback"
    
    print("Current Configuration:")
    print(f"  - Client ID: {client_id[:20]}..." if client_id else "  - Client ID: NOT_SET")
    print(f"  - Client Secret: {'SET' if client_secret else 'NOT_SET'}")
    print(f"  - Frontend URL: {frontend_url}")
    print(f"  - Redirect URI: {redirect_uri}")
    
    print("\n=== Testing Different Redirect URIs ===")
    
    # Test various redirect URIs that might be configured
    test_uris = [
        redirect_uri,  # Current: http://localhost:3000/auth/google/callback
        "http://localhost:3000/auth/google/callback",
        "https://localhost:3000/auth/google/callback", 
        "http://127.0.0.1:3000/auth/google/callback",
        "https://127.0.0.1:3000/auth/google/callback",
        "http://localhost:3000/api/v1/auth/google/callback",
        "https://cybochengine.africa/auth/google/callback",  # Production
    ]
    
    for test_uri in test_uris:
        print(f"\nTesting: {test_uri}")
        
        token_data = {
            'grant_type': 'authorization_code',
            'code': 'fake_test_code_12345',
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': test_uri,
        }
        
        try:
            response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
            
            if response.status_code == 400:
                error_data = response.json()
                error = error_data.get('error', 'unknown')
                description = error_data.get('error_description', 'no description')
                
                if error == 'invalid_grant':
                    print("  ✅ SUCCESS: This redirect URI is configured correctly!")
                    print(f"     (Got expected 'invalid_grant' for fake code)")
                elif error == 'unauthorized_client':
                    print("  ❌ FAILED: 'unauthorized_client' - redirect URI not configured")
                    print(f"     Error: {description}")
                elif error == 'redirect_uri_mismatch':
                    print("  ❌ FAILED: 'redirect_uri_mismatch' - redirect URI not registered")
                    print(f"     Error: {description}")
                else:
                    print(f"  ❌ FAILED: Unexpected error '{error}'")
                    print(f"     Description: {description}")
            else:
                print(f"  ❌ FAILED: Unexpected status {response.status_code}")
                print(f"     Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"  ❌ FAILED: Request exception: {e}")
    
    print("\n=== Solution ===")
    print("To fix the 'unauthorized_client' error:")
    print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
    print("2. Navigate to: APIs & Services > Credentials")
    print("3. Find your OAuth 2.0 Client ID:")
    print(f"   {client_id[:20]}...")
    print("4. Click 'Edit' or 'Configure'")
    print("5. Under 'Authorized redirect URIs', add the correct URI:")
    print(f"   {redirect_uri}")
    print("6. Make sure the URI exactly matches (including http/https and port)")
    print("7. Save the configuration")
    print("8. Wait a few minutes for changes to propagate")
    print("9. Test the OAuth flow again")

if __name__ == "__main__":
    debug_google_oauth_redirect()
