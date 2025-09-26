from django.db import models
from django.utils import timezone
from users.models import UserAccount
from catalog.models import Product, ProductVariant
from django.core.validators import MinValueValidator
from django.db import models

# Enums
ORDER_STATUS_CHOICES = [
    ('open', 'Open'),
    ('pending', 'Pending'),
    ('paid', 'Paid'),
    ('shipped', 'Shipped'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]

CART_STATUS_CHOICES = [
    ('open', 'Open'),
    ('abandoned', 'Abandoned'),
]

PAYMENT_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
    ('refunded', 'Refunded'),
]

SHIPPING_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('shipped', 'Shipped'),
    ('delivered', 'Delivered'),
    ('cancelled', 'Cancelled'),
]

DISCOUNT_TYPE_CHOICES = [
    ('percent', 'Percent'),
    ('fixed', 'Fixed'),
    ('flash', 'Flash'),
    ('bundle', 'Bundle'),
]

# ------------------------
# Cart & CartItem
# ------------------------
class Cart(models.Model):
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    session_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=CART_STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.RESTRICT)
    variant = models.ForeignKey(ProductVariant, on_delete=models.RESTRICT, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

# ------------------------
# Orders
# ------------------------
class CustomerOrder(models.Model):
    user = models.ForeignKey(UserAccount, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

class OrderItem(models.Model):
    order = models.ForeignKey(CustomerOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.RESTRICT)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

# ------------------------
# Payments
# ------------------------
class Payment(models.Model):
    order = models.ForeignKey(CustomerOrder, on_delete=models.CASCADE, related_name='payments')
    provider = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    paid_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

# ------------------------
# Discounts
# ------------------------
class ProductDiscount(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    code = models.CharField(max_length=50, null=True, blank=True)
    type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

class OrderDiscount(models.Model):
    order = models.ForeignKey(CustomerOrder, on_delete=models.CASCADE, related_name='discounts')
    discount = models.ForeignKey(ProductDiscount, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

# ------------------------
# Shipping
# ------------------------
class ShippingMethod(models.Model):
    name = models.CharField(max_length=100)
    region = models.CharField(max_length=100, null=True, blank=True)
    min_cart_value = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    cost = models.DecimalField(max_digits=12, decimal_places=2)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

class OrderShipping(models.Model):
    order = models.ForeignKey(CustomerOrder, on_delete=models.CASCADE, related_name='shippings')
    shipping_method = models.ForeignKey(ShippingMethod, on_delete=models.SET_NULL, null=True)
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tracking_number = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=20, choices=SHIPPING_STATUS_CHOICES, default='pending')
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
