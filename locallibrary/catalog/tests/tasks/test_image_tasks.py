from unittest.mock import patch
from django.test import TestCase
from catalog.tasks.image_tasks import cleanup_needless_images

class CleanupNeedlessImagesTaskTest(TestCase):

    @patch('catalog.tasks.image_tasks.default_storage.delete')
    @patch('catalog.tasks.image_tasks.default_storage.exists')
    def test_deletes_image_when_exists(self, mock_exists, mock_delete):
        mock_exists.return_value = True
        path = "books/test.jpg"

        result = cleanup_needless_images(path)

        mock_exists.assert_called_once_with(path)
        mock_delete.assert_called_once_with(path)
        self.assertIn("successfully deleted", result)

    @patch('catalog.tasks.image_tasks.default_storage.exists')
    def test_skips_when_image_not_found(self, mock_exists):
        mock_exists.return_value = False
        
        result = cleanup_needless_images("non_existent.jpg")

        mock_exists.assert_called_once()
        self.assertIn("not found", result)