"""
Centralized permission utilities for consistent role-based access control.
Provides helper functions to check admin permissions across the platform.
NOTE: Permissions are granted by admin only - these utilities only check existing permissions.
"""
from users.models import Role, UserRole


def has_admin_role(user, role_names=None):
    """
    Check if user has any of the specified admin roles.
    Only checks existing role assignments - does not grant any permissions.
    
    Args:
        user: User instance
        role_names: List of role names to check (defaults to admin roles)
    
    Returns:
        bool: True if user has any of the specified roles
    """
    if not user or not user.is_authenticated:
        return False
    
    # Django staff/superuser always has admin access
    if user.is_staff or user.is_superuser:
        return True
    
    # Default admin roles if not specified
    if role_names is None:
        role_names = ['admin', 'program_director']
    
    # Check role assignments through UserRole system (admin-granted only)
    return UserRole.objects.filter(
        user=user,
        role__name__in=role_names,
        is_active=True
    ).exists()


def has_any_admin_role(user):
    """
    Check if user has any admin-level role (broader check).
    Includes admin, program_director, and other management roles.
    """
    admin_role_names = [
        'admin',
        'program_director', 
        'sponsor_admin',
        'institution_admin',
        'organization_admin',
        'finance',
        'support'
    ]
    return has_admin_role(user, admin_role_names)


def can_manage_users(user):
    """
    Check if user can manage other users.
    Includes staff and user.manage permission through RBAC.
    """
    if not user or not user.is_authenticated:
        return False
    
    if user.is_staff or user.is_superuser:
        return True
    
    # Check for user.manage permission through policy engine
    try:
        from users.utils.policy_engine import check_permission
        allowed, _ = check_permission(user, 'user', 'manage', context=None)
        return allowed
    except ImportError:
        # Fallback to role-based check if policy engine not available
        return has_admin_role(user)


def get_user_primary_role(user):
    """
    Get the primary/most privileged role for a user.
    Used for UI display and routing decisions.
    """
    if not user or not user.is_authenticated:
        return None
    
    # Order of privilege (highest to lowest)
    role_hierarchy = [
        'admin',
        'program_director',
        'sponsor_admin', 
        'institution_admin',
        'organization_admin',
        'finance',
        'support',
        'analyst',
        'mentor',
        'employer',
        'student'
    ]
    
    user_roles = UserRole.objects.filter(
        user=user,
        is_active=True
    ).select_related('role')
    
    # Find the highest privilege role
    for role_name in role_hierarchy:
        if user_roles.filter(role__name=role_name).exists():
            return role_name
    
    # Default to student if no roles found
    return 'student'


def assign_role_if_not_exists(user, role_name, scope='global'):
    """
    Safely assign a role to a user if not already assigned.
    NOTE: This should only be used by admin users or system processes with explicit authorization.
    """
    try:
        role = Role.objects.get(name=role_name)
    except Role.DoesNotExist:
        return False, f"Role {role_name} not found"
    
    user_role, created = UserRole.objects.get_or_create(
        user=user,
        role=role,
        scope=scope,
        defaults={'is_active': True}
    )
    
    return created, f"Role {role_name} {'assigned' if created else 'already assigned'}"
