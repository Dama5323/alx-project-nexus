from rest_framework.test import APITestCase
from django.urls import reverse
from cart.models import Cart, CartItem
from django.contrib.auth import get_user_model

User = get_user_model()

class CartAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='apiuser@example.com', password='testpass123')
        self.client.login(email='apiuser@example.com', password='testpass123')
        self.cart = Cart.objects.create(user=self.user)

    def test_get_cart(self):
        url = reverse('cart-detail', kwargs={'pk': self.cart.pk})  # adapt to your URL names
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
