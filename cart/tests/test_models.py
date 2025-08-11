from django.test import TestCase
from products.models import Product
from cart.models import Cart, CartItem
from django.contrib.auth import get_user_model

User = get_user_model()

class CartItemModelTest(TestCase):
    def setUp(self):
        # Create a user for the cart
        self.user = User.objects.create_user(email='test@example.com', password='testpass123')

        # Create a cart for the user
        self.cart = Cart.objects.create(user=self.user)

        # Create a product instance with a price
        self.product = Product.objects.create(
            name='Test Product',
            price=10.00,
            stock=100,
            # add other required fields for Product here
        )

    def test_cart_item_subtotal(self):
        # Create a CartItem using the real product instance
        item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2,
            price_at_addition=self.product.price
        )
        self.assertEqual(item.subtotal, self.product.price * 2)
