from unittest.mock import patch

from django.db.models.signals import post_save
from django.test import TestCase
from factory.django import mute_signals

from user.models import UserProfile
from user.tests.helper.factories import ProfileFactory, UserFactory


class CleanupProfilePictureOnDeleteSignalTest(TestCase):
    @patch("user.signals.cleanup_storage_file.delay")
    def test_deletes_profile_picture_when_user_deactivated(self, mock_delay):
        user = UserFactory(is_active=True)

        user.profile.profile_picture = "profiles/dummy.jpg"
        user.profile.save()

        user.is_active = False
        user.save()

        mock_delay.assert_called_once_with(file_path="profiles/dummy.jpg")

    @patch("user.signals.cleanup_storage_file.delay")
    def test_does_not_delete_photo_when_other_field_updated(self, mock_delay):
        user = UserFactory(is_active=True)

        user.profile.profile_picture = "profiles/dummy.jpg"
        user.profile.save()

        user.first_name = "Updated Name"
        user.save()

        mock_delay.assert_not_called()

    @patch("user.signals.cleanup_storage_file.delay")
    def test_does_not_fail_when_deactivated_user_has_no_photo(self, mock_delay):
        user = UserFactory(is_active=True)
        user.profile.profile_picture = None
        user.profile.save()

        user.is_active = False
        user.save()

        mock_delay.assert_not_called()

    @patch("user.signals.cleanup_storage_file.delay")
    def test_skips_cleanup_for_new_user_instance(self, mock_delay):
        user = UserFactory.build(is_active=False)
        user.save()

        mock_delay.assert_not_called()


class CleanupOldProfilePhotoOnUpdateSignalTest(TestCase):
    @patch("user.signals.cleanup_storage_file.delay")
    def test_deletes_old_profile_photo_when_replaced(self, mock_delay):
        user = UserFactory()
        profile = user.profile

        profile.profile_picture = "profiles/old_dummy.jpg"
        profile.save()

        profile.profile_picture = "profiles/new_dummy.jpg"
        profile.save()

        mock_delay.assert_called_once_with(file_path="profiles/old_dummy.jpg")

    @patch("user.signals.cleanup_storage_file.delay")
    def test_does_not_delete_photo_when_other_profile_field_updated(self, mock_delay):
        user = UserFactory()
        profile = user.profile

        profile.profile_picture = "profiles/dummy.jpg"
        profile.save()

        mock_delay.reset_mock()

        profile.role = "admin"
        profile.save()

        mock_delay.assert_not_called()

    @patch("user.signals.cleanup_storage_file.delay")
    def test_skips_cleanup_for_new_profile_instance(self, mock_delay):
        with mute_signals(post_save):
            user = UserFactory()

        profile = ProfileFactory.build(user=user)
        profile.save()

        mock_delay.assert_not_called()


class CreateUserProfileSignalTest(TestCase):
    def test_creates_user_profile_on_user_creation(self):
        user = UserFactory(email="signal_test@mail.com", username="signal_test")

        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_does_not_create_profile_on_user_update(self):
        user = UserFactory()
        initial_profile_count = UserProfile.objects.count()

        user.first_name = "Updated"
        user.save()

        self.assertEqual(UserProfile.objects.count(), initial_profile_count)
