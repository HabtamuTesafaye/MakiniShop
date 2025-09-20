from rest_framework import generics, permissions, filters
from .models import Role, Permission, RolePermission
from .rbac_serializers import RoleSerializer, PermissionSerializer, RolePermissionSerializer
from drf_spectacular.utils import extend_schema


# -----------------------------
# Admin-only permission
# -----------------------------
class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff


# -----------------------------
# Permissions
# -----------------------------
@extend_schema(
    description="List all permissions (admin only)",
    responses={200: PermissionSerializer(many=True)}
)
class PermissionListCreateView(generics.ListCreateAPIView):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'description']
    ordering_fields = ['id', 'code']
    ordering = ['id']


class PermissionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAdminUser]


# -----------------------------
# Roles
# -----------------------------
class RoleListCreateView(generics.ListCreateAPIView):
    queryset = Role.objects.prefetch_related(
        'permissions__permission'  # prefetch related permissions for optimal queries
    ).all()
    serializer_class = RoleSerializer
    permission_classes = [IsAdminUser]


class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Role.objects.prefetch_related(
        'permissions__permission'
    ).all()
    serializer_class = RoleSerializer
    permission_classes = [IsAdminUser]


# -----------------------------
# Role-Permissions
# -----------------------------
class RolePermissionListCreateView(generics.ListCreateAPIView):
    queryset = RolePermission.objects.select_related('permission', 'role').all()
    serializer_class = RolePermissionSerializer
    permission_classes = [IsAdminUser]


class RolePermissionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = RolePermission.objects.select_related('permission', 'role').all()
    serializer_class = RolePermissionSerializer
    permission_classes = [IsAdminUser]
