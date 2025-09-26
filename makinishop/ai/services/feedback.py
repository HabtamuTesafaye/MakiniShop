# ai/services/feedback.py
import numpy as np
from ai.models import RecommendationFeedback, UserEmbedding, ProductEmbedding

def update_user_embedding_from_feedback(user_id: int, product_id: int, weight=0.1):
    try:
        user_emb = UserEmbedding.objects.get(user_id=user_id)
        product_emb = ProductEmbedding.objects.get(product_id=product_id)
    except (UserEmbedding.DoesNotExist, ProductEmbedding.DoesNotExist):
        return

    user_vector = np.frombuffer(user_emb.embedding, dtype=np.float32)
    product_vector = np.frombuffer(product_emb.embedding, dtype=np.float32)

    # Simple incremental update: new_user = (1 - w)*old + w*product
    updated_vector = (1 - weight) * user_vector + weight * product_vector
    user_emb.embedding = updated_vector.tobytes()
    user_emb.save()
