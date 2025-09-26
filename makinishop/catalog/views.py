from rest_framework import generics, permissions
from django.utils import timezone
from django.db.models import Q, Prefetch
from django.core.cache import cache
from .models import Category, Product, FeaturedProduct, Wishlist, ProductImage, ProductVariant
from .serializers import (
    CategorySerializer, ProductSerializer, FeaturedProductSerializer, WishlistSerializer
)

CACHE_TIMEOUT = 60  # seconds

# -----------------------------
# Category
# -----------------------------
class CategoryListView(generics.ListAPIView):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()


# -----------------------------
# Product
# -----------------------------
class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Product.objects.none()

        # Encode query params to avoid CacheKeyWarning
        cache_key = f"product_list:{self.request.query_params.urlencode()}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        queryset = Product.objects.filter(is_active=True) \
            .select_related('category') \
            .prefetch_related(
                Prefetch('images', queryset=ProductImage.objects.all()),
                Prefetch('variants', queryset=ProductVariant.objects.all())
            )

        # Filtering
        category_id = self.request.query_params.get('category_id')
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        search = self.request.query_params.get('q')

        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        if search:
            queryset = queryset.filter(name__icontains=search)

        queryset = queryset.order_by('-created_at')
        cache.set(cache_key, queryset, CACHE_TIMEOUT)
        return queryset


class ProductDetailView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.all().select_related('category').prefetch_related('images', 'variants')
    lookup_field = 'id'


# -----------------------------
# Featured Products
# -----------------------------
class FeaturedProductListView(generics.ListAPIView):
    serializer_class = FeaturedProductSerializer
    queryset = FeaturedProduct.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return FeaturedProduct.objects.none()

        now = timezone.now()
        return FeaturedProduct.objects.filter(
            start_date__lte=now,
            is_personalized=False
        ).filter(Q(end_date__gte=now) | Q(end_date__isnull=True)) \
         .select_related('product', 'product__category') \
         .prefetch_related('product__images', 'product__variants') \
         .order_by('-priority', '-start_date')


class PersonalizedFeaturedProductListView(generics.ListAPIView):
    serializer_class = FeaturedProductSerializer
    queryset = FeaturedProduct.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return FeaturedProduct.objects.none()

        user = self.request.user if self.request.user.is_authenticated else None
        now = timezone.now()
        queryset = FeaturedProduct.objects.filter(
            start_date__lte=now,
            is_personalized=True
        ).filter(Q(end_date__gte=now) | Q(end_date__isnull=True)) \
         .select_related('product', 'product__category') \
         .prefetch_related('product__images', 'product__variants')

        if not user:
            return queryset.order_by('-priority', '-start_date')

        # Personalization: wishlist boost
        wishlist_ids = set(Wishlist.objects.filter(user=user).values_list('product_id', flat=True))

        def personalization_score(fp):
            score = 1.0 if fp.product.id in wishlist_ids else 0.0
            return score + (fp.priority / 100)

        items = list(queryset)
        items.sort(key=lambda x: personalization_score(x), reverse=True)
        return items


# -----------------------------
# Admin Featured Products
# -----------------------------
class AdminFeaturedProductCreateView(generics.CreateAPIView):
    serializer_class = FeaturedProductSerializer
    queryset = FeaturedProduct.objects.all()


class AdminFeaturedProductUpdateView(generics.UpdateAPIView):
    serializer_class = FeaturedProductSerializer
    queryset = FeaturedProduct.objects.all()
    lookup_field = 'id'


class AdminFeaturedProductDeleteView(generics.DestroyAPIView):
    serializer_class = FeaturedProductSerializer
    queryset = FeaturedProduct.objects.all()
    lookup_field = 'id'


# -----------------------------
# Wishlist
# -----------------------------
class WishlistListView(generics.ListAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Wishlist.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Wishlist.objects.none()
        return Wishlist.objects.filter(user=self.request.user) \
            .select_related('product', 'product__category') \
            .prefetch_related('product__images', 'product__variants')


class WishlistCreateView(generics.CreateAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WishlistDeleteView(generics.DestroyAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    queryset = Wishlist.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Wishlist.objects.none()
        return Wishlist.objects.filter(user=self.request.user)
