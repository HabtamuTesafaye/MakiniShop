from catalog.models import FeaturedProduct, Wishlist, ProductEmbedding, ProductReview
from user_events.models import UserEvent
from ai.models import UserEmbedding
from django.utils import timezone
from django.db.models import Q
import numpy as np

def personalized_featured(user_id: int, top_n=20):
    featured = FeaturedProduct.objects.filter(
        start_date__lte=timezone.now(),
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=timezone.now())
    ).order_by('-priority', '-start_date')[:50]

    # Compute personalization score
    scored = []
    wishlist_ids = set(Wishlist.objects.filter(user_id=user_id).values_list('product_id', flat=True))
    # Use ProductReview for ratings
    user_ratings = {r.product_id: r.rating for r in ProductReview.objects.filter(user_id=user_id, rating__isnull=False)}
    user_events = {e.product_id: e.event_type for e in UserEvent.objects.filter(user_id=user_id)}

    user_emb = UserEmbedding.objects.filter(user_id=user_id).first()
    if user_emb:
        user_vector = np.frombuffer(user_emb.embedding, dtype=np.float32)
    else:
        user_vector = None

    for f in featured:
        score = 0
        score += 0.4 if f.product_id in wishlist_ids else 0
        score += 0.3 * (user_ratings.get(f.product_id, 0) / 5.0)
        if user_vector:
            prod_emb = ProductEmbedding.objects.filter(product=f.product).first()
            if prod_emb:
                prod_vector = np.frombuffer(prod_emb.embedding, dtype=np.float32)
                # Avoid division by zero
                denom = np.linalg.norm(user_vector) * np.linalg.norm(prod_vector)
                if denom > 0:
                    score += 0.2 * (np.dot(user_vector, prod_vector) / denom)
        # Events weight
        event_score = 0
        if f.product_id in user_events:
            event_type = user_events[f.product_id]
            if event_type == 'view': event_score = 0.1
            elif event_type == 'cart': event_score = 0.5
            elif event_type == 'purchase': event_score = 1.0
        score += 0.1 * event_score
        scored.append((score, f.product))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:top_n]]