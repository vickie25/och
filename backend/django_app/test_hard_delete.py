#!/usr/bin/env python3
"""
Test script to verify hard delete functionality for admin users.
"""

import sys

import requests

BASE_URL = "http://django:8000/api/v1"  # Inside container

def test_hard_delete():
    """Test the hard delete functionality for users."""

    print("🧪 Testing Hard Delete Functionality")
    print("=" * 50)

    # First, let's create a test user to delete
    print("\n1. Creating test user...")
    create_data = {
        "email": "test_delete_user@example.com",
        "password": "testpass123",
        "first_name": "Test",
        "last_name": "Delete"
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/signup", json=create_data)
        if response.status_code == 201:
            print("✅ Test user created successfully")
            test_user_id = response.json().get('id')
            print(f"   User ID: {test_user_id}")
        else:
            print(f"❌ Failed to create test user: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return False

    # Now login as admin to get auth token
    print("\n2. Logging in as admin...")
    login_data = {
        "email": "admin@och.com",  # Assuming this exists
        "password": "admin123"    # Assuming this password
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            print("✅ Admin login successful")
            auth_token = response.json().get('access')
            headers = {'Authorization': f'Bearer {auth_token}'}
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            print("   Trying alternative admin credentials...")

            # Try alternative admin credentials
            alt_login = {
                "email": "nelsonochieng516@gmail.com",  # From OAuth overrides
                "password": "password123"
            }
            response = requests.post(f"{BASE_URL}/auth/login", json=alt_login)
            if response.status_code == 200:
                print("✅ Alternative admin login successful")
                auth_token = response.json().get('access')
                headers = {'Authorization': f'Bearer {auth_token}'}
            else:
                print("❌ No admin credentials worked - skipping delete test")
                return False
    except Exception as e:
        print(f"❌ Error during admin login: {e}")
        return False

    # Test regular user access (should be denied)
    print("\n3. Testing permission check with regular user...")
    regular_login = {
        "email": "test_delete_user@example.com",
        "password": "testpass123"
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=regular_login)
        if response.status_code == 200:
            regular_token = response.json().get('access')
            regular_headers = {'Authorization': f'Bearer {regular_token}'}

            # Try to delete with regular user token
            delete_response = requests.delete(f"{BASE_URL}/users/{test_user_id}", headers=regular_headers)
            if delete_response.status_code == 403:
                print("✅ Regular user correctly denied permission to delete")
            else:
                print(f"❌ Regular user should be denied but got: {delete_response.status_code}")
                print(f"   Response: {delete_response.text}")
        else:
            print("❌ Could not login as regular user")
    except Exception as e:
        print(f"❌ Error testing regular user permissions: {e}")

    # Test admin hard delete
    print("\n4. Testing admin hard delete...")
    try:
        delete_response = requests.delete(f"{BASE_URL}/users/{test_user_id}", headers=headers)

        if delete_response.status_code == 200:
            print("✅ Hard delete successful")
            print(f"   Response: {delete_response.json()}")
        elif delete_response.status_code == 403:
            print("❌ Admin permission denied - check role assignments")
            print(f"   Response: {delete_response.text}")
        elif delete_response.status_code == 404:
            print("❌ User not found - may have been deleted already")
        else:
            print(f"❌ Unexpected status: {delete_response.status_code}")
            print(f"   Response: {delete_response.text}")
    except Exception as e:
        print(f"❌ Error during hard delete: {e}")
        return False

    # Verify user is actually deleted
    print("\n5. Verifying user is deleted...")
    try:
        verify_response = requests.get(f"{BASE_URL}/users/{test_user_id}", headers=headers)
        if verify_response.status_code == 404:
            print("✅ User confirmed deleted (404 Not Found)")
        else:
            print(f"❌ User still found: {verify_response.status_code}")
            print(f"   Response: {verify_response.text}")
    except Exception as e:
        print(f"❌ Error verifying deletion: {e}")

    print("\n🎯 Hard Delete Test Complete!")
    return True

if __name__ == "__main__":
    success = test_hard_delete()
    sys.exit(0 if success else 1)
