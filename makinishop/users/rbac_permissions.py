# users/rbac_permissions.py
from rest_framework import permissions
from .models import Permission

class HasPermission(permissions.BasePermission):
    """
    Check if the authenticated user has the required permission.
    Usage: @permission_classes([HasPermission('permission_codename')])
    """

    def __init__(self, codename):
        self.codename = codename

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        if user.is_staff or user.is_superuser:
            return True

        # Cache permissions to avoid repeated DB hits
        if not hasattr(user, '_cached_permissions'):
            role_perms = Permission.objects.filter(
                rolepermission__role__users=user
            ).values_list('code', flat=True)
            user_perms = user.user_permissions.values_list('codename', flat=True)
            user._cached_permissions = set(role_perms) | set(user_perms)

        return self.codename in user._cached_permissions
