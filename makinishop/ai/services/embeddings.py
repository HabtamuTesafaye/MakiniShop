import numpy as np
from catalog.models import Product
from ai.models import ProductEmbedding, UserEmbedding
from users.models import UserAccount
from django.db import transaction

VECTOR_DIM = 128  # example dimension

def generate_product_embedding(product: Product) -> np.ndarray:
    text_features = (product.name + " " + product.description).lower()
    vector = np.random.rand(VECTOR_DIM).astype(np.float32)  # mock embedding
    return vector

def generate_user_embedding(user: UserAccount) -> np.ndarray:
    vector = np.random.rand(VECTOR_DIM).astype(np.float32)
    return vector

def update_product_embeddings():
    products = Product.objects.all()
    for product in products:
        vector = generate_product_embedding(product)
        ProductEmbedding.objects.update_or_create(
            product=product,
            defaults={
                'embedding': vector.tobytes(),
                'model': 'mock-product-v1'
            }
        )

def update_user_embeddings():
    users = UserAccount.objects.all()
    for user in users:
        vector = generate_user_embedding(user)
        UserEmbedding.objects.update_or_create(
            user=user,
            defaults={
                'embedding': vector.tobytes(),
                'model': 'mock-user-v1'
            }
        )