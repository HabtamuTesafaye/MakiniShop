from rest_framework import serializers
from .models import Category, Product, ProductImage, ProductVariant, FeaturedProduct, ProductEmbedding, Wishlist

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'created_at', 'updated_at']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'path', 'is_primary', 'width', 'height', 'metadata', 'created_at', 'updated_at']

class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'product', 'sku', 'name', 'price', 'stock', 'metadata', 'created_at', 'updated_at']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name', 'slug', 'description', 'price', 'stock', 'is_active',
            'avg_rating', 'rating_count', 'review_count', 'view_count', 'purchase_count',
            'metadata', 'category', 'images', 'variants', 'created_at', 'updated_at'
        ]

class FeaturedProductSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = FeaturedProduct
        fields = ['id', 'product', 'start_date', 'end_date', 'priority', 'is_personalized', 'metadata', 'created_at', 'updated_at']

class WishlistSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = ["id", "user", "product", "created_at"]
