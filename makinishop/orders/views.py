
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from orders.models import (
    Cart, CartItem, CustomerOrder, OrderItem, Payment,
    ProductDiscount, OrderDiscount, ShippingMethod, OrderShipping
)

# Email utility
from utils.email_utils import send_templated_email
import os
from orders.serializers import (
    CartSerializer, CartItemSerializer, CustomerOrderSerializer,
    PaymentSerializer, ProductDiscountSerializer, OrderDiscountSerializer,
    ShippingMethodSerializer, OrderShippingSerializer, OrderItemSerializer
)

# --- Security decorators ---
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from utils.security import block_ip

# ------------------------
# Cart Views
# ------------------------

@method_decorator(ratelimit(key='user', rate='30/m', block=True), name='dispatch')
@method_decorator(block_ip, name='dispatch')
class CartListCreateView(generics.ListCreateAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Cart.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Cart.objects.none()
        return Cart.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CartDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Cart.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Cart.objects.none()
        return Cart.objects.filter(user=self.request.user)


class CartAddItemView(generics.CreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = CartItem.objects.none()
    swagger_fake_view = True

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CartRemoveItemView(generics.DestroyAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = CartItem.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return CartItem.objects.none()
        return CartItem.objects.filter(cart__user=self.request.user)


class CartCheckoutView(generics.GenericAPIView):
    serializer_class = CustomerOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = CustomerOrder.objects.none()
    swagger_fake_view = True

    @transaction.atomic
    def post(self, request, cart_id):
        cart = get_object_or_404(Cart, id=cart_id, user=request.user)
        if not cart.items.exists():
            return Response({"error": "Cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        cart_items = cart.items.select_related('product').all()
        product_ids = [item.product_id for item in cart_items]

        active_discounts = ProductDiscount.objects.filter(
            product_id__in=product_ids,
            active=True,
            starts_at__lte=now,
            ends_at__gte=now
        )
        discount_map = {}
        for disc in active_discounts:
            discount_map.setdefault(disc.product_id, []).append(disc)

        order = CustomerOrder.objects.create(user=request.user, total=0, status='pending')
        order_total = Decimal(0)
        order_items = []

        for item in cart_items:
            original_total = Decimal(item.total)
            discounted_total = original_total
            applied_discounts = []

            for discount in discount_map.get(item.product_id, []):
                if discount.type == 'percent':
                    discounted_total *= (Decimal(100) - discount.amount) / Decimal(100)
                elif discount.type in ['fixed', 'flash']:
                    discounted_total = max(discounted_total - discount.amount, Decimal(0))
                applied_discounts.append(discount)

            discounted_total = discounted_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            OrderItem.objects.create(
                order=order,
                product=item.product,
                unit_price=item.unit_price,
                quantity=item.quantity,
                total=discounted_total
            )
            order_items.append({
                'name': item.product.name,
                'quantity': item.quantity
            })

            for discount in applied_discounts:
                OrderDiscount.objects.create(
                    order=order,
                    discount=discount,
                    amount=original_total - discounted_total
                )

            order_total += discounted_total

        order.total = order_total
        order.save()

        cart.status = 'abandoned'
        cart.items.all().delete()
        cart.save()

        # Send order confirmation email
        base_url = os.environ.get('BASE_URL', 'http://localhost:8000')
        send_templated_email.delay(
            subject=f"Order Confirmation #{order.id}",
            to_email=request.user.email,
            template_name="order_confirmation.html",
            context={
                'user': request.user,
                'order_id': order.id,
                'order_items': order_items,
                'order_total': order_total,
            },
            base_url=base_url
        )

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ------------------------
# Order Views
# ------------------------
class OrderListCreateView(generics.ListCreateAPIView):
    serializer_class = CustomerOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = CustomerOrder.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return CustomerOrder.objects.none()
        return CustomerOrder.objects.filter(user=self.request.user)


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CustomerOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = CustomerOrder.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return CustomerOrder.objects.none()
        return CustomerOrder.objects.filter(user=self.request.user)


class OrderUpdateStatusView(generics.UpdateAPIView):
    serializer_class = CustomerOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    fields = ['status']
    queryset = CustomerOrder.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return CustomerOrder.objects.none()
        return CustomerOrder.objects.filter(user=self.request.user)


# ------------------------
# OrderItem Views
# ------------------------
class OrderItemListView(generics.ListAPIView):
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = OrderItem.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return OrderItem.objects.none()
        order_id = self.kwargs.get('order_id')
        if not order_id:
            return OrderItem.objects.none()
        return OrderItem.objects.filter(order__id=order_id, order__user=self.request.user)


class OrderItemDetailView(generics.RetrieveAPIView):
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = OrderItem.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return OrderItem.objects.none()
        order_id = self.kwargs.get('order_id')
        if not order_id:
            return OrderItem.objects.none()
        return OrderItem.objects.filter(order__id=order_id, order__user=self.request.user)


# ------------------------
# Payment Views
# ------------------------
class PaymentListCreateView(generics.ListCreateAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Payment.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Payment.objects.none()
        order_id = self.kwargs.get('order_id')
        if not order_id:
            return Payment.objects.none()
        return Payment.objects.filter(order__id=order_id, order__user=self.request.user)

    def perform_create(self, serializer):
        payment = serializer.save(user=self.request.user)
        # Send payment success email
        base_url = os.environ.get('BASE_URL', 'http://localhost:8000')
        send_templated_email.delay(
            subject=f"Payment Successful for Order #{payment.order.id}",
            to_email=payment.user.email,
            template_name="payment_success.html",
            context={
                'user': payment.user,
                'order_id': payment.order.id,
            },
            base_url=base_url
        )


class PaymentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Payment.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Payment.objects.none()
        order_id = self.kwargs.get('order_id')
        if not order_id:
            return Payment.objects.none()
        return Payment.objects.filter(order__id=order_id, order__user=self.request.user)


class PaymentConfirmView(generics.UpdateAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    fields = ['status']
    queryset = Payment.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Payment.objects.none()
        order_id = self.kwargs.get('order_id')
        if not order_id:
            return Payment.objects.none()
        return Payment.objects.filter(order__id=order_id, order__user=self.request.user)


# ------------------------
# Discount Views
# ------------------------
class OrderDiscountListCreateView(generics.ListCreateAPIView):
    serializer_class = OrderDiscountSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = OrderDiscount.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return OrderDiscount.objects.none()
        order_id = self.kwargs.get('order_id')
        if not order_id:
            return OrderDiscount.objects.none()
        return OrderDiscount.objects.filter(order__id=order_id, order__user=self.request.user)


class OrderDiscountDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderDiscountSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = OrderDiscount.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return OrderDiscount.objects.none()
        order_id = self.kwargs.get('order_id')
        if not order_id:
            return OrderDiscount.objects.none()
        return OrderDiscount.objects.filter(order__id=order_id, order__user=self.request.user)


# ------------------------
# Shipping Views
# ------------------------
class ShippingMethodViewSet(viewsets.ModelViewSet):
    queryset = ShippingMethod.objects.all()
    serializer_class = ShippingMethodSerializer
    permission_classes = [permissions.IsAuthenticated]


class OrderShippingListCreateView(generics.ListCreateAPIView):
    serializer_class = OrderShippingSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = OrderShipping.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return OrderShipping.objects.none()
        order_id = self.kwargs.get('order_id')
        if not order_id:
            return OrderShipping.objects.none()
        return OrderShipping.objects.filter(order__id=order_id, order__user=self.request.user)


class OrderShippingDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderShippingSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = OrderShipping.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return OrderShipping.objects.none()
        order_id = self.kwargs.get('order_id')
        if not order_id:
            return OrderShipping.objects.none()
        return OrderShipping.objects.filter(order__id=order_id, order__user=self.request.user)


class OrderShippingUpdateStatusView(generics.UpdateAPIView):
    serializer_class = OrderShippingSerializer
    permission_classes = [permissions.IsAuthenticated]
    fields = ['status']
    queryset = OrderShipping.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return OrderShipping.objects.none()
        order_id = self.kwargs.get('order_id')
        if not order_id:
            return OrderShipping.objects.none()
        return OrderShipping.objects.filter(order__id=order_id, order__user=self.request.user)
