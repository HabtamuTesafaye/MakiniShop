from rest_framework import serializers
from .models import Role, Permission, RolePermission

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'code', 'description']


class RolePermissionSerializer(serializers.ModelSerializer):
    permission_detail = PermissionSerializer(source='permission', read_only=True)

    class Meta:
        model = RolePermission
        fields = ['id', 'role', 'permission', 'permission_detail']


class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permissions']

    def get_permissions(self, obj):
        """
        Fully nested permissions with zero extra queries.
        Assumes obj.permissions is prefetched with select_related('permission').
        """
        role_perms = obj.permissions.all()  # prefetched
        return RolePermissionSerializer(role_perms, many=True).data
