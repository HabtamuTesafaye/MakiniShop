from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from orders.models import (
    Cart, CartItem,
    CustomerOrder, OrderItem,
    Payment, ShippingMethod, OrderShipping
)
from .serializers import (
    CartSerializer, CartItemSerializer,
    CustomerOrderSerializer, OrderItemSerializer,
    PaymentSerializer, ShippingMethodSerializer, OrderShippingSerializer
)
from django.shortcuts import get_object_or_404
from django.db import transaction

# ------------------------
# Cart
# ------------------------
class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        cart = self.get_object()
        serializer = CartItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(cart=cart)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ------------------------
# Orders
# ------------------------
class CustomerOrderViewSet(viewsets.ModelViewSet):
    queryset = CustomerOrder.objects.all()
    serializer_class = CustomerOrderSerializer

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def create_from_cart(self, request):
        user = request.user
        cart_id = request.data.get('cart_id')
        cart = get_object_or_404(Cart, id=cart_id, user=user)
        
        order = CustomerOrder.objects.create(user=user, total=0)
        total = 0
        for item in cart.items.all():
            oi = OrderItem.objects.create(
                order=order,
                product=item.product,
                variant=item.variant,
                unit_price=item.unit_price,
                quantity=item.quantity,
                total=item.total
            )
            total += item.total
        order.total = total
        order.save()
        cart.status = 'abandoned'
        cart.save()
        serializer = CustomerOrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# ------------------------
# Payments
# ------------------------
class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

# ------------------------
# Shipping
# ------------------------
class ShippingMethodViewSet(viewsets.ModelViewSet):
    queryset = ShippingMethod.objects.all()
    serializer_class = ShippingMethodSerializer

class OrderShippingViewSet(viewsets.ModelViewSet):
    queryset = OrderShipping.objects.all()
    serializer_class = OrderShippingSerializer
