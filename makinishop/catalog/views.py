from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from .models import Category, Product, FeaturedProduct
from .serializers import CategorySerializer, ProductSerializer, FeaturedProductSerializer


# -----------------------------
# Category
# -----------------------------
class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


# -----------------------------
# Product
# -----------------------------
class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('category')
        queryset = queryset.prefetch_related('images', 'variants')  # ManyToMany / reverse relations

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

        return queryset.order_by('-created_at')



class ProductDetailView(generics.RetrieveAPIView):from rest_framework import generics, status
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from .models import Category, Product, FeaturedProduct
from .serializers import CategorySerializer, ProductSerializer, FeaturedProductSerializer


# -----------------------------
# Category
# -----------------------------
class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


# -----------------------------
# Product
# -----------------------------
class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('category')
        queryset = queryset.prefetch_related('images', 'variants')

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

        return queryset.order_by('-created_at')


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'id'


# -----------------------------
# Featured Products
# -----------------------------
class FeaturedProductListView(generics.ListAPIView):
    serializer_class = FeaturedProductSerializer

    def get_queryset(self):
        now = timezone.now()
        return FeaturedProduct.objects.filter(
            start_date__lte=now,
        ).filter(
            Q(end_date__gte=now) | Q(end_date__isnull=True),
            is_personalized=False
        ).select_related('product', 'product__category') \
         .prefetch_related('product__images', 'product__variants') \
         .order_by('-priority', '-start_date')


class PersonalizedFeaturedProductListView(generics.ListAPIView):
    serializer_class = FeaturedProductSerializer

    def get_queryset(self):
        now = timezone.now()
        user_id = self.request.query_params.get('user_id')
        anon_id = self.request.query_params.get('anon_id')

        # Start from active personalized featured products
        queryset = FeaturedProduct.objects.filter(
            start_date__lte=now,
            is_personalized=True
        ).filter(
            Q(end_date__gte=now) | Q(end_date__isnull=True)
        ).select_related('product', 'product__category') \
         .prefetch_related('product__images', 'product__variants')

        # TODO: Implement personalization logic using wishlist, ratings, embeddings, events
        # Example placeholder: just returning the queryset for now
        return queryset.order_by('-priority', '-start_date')


# -----------------------------
# Admin Featured Products CRUD
# -----------------------------
class AdminFeaturedProductCreateView(generics.CreateAPIView):
    serializer_class = FeaturedProductSerializer
    queryset = FeaturedProduct.objects.all()


class AdminFeaturedProductUpdateView(generics.UpdateAPIView):
    serializer_class = FeaturedProductSerializer
    queryset = FeaturedProduct.objects.all()
    lookup_field = 'id'


class AdminFeaturedProductDeleteView(generics.DestroyAPIView):
    queryset = FeaturedProduct.objects.all()
    lookup_field = 'id'

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'id'


# -----------------------------
# Featured Products
# -----------------------------
class FeaturedProductListView(generics.ListAPIView):
    serializer_class = FeaturedProductSerializer

    def get_queryset(self):
        now = timezone.now()
        return FeaturedProduct.objects.filter(
            start_date__lte=now,
        ).filter(
            Q(end_date__gte=now) | Q(end_date__isnull=True)
        ).select_related('product', 'product__category') \
         .prefetch_related('product__images', 'product__variants') \
         .order_by('-priority', '-start_date')

