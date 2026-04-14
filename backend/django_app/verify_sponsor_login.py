"""
Verify sponsor user can login and check credentials.
"""
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from django.contrib.auth import authenticate, get_user_model

User = get_user_model()

def main():
    print("=" * 60)
    print("Verifying Sponsor User Login")
    print("=" * 60)

    email = 'sponsor@test.com'
    password = 'testpass123'

    # Get user
    try:
        user = User.objects.get(email=email)
        print(f"\n✅ User found: {email}")
        print(f"   Account Status: {user.account_status}")
        print(f"   Email Verified: {user.email_verified}")
        print(f"   Is Active: {user.is_active}")

        # Check organization
        if user.org_id:
            print(f"   Organization: {user.org_id.name} ({user.org_id.org_type})")
        else:
            print("   ⚠️  No organization assigned")

        # Check roles
        roles = user.user_roles.filter(is_active=True)
        if roles.exists():
            print(f"   Roles: {', '.join([r.role.name for r in roles])}")
        else:
            print("   ⚠️  No active roles")

    except User.DoesNotExist:
        print(f"\n❌ User not found: {email}")
        return

    # Verify password
    print("\n🔐 Testing password authentication...")
    authenticated_user = authenticate(username=email, password=password)

    if authenticated_user:
        print("✅ Password authentication SUCCESSFUL!")
        print(f"   Authenticated user: {authenticated_user.email}")
    else:
        print("❌ Password authentication FAILED!")
        print(f"   Resetting password to: {password}")
        user.set_password(password)
        user.save()
        print("✅ Password reset complete")

        # Test again
        authenticated_user = authenticate(username=email, password=password)
        if authenticated_user:
            print("✅ Password verification SUCCESSFUL after reset!")
        else:
            print("❌ Password verification still failing!")

    print("\n" + "=" * 60)
    print("Login Test Complete")
    print("=" * 60)
    print("\nCredentials:")
    print(f"  Email: {email}")
    print(f"  Password: {password}")

if __name__ == '__main__':
    main()
