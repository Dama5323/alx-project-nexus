from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from products.models import Product
from cart.models import Cart, CartItem

User = get_user_model()

class CartAPITests(APITestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test products
        self.product1 = Product.objects.create(
            name='Samsung Galaxy S24 Ultra',
            price=999.99,
            stock=10,
            slug='samsung-galaxy-s24-ultra'
        )
        self.product2 = Product.objects.create(
            name='HP Desktop',
            price=599.99,
            stock=5,
            slug='hp-desktop'
        )
        
        # Authenticate client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # API endpoints
        self.cart_url = reverse('cart:cart-list')
        self.add_item_url = reverse('cart:cart-add-item')
        self.remove_item_url = reverse('cart:cart-remove-item')
        self.clear_cart_url = reverse('cart:cart-clear')

    def test_get_empty_cart(self):
        """Test retrieving empty cart"""
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 0)

    def test_add_item_to_cart(self):
        """Test adding an item to cart"""
        data = {'product_id': self.product1.id, 'quantity': 1}
        response = self.client.post(self.add_item_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['product'], self.product1.id)
        self.assertEqual(response.data['items'][0]['quantity'], 1)

    def test_add_multiple_items(self):
        """Test adding multiple items to cart"""
        # Add first product
        self.client.post(self.add_item_url, {
            'product_id': self.product1.id,
            'quantity': 1
        }, format='json')
        
        # Add second product
        response = self.client.post(self.add_item_url, {
            'product_id': self.product2.id,
            'quantity': 3
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 2)

    def test_add_item_insufficient_stock(self):
        """Test adding more items than available stock"""
        data = {
            'product_id': self.product1.id,
            'quantity': 15  # More than available stock (10)
        }
        response = self.client.post(self.add_item_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Not enough stock available', str(response.data))

    def test_update_existing_item(self):
        """Test updating quantity of existing cart item"""
        # Add initial item
        self.client.post(self.add_item_url, {
            'product_id': self.product1.id,
            'quantity': 1
        }, format='json')
        
        # Add more of the same item
        response = self.client.post(self.add_item_url, {
            'product_id': self.product1.id,
            'quantity': 2
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['items'][0]['quantity'], 3)

    def test_remove_item_from_cart(self):
        """Test removing an item from cart"""
        # First add an item
        self.client.post(self.add_item_url, {
            'product_id': self.product1.id,
            'quantity': 3
        }, format='json')
        
        # Then remove some quantity
        response = self.client.post(self.remove_item_url, {
            'product_id': self.product1.id,
            'quantity': 1
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['items'][0]['quantity'], 2)

    def test_remove_all_quantity(self):
        """Test removing all quantity of an item"""
        self.client.post(self.add_item_url, {
            'product_id': self.product1.id,
            'quantity': 2
        }, format='json')
        
        response = self.client.post(self.remove_item_url, {
            'product_id': self.product1.id,
            'quantity': 2
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 0)

    def test_remove_nonexistent_item(self):
        """Test removing an item not in cart"""
        response = self.client.post(self.remove_item_url, {
            'product_id': self.product2.id,
            'quantity': 1
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Item not in cart', str(response.data))

    def test_clear_cart(self):
        """Test clearing the entire cart"""
        # Add some items first
        self.client.post(self.add_item_url, {
            'product_id': self.product1.id,
            'quantity': 2
        }, format='json')
        self.client.post(self.add_item_url, {
            'product_id': self.product2.id,
            'quantity': 1
        }, format='json')
        
        # Clear cart
        response = self.client.delete(self.clear_cart_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 0)

    def test_unauthorized_access(self):
        """Test that unauthorized users can't access cart"""
        self.client.logout()
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)