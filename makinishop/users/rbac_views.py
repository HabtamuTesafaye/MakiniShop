from rest_framework import generics, permissions, filters, status
from users.models import Role, Permission, RolePermission, UserRole
from users.rbac_serializers import RoleSerializer, PermissionSerializer, RolePermissionSerializer, UserRoleSerializer, ChangePasswordSerializer
from drf_spectacular.utils import extend_schema
from users.serializers import EmptySerializer
from rest_framework.response import Response
from rest_framework.views import APIView

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


# -----------------------------
# UserRole management
# -----------------------------
class UserRoleListView(generics.ListCreateAPIView):
    queryset = UserRole.objects.select_related('user', 'role').all()
    serializer_class = UserRoleSerializer
    permission_classes = [permissions.IsAdminUser]

class UserRoleDetailView(generics.RetrieveDestroyAPIView):
    queryset = UserRole.objects.select_related('user', 'role').all()
    serializer_class = UserRoleSerializer
    permission_classes = [permissions.IsAdminUser]

# -----------------------------
# Change Password
# -----------------------------
class ChangePasswordView(APIView):
    serializer_class = EmptySerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        old_password = serializer.validated_data['old_password']
        if not user.check_password(old_password):
            return Response({"old_password": "Wrong password."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)