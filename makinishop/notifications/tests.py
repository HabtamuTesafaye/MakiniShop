
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import NotificationTemplate

class NotificationTemplateTest(APITestCase):
	def test_list_templates_unauthenticated(self):
		url = reverse('notification-template-list')
		response = self.client.get(url)
		self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED])

class NotificationModelTest(APITestCase):
	def test_create_template(self):
		NotificationTemplate.objects.create(name='Test', subject='Sub', body='Body')
		self.assertTrue(NotificationTemplate.objects.filter(name='Test').exists())
