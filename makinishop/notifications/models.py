from django.db import models
from django.conf import settings

class NotificationTemplate(models.Model):
	name = models.CharField(max_length=100, unique=True)
	channel = models.CharField(max_length=32)  # e.g. 'email', 'sms'
	subject_template = models.CharField(max_length=255, blank=True)
	body_template = models.TextField()
	metadata = models.JSONField(default=dict, blank=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

class UserNotificationPref(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	channel = models.CharField(max_length=32)
	event_type = models.CharField(max_length=64)
	enabled = models.BooleanField(default=True)
	frequency = models.CharField(max_length=32, default='immediate')
	metadata = models.JSONField(default=dict, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		unique_together = ('user', 'channel', 'event_type')

class NotificationQueue(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
	anon_id = models.UUIDField(null=True, blank=True)
	channel = models.CharField(max_length=32)
	template = models.ForeignKey(NotificationTemplate, null=True, blank=True, on_delete=models.SET_NULL)
	context = models.JSONField(default=dict, blank=True)
	priority = models.IntegerField(default=100)
	status = models.CharField(max_length=32, default='pending')
	error = models.TextField(blank=True)
	scheduled_at = models.DateTimeField(auto_now_add=True)
	attempts = models.IntegerField(default=0)
	max_attempts = models.IntegerField(default=3)
	last_attempt_at = models.DateTimeField(null=True, blank=True)
	provider_message_id = models.CharField(max_length=255, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
