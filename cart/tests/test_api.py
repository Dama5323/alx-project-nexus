from django.urls import reverse
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from cart.models import Cart, CartItem
from products.models import Product

User = get_user_model()

class CartViewTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        cls.cart = Cart.objects.create(user=cls.user)
        cls.product = Product.objects.create(
            name="Test Product",
            price=10.00,
            stock=10
        )

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    # def test_get_cart_summary(self):
    #     url = reverse('cart:summary')
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertIn('items', response.data)

    def test_add_item_to_cart(self):
        url = reverse('cart:cart-add-item/')
        data = {'product_id': self.product.id, 'quantity': 2}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['items'][0]['quantity'], 2)

    # def test_remove_item_from_cart(self):
    #     CartItem.objects.create(
    #         cart=self.cart,
    #         product=self.product,
    #         quantity=3
    #     )
    #     url = reverse('cart:remove-item')
    #     data = {'product_id': self.product.id, 'quantity': 1}
    #     response = self.client.post(url, data, format='json')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.data['items'][0]['quantity'], 2)

    # def test_clear_cart(self):
    #     url = reverse('cart:clear')
    #     response = self.client.delete(url)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(len(response.data['items']), 0)