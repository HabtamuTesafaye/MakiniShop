# users/views.py
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from users.serializers import UserSignupSerializer, UserLoginSerializer, UserProfileSerializer, UserAddressSerializer,EmptySerializer
from users.models import UserAccount, UserAddress
from rest_framework_simplejwt.tokens import RefreshToken

class SignupView(generics.CreateAPIView):
    serializer_class = UserSignupSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserProfileSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = UserAccount.objects.filter(email=serializer.validated_data['email']).first()
        if user and user.check_password(serializer.validated_data['password']):
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserProfileSerializer(user).data
            })
        return Response({'error': 'Invalid credentials'}, status=401)

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
        except Exception:
            return Response({"error": "Invalid token"}, status=400)

# -----------------------------
# Set Default Address
# -----------------------------
class SetDefaultAddressView(generics.GenericAPIView):
    serializer_class = None
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id, *args, **kwargs):
        address = UserAddress.objects.filter(id=id, user=request.user).first()
        if not address:
            return Response({'error': 'Address not found'}, status=status.HTTP_404_NOT_FOUND)
        address.is_default = True
        address.save()
        return Response({'message': 'Default address updated'}, status=status.HTTP_200_OK)

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

class UserAddressListView(generics.ListCreateAPIView):
    serializer_class = UserAddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Avoid schema generation errors
        if getattr(self, 'swagger_fake_view', False):
            return UserAddress.objects.none()
        return UserAddress.objects.filter(user=self.request.user)


class UserAddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserAddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserAddress.objects.filter(user=self.request.user)

class SetDefaultAddressView(generics.GenericAPIView):
    serializer_class = EmptySerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id, *args, **kwargs):
        address = UserAddress.objects.filter(id=id, user=request.user).first()
        if not address:
            return Response({'error': 'Address not found'}, status=status.HTTP_404_NOT_FOUND)
        address.is_default = True
        address.save()
        return Response({'message': 'Default address updated'}, status=status.HTTP_200_OK)
