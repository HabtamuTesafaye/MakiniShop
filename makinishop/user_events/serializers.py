from rest_framework import serializers
from .models import UserEvent

class UserEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserEvent
        fields = ['id', 'user', 'event_type', 'product', 'review', 'order', 'metadata', 'created_at']
        read_only_fields = ['user', 'created_at']
