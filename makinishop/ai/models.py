from django.db import models
from django.conf import settings
from catalog.models import Product
from django.utils import timezone
import uuid

# ==========================================================
# PRODUCT RECOMMENDATION
# ==========================================================
class ProductRecommendation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='recommendations'
    )
    recommended_product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='recommended_by'
    )
    score = models.FloatField(default=0)  # Confidence score
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'product', 'recommended_product')
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.product.name} → {self.recommended_product.name}"


# ==========================================================
# PRODUCT EMBEDDING (AI)
# ==========================================================
class ProductEmbedding(models.Model):
    product = models.OneToOneField(
        Product, on_delete=models.CASCADE, related_name='ai_embedding'
    )
    embedding = models.BinaryField()  # Serialized vector
    model = models.CharField(max_length=255)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Embedding: {self.product.name}"


# ==========================================================
# USER EMBEDDING (AI)
# ==========================================================
class UserEmbedding(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_embedding'
    )
    embedding = models.BinaryField()
    model = models.CharField(max_length=255)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"UserEmbedding: {self.user.email}"


# ==========================================================
# RECOMMENDATION FEEDBACK
# ==========================================================
class RecommendationFeedback(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)  # e.g., 'click', 'purchase', 'skip'
    score = models.FloatField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['product']),
        ]

    def __str__(self):
        return f"Feedback: {self.user.email} → {self.product.name} ({self.action})"


class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,  # allow null for anonymous
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session {self.id} for {self.user}"

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=50)  # "user" or "bot"
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
