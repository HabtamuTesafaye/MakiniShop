# users/views.py

from rest_framework import status, generics, permissions, serializers
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from users.serializers import UserSignupSerializer, UserLoginSerializer, UserProfileSerializer, UserAddressSerializer, EmptySerializer
from users.models import UserAccount, UserAddress
from rest_framework_simplejwt.tokens import RefreshToken

# --- Security, Rate Limiting, Email, Logging ---
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
import bleach
import logging
from django.conf import settings
from django.http import HttpResponseForbidden
from utils.email_utils import send_templated_email
import os


# Optional: Sentry integration
try:
    import sentry_sdk
    SENTRY_ENABLED = hasattr(settings, 'SENTRY_DSN') and bool(settings.SENTRY_DSN)
except ImportError:
    SENTRY_ENABLED = False

# Simple IP blocklist (could be moved to DB or settings)
BLOCKED_IPS = getattr(settings, 'BLOCKED_IPS', set())

def block_ip(view_func):
    def _wrapped_view(request, *args, **kwargs):
        ip = request.META.get('REMOTE_ADDR')
        if ip in BLOCKED_IPS:
            return HttpResponseForbidden('Your IP is blocked.')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

logger = logging.getLogger(__name__)


@method_decorator(ratelimit(key='ip', rate='10/m', block=True), name='dispatch')
@method_decorator(block_ip, name='dispatch')
class SignupView(generics.CreateAPIView):
    serializer_class = UserSignupSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            data = request.data.copy()
            for field in ['email', 'first_name', 'last_name']:
                if field in data:
                    data[field] = bleach.clean(data[field])

            serializer = self.get_serializer(data=data)
            try:
                serializer.is_valid(raise_exception=True)
                user = serializer.save()
            except serializers.ValidationError as e:
                logger.warning(f"Signup error: {e.detail}")
                return Response({'errors': e.detail}, status=status.HTTP_400_BAD_REQUEST)

            refresh = RefreshToken.for_user(user)

            # Send welcome email asynchronously
            base_url = os.environ.get('BASE_URL', 'http://localhost:8000')
            send_templated_email.delay(
                subject='Welcome to MakiniShop',
                to_email=user.email,
                template_name='welcome_email.html',
                context={
                    'user_id': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email
                },
                base_url=base_url
            )

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserProfileSerializer(user).data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Unexpected signup error: {e}")
            if SENTRY_ENABLED:
                sentry_sdk.capture_exception(e)
            return Response({'error': 'Signup failed'}, status=500)


# Example password reset endpoint (add to your views if not present)
class PasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request, *args, **kwargs):
        import os
        email = request.data.get('email')
        user = UserAccount.objects.filter(email=email).first()
        if not user:
            return Response({'error': 'User not found'}, status=404)
        # Generate reset link (example, replace with your logic)
        reset_token = 'dummy-token'  # Replace with real token logic
        base_url = os.environ.get('BASE_URL', 'http://localhost:8000')
        reset_link = f"{base_url}/reset-password/{reset_token}/"
        from makinishop.utils.email_utils import send_templated_email
        send_templated_email.delay(
            subject='Password Reset Request',
            to_email=user.email,
            template_name='password_reset.html',
            context={'user': user, 'reset_link': reset_link},
            base_url=base_url
        )
        return Response({'message': 'Password reset email sent.'})



@method_decorator(ratelimit(key='ip', rate='20/m', block=True), name='dispatch')
@method_decorator(block_ip, name='dispatch')
class LoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            data = request.data.copy()
            for field in ['email']:
                if field in data:
                    data[field] = bleach.clean(data[field])
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            user = UserAccount.objects.filter(email=serializer.validated_data['email']).first()
            if user and user.check_password(serializer.validated_data['password']):
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': UserProfileSerializer(user).data
                })
            logger.warning(f"Failed login attempt for email: {serializer.validated_data.get('email')}")
            return Response({'error': 'Invalid credentials'}, status=401)
        except Exception as e:
            logger.error(f"Login error: {e}")
            if SENTRY_ENABLED:
                sentry_sdk.capture_exception(e)
            return Response({'error': 'Login failed'}, status=500)


@method_decorator(ratelimit(key='ip', rate='30/m', block=True), name='dispatch')
@method_decorator(block_ip, name='dispatch')
class LogoutView(generics.GenericAPIView):
    serializer_class = EmptySerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({"error": "Refresh token required"}, status=400)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Successfully logged out"})
        except Exception as e:
            logger.warning(f"Logout error: {e}")
            if SENTRY_ENABLED:
                sentry_sdk.capture_exception(e)
            return Response({"error": "Invalid token"}, status=400)


# -----------------------------
# Set Default Address
# -----------------------------
@method_decorator(ratelimit(key='user', rate='10/m', block=True), name='dispatch')
@method_decorator(block_ip, name='dispatch')
class SetDefaultAddressView(generics.GenericAPIView):
    serializer_class = EmptySerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id, *args, **kwargs):
        try:
            address = UserAddress.objects.filter(id=id, user=request.user).first()
            if not address:
                return Response({'error': 'Address not found'}, status=status.HTTP_404_NOT_FOUND)
            address.is_default = True
            address.save()
            return Response({'message': 'Default address updated'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Set default address error: {e}")
            if SENTRY_ENABLED:
                sentry_sdk.capture_exception(e)
            return Response({'error': 'Failed to set default address'}, status=500)


@method_decorator(ratelimit(key='user', rate='30/m', block=True), name='dispatch')
@method_decorator(block_ip, name='dispatch')
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


@method_decorator(ratelimit(key='user', rate='30/m', block=True), name='dispatch')
@method_decorator(block_ip, name='dispatch')
class UserAddressListView(generics.ListCreateAPIView):
    serializer_class = UserAddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Avoid schema generation errors
        if getattr(self, 'swagger_fake_view', False):
            return UserAddress.objects.none()
        return UserAddress.objects.filter(user=self.request.user)



@method_decorator(ratelimit(key='user', rate='30/m', block=True), name='dispatch')
@method_decorator(block_ip, name='dispatch')
class UserAddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserAddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserAddress.objects.filter(user=self.request.user)

