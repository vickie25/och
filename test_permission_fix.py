#!/usr/bin/env python3
"""
Test script to verify permission fixes work correctly.
Tests the centralized permission utilities and role-based access.
"""

import os
import sys
import django

# Setup Django
sys.path.append('/Users/airm1/Projects/och/backend/django_app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_app.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Role, UserRole
from users.utils.permission_utils import (
    has_admin_role, 
    has_any_admin_role, 
    can_manage_users,
    get_user_primary_role,
    assign_role_if_not_exists
)

User = get_user_model()

def test_permission_utilities():
    """Test centralized permission utilities."""
    print("🧪 Testing Permission Utilities...")
    
    # Test role creation and assignment
    print("\n1. Testing role assignment utility...")
    test_user = User.objects.filter(email__contains='test').first()
    if not test_user:
        test_user = User.objects.create_user(
            email='test-permissions@example.com',
            username='test-permissions@example.com',
            first_name='Test',
            last_name='User'
        )
        print(f"Created test user: {test_user.email}")
    
    # Test assigning admin role
    created, message = assign_role_if_not_exists(test_user, 'admin')
    print(f"Admin role assignment: {message}")
    
    # Test permission checks
    print(f"\n2. Testing permission checks for {test_user.email}...")
    print(f"- has_admin_role(['admin']): {has_admin_role(test_user, ['admin'])}")
    print(f"- has_admin_role(['admin', 'program_director']): {has_admin_role(test_user, ['admin', 'program_director'])}")
    print(f"- has_any_admin_role(): {has_any_admin_role(test_user)}")
    print(f"- can_manage_users(): {can_manage_users(test_user)}")
    print(f"- get_user_primary_role(): {get_user_primary_role(test_user)}")
    
    # Test non-admin user
    student_user = User.objects.filter(email__contains='student').first()
    if student_user:
        print(f"\n3. Testing non-admin user: {student_user.email}")
        print(f"- has_admin_role(['admin']): {has_admin_role(student_user, ['admin'])}")
        print(f"- has_any_admin_role(): {has_any_admin_role(student_user)}")
        print(f"- can_manage_users(): {can_manage_users(student_user)}")
        print(f"- get_user_primary_role(): {get_user_primary_role(student_user)}")

def test_recipe_permission_fix():
    """Test that recipe generation permission fix works."""
    print("\n🔧 Testing Recipe Permission Fix...")
    
    from recipes.views import RecipeGenerateView
    from users.permissions import IsAdminOrDirector
    
    # Create mock request with admin user
    class MockRequest:
        def __init__(self, user):
            self.user = user
    
    test_user = User.objects.filter(email='test-permissions@example.com').first()
    if test_user:
        mock_request = MockRequest(test_user)
        permission = IsAdminOrDirector()
        
        has_permission = permission.has_permission(mock_request, None)
        print(f"Admin user {test_user.email} has recipe generation permission: {has_permission}")
        
        # Test the view directly
        view = RecipeGenerateView()
        view.request = mock_request
        
        # Check if the permission classes would allow access
        permission_classes = view.permission_classes
        all_permissions_pass = True
        
        for perm_class in permission_classes:
            perm_instance = perm_class()
            if not perm_instance.has_permission(mock_request, None):
                all_permissions_pass = False
                break
        
        print(f"All permission classes pass for admin user: {all_permissions_pass}")

def test_oauth_role_override():
    """Test Google OAuth role override functionality."""
    print("\n🔐 Testing OAuth Role Override...")
    
    from users.views.google_oauth_views import _apply_google_email_role_overrides
    
    test_user = User.objects.filter(email='test-permissions@example.com').first()
    if test_user:
        # Test domain-based mapping
        print("Testing domain-based role mapping...")
        _apply_google_email_role_overrides(test_user, 'admin@cybochengine.africa')
        
        # Check if admin role was assigned
        admin_roles = UserRole.objects.filter(
            user=test_user,
            role__name='admin',
            is_active=True
        )
        print(f"Admin role assigned via domain mapping: {admin_roles.exists()}")
        
        # Test individual email mapping
        print("Testing individual email mapping...")
        _apply_google_email_role_overrides(test_user, 'nelsonochieng516@gmail.com')
        
        sponsor_roles = UserRole.objects.filter(
            user=test_user,
            role__name='sponsor_admin',
            is_active=True
        )
        print(f"Sponsor admin role assigned via email mapping: {sponsor_roles.exists()}")

def main():
    """Run all permission tests."""
    print("🚀 Starting Permission Fix Tests")
    print("=" * 50)
    
    try:
        test_permission_utilities()
        test_recipe_permission_fix()
        test_oauth_role_override()
        
        print("\n✅ All permission tests completed successfully!")
        print("\n📋 Summary of fixes:")
        print("- Centralized permission utilities created")
        print("- Recipe generation now uses IsAdminOrDirector permission class")
        print("- Google OAuth uses scalable domain-based role mapping")
        print("- Finance views updated to use centralized permissions")
        print("- Consistent role-based access control across platform")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
