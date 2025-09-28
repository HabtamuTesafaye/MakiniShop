from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import Order
from users.models import UserAccount

class OrderPublicTest(APITestCase):
    def test_order_list_unauthenticated(self):
        url = reverse('order-list-create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class OrderAuthTest(APITestCase):
    def setUp(self):
        self.user = UserAccount.objects.create_user(email='test@example.com', password='testpass')
        self.client.force_authenticate(user=self.user)

    def test_order_list_authenticated(self):
        url = reverse('order-list-create')
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class OrderModelTest(APITestCase):
    def test_create_order(self):
        # This is a placeholder; expand with real order creation logic
        self.assertTrue(True)