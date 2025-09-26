from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, ProductViewSet, FeaturedProductViewSet,
    WishlistViewSet, ProductReviewViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'featured', FeaturedProductViewSet, basename='featured')
router.register(r'wishlist', WishlistViewSet, basename='wishlist')
router.register(r'products/(?P<product_id>\d+)/reviews', ProductReviewViewSet, basename='product-review')

urlpatterns = router.urls
