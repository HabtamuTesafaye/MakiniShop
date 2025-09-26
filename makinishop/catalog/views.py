from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q, Prefetch
from django.core.cache import cache
from django.utils.text import slugify
from .models import Category, Product, ProductImage, ProductVariant, FeaturedProduct, Wishlist, ProductReview
from .serializers import (
    CategorySerializer, ProductSerializer, FeaturedProductSerializer,
    WishlistSerializer, ProductReviewSerializer
)

CACHE_TIMEOUT = 60  # seconds

# -----------------------------
# Category
# -----------------------------
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        name = serializer.validated_data.get('name')
        serializer.save(slug=slugify(name))

    @action(detail=False, methods=['GET'], url_path='search')
    def search(self, request):
        if getattr(self, "swagger_fake_view", False):
            return Response([])
        query = request.query_params.get('q', '')
        qs = Category.objects.filter(name__icontains=query) if query else Category.objects.all()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


# -----------------------------
# Product
# -----------------------------
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Product.objects.none()  # safe default

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Product.objects.none()

        cache_key = f"product_list:{self.request.query_params.urlencode()}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        qs = Product.objects.filter(is_active=True) \
            .select_related('category') \
            .prefetch_related(
                Prefetch('images', queryset=ProductImage.objects.all()),
                Prefetch('variants', queryset=ProductVariant.objects.all())
            )

        category_id = self.request.query_params.get('category_id')
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        search = self.request.query_params.get('q')

        if category_id:
            qs = qs.filter(category_id=category_id)
        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)
        if search:
            qs = qs.filter(name__icontains=search)

        qs = qs.order_by('-created_at')
        cache.set(cache_key, qs, CACHE_TIMEOUT)
        return qs

    @action(detail=False, methods=['GET'], url_path='search')
    def search(self, request):
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


# -----------------------------
# Featured Products
# -----------------------------
class FeaturedProductViewSet(viewsets.ModelViewSet):
    serializer_class = FeaturedProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = FeaturedProduct.objects.none()  # safe default

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

    @action(detail=False, methods=['GET'], url_path='personalized')
    def personalized_featured_products(self, request):
        if getattr(self, "swagger_fake_view", False):
            return Response([])
        user = request.user if request.user.is_authenticated else None
        now = timezone.now()
        qs = FeaturedProduct.objects.filter(
            start_date__lte=now,
            is_personalized=True
        ).filter(Q(end_date__gte=now) | Q(end_date__isnull=True)) \
         .select_related('product', 'product__category') \
         .prefetch_related('product__images', 'product__variants')

        if not user:
            serializer = self.get_serializer(qs.order_by('-priority', '-start_date'), many=True)
            return Response(serializer.data)

        wishlist_ids = set(Wishlist.objects.filter(user=user).values_list('product_id', flat=True))

        def score(fp):
            return (fp.priority / 100) + (1.0 if fp.product.id in wishlist_ids else 0.0)

        items = sorted(qs, key=score, reverse=True)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'], url_path='search')
    def search(self, request):
        if getattr(self, "swagger_fake_view", False):
            return Response([])
        query = request.query_params.get('q', '')
        qs = self.get_queryset()
        if query:
            qs = qs.filter(product__name__icontains=query)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


# -----------------------------
# Wishlist
# -----------------------------
class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Wishlist.objects.none()  # safe default

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Wishlist.objects.none()
        user = self.request.user
        if not user.is_authenticated:
            return Wishlist.objects.none()
        return Wishlist.objects.filter(user=user) \
            .select_related('product', 'product__category') \
            .prefetch_related('product__images', 'product__variants')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['GET'], url_path='search')
    def search(self, request):
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


# -----------------------------
# Product Review
# -----------------------------
class ProductReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = ProductReview.objects.none()  # safe default

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ProductReview.objects.none()
        product_id = self.kwargs.get('product_id')
        if not product_id:
            return ProductReview.objects.none()
        return ProductReview.objects.filter(product_id=product_id, is_public=True)

    def perform_create(self, serializer):
        product_id = self.kwargs.get('product_id')
        if not product_id:
            return
        product = self.get_product_or_404(product_id)
        serializer.save(user=self.request.user, product=product)

    def get_product_or_404(self, product_id):
        from django.shortcuts import get_object_or_404
        return get_object_or_404(Product, id=product_id)

    @action(detail=False, methods=['GET'], url_path='search')
    def search(self, request):
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
