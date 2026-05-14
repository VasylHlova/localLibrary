from http import HTTPStatus

from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings
from django.urls import reverse

from catalog.models import Book
from catalog.tests.helper.mixins import PermissionViewTestMixin
from catalog.tests.helper.factories import (
    AuthorFactory, BookFactory,
    UserFactory, GenreFactory,
    BookInstanceFactory, LanguageFactory
)

@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}})
class BookListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        BookFactory.create_batch(13)

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/catalog/books/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("books"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("books"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "catalog/book_list.html")

    def test_pagination_is_ten(self):
        response = self.client.get(reverse("books"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(len(response.context["book_list"]), 10)

    def test_lists_all_book(self):
        response = self.client.get(reverse("books") + "?page=2")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(len(response.context["book_list"]), 3)


class BookDetailViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.book = BookFactory()
        cls.url = reverse("book-detail", kwargs={'pk': cls.book.pk})
    
    def test_view_url_exists_at_desired_location(self):
        response = self.client.get(f"/catalog/book/{self.book.pk}")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_view_uses_correct_template(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "catalog/book_detail.html")

    def test_view_returns_404_for_non_existent_book(self):
        non_existent_id = 99999 
        response = self.client.get(reverse('book-detail', kwargs={'pk': non_existent_id}))
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_view_context_contains_correct_book(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context['book'], self.book)


class BookCreateViewTest(PermissionViewTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_no_perms = UserFactory()
        cls.user_with_perms = UserFactory()
        
        permission = Permission.objects.get(codename='add_book')
        cls.user_with_perms.user_permissions.add(permission)
        
        cls.url = reverse('book-create')

    def test_view_uses_correct_template(self):
        self.client.force_login(self.user_with_perms)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "catalog/book_form.html")

    def test_post_valid_data_creates_book_and_redirects(self):
        self.client.force_login(self.user_with_perms)
        author = AuthorFactory()
        genre = GenreFactory()
        language = LanguageFactory()

        form_data = {
            'title': 'Test Book Title',
            'author': author.id,
            'summary': 'Test summary text.',
            'isbn': '1234567890123',
            'genre': [genre.id],
            'language': language.id,
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(Book.objects.count(), 1)
        created_book = Book.objects.first()
        self.assertEqual(created_book.title, 'Test Book Title')
        self.assertEqual(created_book.author, author)
        self.assertTrue(created_book.genre.filter(id=genre.id).exists())
        self.assertRedirects(response, created_book.get_absolute_url())

    def test_post_invalid_data_does_not_create_book_and_returns_form_errors(self):
        self.client.force_login(self.user_with_perms)
        response = self.client.post(self.url, data={'title': '', 'summary': ''})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Book.objects.count(), 0)
        self.assertFormError(response.context['form'], 'title', 'This field is required.')


class BookUpdateViewTest(PermissionViewTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_no_perms = UserFactory()
        cls.user_with_perms = UserFactory()
        
        permission = Permission.objects.get(codename='change_book')
        cls.user_with_perms.user_permissions.add(permission)
        
        cls.book = BookFactory()
        cls.url = reverse('book-update', kwargs={'pk': cls.book.pk})

    def test_view_uses_correct_template(self):
        self.client.force_login(self.user_with_perms)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "catalog/book_form.html")

    def test_view_returns_404_if_logged_in_with_permissions_for_non_existent_book(self):
        self.client.force_login(self.user_with_perms)
        response = self.client.get(reverse('book-update', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_valid_data_updates_book_and_redirects(self):
        self.client.force_login(self.user_with_perms)
        form_data = {
            'title': 'Updated Title',
            'author': self.book.author.id,
            'summary': 'Updated summary.',
            'isbn': self.book.isbn,
            'genre': list(self.book.genre.values_list('id', flat=True)),
            'language': self.book.language.id,
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(Book.objects.count(), 1)
        updated_book = Book.objects.get(pk=self.book.pk)
        self.assertEqual(updated_book.title, 'Updated Title')
        self.assertRedirects(response, updated_book.get_absolute_url())

    def test_post_invalid_data_does_not_update_book_and_returns_form_errors(self):
        self.client.force_login(self.user_with_perms)
        original_title = self.book.title
        response = self.client.post(self.url, data={'title': '', 'summary': ''})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.book.refresh_from_db()
        self.assertEqual(self.book.title, original_title)
        self.assertFormError(response.context['form'], 'title', 'This field is required.')


class BookDeleteViewTest(PermissionViewTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_no_perms = UserFactory()       
        cls.user_with_perms = UserFactory()
        
        permission = Permission.objects.get(codename='delete_book')
        cls.user_with_perms.user_permissions.add(permission)
        
        cls.book = BookFactory()
        cls.url = reverse('book-delete', kwargs={'pk': cls.book.pk})

    def test_view_uses_correct_template(self):
        self.client.force_login(self.user_with_perms)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "catalog/book_confirm_delete.html")

    def test_view_returns_404_if_logged_in_with_permissions_for_non_existent_author(self):
        self.client.force_login(self.user_with_perms)
        non_existent_id = 99999 
        response = self.client.get(reverse('book-delete', kwargs={'pk': non_existent_id}))
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_fails_to_delete_book_with_books_and_redirects_back(self):
        self.client.force_login(self.user_with_perms)
        BookInstanceFactory(book=self.book)
        self.assertEqual(Book.objects.count(), 1)

        response = self.client.post(self.url)
        self.assertEqual(Book.objects.count(), 1)
        self.assertRedirects(response, self.url)

    def test_post_deletes_book_and_redirects(self):
        book_to_delete = BookFactory()
        self.client.force_login(self.user_with_perms)
        self.assertEqual(Book.objects.count(), 2)
        
        response = self.client.post(reverse('book-delete', kwargs={'pk': book_to_delete.pk}))
        self.assertEqual(Book.objects.count(), 1)
        
        with self.assertRaises(Book.DoesNotExist):
            Book.objects.get(pk=book_to_delete.pk)

        self.assertRedirects(response, reverse('books'))