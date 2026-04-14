#!/usr/bin/env python3
"""
Script to delete a user from the OCH platform
Usage: python delete_user_script.py applicationsoptiohire@gmail.com
"""

import sys

import requests

BASE_URL = "http://django:8000/api/v1"  # Inside container

def get_admin_token():
    """Get admin authentication token"""
    # Try multiple admin credentials
    admin_credentials = [
        {"email": "admin@och.com", "password": "admin123"},
        {"email": "nelsonochieng516@gmail.com", "password": "password123"},
    ]

    for creds in admin_credentials:
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json=creds)
            if response.status_code == 200:
                data = response.json()
                if 'access' in data:
                    print(f"✅ Logged in as: {creds['email']}")
                    return data['access']
        except Exception as e:
            print(f"❌ Login failed for {creds['email']}: {e}")
            continue

    return None

def find_user(email, token):
    """Find user by email"""
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(f"{BASE_URL}/users/", headers=headers)
        if response.status_code == 200:
            data = response.json()
            users = data.get('results', []) if isinstance(data, dict) else data

            for user in users:
                if user.get('email', '').lower() == email.lower():
                    print(f"✅ Found user: {user['email']} (ID: {user['id']})")
                    print(f"   Roles: {[r.get('role', r.get('name', 'unknown')) for r in user.get('roles', [])]}")
                    print(f"   Account status: {user.get('account_status', 'unknown')}")
                    return user['id']

        print(f"❌ User {email} not found")
        return None
    except Exception as e:
        print(f"❌ Error finding user: {e}")
        return None

def delete_user(user_id, token):
    """Hard delete user"""
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.delete(f"{BASE_URL}/users/{user_id}/", headers=headers)

        if response.status_code == 200:
            print(f"✅ User {user_id} deleted successfully")
            return True
        elif response.status_code == 403:
            print("❌ Permission denied - admin rights required")
            print(f"   Response: {response.text}")
        elif response.status_code == 404:
            print("❌ User not found")
        else:
            print(f"❌ Delete failed with status {response.status_code}")
            print(f"   Response: {response.text}")

        return False
    except Exception as e:
        print(f"❌ Error deleting user: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python delete_user_script.py <email>")
        print("Example: python delete_user_script.py applicationsoptiohire@gmail.com")
        sys.exit(1)

    email = sys.argv[1]
    print(f"🗑️  Attempting to delete user: {email}")

    # Get admin token
    print("🔐 Getting admin authentication...")
    token = get_admin_token()
    if not token:
        print("❌ Could not authenticate as admin")
        sys.exit(1)

    # Find user
    print("🔍 Searching for user...")
    user_id = find_user(email, token)
    if not user_id:
        print("❌ User not found - nothing to delete")
        sys.exit(0)

    # Confirm deletion
    confirm = input(f"⚠️  Are you sure you want to permanently delete {email}? This will remove ALL data. Type 'DELETE' to confirm: ")
    if confirm != 'DELETE':
        print("❌ Deletion cancelled")
        sys.exit(0)

    # Delete user
    print("🗑️  Deleting user...")
    if delete_user(user_id, token):
        print("✅ User successfully deleted from the platform")
    else:
        print("❌ Failed to delete user")
        sys.exit(1)

if __name__ == "__main__":
    main()
