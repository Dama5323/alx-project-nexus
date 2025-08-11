from django.test import TestCase
from products.models import Product  

class ProductModelTest(TestCase):
    def test_create_product(self):
        product = Product.objects.create(name="Test Product", price=9.99, stock=10)
        self.assertEqual(product.name, "Test Product")
        self.assertEqual(product.price, 9.99)
