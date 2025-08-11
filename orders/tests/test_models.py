from django.test import TestCase
from orders.models import Order
from django.contrib.auth import get_user_model

User = get_user_model()

class OrderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='orderuser@example.com', password='pass1234')

    def test_order_creation(self):
        order = Order.objects.create(user=self.user, total_price=100.00)
        self.assertEqual(order.user.email, 'orderuser@example.com')
        self.assertEqual(order.total_price, 100.00)
