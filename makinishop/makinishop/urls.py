# makinishop/urls.py
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    # API Root + Docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # App-specific routes — each under their own namespace
    path('api/users/', include('users.urls')), 
    path('api/users/rbac/', include('users.rbac_urls')),        
    # path('api/catalog/', include('catalog.urls')),      
    # path('api/cart/', include('cart.urls')),            
    # path('api/orders/', include('orders.urls')),        
    # path('api/ai/', include('ai.urls')),               
    # path('api/reviews/', include('reviews.urls')),
    # path('api/wishlist/', include('wishlist.urls')),
    # path('api/shipping/', include('shipping.urls')),
    # path('api/discounts/', include('discounts.urls')),
    # path('api/addresses/', include('users.address_urls')),  
    # path('api/notifications/', include('notifications.urls')),
    # path('api/events/', include('events.urls')),
    # path('api/refunds/', include('refunds.urls')),
    # path('api/adminpanel/', include('adminpanel.urls')),   
]