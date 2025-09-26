from django.db import models
from django.conf import settings
from django.utils import timezone
from catalog.models import Product, ProductReview
from orders.models import CustomerOrder as Order

class UserEvent(models.Model):
    EVENT_TYPES = [
        ('review', 'Product Review'),
        ('wishlist_add', 'Wishlist Add'),
        ('purchase', 'Purchase'),
        ('featured_view', 'Featured Product View'),
        ('product_view', 'Product View'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    review = models.ForeignKey(ProductReview, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)  # Extra data like page, source, etc.
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'event_type', 'created_at']),
            models.Index(fields=['product']),
        ]

    def __str__(self):
        return f"{self.user} → {self.event_type} ({self.product})"
