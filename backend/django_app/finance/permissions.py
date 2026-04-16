"""
Finance permissions.

Design goal: keep existing admin/finance assignments intact while enforcing RBAC
for finance-wide endpoints. Object-level scoping is still handled primarily by
querysets in viewsets (e.g. users can only see their own wallets/invoices).
"""

from rest_framework import permissions

from programs.permissions import user_has_finance_role
from users.utils.permission_utils import has_admin_role


class IsFinanceOrAdmin(permissions.BasePermission):
    """
    True for staff/superusers, finance role holders, or platform admins.

    Note: platform "admin" role is not necessarily Django is_staff; we preserve
    existing behavior by also checking RBAC roles via `has_admin_role`.
    """

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
            return True
        if user_has_finance_role(user):
            return True
        return has_admin_role(user, ["admin", "finance"])

