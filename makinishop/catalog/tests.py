
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import Category, Product

class CategoryPublicTest(APITestCase):
	def test_list_categories_public(self):
		url = reverse('category-list')
		response = self.client.get(url)
		self.assertEqual(response.status_code, status.HTTP_200_OK)

class ProductModelTest(APITestCase):
	def test_create_product(self):
		cat = Category.objects.create(name='TestCat')
		prod = Product.objects.create(name='TestProd', category=cat)
		self.assertTrue(Product.objects.filter(name='TestProd').exists())
