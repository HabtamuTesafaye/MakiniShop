from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ProductReview, Wishlist
from user_events.models import UserEvent

@receiver(post_save, sender=ProductReview)
def create_review_event(sender, instance, created, **kwargs):
    if created and instance.user:
        UserEvent.objects.create(
            user=instance.user,
            event_type='review',
            product=instance.product,
            review=instance
        )

@receiver(post_save, sender=Wishlist)
def create_wishlist_event(sender, instance, created, **kwargs):
    if created:
        UserEvent.objects.create(
            user=instance.user,
            event_type='wishlist_add',
            product=instance.product
        )
