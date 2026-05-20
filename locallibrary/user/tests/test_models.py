from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from .helper.factories import UserFactory, ProfileFactory, ImageFactory
from user.choices import UserRole

class CustomUserModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(email='johndoe@mail.com', username='john doe')

    def test_email_field_verbose_name_is_email_address(self):
        verborse_name = self.user._meta.get_field("email").verbose_name
        self.assertEqual(verborse_name, 'email address')

    def test_email_field_raise_error_when_user_with_this_email_already_exists(self):
        with self.assertRaises(IntegrityError):
            UserFactory(email='johndoe@mail.com')

    def test_username_field_verbose_name_is_username(self):
        verborse_name = self.user._meta.get_field("username").verbose_name
        self.assertEqual(verborse_name, 'username')

    def test_username_max_length_is_150(self):
        max_length = self.user._meta.get_field("username").max_length
        self.assertEqual(max_length, 150)

    def test_username_field_raise_error_when_user_with_this_username_already_exists(self):
        with self.assertRaises(IntegrityError):
            UserFactory(username='john doe')

    def test_username_help_text_is_correct(self):
        help_text = self.user._meta.get_field("username").help_text
        self.assertEqual(help_text, "Optional. 150 characters or fewer.")

    def test_first_name_field_verbose_name_is_first_name(self):
        verborse_name = self.user._meta.get_field("first_name").verbose_name
        self.assertEqual(verborse_name, 'first name')

    def test_first_name_max_length_is_150(self):
        max_length = self.user._meta.get_field("first_name").max_length
        self.assertEqual(max_length, 150)

    def test_last_name_field_verbose_name_is_last_name(self):
        verborse_name = self.user._meta.get_field("last_name").verbose_name
        self.assertEqual(verborse_name, 'last name')

    def test_last_name_max_length_is_150(self):
        max_length = self.user._meta.get_field("last_name").max_length
        self.assertEqual(max_length, 150)

    def test_str_returns_first_and_last_names(self):
        self.assertEqual(str(self.user), f'{self.user.first_name} {self.user.last_name}')

    def test_get_absolute_url_returns_correct_url(self):
        self.assertEqual(self.user.get_absolute_url(), f"/user/{self.user.pk}/profile")


class UserProfileModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.profile = ProfileFactory()

    def test_role_max_length_is_150(self):
        max_length = self.profile._meta.get_field("role").max_length
        self.assertEqual(max_length, 150)

    def test_role_defaulte_value_is_customer(self):
        self.assertEqual(self.profile.role, UserRole.CUSTOMER)

    def test_date_of_birth_field_verbose_name_is_born(self):
        verborse_name = self.profile._meta.get_field("date_of_birth").verbose_name
        self.assertEqual(verborse_name, 'born')

    def test_profile_picture_max_length_is_300(self):
        max_length = self.profile._meta.get_field("profile_picture").max_length
        self.assertEqual(max_length, 300)

    def test_full_clean_passes_when_profile_picture_has_valid_extension(self):
        user = UserFactory(username='unique')
        for ext, fmt, content_type in [
            ("jpg", "JPEG", "image/jpeg"),
            ("jpeg", "JPEG", "image/jpeg"),
            ("png", "PNG", "image/png"),
            ("webp", "WEBP", "image/webp"),
        ]:
            with self.subTest(ext=ext):
                profile = user.profile
                profile.profile_picture = ImageFactory.create(name=f"test.{ext}", format=fmt, content_type=content_type)
                profile.full_clean()

    def test_full_clean_raises_error_when_profile_picture_has_invalid_extension(self):
        user = UserFactory(username='unique')
        profile = user.profile
        profile.profile_picture = ImageFactory.create_invalid_extension()

        with self.assertRaises(ValidationError) as context:
            profile.full_clean()

        self.assertIn("profile_picture", context.exception.message_dict)
        self.assertIn("Invalid file extension", context.exception.message_dict["profile_picture"][0])

    def test_full_clean_raises_error_when_profile_picture_exceeds_max_size(self):
        user = UserFactory(username='unique')
        profile = user.profile
        profile.profile_picture = ImageFactory.create_oversized()

        with self.assertRaises(ValidationError) as context:
            profile.full_clean()

        self.assertIn("profile_picture", context.exception.message_dict)
        self.assertIn("Exceeded max file size(20MB)", context.exception.message_dict["profile_picture"])
        
    def test_full_clean_passes_when_profile_picture_is_none(self):
        user = UserFactory(username='unique')
        profile = user.profile
        profile.profile_picture = None
        profile.full_clean()

    def test_str_returns_user_first_and_last_names_and_role(self):
        self.assertEqual(str(self.profile), f'{self.profile.user.first_name} {self.profile.user.last_name} ({self.profile.role})')

