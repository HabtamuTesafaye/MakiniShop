from django.urls import path
from .views import (
    ProductRecommendationView,
    UserRecommendationView,
    RecommendationFeedbackView,
    AIProductRecommendationView,
    AIUserRecommendationView,
    TrendingProductsView,
    ChatbotView
)

urlpatterns = [
    path('products/<int:product_id>/recommendations/', ProductRecommendationView.as_view(), name='product-recommendation'),
    path('user/<int:user_id>/recommendations/', UserRecommendationView.as_view(), name='user-recommendation'),
    path('recommendations/feedback/', RecommendationFeedbackView.as_view(), name='recommendation-feedback'),
    path('recommendations/product/<int:product_id>/', AIProductRecommendationView.as_view(), name='ai-product-recommendation'),
    path('recommendations/user/<int:user_id>/', AIUserRecommendationView.as_view(), name='ai-user-recommendation'),
    path('trending/', TrendingProductsView.as_view(), name='trending-products'),
    path('chat/', ChatbotView.as_view(), name='ai-chatbot'), 

]
