import user.signals
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.db.models.signals import post_save
from factory.django import mute_signals

from .helper.factories import UserFactory, ProfileFactory
from user.models import UserProfile


class CleanupProfilePictureOnDeleteSignalTest(TestCase):
    @patch('django.db.transaction.on_commit')
    def test_deletes_profile_picture_when_user_deactivated(self, mock_on_commit):
        user = UserFactory(is_active=True)
        mock_on_commit.reset_mock()

        mock_photo = MagicMock()
        mock_photo.name = "dummy.jpg"
        user.profile.profile_picture = mock_photo

        user.is_active = False
        user.save()

        mock_on_commit.assert_called_once()
        callback = mock_on_commit.call_args[0][0]
        callback()
        mock_photo.delete.assert_called_once_with(save=False)

    @patch('django.db.transaction.on_commit')
    def test_does_not_delete_photo_when_other_field_updated(self, mock_on_commit):
        user = UserFactory(is_active=True)
        mock_on_commit.reset_mock()
        
        mock_photo = MagicMock()
        user.profile.profile_picture = mock_photo

        user.first_name = "Updated"
        user.save()

        mock_on_commit.assert_not_called()

    def test_does_not_fail_when_deactivated_user_has_no_photo(self):
        user = UserFactory(is_active=True)
        user.profile.profile_picture = None
        
        user.is_active = False
        user.save()

    def test_skips_cleanup_for_new_user_instance(self):
        user = UserFactory.build(is_active=False)
        user.save()


class CleanupOldProfilePhotoOnUpdateSignalTest(TestCase):
    @patch('django.db.transaction.on_commit')
    @patch('user.models.UserProfile.objects.get')
    def test_deletes_old_profile_photo_when_replaced(self, mock_get, mock_on_commit):
        user = UserFactory()
        profile = user.profile
        mock_on_commit.reset_mock()

        mock_old_instance = MagicMock()
        mock_old_instance.profile_picture = MagicMock()
        mock_old_instance.profile_picture.name = "dummy.jpg"
        mock_get.return_value = mock_old_instance

        profile.profile_picture = "new_dummy.jpg"
        profile.save()

        mock_on_commit.assert_called_once()
        callback = mock_on_commit.call_args[0][0]
        callback()
        mock_old_instance.profile_picture.delete.assert_called_once_with(save=False)

    @patch('django.db.transaction.on_commit')
    def test_does_not_delete_photo_when_other_profile_field_updated(self, mock_on_commit):
        user = UserFactory()
        profile = user.profile
        mock_on_commit.reset_mock()

        profile.role = "admin"
        profile.save()

        mock_on_commit.assert_not_called()

    def test_skips_cleanup_for_new_profile_instance(self):
        with mute_signals(post_save):
            user = UserFactory()
        profile = ProfileFactory.build(user=user)
        profile.save()


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