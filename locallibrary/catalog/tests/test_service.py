from datetime import date, timedelta

from django.test import TestCase
from django.db import IntegrityError, transaction

from catalog.models import Loan
from utils.choices import InstanceStatus, LoanStatus
from catalog.services import (
    borrow_book,
    return_book,
    _close_loan
)
from catalog.tests.helper.factories import (
    UserFactory,
    AvailableBookInstanceFactory,
    OnLoanBookInstanceFactory,
    LoanFactory,
    OverdueBookInstanceFactory,
)


class BorrowBookServiceTest(TestCase):
    def test_borrow_book_when_status_on_loan_updates_instance_and_creates_loan(self):
        user = UserFactory()
        instance = AvailableBookInstanceFactory()
        due_back = date.today() + timedelta(weeks=2)

        borrow_book(
            book_instance=instance, 
            user=user, 
            due_back=due_back, 
            status=InstanceStatus.ON_LOAN
        )

        self.assertEqual(instance.borrower, user)
        self.assertEqual(instance.status, InstanceStatus.ON_LOAN)
        self.assertEqual(instance.due_back, due_back)
        self.assertTrue(
            Loan.objects.filter(
                book_instance=instance,
                borrower=user,
                status=LoanStatus.ACTIVE,
            ).exists()
        )

    def test_borrow_book_when_status_reserved_updates_instance_and_not_creates_loan(self):
        user = UserFactory()
        instance = AvailableBookInstanceFactory()
        due_back = date.today() + timedelta(weeks=2)

        borrow_book(
            book_instance=instance, 
            user=user, 
            due_back=due_back, 
            status=InstanceStatus.RESERVED
        )

        self.assertEqual(instance.status, InstanceStatus.RESERVED)
        self.assertFalse(
            Loan.objects.filter(book_instance=instance, status=LoanStatus.ACTIVE).exists()
        )

    def test_borrow_book_when_invalid_status_does_not_update_instance_or_create_loan(self):
        user = UserFactory()
        instance = AvailableBookInstanceFactory()

        borrow_book(
            book_instance=instance,
            user=user,
            due_back=date.today() + timedelta(weeks=2),
            status=InstanceStatus.MAINTENANCE,
        )

        self.assertIsNone(instance.borrower)
        self.assertEqual(instance.status, InstanceStatus.AVAILABLE)
        self.assertIsNone(instance.due_back)
        self.assertFalse(Loan.objects.filter(book_instance=instance).exists())

    def test_borrow_book_raises_integrity_error_when_borrower_is_none_and_status_on_loan(self):
        instance = AvailableBookInstanceFactory()

        with self.assertRaises(IntegrityError) as context:
            with transaction.atomic():
                borrow_book(
                    book_instance=instance,
                    user=None,
                    due_back=date.today() + timedelta(weeks=2),
                    status=InstanceStatus.ON_LOAN,
                )

        self.assertIn(
            "check_due_back_and_borrower_if_on_loan_or_reserved",
            str(context.exception),
        )


class ReturnBookServiceTest(TestCase):
    def test_return_book_when_already_available_does_not_change_state(self):
        instance = AvailableBookInstanceFactory()

        return_book(book_instance=instance)

        self.assertIsNone(instance.borrower)
        self.assertEqual(instance.status, InstanceStatus.AVAILABLE)
        self.assertIsNone(instance.due_back)

    def test_return_book_when_on_loan_clears_borrower_and_sets_available(self):
        instance = OnLoanBookInstanceFactory()

        return_book(book_instance=instance)

        self.assertIsNone(instance.borrower)
        self.assertEqual(instance.status, InstanceStatus.AVAILABLE)
        self.assertIsNone(instance.due_back)


class CloseLoanServiceTest(TestCase):
    def test_close_loan_when_returned_after_due_back_sets_overdue_fields(self):
        instance = OverdueBookInstanceFactory()
        loan = LoanFactory(book_instance=instance, borrower=instance.borrower)

        _close_loan(loan=loan)

        self.assertEqual(loan.returned_at, date.today())
        self.assertEqual(loan.status, LoanStatus.RETURNED)
        self.assertTrue(loan.is_overdue)
        self.assertIsNotNone(loan.overdue_days)
        self.assertGreater(loan.overdue_days, 0)

    def test_close_loan_when_returned_before_due_back_sets_not_overdue(self):
        instance = OnLoanBookInstanceFactory()
        loan = LoanFactory(book_instance=instance, borrower=instance.borrower)

        _close_loan(loan=loan)

        self.assertEqual(loan.returned_at, date.today())
        self.assertEqual(loan.status, LoanStatus.RETURNED)
        self.assertFalse(loan.is_overdue)
        self.assertIsNone(loan.overdue_days)