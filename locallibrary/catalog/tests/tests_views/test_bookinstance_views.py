import datetime
import uuid
from datetime import date, timedelta
from http import HTTPStatus
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages
from django.test import TestCase, override_settings
from django.urls import reverse

from catalog.choices import InstanceStatus
from catalog.models import BookInstance
from catalog.tests.helper.factories import (
    AvailableBookInstanceFactory,
    LibrarianUserFactory,
    MaintenanceBookInstanceFactory,
    OnLoanBookInstanceFactory,
    ReservedBookInstanceFactory,
    UserFactory,
)
from catalog.tests.helper.mixins import PermissionViewTestMixin


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}})
class UserBorrowedBooksListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_with_borrowed = UserFactory()
        cls.user_no_borrowed = UserFactory(first_name="Jane")

        OnLoanBookInstanceFactory.create_batch(size=5, borrower=cls.user_with_borrowed)
        OnLoanBookInstanceFactory.create_batch(
            size=5, borrower=cls.user_with_borrowed, due_back=date.today() + timedelta(weeks=3)
        )
        ReservedBookInstanceFactory.create_batch(size=3, borrower=cls.user_with_borrowed)
        MaintenanceBookInstanceFactory.create_batch(size=5, borrower=cls.user_with_borrowed)
        MaintenanceBookInstanceFactory.create_batch(size=10, borrower=cls.user_no_borrowed)

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse("my-borrowed"))
        self.assertRedirects(response, "/accounts/login/?next=/catalog/mybooks/")

    def test_logged_in_uses_correct_template(self):
        self.client.force_login(self.user_with_borrowed)
        response = self.client.get(reverse("my-borrowed"))
        self.assertEqual(str(response.context["user"]), str(self.user_with_borrowed))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "catalog/bookinstance_list_borrowed_user.html")

    def test_if_user_has_no_borrowed_books_and_list_is_empty(self):
        self.client.force_login(self.user_no_borrowed)
        response = self.client.get(reverse("my-borrowed"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue("bookinstance_list" in response.context)
        self.assertEqual(len(response.context["bookinstance_list"]), 0)

    def test_user_has_borrowed_book_and_list_has_len_13(self):
        self.client.force_login(self.user_with_borrowed)
        response = self.client.get(reverse("my-borrowed"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue("bookinstance_list" in response.context)
        self.assertEqual(response.context["paginator"].count, 13)
        for book_item in response.context["bookinstance_list"]:
            self.assertEqual(response.context["user"], book_item.borrower)
            self.assertTrue(book_item.status in [InstanceStatus.ON_LOAN, InstanceStatus.RESERVED])

    def test_reserved_books_appear_in_list(self):
        self.client.force_login(self.user_with_borrowed)
        all_instances = []
        page = 1
        while True:
            response = self.client.get(reverse("my-borrowed") + f"?page={page}")
            all_instances.extend(response.context["bookinstance_list"])
            if not response.context.get("is_paginated") or page >= response.context["paginator"].num_pages:
                break
            page += 1
        statuses = {item.status for item in all_instances}
        self.assertIn(InstanceStatus.RESERVED, statuses)
        self.assertNotIn(InstanceStatus.MAINTENANCE, statuses)

    def test_pages_ordered_by_due_date(self):
        self.client.force_login(self.user_with_borrowed)
        response = self.client.get(reverse("my-borrowed"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        last_date = None
        for book in response.context["bookinstance_list"]:
            if last_date is None:
                last_date = book.due_back
            else:
                self.assertLessEqual(last_date, book.due_back)
                last_date = book.due_back


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}})
class AllBorrowedBooksListViewTest(PermissionViewTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_with_perms = LibrarianUserFactory()
        cls.user_no_perms = UserFactory()

        OnLoanBookInstanceFactory.create_batch(size=5, borrower=cls.user_with_perms)
        OnLoanBookInstanceFactory.create_batch(
            size=5, borrower=cls.user_with_perms, due_back=date.today() + timedelta(weeks=3)
        )
        ReservedBookInstanceFactory.create_batch(size=3, borrower=cls.user_no_perms)
        MaintenanceBookInstanceFactory.create_batch(size=5, borrower=cls.user_with_perms)
        OnLoanBookInstanceFactory.create_batch(size=3, borrower=cls.user_no_perms)
        MaintenanceBookInstanceFactory.create_batch(size=7, borrower=cls.user_no_perms)

        cls.url = reverse("all-borrowed")

    def test_logged_in_uses_correct_template(self):
        self.client.force_login(self.user_with_perms)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "catalog/bookinstance_list_borrowed.html")

    def test_list_contains_on_loan_and_reserved_only(self):
        self.client.force_login(self.user_with_perms)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue("bookinstance_list" in response.context)
        self.assertEqual(response.context["paginator"].count, 16)
        for book_item in response.context["bookinstance_list"]:
            self.assertIn(book_item.status, [InstanceStatus.ON_LOAN, InstanceStatus.RESERVED])

    def test_reserved_books_appear_in_list(self):
        self.client.force_login(self.user_with_perms)
        all_instances = []
        page = 1
        while True:
            response = self.client.get(reverse("all-borrowed") + f"?page={page}")
            all_instances.extend(response.context["bookinstance_list"])
            if not response.context.get("is_paginated") or page >= response.context["paginator"].num_pages:
                break
            page += 1
        statuses = {i.status for i in all_instances}
        self.assertIn(InstanceStatus.RESERVED, statuses)

    def test_maintenance_books_do_not_appear_in_list(self):
        self.client.force_login(self.user_with_perms)
        response = self.client.get(self.url)
        for book_item in response.context["bookinstance_list"]:
            self.assertNotEqual(book_item.status, InstanceStatus.MAINTENANCE)

    def test_pages_ordered_by_due_date(self):
        self.client.force_login(self.user_with_perms)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        last_date = None
        for book in response.context["bookinstance_list"]:
            if last_date is None:
                last_date = book.due_back
            else:
                self.assertLessEqual(last_date, book.due_back)
                last_date = book.due_back


class RenewBookLibrarianViewTest(PermissionViewTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_with_perms = LibrarianUserFactory()
        cls.user_no_perms = UserFactory()

        permission_change = Permission.objects.get(codename="change_bookinstance")

        cls.user_with_perms.user_permissions.add(permission_change)

        cls.read_only_bookinstance = OnLoanBookInstanceFactory(borrower=cls.user_with_perms)
        cls.another_borrower_read_only_bookinstance = OnLoanBookInstanceFactory(borrower=cls.user_no_perms)

        cls.url = reverse("bookinstance-renew", kwargs={"pk": cls.read_only_bookinstance.pk})
        cls.another_borrower_url = reverse(
            "bookinstance-renew", kwargs={"pk": cls.another_borrower_read_only_bookinstance.pk}
        )

    def test_logged_in_with_permission_borrowed_book(self):
        self.client.force_login(self.user_with_perms)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_logged_in_with_permission_another_users_borrowed_book(self):
        self.client.force_login(self.user_with_perms)
        response = self.client.get(self.another_borrower_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_HTTP404_for_invalid_book_if_logged_in(self):
        test_uid = uuid.uuid4()
        self.client.force_login(self.user_with_perms)
        response = self.client.get(reverse("bookinstance-renew", kwargs={"pk": test_uid}))
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_uses_correct_template(self):
        self.client.force_login(self.user_with_perms)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "catalog/book_renew_librarian.html")

    def test_redirects_to_all_borrowed_book_list_on_success(self):
        bookinstance_to_renew = OnLoanBookInstanceFactory()
        valid_date = datetime.date.today() + datetime.timedelta(weeks=2)

        self.client.force_login(self.user_with_perms)
        response = self.client.post(
            reverse(
                "bookinstance-renew",
                kwargs={
                    "pk": bookinstance_to_renew.pk,
                },
            ),
            {"due_back": valid_date.strftime("%Y-%m-%d")},
        )
        self.assertRedirects(response, reverse("all-borrowed"))

    def test_form_invalid_renewal_date(self):
        bookinstance = OnLoanBookInstanceFactory()
        invalid_date = datetime.date.today() - datetime.timedelta(weeks=4)

        self.client.force_login(self.user_with_perms)
        response = self.client.post(
            reverse(
                "bookinstance-renew",
                kwargs={
                    "pk": bookinstance.pk,
                },
            ),
            {"due_back": invalid_date},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFormError(response.context["form"], "due_back", "Invalid date - renewal in past!")

    def test_invalid_status(self):
        bookinstance = AvailableBookInstanceFactory()
        valid_date = datetime.date.today() + datetime.timedelta(weeks=1)

        self.client.force_login(self.user_with_perms)
        response = self.client.post(
            reverse(
                "bookinstance-renew",
                kwargs={
                    "pk": bookinstance.pk,
                },
            ),
            {"due_back": valid_date},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFormError(response.context["form"], None, "This book has bad status (a) for this action!")


class BorrowReservedBookViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.read_only_bookinstance = ReservedBookInstanceFactory()

        cls.url = reverse("bookinstance-borrow-reserved", kwargs={"pk": cls.read_only_bookinstance.pk})

    def test_redirects_to_login_if_anonymous(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/accounts/login/?next={self.url}")

    def test_returns_200_if_logged_in(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_HTTP404_for_invalid_book_if_logged_in(self):
        test_uid = uuid.uuid4()
        self.client.force_login(self.user)
        response = self.client.get(reverse("bookinstance-borrow-reserved", kwargs={"pk": test_uid}))
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_uses_correct_template(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "catalog/book_borrow_reserved.html")

    def test_redirects_to_all_borrowed_book_list_on_success(self):
        bookinstance_to_borrow = ReservedBookInstanceFactory(borrower=self.user)
        valid_date = datetime.date.today() + datetime.timedelta(weeks=2)

        self.client.force_login(self.user)
        response = self.client.post(
            reverse(
                "bookinstance-borrow-reserved",
                kwargs={
                    "pk": bookinstance_to_borrow.pk,
                },
            ),
            {"due_back": valid_date.strftime("%Y-%m-%d")},
        )
        self.assertRedirects(response, reverse("my-borrowed"))

    def test_form_invalid_due_back_date(self):
        bookinstance = ReservedBookInstanceFactory()
        invalid_date = datetime.date.today() - datetime.timedelta(weeks=4)

        self.client.force_login(self.user)
        response = self.client.post(
            reverse(
                "bookinstance-borrow-reserved",
                kwargs={
                    "pk": bookinstance.pk,
                },
            ),
            {"due_back": invalid_date},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFormError(response.context["form"], "due_back", "Invalid date - renewal in past!")

    def test_form_invalid_status(self):
        bookinstance = AvailableBookInstanceFactory()
        valid_date = datetime.date.today() + datetime.timedelta(weeks=1)

        self.client.force_login(self.user)
        response = self.client.post(
            reverse(
                "bookinstance-borrow-reserved",
                kwargs={
                    "pk": bookinstance.pk,
                },
            ),
            {"due_back": valid_date},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFormError(response.context["form"], None, "This book has bad status (a) for this action!")


class BorrowOrReserveBookViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.read_only_instance = AvailableBookInstanceFactory()
        cls.read_only_url = reverse("bookinstance-borrow", kwargs={"pk": cls.read_only_instance.pk})

    def test_redirects_to_login_if_anonymous_user(self):
        response = self.client.get(self.read_only_url)
        self.assertRedirects(response, f"/accounts/login/?next={self.read_only_url}")

    def test_returns_200_and_uses_correct_template_for_logged_in_user(self):
        self.client.force_login(self.user)
        response = self.client.get(self.read_only_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "catalog/bookinstance_form.html")

    def test_post_valid_data_updates_instance_and_redirects(self):
        self.client.force_login(self.user)
        instance_to_mutate = AvailableBookInstanceFactory()
        mutate_url = reverse("bookinstance-borrow", kwargs={"pk": instance_to_mutate.pk})
        valid_date = date.today() + timedelta(days=10)
        form_data = {
            "due_back": valid_date.strftime("%Y-%m-%d"),
            "status": InstanceStatus.ON_LOAN,
        }
        response = self.client.post(mutate_url, data=form_data)
        self.assertRedirects(response, reverse("my-borrowed"))
        updated_instance = BookInstance.objects.get(pk=instance_to_mutate.pk)
        self.assertEqual(updated_instance.due_back, valid_date)
        self.assertEqual(updated_instance.borrower, self.user)

    def test_post_invalid_data_does_not_update_and_returns_form_errors(self):
        self.client.force_login(self.user)
        instance_to_mutate = AvailableBookInstanceFactory()
        mutate_url = reverse("bookinstance-borrow", kwargs={"pk": instance_to_mutate.pk})
        invalid_date = date.today() - timedelta(days=5)
        form_data = {
            "due_back": invalid_date.strftime("%Y-%m-%d"),
            "status": InstanceStatus.ON_LOAN,
        }
        response = self.client.post(mutate_url, data=form_data)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        updated_instance = BookInstance.objects.get(pk=instance_to_mutate.pk)
        self.assertIsNone(updated_instance.due_back)
        self.assertIsNone(updated_instance.borrower)

    def test_post_cannot_borrow_already_on_loan_instance(self):
        self.client.force_login(self.user)
        on_loan_instance = OnLoanBookInstanceFactory()
        mutate_url = reverse("bookinstance-borrow", kwargs={"pk": on_loan_instance.pk})
        valid_date = date.today() + timedelta(days=10)
        form_data = {
            "due_back": valid_date.strftime("%Y-%m-%d"),
            "status": InstanceStatus.ON_LOAN,
        }
        response = self.client.post(mutate_url, data=form_data)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        unchanged_instance = BookInstance.objects.get(pk=on_loan_instance.pk)
        self.assertNotEqual(unchanged_instance.borrower, self.user)
        self.assertEqual(unchanged_instance.status, InstanceStatus.ON_LOAN)

    def test_post_can_reserve_available_instance(self):
        self.client.force_login(self.user)
        instance_to_reserve = AvailableBookInstanceFactory()
        mutate_url = reverse("bookinstance-borrow", kwargs={"pk": instance_to_reserve.pk})
        valid_date = date.today() + timedelta(days=7)
        form_data = {
            "due_back": valid_date.strftime("%Y-%m-%d"),
            "status": InstanceStatus.RESERVED,
        }
        response = self.client.post(mutate_url, data=form_data)
        self.assertRedirects(response, reverse("my-borrowed"))
        updated_instance = BookInstance.objects.get(pk=instance_to_reserve.pk)
        self.assertEqual(updated_instance.status, InstanceStatus.RESERVED)
        self.assertEqual(updated_instance.borrower, self.user)


class ChangeBookStatusViewTest(PermissionViewTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_with_perms = LibrarianUserFactory()
        cls.user_no_perms = UserFactory()

        can_change_perm = Permission.objects.get(codename="can_change_status")
        cls.user_with_perms.user_permissions.add(can_change_perm)

        cls.read_only_instance = OnLoanBookInstanceFactory()
        cls.url = reverse("bookinstance-change-status", kwargs={"pk": cls.read_only_instance.pk})

    def test_uses_correct_template(self):
        self.client.force_login(self.user_with_perms)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "catalog/book_change_status.html")

    def test_returns_404_for_non_existent_book(self):
        self.client.force_login(self.user_with_perms)
        invalid_url = reverse("bookinstance-change-status", kwargs={"pk": uuid.uuid4()})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_valid_data_status_available_without_due_back(self):
        self.client.force_login(self.user_with_perms)

        instance_to_mutate = OnLoanBookInstanceFactory()
        mutate_url = reverse("bookinstance-change-status", kwargs={"pk": instance_to_mutate.pk})

        form_data = {
            "status": InstanceStatus.AVAILABLE,
            "due_back": "",
        }

        response = self.client.post(mutate_url, data=form_data)
        self.assertRedirects(response, reverse("all-borrowed"))

        updated_instance = BookInstance.objects.get(pk=instance_to_mutate.pk)
        self.assertEqual(updated_instance.status, InstanceStatus.AVAILABLE)
        self.assertIsNone(updated_instance.due_back)

    def test_post_invalid_data_status_available_with_due_back_returns_error(self):
        self.client.force_login(self.user_with_perms)

        instance_to_mutate = OnLoanBookInstanceFactory()
        mutate_url = reverse("bookinstance-change-status", kwargs={"pk": instance_to_mutate.pk})

        invalid_date = datetime.date.today() + datetime.timedelta(weeks=2)
        form_data = {
            "status": InstanceStatus.AVAILABLE,
            "due_back": invalid_date.strftime("%Y-%m-%d"),
        }

        response = self.client.post(mutate_url, data=form_data)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFormError(
            response.context["form"], "due_back", "The due back field must be empty for this status!"
        )


class ReturnBookViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_with_perms = LibrarianUserFactory()
        cls.user_no_perms = UserFactory()

        cls.read_only_instance = OnLoanBookInstanceFactory()
        cls.url = reverse("bookinstance-return", kwargs={"pk": cls.read_only_instance.pk})

    def test_redirects_to_login_if_anonymous(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, f"/accounts/login/?next={self.url}")

    def test_returns_403_without_permissions(self):
        self.client.force_login(self.user_no_perms)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_returns_200_with_permissions(self):
        self.client.force_login(self.user_with_perms)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_returns_405_if_get_request(self):
        self.client.force_login(self.user_with_perms)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_returns_404_for_non_existent_book(self):
        self.client.force_login(self.user_with_perms)
        invalid_url = reverse("bookinstance-return", kwargs={"pk": uuid.uuid4()})
        response = self.client.post(invalid_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_valid_request_returns_book_adds_message_and_redirects(self):
        self.client.force_login(self.user_with_perms)

        instance_to_mutate = OnLoanBookInstanceFactory()
        mutate_url = reverse("bookinstance-return", kwargs={"pk": instance_to_mutate.pk})

        response = self.client.post(mutate_url)

        self.assertRedirects(response, reverse("all-borrowed"))

        updated_instance = BookInstance.objects.get(pk=instance_to_mutate.pk)
        self.assertEqual(updated_instance.status, InstanceStatus.AVAILABLE)
        self.assertIsNone(updated_instance.borrower)
        self.assertIsNone(updated_instance.due_back)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            f"Book '{updated_instance.book.title}' ({updated_instance.id}) successfuly returned.",
        )
        self.assertEqual(messages[0].level_tag, "success")

    @patch("catalog.views.return_book")
    def test_post_exception_adds_error_message_and_redirects(self, mock_return_book):
        self.client.force_login(self.user_with_perms)
        mock_return_book.side_effect = Exception("Simulated database error")

        instance_to_mutate = OnLoanBookInstanceFactory()
        mutate_url = reverse("bookinstance-return", kwargs={"pk": instance_to_mutate.pk})

        response = self.client.post(mutate_url)

        self.assertRedirects(response, reverse("all-borrowed"))

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Error during returning: Simulated database error")
        self.assertEqual(messages[0].level_tag, "error")
