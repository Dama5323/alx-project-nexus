from django.test import TestCase
from django.core.exceptions import ValidationError
from products.models import Product
from cart.models import Cart, CartItem
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

class CartItemModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Create test data once for all tests"""
        cls.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        cls.cart = Cart.objects.create(user=cls.user)
        cls.product = Product.objects.create(
            name='Test Product',
            description='Test description',
            price=Decimal('10.00'),
            stock=100,
            available=True
        )

    def setUp(self):
        """Clear cart items before each test"""
        CartItem.objects.all().delete()

    def test_cart_item_subtotal(self):
        """Test subtotal calculation with various quantities"""
        test_cases = [
            (1, Decimal('10.00')),
            (2, Decimal('20.00')),
            (5, Decimal('50.00'))
        ]

        for quantity, expected in test_cases:
            with self.subTest(quantity=quantity, expected=expected):
                item = CartItem.objects.create(
                    cart=self.cart,
                    product=self.product,
                    quantity=quantity
                )
                self.assertEqual(item.subtotal, expected)

    def test_price_at_addition_defaults_to_product_price(self):
        """Test that price_at_addition defaults to product price"""
        item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=1
        )
        self.assertEqual(item.price_at_addition, self.product.price)

    def test_cannot_add_same_product_twice(self):
        """Test unique constraint for same product in cart"""
        # First add should succeed
        CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=1
        )
        
        # Second add should fail
        with self.assertRaises(ValidationError):
            item = CartItem(
                cart=self.cart,
                product=self.product,
                quantity=2
            )
            item.full_clean()  # Explicit validation check
            item.save()  # This would also raise the error

    def test_string_representation(self):
        """Test the __str__ method"""
        item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )
        self.assertIn(str(self.product.name), str(item))
        self.assertIn(str(self.cart.id), str(item))