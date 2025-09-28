
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
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from utils.security import block_ip
from utils.cloudinary_utils import upload_image_to_cloudinary
from utils.email_utils import send_templated_email


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
@method_decorator(ratelimit(key='ip', rate='60/m', block=True), name='dispatch')
@method_decorator(block_ip, name='dispatch')
class ProductViewSet(viewsets.ModelViewSet):
    # Example: override create to handle image upload
    def create(self, request, *args, **kwargs):
        # If image file is present in request.FILES, upload to Cloudinary
        image_file = request.FILES.get('image')
        if image_file:
            image_url = upload_image_to_cloudinary(image_file, folder='products')
            # Add image_url to validated_data or serializer context as needed
            # Example: request.data['image_url'] = image_url
            # You may need to adjust your ProductSerializer to accept image_url
        # ...existing code for create...
        return super().create(request, *args, **kwargs)
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Product.objects.none()  # safe default

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Product.objects.none()

        # Build cache key based on all query params
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

        # Filtering
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

import os

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
        wishlist = serializer.save(user=self.request.user)
        # Example: get product image URL from Cloudinary (if available)
        product_image_url = None
        if wishlist.product.images.exists():
            # Assuming ProductImage model has a 'file' field
            product_image = wishlist.product.images.first()
            if hasattr(product_image, 'file'):
                product_image_url = upload_image_to_cloudinary(product_image.file, folder='products')
        base_url = os.environ.get('BASE_URL', 'http://localhost:8000')
        send_templated_email.delay(
            subject=f"Added to Cart: {wishlist.product.name}",
            to_email=wishlist.user.email,
            template_name="add_to_cart.html",
            context={
                'user': wishlist.user,
                'product_name': wishlist.product.name,
                'cart_link': f"{base_url}/cart/",
                'product_image_url': product_image_url,
            },
            base_url=base_url
        )

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
