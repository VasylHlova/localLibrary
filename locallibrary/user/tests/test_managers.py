from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserManagerTest(TestCase):
    def test_create_user_with_valid_data(self):
        user = User.objects.create_user(
            email="normal@user.com", 
            password="foo", 
            first_name="Normal", 
            last_name="User"
        )
        
        self.assertEqual(user.email, "normal@user.com")
        self.assertTrue(user.check_password("foo"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_without_email_raises_error(self):
        with self.assertRaisesMessage(ValueError, "Email must be set"):
            User.objects.create_user(email="", password="foo")

    def test_create_superuser_with_valid_data(self):
        admin_user = User.objects.create_superuser(
            email="super@user.com", 
            password="foo", 
            first_name="Super", 
            last_name="User"
        )
        
        self.assertEqual(admin_user.email, "super@user.com")
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)

    def test_create_superuser_with_is_staff_false_raises_error(self):
        with self.assertRaisesMessage(ValueError, "Superuser must have is_staff=True."):
            User.objects.create_superuser(
                email="super@user.com", 
                password="foo", 
                is_staff=False
            )

    def test_create_superuser_with_is_superuser_false_raises_error(self):
        with self.assertRaisesMessage(ValueError, "Superuser must have is_superuser=True."):
            User.objects.create_superuser(
                email="super@user.com", 
                password="foo", 
                is_superuser=False
            )