from datetime import date, timedelta

from django.test import TestCase
from django.db import IntegrityError, transaction

from catalog.models import Loan
from catalog.choices import InstanceStatus, LoanStatus
from catalog.services import (
    borrow_or_reserve_book,
    borrow_reserved_book,
    return_book,
    _close_loan,
    renew_book
)
from catalog.tests.helper.factories import (
    UserFactory,
    AvailableBookInstanceFactory,
    OnLoanBookInstanceFactory,
    ReservedBookInstanceFactory,
    LoanFactory,
    OverdueBookInstanceFactory,
    BookInstanceFactory,
    MaintenanceBookInstanceFactory,
)


class BorrowOrReserveBookServiceTest(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.due_back = date.today() + timedelta(weeks=2)

    def test_borrow_updates_instance_and_creates_loan(self):
        instance = AvailableBookInstanceFactory()

        borrow_or_reserve_book(
            book_instance=instance,
            user=self.user,
            due_back=self.due_back,
            status=InstanceStatus.ON_LOAN
        )

        self.assertEqual(instance.borrower, self.user)
        self.assertEqual(instance.status, InstanceStatus.ON_LOAN)
        self.assertEqual(instance.due_back, self.due_back)
        self.assertTrue(
            Loan.objects.filter(
                book_instance=instance,
                borrower=self.user,
                status=LoanStatus.ACTIVE,
            ).exists()
        )

    def test_reserve_updates_instance_and_does_not_create_loan(self):
        instance = AvailableBookInstanceFactory()

        borrow_or_reserve_book(
            book_instance=instance,
            user=self.user,
            due_back=self.due_back,
            status=InstanceStatus.RESERVED
        )

        self.assertEqual(instance.status, InstanceStatus.RESERVED)
        self.assertEqual(instance.borrower, self.user)
        self.assertFalse(
            Loan.objects.filter(book_instance=instance).exists()
        )

    def test_raises_value_error_when_invalid_status(self):
        instance = AvailableBookInstanceFactory()

        with self.assertRaises(ValueError):
            borrow_or_reserve_book(
                book_instance=instance,
                user=self.user,
                due_back=self.due_back,
                status=InstanceStatus.MAINTENANCE,
            )

    def test_raises_value_error_when_book_not_available(self):
        instance = OnLoanBookInstanceFactory()

        with self.assertRaises(ValueError):
            borrow_or_reserve_book(
                book_instance=instance,
                user=self.user,
                due_back=self.due_back,
                status=InstanceStatus.ON_LOAN,
            )

    def test_raises_integrity_error_when_borrower_is_none(self):
        instance = AvailableBookInstanceFactory()

        with self.assertRaises(IntegrityError) as context:
            with transaction.atomic():
                borrow_or_reserve_book(
                    book_instance=instance,
                    user=None,
                    due_back=self.due_back,
                    status=InstanceStatus.ON_LOAN,
                )

        self.assertIn(
            "check_due_back_and_borrower_if_on_loan_or_reserved",
            str(context.exception),
        )

    def test_is_atomic_rolls_back_on_error(self):
        instance = AvailableBookInstanceFactory()

        with self.assertRaises(ValueError):
            borrow_or_reserve_book(
                book_instance=instance,
                user=self.user,
                due_back=self.due_back,
                status=InstanceStatus.MAINTENANCE,
            )

        instance.refresh_from_db()
        self.assertEqual(instance.status, InstanceStatus.AVAILABLE)
        self.assertFalse(Loan.objects.filter(book_instance=instance).exists())


class ReturnBookServiceTest(TestCase):
    def test_return_on_loan_clears_borrower_and_sets_available(self):
        instance = OnLoanBookInstanceFactory()
        LoanFactory(book_instance=instance)

        return_book(book_instance=instance)

        self.assertIsNone(instance.borrower)
        self.assertEqual(instance.status, InstanceStatus.AVAILABLE)
        self.assertIsNone(instance.due_back)

    def test_return_on_loan_closes_active_loan(self):
        instance = OnLoanBookInstanceFactory()
        loan = LoanFactory(book_instance=instance)

        return_book(book_instance=instance)

        loan.refresh_from_db()
        self.assertEqual(loan.status, LoanStatus.RETURNED)
        self.assertIsNotNone(loan.returned_at)

    def test_return_reserved_clears_borrower_and_sets_available(self):
        instance = ReservedBookInstanceFactory()

        return_book(book_instance=instance)

        self.assertIsNone(instance.borrower)
        self.assertEqual(instance.status, InstanceStatus.AVAILABLE)
        self.assertIsNone(instance.due_back)

    def test_return_reserved_does_not_create_or_close_loan(self):
        instance = ReservedBookInstanceFactory()

        return_book(book_instance=instance)

        self.assertFalse(Loan.objects.filter(book_instance=instance).exists())

    def test_raises_value_error_when_status_not_active(self):
        instance = AvailableBookInstanceFactory()

        with self.assertRaises(ValueError):
            return_book(book_instance=instance)


class RenewBookServiceTest(TestCase):
    def setUp(self):
        self.new_due_back = date.today() + timedelta(weeks=3)

    def test_renew_on_loan_updates_due_back(self):
        instance = OnLoanBookInstanceFactory()

        renew_book(book_instance=instance, due_back=self.new_due_back)

        instance.refresh_from_db()
        self.assertEqual(instance.due_back, self.new_due_back)

    def test_renew_reserved_updates_due_back(self):
        instance = ReservedBookInstanceFactory()

        renew_book(book_instance=instance, due_back=self.new_due_back)

        instance.refresh_from_db()
        self.assertEqual(instance.due_back, self.new_due_back)

    def test_raises_value_error_when_status_not_active(self):
        instance = AvailableBookInstanceFactory()

        with self.assertRaises(ValueError):
            renew_book(book_instance=instance, due_back=self.new_due_back)

    def test_raises_value_error_when_maintenance(self):
        instance = MaintenanceBookInstanceFactory()

        with self.assertRaises(ValueError):
            renew_book(book_instance=instance, due_back=self.new_due_back)


class BorrowReservedBookServiceTest(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.due_back = date.today() + timedelta(weeks=2)

    def test_borrow_reserved_updates_status_and_borrower_and_create_loan(self):
        instance = ReservedBookInstanceFactory(borrower=self.user)

        borrow_reserved_book(
            book_instance=instance,
            user=self.user,
            due_back=self.due_back
        )

        instance.refresh_from_db()
        self.assertEqual(instance.status, InstanceStatus.ON_LOAN)
        self.assertEqual(instance.borrower, self.user)
        self.assertEqual(instance.due_back, self.due_back)
        self.assertTrue(
            Loan.objects.filter(
                book_instance=instance,
                borrower=self.user,
                status=LoanStatus.ACTIVE,
            ).exists()
        )
        
    def test_raises_value_error_when_not_reserved(self):
        instance = AvailableBookInstanceFactory()

        with self.assertRaises(ValueError):
            borrow_reserved_book(
                book_instance=instance,
                user=self.user,
                due_back=self.due_back
            )

    def test_raises_value_error_when_on_loan(self):
        instance = OnLoanBookInstanceFactory()

        with self.assertRaises(ValueError):
            borrow_reserved_book(
                book_instance=instance,
                user=self.user,
                due_back=self.due_back
            )


class CloseLoanServiceTest(TestCase):
    def test_close_loan_when_overdue_sets_overdue_fields(self):
        instance = OverdueBookInstanceFactory()
        loan = LoanFactory(book_instance=instance)

        _close_loan(loan=loan, book_instance=instance)

        self.assertEqual(loan.returned_at, date.today())
        self.assertEqual(loan.status, LoanStatus.RETURNED)
        self.assertTrue(loan.is_overdue)
        self.assertIsNotNone(loan.overdue_days)
        self.assertGreater(loan.overdue_days, 0)

    def test_close_loan_when_not_overdue_sets_not_overdue(self):
        instance = OnLoanBookInstanceFactory()
        loan = LoanFactory(book_instance=instance)

        _close_loan(loan=loan, book_instance=instance)

        self.assertEqual(loan.returned_at, date.today())
        self.assertEqual(loan.status, LoanStatus.RETURNED)
        self.assertFalse(loan.is_overdue)
        self.assertIsNone(loan.overdue_days)