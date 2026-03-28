from http import HTTPStatus

from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings
from django.urls import reverse

from catalog.models import Author
from ..helper.mixins import PermissionViewTestMixin
from ..helper.factories import (
    AuthorFactory, BookFactory,
    UserFactory,
)


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}})
class AuthorListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        AuthorFactory.create_batch(13)

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/catalog/authors/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("authors"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("authors"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "catalog/author_list.html")

    def test_pagination_is_ten(self):
        response = self.client.get(reverse("authors"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue("is_paginated" in response.context)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(len(response.context["author_list"]), 10)

    def test_lists_all_authors(self):
        response = self.client.get(reverse("authors") + "?page=2")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue("is_paginated" in response.context)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(len(response.context["author_list"]), 3)


class AuthorDetailViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = AuthorFactory()
    
    def test_view_url_exists_at_desired_location(self):
        response = self.client.get(f"/catalog/author/{self.author.pk}")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("author-detail", kwargs={'pk': self.author.pk}))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("author-detail", kwargs={'pk': self.author.pk}))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "catalog/author_detail.html")

    def test_view_returns_404_for_non_existent_author(self):
        non_existent_id = 99999 
        response = self.client.get(reverse('author-detail', kwargs={'pk': non_existent_id}))
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_view_context_contains_correct_author(self):
        response = self.client.get(reverse('author-detail', kwargs={'pk': self.author.pk}))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context['author'], self.author)


class AuthorCreateViewTest(PermissionViewTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_no_perms = UserFactory()
        cls.user_with_perms = UserFactory()
        
        permission = Permission.objects.get(codename='add_author')
        cls.user_with_perms.user_permissions.add(permission)
        
        cls.url = reverse('author-create')

    def test_view_uses_correct_template(self):
        self.client.force_login(self.user_with_perms)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "catalog/author_form.html")

    def test_form_contains_initial_data(self):
        self.client.force_login(self.user_with_perms)
        response = self.client.get(self.url)
        self.assertEqual(response.context['form'].initial['date_of_birth'], '31.12.2020')

    def test_post_valid_data_creates_author_and_redirects(self):
        self.client.force_login(self.user_with_perms)
        form_data = {
            'first_name': 'Test',
            'last_name': 'Author',
            'date_of_birth': '2000-01-01',
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(Author.objects.count(), 1)
        created_author = Author.objects.first()
        self.assertEqual(created_author.first_name, 'Test')
        self.assertRedirects(response, created_author.get_absolute_url())

    def test_post_invalid_data_does_not_create_author_and_returns_form_errors(self):
        self.client.force_login(self.user_with_perms)
        response = self.client.post(self.url, data={'first_name': '', 'last_name': ''})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Author.objects.count(), 0)
        self.assertFormError(response.context['form'], 'first_name', 'This field is required.')
        self.assertFormError(response.context['form'], 'last_name', 'This field is required.')


class AuthorUpdateViewTest(PermissionViewTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_no_perms = UserFactory()
        cls.user_with_perms = UserFactory()
        
        permission = Permission.objects.get(codename='change_author')
        cls.user_with_perms.user_permissions.add(permission)
        
        cls.author = AuthorFactory()
        cls.url = reverse('author-update', kwargs={'pk': cls.author.pk})

    def test_view_uses_correct_template(self):
        self.client.force_login(self.user_with_perms)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "catalog/author_form.html")

    def test_post_valid_data_updates_author_and_redirects(self):
        self.client.force_login(self.user_with_perms)
        form_data = {
            'first_name': 'Test',
            'last_name': 'Author',
            'date_of_birth': '2000-01-01',
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(Author.objects.count(), 1)
        updated_author = Author.objects.get(pk=self.author.pk)
        self.assertEqual(updated_author.first_name, 'Test')
        self.assertRedirects(response, updated_author.get_absolute_url())

    def test_post_invalid_data_does_not_update_author_and_returns_form_errors(self):
        self.client.force_login(self.user_with_perms)
        original_first_name = self.author.first_name
        response = self.client.post(self.url, data={'first_name': '', 'last_name': ''})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.author.refresh_from_db()
        self.assertEqual(self.author.first_name, original_first_name)
        self.assertFormError(response.context['form'], 'first_name', 'This field is required.')

class AuthorDeleteViewTest(PermissionViewTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_no_perms = UserFactory()
        cls.user_with_perms = UserFactory()
        
        permission = Permission.objects.get(codename='delete_author')
        cls.user_with_perms.user_permissions.add(permission)
        
        cls.author = AuthorFactory()
        cls.url = reverse('author-delete', kwargs={'pk': cls.author.pk})

    def test_view_uses_correct_template(self):
        self.client.force_login(self.user_with_perms)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "catalog/author_confirm_delete.html")

    def test_view_returns_404_if_logged_in_with_permissions_for_non_existent_author(self):
        self.client.force_login(self.user_with_perms)
        non_existent_id = 99999 
        response = self.client.get(reverse('author-delete', kwargs={'pk': non_existent_id}))
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_fails_to_delete_author_with_books_and_redirects_back(self):
        self.client.force_login(self.user_with_perms)
        BookFactory(author=self.author)
        self.assertEqual(Author.objects.count(), 1)

        response = self.client.post(self.url)
        self.assertEqual(Author.objects.count(), 1)
        self.assertRedirects(response, self.url)

    def test_post_deletes_author_and_redirects(self):
        author_to_delete = AuthorFactory()
        self.client.force_login(self.user_with_perms)
        self.assertEqual(Author.objects.count(), 2)
        
        response = self.client.post(reverse('author-delete', kwargs={'pk': author_to_delete.pk}))
        self.assertEqual(Author.objects.count(), 1)
        
        with self.assertRaises(Author.DoesNotExist):
            Author.objects.get(pk=author_to_delete.pk)

        self.assertRedirects(response, reverse('authors'))