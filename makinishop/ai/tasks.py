# ai/tasks.py
from celery import shared_task
from ai.services.embeddings import update_product_embeddings, update_user_embeddings
from ai.services.recommendations import get_product_recommendations, get_user_recommendations

@shared_task
def recompute_all_embeddings():
    update_product_embeddings()
    update_user_embeddings()
