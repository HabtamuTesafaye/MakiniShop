from rest_framework import serializers
from orders.models import (
    Cart, CartItem,
    CustomerOrder, OrderItem,
    Payment, ProductDiscount, OrderDiscount,
    ShippingMethod, OrderShipping
)
from catalog.models import Product, ProductVariant

# ------------------------
# Cart & CartItem
# ------------------------
class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = '__all__'

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = '__all__'

# ------------------------
# Orders
# ------------------------
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'

class CustomerOrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    class Meta:
        model = CustomerOrder
        fields = '__all__'

# ------------------------
# Payments
# ------------------------
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

# ------------------------
# Discounts
# ------------------------
class ProductDiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductDiscount
        fields = '__all__'

class OrderDiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDiscount
        fields = '__all__'

# ------------------------
# Shipping
# ------------------------
class ShippingMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingMethod
        fields = '__all__'

class OrderShippingSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderShipping
        fields = '__all__'
