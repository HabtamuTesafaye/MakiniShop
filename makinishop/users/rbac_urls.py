# rbac_urls/urls.py
from django.urls import path
from . import rbac_views

urlpatterns = [
    # Permissions
    path('permissions/', rbac_views.PermissionListCreateView.as_view(), name='permission-list'),
    path('permissions/<int:pk>/', rbac_views.PermissionDetailView.as_view(), name='permission-detail'),

    # Roles
    path('roles/', rbac_views.RoleListCreateView.as_view(), name='role-list'),
    path('roles/<int:pk>/', rbac_views.RoleDetailView.as_view(), name='role-detail'),

    # RolePermissions
    path('role-permissions/', rbac_views.RolePermissionListCreateView.as_view(), name='role-permission-list'),
    path('role-permissions/<int:pk>/', rbac_views.RolePermissionDetailView.as_view(), name='role-permission-detail'),
]
