from rest_framework import serializers
from users.models import Role, Permission, RolePermission, UserRole
from drf_spectacular.utils import extend_schema_field

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
    @extend_schema_field(RolePermissionSerializer(many=True))
    def get_permissions(self, obj):
        """
        Fully nested permissions with zero extra queries.
        Assumes obj.permissions is prefetched with select_related('permission').
        """
        role_perms = obj.permissions.all()  # prefetched
        return RolePermissionSerializer(role_perms, many=True).data


class UserRoleSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)

    class Meta:
        model = UserRole
        fields = ['id', 'user', 'role', 'user_email', 'role_name']
        extra_kwargs = {
            'user': {'write_only': True},
            'role': {'write_only': True}
        }

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    new_password2 = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "New passwords must match."})
        return attrs