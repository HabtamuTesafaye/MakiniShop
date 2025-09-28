from rest_framework import serializers
from catalog.models import Product
from .models import ProductRecommendation, RecommendationFeedback, ChatMessage, ChatSession

class AIProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'price', 'category', 'avg_rating', 'view_count', 'purchase_count']

class ProductRecommendationSerializer(serializers.ModelSerializer):
    recommended_product = AIProductSerializer()
    class Meta:
        model = ProductRecommendation
        fields = ['recommended_product', 'score']

class RecommendationFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationFeedback
        fields = ['user', 'product', 'action', 'score']


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'session', 'sender', 'message', 'created_at']

class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ['id', 'user', 'created_at', 'messages']
class ChatbotRequestSerializer(serializers.Serializer):
    message = serializers.CharField(help_text="The message to send to the chatbot")
    session_id = serializers.IntegerField(required=False, help_text="Optional session ID to continue a conversation")
