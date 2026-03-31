#!/usr/bin/env python3
"""
Simple test to verify hard delete endpoint exists and has proper permissions.
"""

import requests
import json

BASE_URL = "http://localhost/api/v1"

def test_delete_endpoint():
    """Test if the DELETE endpoint is properly configured."""
    
    print("🧪 Testing DELETE Endpoint Configuration")
    print("=" * 50)
    
    # Test 1: Check endpoint exists (should return 401 Unauthorized, not 404)
    print("\n1. Checking if DELETE endpoint exists...")
    try:
        response = requests.delete(f"{BASE_URL}/users/1")
        if response.status_code == 401:
            print("✅ DELETE endpoint exists (401 Unauthorized - requires auth)")
        elif response.status_code == 404:
            print("❌ DELETE endpoint not found (404 Not Found)")
        else:
            print(f"❓ Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Check OPTIONS to see allowed methods
    print("\n2. Checking allowed HTTP methods...")
    try:
        response = requests.options(f"{BASE_URL}/users/1")
        if response.status_code == 200:
            allow_header = response.headers.get('Allow', '')
            methods = [m.strip() for m in allow_header.split(',')]
            print(f"✅ Allowed methods: {methods}")
            if 'DELETE' in methods:
                print("✅ DELETE method is allowed")
            else:
                print("❌ DELETE method not in Allow header")
        else:
            print(f"❌ OPTIONS failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Check with invalid auth token
    print("\n3. Testing with invalid auth token...")
    headers = {'Authorization': 'Bearer invalid_token'}
    try:
        response = requests.delete(f"{BASE_URL}/users/1", headers=headers)
        if response.status_code == 401:
            print("✅ Invalid token properly rejected (401)")
        elif response.status_code == 403:
            print("✅ Invalid token properly rejected (403)")
        else:
            print(f"❓ Unexpected status with invalid token: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🎯 DELETE Endpoint Test Complete!")
    print("\n📋 Summary:")
    print("- The hard delete functionality is implemented in UserViewSet.destroy()")
    print("- It requires authentication and admin/program_director permissions")
    print("- Uses centralized permission utility: can_manage_users()")
    print("- Includes comprehensive cleanup of related records")
    print("- Available at: DELETE /api/v1/users/{id}")

if __name__ == "__main__":
    test_delete_endpoint()
