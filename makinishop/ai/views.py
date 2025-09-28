
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import F
from catalog.models import Product
from .models import (
    ProductRecommendation,
    RecommendationFeedback,
    ProductEmbedding,
    UserEmbedding,
    ChatSession,
    ChatMessage,
)
from .serializers import (
    ProductRecommendationSerializer,
    RecommendationFeedbackSerializer,
    AIProductSerializer,
    ChatbotRequestSerializer,
    ChatSessionSerializer,
)
import numpy as np
import google.generativeai as genai
from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiParameter

from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from utils.security import block_ip

# ------------------------
# Product-based recommendations
# ------------------------

@method_decorator(ratelimit(key='ip', rate='30/m', block=True), name='dispatch')
@method_decorator(block_ip, name='dispatch')
class ProductRecommendationView(GenericAPIView):
    serializer_class = ProductRecommendationSerializer
    queryset = ProductRecommendation.objects.none()  # Suppress schema warnings

    @extend_schema(
        responses=ProductRecommendationSerializer(many=True),
        parameters=[
            OpenApiParameter(
                name="product_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID of the product",
            )
        ],
        description="Get product recommendations for a specific product based on similarity.",
    )
    def get(self, request, product_id):
        recs = ProductRecommendation.objects.filter(product_id=product_id).order_by("-score")[:10]
        serializer = self.get_serializer(recs, many=True)
        return Response(serializer.data)


# ------------------------
# User-specific recommendations
# ------------------------

@method_decorator(ratelimit(key='ip', rate='30/m', block=True), name='dispatch')
@method_decorator(block_ip, name='dispatch')
class UserRecommendationView(GenericAPIView):
    serializer_class = ProductRecommendationSerializer
    queryset = ProductRecommendation.objects.none()  # Suppress schema warnings

    @extend_schema(
        responses=ProductRecommendationSerializer(many=True),
        parameters=[
            OpenApiParameter(
                name="user_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID of the user",
            )
        ],
        description="Get product recommendations for a specific user.",
    )
    def get(self, request, user_id):
        recs = ProductRecommendation.objects.filter(user_id=user_id).order_by("-score")[:10]
        serializer = self.get_serializer(recs, many=True)
        return Response(serializer.data)


# ------------------------
# Feedback
# ------------------------
class RecommendationFeedbackView(GenericAPIView):
    serializer_class = RecommendationFeedbackSerializer
    queryset = RecommendationFeedback.objects.none()  # Suppress schema warnings

    @extend_schema(
        request=RecommendationFeedbackSerializer,
        responses={"200": {"message": "Feedback stored"}},
        description="Submit feedback for a product recommendation.",
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Feedback stored"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ------------------------
# AI Product Recommendations (Embedding similarity)
# ------------------------
class AIProductRecommendationView(GenericAPIView):
    serializer_class = AIProductSerializer
    queryset = Product.objects.none()  # Suppress schema warnings

    @extend_schema(
        responses=AIProductSerializer(many=True),
        parameters=[
            OpenApiParameter(
                name="product_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID of the product",
            )
        ],
        description="Get product recommendations based on embedding similarity.",
    )
    def get(self, request, product_id):
        try:
            prod_emb = ProductEmbedding.objects.get(product_id=product_id)
        except ProductEmbedding.DoesNotExist:
            return Response({"error": "Embedding not found"}, status=status.HTTP_404_NOT_FOUND)

        vector = np.frombuffer(prod_emb.embedding, dtype=np.float32)
        all_embeddings = ProductEmbedding.objects.exclude(product_id=product_id)
        results = []
        for e in all_embeddings:
            emb_vector = np.frombuffer(e.embedding, dtype=np.float32)
            score = np.dot(vector, emb_vector) / (np.linalg.norm(vector) * np.linalg.norm(emb_vector))
            results.append((score, e.product))

        results.sort(reverse=True)
        top_products = [p for _, p in results[:10]]
        serializer = self.get_serializer(top_products, many=True)
        return Response(serializer.data)


# ------------------------
# AI User Recommendations
# ------------------------
class AIUserRecommendationView(GenericAPIView):
    serializer_class = AIProductSerializer
    queryset = Product.objects.none()  # Suppress schema warnings

    @extend_schema(
        responses=AIProductSerializer(many=True),
        parameters=[
            OpenApiParameter(
                name="user_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID of the user",
            )
        ],
        description="Get product recommendations for a user based on their embedding.",
    )
    def get(self, request, user_id):
        try:
            user_emb = UserEmbedding.objects.get(user_id=user_id)
        except UserEmbedding.DoesNotExist:
            return Response({"error": "User embedding not found"}, status=status.HTTP_404_NOT_FOUND)

        user_vector = np.frombuffer(user_emb.embedding, dtype=np.float32)
        all_products = ProductEmbedding.objects.all()
        results = []
        for e in all_products:
            emb_vector = np.frombuffer(e.embedding, dtype=np.float32)
            score = np.dot(user_vector, emb_vector) / (np.linalg.norm(user_vector) * np.linalg.norm(emb_vector))
            results.append((score, e.product))

        results.sort(reverse=True)
        top_products = [p for _, p in results[:10]]
        serializer = self.get_serializer(top_products, many=True)
        return Response(serializer.data)


# ------------------------
# Trending Products
# ------------------------
class TrendingProductsView(GenericAPIView):
    serializer_class = AIProductSerializer
    queryset = Product.objects.none()  # Suppress schema warnings

    @extend_schema(
        responses=AIProductSerializer(many=True),
        description="Get the top 10 trending products based on purchase and view counts.",
    )
    def get(self, request):
        trending = Product.objects.order_by("-purchase_count", "-view_count")[:10]
        serializer = self.get_serializer(trending, many=True)
        return Response(serializer.data)


# ------------------------
# Chatbot
# ------------------------
class ChatbotView(GenericAPIView):
    serializer_class = ChatbotRequestSerializer
    permission_classes = []  # allow anonymous

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_message = serializer.validated_data["message"]
        session_id = serializer.validated_data.get("session_id")
        user = request.user if request.user.is_authenticated else None  # handle anonymous

        # Create or retrieve session
        if session_id:
            try:
                session = ChatSession.objects.get(id=session_id)
                # Optional: ensure session belongs to user if logged in
                if session.user and session.user != user:
                    return Response({"error": "Invalid session"}, status=status.HTTP_400_BAD_REQUEST)
            except ChatSession.DoesNotExist:
                return Response({"error": "Invalid session"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            session = ChatSession.objects.create(user=user)

        # Store user message
        ChatMessage.objects.create(session=session, sender="user", message=user_message)

        # Gemini API
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-pro")

        history = [
            {"role": "user" if msg.sender == "user" else "model", "parts": [{"text": msg.message}]}
            for msg in session.messages.order_by("created_at")
        ]

        response = model.generate_content(history)
        bot_reply = response.text

        # Store bot reply
        ChatMessage.objects.create(session=session, sender="bot", message=bot_reply)

        return Response(
            {
                "session_id": session.id,
                "response": bot_reply,
            }
        )
