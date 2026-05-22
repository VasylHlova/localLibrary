from django.test import TestCase

from catalog.models import BookInstance
from catalog.tests.helper.factories import (
    AvailableBookInstanceFactory,
    MaintenanceBookInstanceFactory,
    OnLoanBookInstanceFactory,
    ReservedBookInstanceFactory,
    UserFactory,
)


class BookInstanceManagerTest(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.available = AvailableBookInstanceFactory()
        self.on_loan = OnLoanBookInstanceFactory(borrower=self.user)
        self.reserved = ReservedBookInstanceFactory(borrower=self.user)
        self.maintenance = MaintenanceBookInstanceFactory()

    def test_active_loans_returns_on_loan_and_reserved(self):
        qs = BookInstance.objects.active_loans()
        self.assertIn(self.on_loan, qs)
        self.assertIn(self.reserved, qs)

    def test_active_loans_excludes_other_statuses(self):
        qs = BookInstance.objects.active_loans()
        self.assertNotIn(self.available, qs)
        self.assertNotIn(self.maintenance, qs)

    def test_active_loans_by_user_returns_only_user_loans(self):
        other_instance = OnLoanBookInstanceFactory()
        qs = BookInstance.objects.active_loans_by_user(self.user)
        self.assertIn(self.on_loan, qs)
        self.assertNotIn(other_instance, qs)

    def test_active_loans_by_user_excludes_available(self):
        qs = BookInstance.objects.active_loans_by_user(self.user)
        self.assertNotIn(self.available, qs)

    def test_available_book_instances_returns_only_available(self):
        qs = BookInstance.objects.available_book_instances()
        self.assertIn(self.available, qs)
        self.assertNotIn(self.on_loan, qs)
        self.assertNotIn(self.reserved, qs)
        self.assertNotIn(self.maintenance, qs)
