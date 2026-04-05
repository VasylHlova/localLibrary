import catalog.signals
from unittest.mock import patch

from django.test import TestCase

from .helper.factories import AuthorFactory, BookFactory, BookInstanceFactory, LanguageFactory


class CleanupImageOnDeleteSignalTest(TestCase):
    
    @patch('catalog.signals.cleanup_needless_images.delay')
    def test_deletes_author_image_on_delete(self, mock_delay):
        author = AuthorFactory()

        author.image = "authors/dummy.jpg"
        author.save()

        author.delete()

        mock_delay.assert_called_once_with(file_path="authors/dummy.jpg")

    @patch('catalog.signals.cleanup_needless_images.delay')
    def test_deletes_book_image_on_delete(self, mock_delay):
        book = BookFactory()

        book.image = "books/dummy.jpg"
        book.save()

        book.delete()

        mock_delay.assert_called_once_with(file_path="books/dummy.jpg")

    @patch('catalog.signals.cleanup_needless_images.delay')
    def test_does_not_fail_when_author_has_no_image(self, mock_delay):
        author = AuthorFactory(image=None)
        author.delete()
        
        mock_delay.assert_not_called()

    @patch('catalog.signals.cleanup_needless_images.delay')
    def test_does_not_fail_when_book_has_no_image(self, mock_delay):
        book = BookFactory(image=None)
        book.delete()
        
        mock_delay.assert_not_called()


class CleanupOldImageOnUpdateSignalTest(TestCase):
    
    @patch('catalog.signals.cleanup_needless_images.delay')
    def test_deletes_old_author_image_when_replaced(self, mock_delay):
        author = AuthorFactory()
        
        author.image = "authors/old_dummy.jpg"
        author.save()

        author.image = "authors/new_dummy.jpg"
        author.save()

        mock_delay.assert_called_once_with(file_path="authors/old_dummy.jpg")

    @patch('catalog.signals.cleanup_needless_images.delay')
    def test_deletes_old_book_image_when_replaced(self, mock_delay):
        book = BookFactory()

        book.image = "books/old_dummy.jpg"
        book.save()

        book.image = "books/new_dummy.jpg"
        book.save()

        mock_delay.assert_called_once_with(file_path="books/old_dummy.jpg")

    @patch('catalog.signals.cleanup_needless_images.delay')
    def test_does_not_delete_author_image_when_other_field_updated(self, mock_delay):
        author = AuthorFactory()
        
        author.image = "authors/dummy.jpg"
        author.save()

        mock_delay.reset_mock()

        author.first_name = "Updated"
        author.save()

        mock_delay.assert_not_called()

    @patch('catalog.signals.cleanup_needless_images.delay')
    def test_does_not_delete_book_image_when_other_field_updated(self, mock_delay):
        book = BookFactory()
        
        book.image = "books/dummy.jpg"
        book.save()

        mock_delay.reset_mock()

        book.title = "Updated Title"
        book.save()

        mock_delay.assert_not_called()

    @patch('catalog.signals.cleanup_needless_images.delay')
    def test_skips_cleanup_for_new_author_instance(self, mock_delay):
        author = AuthorFactory.build()
        author.save()
        
        mock_delay.assert_not_called()

    @patch('catalog.signals.cleanup_needless_images.delay')
    def test_skips_cleanup_for_new_book_instance(self, mock_delay):
        author = AuthorFactory()
        language = LanguageFactory()
        book = BookFactory.build(author=author, language=language)
        book.save()
        
        mock_delay.assert_not_called()


class InvalidateCacheSignalTest(TestCase):
    @patch("catalog.signals.increment_model_cache_version")
    def test_cache_invalidated_on_author_create(self, mock_increment):
        AuthorFactory()
        mock_increment.assert_called_with("author")

    @patch("catalog.signals.increment_model_cache_version")
    def test_cache_invalidated_on_author_update(self, mock_increment):
        author = AuthorFactory()
        mock_increment.reset_mock()

        author.first_name = "Updated"
        author.save()

        mock_increment.assert_called_with("author")

    @patch("catalog.signals.increment_model_cache_version")
    def test_cache_invalidated_on_author_delete(self, mock_increment):
        author = AuthorFactory()
        mock_increment.reset_mock()

        author.delete()

        mock_increment.assert_called_with("author")

    @patch("catalog.signals.increment_model_cache_version")
    def test_cache_invalidated_on_book_create(self, mock_increment):
        BookFactory()
        mock_increment.assert_called_with("book")

    @patch("catalog.signals.increment_model_cache_version")
    def test_cache_invalidated_on_book_update(self, mock_increment):
        book = BookFactory()
        mock_increment.reset_mock()

        book.title = "Updated"
        book.save()

        mock_increment.assert_called_with("book")

    @patch("catalog.signals.increment_model_cache_version")
    def test_cache_invalidated_on_book_delete(self, mock_increment):
        book = BookFactory()
        mock_increment.reset_mock()

        book.delete()

        mock_increment.assert_called_with("book")

    @patch("catalog.signals.increment_model_cache_version")
    def test_cache_invalidated_on_bookinstance_create(self, mock_increment):
        BookInstanceFactory()
        mock_increment.assert_called_with("bookinstance")

    @patch("catalog.signals.increment_model_cache_version")
    def test_cache_invalidated_on_bookinstance_update(self, mock_increment):
        instance = BookInstanceFactory()
        mock_increment.reset_mock()

        instance.save()

        mock_increment.assert_called_with("bookinstance")

    @patch("catalog.signals.increment_model_cache_version")
    def test_cache_invalidated_on_bookinstance_delete(self, mock_increment):
        instance = BookInstanceFactory()
        mock_increment.reset_mock()

        instance.delete()

        mock_increment.assert_called_with("bookinstance")