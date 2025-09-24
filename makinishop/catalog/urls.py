from django.urls import path
from .views import (
    CategoryListView, ProductListView, ProductDetailView,
    FeaturedProductListView, PersonalizedFeaturedProductListView,
    AdminFeaturedProductCreateView, AdminFeaturedProductUpdateView, AdminFeaturedProductDeleteView
)

urlpatterns = [
    # Categories
    path('categories/', CategoryListView.as_view(), name='category-list'),

    # Products
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<int:id>/', ProductDetailView.as_view(), name='product-detail'),

    # Featured products
    path('featured/', FeaturedProductListView.as_view(), name='featured-list'),
    path('featured/personalized/', PersonalizedFeaturedProductListView.as_view(), name='featured-personalized-list'),

    # Admin Featured products
    path('admin/featured/', AdminFeaturedProductCreateView.as_view(), name='admin-featured-create'),
    path('admin/featured/<int:id>/', AdminFeaturedProductUpdateView.as_view(), name='admin-featured-update'),
    path('admin/featured/<int:id>/delete/', AdminFeaturedProductDeleteView.as_view(), name='admin-featured-delete'),
]
