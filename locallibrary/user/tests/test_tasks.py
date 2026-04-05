from unittest.mock import patch
from django.test import TestCase

from user.tasks.profile_picture_tasks import cleanup_needless_profile_picture


class CleanupNeedlessProfilePictureTaskTest(TestCase):

    @patch('user.tasks.profile_picture_tasks.default_storage.delete')
    @patch('user.tasks.profile_picture_tasks.default_storage.exists')
    def test_deletes_file_when_path_exists(self, mock_exists, mock_delete):
        mock_exists.return_value = True
        file_path = "profiles/test_image.jpg"

        result = cleanup_needless_profile_picture(file_path)

        mock_exists.assert_called_once_with(file_path)
        mock_delete.assert_called_once_with(file_path)
        self.assertEqual(result, f"File {file_path} successfully deleted from storage.")

    @patch('user.tasks.profile_picture_tasks.default_storage.delete')
    @patch('user.tasks.profile_picture_tasks.default_storage.exists')
    def test_does_not_delete_when_file_not_found(self, mock_exists, mock_delete):
        mock_exists.return_value = False
        file_path = "profiles/non_existent.jpg"

        result = cleanup_needless_profile_picture(file_path)

        mock_exists.assert_called_once_with(file_path)
        mock_delete.assert_not_called()
        self.assertEqual(result, f"File {file_path} not found in storage or path is empty.")

    @patch('user.tasks.profile_picture_tasks.default_storage.delete')
    @patch('user.tasks.profile_picture_tasks.default_storage.exists')
    def test_does_not_delete_when_path_is_empty(self, mock_exists, mock_delete):
        file_path = ""

        result = cleanup_needless_profile_picture(file_path)

        mock_exists.assert_not_called()
        mock_delete.assert_not_called()
        self.assertEqual(result, f"File {file_path} not found in storage or path is empty.")

    @patch('user.tasks.profile_picture_tasks.default_storage.delete')
    @patch('user.tasks.profile_picture_tasks.default_storage.exists')
    def test_does_not_delete_when_path_is_none(self, mock_exists, mock_delete):
        file_path = None

        result = cleanup_needless_profile_picture(file_path)

        mock_exists.assert_not_called()
        mock_delete.assert_not_called()
        self.assertEqual(result, f"File {file_path} not found in storage or path is empty.")