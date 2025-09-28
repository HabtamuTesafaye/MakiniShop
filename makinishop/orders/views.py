
from rest_framework import generics, permissions, status, viewsets
from rest_framework.views import APIView
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


from utils.chapa import create_chapa_payment

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

        # --- create order as before ---
        now = timezone.now()
        cart_items = cart.items.select_related('product').all()
        order = CustomerOrder.objects.create(user=request.user, total=0, status='pending')
        order_total = Decimal(0)

        for item in cart_items:
            total = Decimal(item.total)
            OrderItem.objects.create(
                order=order,
                product=item.product,
                unit_price=item.unit_price,
                quantity=item.quantity,
                total=total
            )
            order_total += total

        order.total = order_total
        order.save()

        # --- initialize Chapa payment ---
        callback_url = f"{os.environ.get('BASE_URL')}/api/payment/confirm/{order.id}/"
        try:
            chapa_resp = create_chapa_payment(
                email=request.user.email,
                amount=float(order_total),
                tx_ref=str(order.id),
                callback_url=callback_url
            )
        except Exception as e:
            return Response({"error": f"Chapa payment failed: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Return Chapa payment URL to frontend
        return Response({
            "order_id": order.id,
            "checkout_url": chapa_resp.get("data", {}).get("checkout_url")
        }, status=status.HTTP_201_CREATED)
    

class ChapaPaymentConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, order_id):
        tx_ref = request.data.get("tx_ref")
        status = request.data.get("status")

        order = get_object_or_404(CustomerOrder, id=order_id)

        if status == "success":
            Payment.objects.create(
                order=order,
                user=order.user,
                amount=order.total,
                status="paid",
                transaction_reference=tx_ref
            )
            order.status = "paid"
            order.save()

        return Response({"message": "Payment processed"})


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
