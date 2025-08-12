from django.test import TestCase
from django.urls import reverse
from cart.models import Cart
from django.contrib.auth import get_user_model

User = get_user_model()

class CartViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        cls.cart = Cart.objects.create(user=cls.user)

    def test_get_cart(self):
        self.client.force_login(self.user)
        url = reverse('cart:cart-detail', kwargs={'pk': self.cart.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)