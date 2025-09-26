from rest_framework import generics, permissions
from .models import UserEvent
from .serializers import UserEventSerializer

class UserEventListView(generics.ListAPIView):
    serializer_class = UserEventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserEvent.objects.filter(user=self.request.user).order_by('-created_at')
