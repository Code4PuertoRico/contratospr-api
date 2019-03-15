from django.test import TestCase

from .models import User


class CustomUserModelTest(TestCase):
    def test_user_str_repr(self):
        user = User.objects.create(username="Test User", password="sUp3rP@as$w0rD123")
        self.assertEquals(str(user), "Test User")
