from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="MakiniShop API",
        default_version='v1',
        description="📦 Modern, clean, and easy-to-use API docs for MakiniShop",
        contact=openapi.Contact(email="support@makinishop.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Swagger UI
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='redoc'),

    # App-specific routes
    path('api/users/', include('users.urls')), 
    path('api/users/rbac/', include('users.rbac_urls')),        
    path('api/catalog/', include('catalog.urls')),      
    path('api/orders/', include('orders.urls')),        
    path('api/ai/', include('ai.urls')),
    path('api/audit/', include('audit.urls')),               
    path('api/events/', include('user_events.urls')),
    path('api/notifications/', include('notifications.urls')),
]

