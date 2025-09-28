# ai/tasks.py
from celery import shared_task
from ai.services.embeddings import update_product_embeddings, update_user_embeddings

@shared_task
def recompute_all_embeddings():
    update_product_embeddings()
    update_user_embeddings()
