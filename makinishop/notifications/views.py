
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import NotificationTemplate, UserNotificationPref, NotificationQueue
from .serializers import NotificationTemplateSerializer, UserNotificationPrefSerializer, NotificationQueueSerializer
from .tasks import send_notification_email
# --- Trigger Notification Endpoint ---
from rest_framework.views import APIView

# --- Notification Template Views ---
class NotificationTemplateListView(generics.ListAPIView):
	queryset = NotificationTemplate.objects.filter(is_active=True)
	serializer_class = NotificationTemplateSerializer
	permission_classes = [permissions.AllowAny]  # Publicly visible
	swagger_fake_view = False

class NotificationTemplateCreateView(generics.CreateAPIView):
	queryset = NotificationTemplate.objects.all()
	serializer_class = NotificationTemplateSerializer
	permission_classes = [permissions.IsAdminUser]
	swagger_fake_view = False

# --- User Notification Preferences ---
class UserNotificationPrefListCreateView(generics.ListCreateAPIView):
	serializer_class = UserNotificationPrefSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		return UserNotificationPref.objects.filter(user=self.request.user)

	def perform_create(self, serializer):
		serializer.save(user=self.request.user)

class UserNotificationPrefListCreateView(generics.ListCreateAPIView):
    serializer_class = UserNotificationPrefSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return UserNotificationPref.objects.none()  # return empty queryset for schema generation
        return UserNotificationPref.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserNotificationPrefDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserNotificationPrefSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return UserNotificationPref.objects.none()
        return UserNotificationPref.objects.filter(user=self.request.user)


# --- Notification Queue (Admin/Debug) ---
class NotificationQueueListView(generics.ListAPIView):
	queryset = NotificationQueue.objects.all()
	serializer_class = NotificationQueueSerializer
	permission_classes = [permissions.IsAdminUser]



class TriggerNotificationView(APIView):
	permission_classes = [permissions.IsAuthenticated]
	swagger_fake_view = False

	def post(self, request, *args, **kwargs):
		"""
		Expects: {"template_id": int, "context": {"email": ...}}
		"""
		template_id = request.data.get('template_id')
		context = request.data.get('context', {})
		try:
			template = NotificationTemplate.objects.get(id=template_id, is_active=True)
			queue = NotificationQueue.objects.create(
				user=request.user,
				template=template,
				channel=template.channel,
				context=context,
			)
			send_notification_email.delay(queue.id)
			return Response({'message': 'Notification queued.'}, status=status.HTTP_202_ACCEPTED)
		except NotificationTemplate.DoesNotExist:
			return Response({'error': 'Template not found.'}, status=404)
		except Exception as e:
			return Response({'error': str(e)}, status=400)
