from .models import User


class CustomUserModelTest:
    def test_user_str_repr(self):
        user = User.objects.create(username="Test User", password="sUp3rP@as$w0rD123")
        self.assertEqual(str(user), "Test User")
