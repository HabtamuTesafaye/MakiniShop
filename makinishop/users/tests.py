
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import UserAccount

class UserSignupLoginTest(APITestCase):
	def test_signup_and_login(self):
		signup_url = reverse('signup')
		data = {
			'email': 'testuser@example.com',
			'password': 'testpass123',
			'first_name': 'Test',
			'last_name': 'User'
		}
		response = self.client.post(signup_url, data)
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		login_url = reverse('login')
		response = self.client.post(login_url, {'email': 'testuser@example.com', 'password': 'testpass123'})
		self.assertEqual(response.status_code, status.HTTP_200_OK)

class UserModelTest(APITestCase):
	def test_create_user(self):
		user = UserAccount.objects.create_user(email='modeluser@example.com', password='pass')
		self.assertTrue(UserAccount.objects.filter(email='modeluser@example.com').exists())
