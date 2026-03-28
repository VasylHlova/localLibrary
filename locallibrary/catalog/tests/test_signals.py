import catalog.signals
from unittest.mock import MagicMock, patch

from django.test import TestCase

from .helper.factories import AuthorFactory, BookFactory, BookInstanceFactory, LanguageFactory


class CleanupPhotoOnDeleteSignalTest(TestCase):
    @patch('django.db.transaction.on_commit')
    def test_deletes_author_photo_on_delete(self, mock_on_commit):
        author = AuthorFactory()
        mock_on_commit.reset_mock()

        mock_photo = MagicMock()
        mock_photo.name = "dummy.jpg"
        author.photo = mock_photo

        author.delete()

        mock_on_commit.assert_called_once()
        callback = mock_on_commit.call_args[0][0]
        callback()
        mock_photo.delete.assert_called_once_with(save=False)

    @patch('django.db.transaction.on_commit')
    def test_deletes_book_photo_on_delete(self, mock_on_commit):
        book = BookFactory()
        mock_on_commit.reset_mock()

        mock_photo = MagicMock()
        mock_photo.name = "dummy.jpg"
        book.photo = mock_photo

        book.delete()

        mock_on_commit.assert_called_once()
        callback = mock_on_commit.call_args[0][0]
        callback()
        mock_photo.delete.assert_called_once_with(save=False)

    def test_does_not_fail_when_author_has_no_photo(self):
        author = AuthorFactory(photo=None)
        author.delete()

    def test_does_not_fail_when_book_has_no_photo(self):
        book = BookFactory(photo=None)
        book.delete()


class CleanupOldPhotoOnUpdateSignalTest(TestCase):
    @patch('django.db.transaction.on_commit')
    @patch('catalog.models.Author.objects.get')
    def test_deletes_old_author_photo_when_replaced(self, mock_get, mock_on_commit):
        author = AuthorFactory()
        mock_on_commit.reset_mock()

        mock_old_instance = MagicMock()
        mock_old_instance.photo = MagicMock()
        mock_old_instance.photo.name = "dummy.jpg"
        mock_get.return_value = mock_old_instance

        author.photo = "new_dummy.jpg"
        author.save()

        mock_on_commit.assert_called_once()
        callback = mock_on_commit.call_args[0][0]
        callback()
        mock_old_instance.photo.delete.assert_called_once_with(save=False)

    @patch('django.db.transaction.on_commit')
    @patch('catalog.models.Book.objects.get')
    def test_deletes_old_book_photo_when_replaced(self, mock_get, mock_on_commit):
        book = BookFactory()
        mock_on_commit.reset_mock()

        mock_old_instance = MagicMock()
        mock_old_instance.photo = MagicMock()
        mock_old_instance.photo.name = "dummy.jpg"
        mock_get.return_value = mock_old_instance

        book.photo = "new_dummy.jpg"
        book.save()

        mock_on_commit.assert_called_once()
        callback = mock_on_commit.call_args[0][0]
        callback()
        mock_old_instance.photo.delete.assert_called_once_with(save=False)

    @patch('django.db.transaction.on_commit')
    def test_does_not_delete_author_photo_when_other_field_updated(self, mock_on_commit):
        author = AuthorFactory()
        mock_on_commit.reset_mock()

        author.first_name = "Updated"
        author.save()

        mock_on_commit.assert_not_called()

    @patch('django.db.transaction.on_commit')
    def test_does_not_delete_book_photo_when_other_field_updated(self, mock_on_commit):
        book = BookFactory()
        mock_on_commit.reset_mock()

        book.title = "Updated Title"
        book.save()

        mock_on_commit.assert_not_called()

    def test_skips_cleanup_for_new_author_instance(self):
        author = AuthorFactory.build()
        author.save()

    def test_skips_cleanup_for_new_book_instance(self):
        author = AuthorFactory()
        language = LanguageFactory()
        book = BookFactory.build(author=author, language=language)
        book.save()


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