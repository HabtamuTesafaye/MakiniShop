from rest_framework import serializers
from .models import NotificationTemplate, UserNotificationPref, NotificationQueue

class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = '__all__'

class UserNotificationPrefSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotificationPref
        fields = '__all__'

class NotificationQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationQueue
        fields = '__all__'
