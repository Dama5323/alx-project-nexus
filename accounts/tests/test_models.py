from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(email='user@example.com', password='pass1234')
        self.assertEqual(user.email, 'user@example.com')
        self.assertTrue(user.check_password('pass1234'))
