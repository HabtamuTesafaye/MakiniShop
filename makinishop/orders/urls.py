from django.urls import path
from orders.views import (
    CartListCreateView, CartDetailView, CartAddItemView, CartRemoveItemView, CartCheckoutView,
    OrderListCreateView, OrderDetailView, OrderUpdateStatusView,
    OrderItemListView, OrderItemDetailView,
    PaymentListCreateView, PaymentDetailView, PaymentConfirmView,
    OrderDiscountListCreateView, OrderDiscountDetailView,
    OrderShippingListCreateView, OrderShippingDetailView, OrderShippingUpdateStatusView,ChapaPaymentConfirmView
)

urlpatterns = [
    # Cart
    path('cart/', CartListCreateView.as_view(), name='cart-list-create'),
    path('cart/<int:pk>/', CartDetailView.as_view(), name='cart-detail'),
    path('cart/<int:pk>/add-item/', CartAddItemView.as_view(), name='cart-add-item'),
    path('cart/<int:pk>/remove-item/<int:item_id>/', CartRemoveItemView.as_view(), name='cart-remove-item'),
    path('cart/<int:pk>/checkout/', CartCheckoutView.as_view(), name='cart-checkout'),

    # Orders
    path('orders/', OrderListCreateView.as_view(), name='order-list-create'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:pk>/update-status/', OrderUpdateStatusView.as_view(), name='order-update-status'),

    # Order Items
    path('orders/<int:order_id>/items/', OrderItemListView.as_view(), name='order-items-list'),
    path('orders/<int:order_id>/items/<int:pk>/', OrderItemDetailView.as_view(), name='order-item-detail'),

    # Payments
    path('orders/<int:order_id>/payments/', PaymentListCreateView.as_view(), name='payment-list-create'),
    path('orders/<int:order_id>/payments/<int:pk>/', PaymentDetailView.as_view(), name='payment-detail'),
    path('orders/<int:order_id>/payments/<int:pk>/confirm/', PaymentConfirmView.as_view(), name='payment-confirm'),
    path('payment/confirm/<int:order_id>/', ChapaPaymentConfirmView.as_view(), name='chapa-payment-confirm'),

    # Discounts
    path('orders/<int:order_id>/discounts/', OrderDiscountListCreateView.as_view(), name='order-discount-list-create'),
    path('orders/<int:order_id>/discounts/<int:pk>/', OrderDiscountDetailView.as_view(), name='order-discount-detail'),

    # Shipping
    path('orders/<int:order_id>/shipping/', OrderShippingListCreateView.as_view(), name='order-shipping-list-create'),
    path('orders/<int:order_id>/shipping/<int:pk>/', OrderShippingDetailView.as_view(), name='order-shipping-detail'),
    path('orders/<int:order_id>/shipping/<int:pk>/update-status/', OrderShippingUpdateStatusView.as_view(), name='order-shipping-update-status'),
]
