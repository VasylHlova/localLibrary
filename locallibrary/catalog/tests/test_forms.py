import datetime

from utils.choices import InstanceStatus
from django.test import TestCase

from catalog.models import  Loan
from catalog.forms import (
    BaseBookInstanceForm,
    BorrowOrReserveBookForm,
    ChangeBookStatusForm,
    RenewBookForm,
)
from .helper.factories import (
    UserFactory, 
    AvailableBookInstanceFactory, 
    OnLoanBookInstanceFactory
)


class RenewBookFormTest(TestCase):
    def test_renew_from_no_date(self):
        date = None
        form = RenewBookForm(data={"due_back": date})
        self.assertFalse(form.is_valid())

    def test_renew_form_date_in_past(self):
        date = datetime.date.today() - datetime.timedelta(days=1)
        form = RenewBookForm(data={"due_back": date})
        self.assertFalse(form.is_valid())
        self.assertIn("due_back", form.errors)
        self.assertEqual(form.errors["due_back"][0], "Invalid date - renewal in past!")

    def test_renew_form_date_too_far_in_future(self):
        date = datetime.date.today() + datetime.timedelta(weeks=4) + datetime.timedelta(days=1)
        form = RenewBookForm(data={"due_back": date})
        self.assertFalse(form.is_valid())
        self.assertIn("due_back", form.errors)
        self.assertEqual(form.errors["due_back"][0], "Invalid date - renewal more than 4 weeks ahead!")

    def test_renew_form_date_today(self):
        date = datetime.date.today()
        form = RenewBookForm(data={"due_back": date})
        self.assertTrue(form.is_valid())

    def test_renew_form_date_max(self):
        date = datetime.date.today() + datetime.timedelta(weeks=4)
        form = RenewBookForm(data={"due_back": date})
        self.assertTrue(form.is_valid())


class BaseBookInstanceFormTest(TestCase):
    def test_past_due_date_is_invalid(self):
        past_date = datetime.date.today() - datetime.timedelta(days=1)
        data = {"status": InstanceStatus.ON_LOAN, "due_back": past_date}
        form = BaseBookInstanceForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("due_back", form.errors)
        self.assertEqual(form.errors["due_back"][0], "Invalid date - renewal in past!")

    def test_term_limit_exceeded_for_loan_status(self):
        too_far_date = datetime.date.today() + datetime.timedelta(weeks=4) + datetime.timedelta(days=1)
        data = {"status": InstanceStatus.ON_LOAN, "due_back": too_far_date}
        form = BaseBookInstanceForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("due_back", form.errors)
        self.assertEqual(form.errors["due_back"][0], "Invalid date - renewal more than 4 weeks ahead!")

    def test_term_limit_exceeded_for_reserve_status(self):
        too_far_date = datetime.date.today() + datetime.timedelta(weeks=2) + datetime.timedelta(days=1)
        data = {"status": InstanceStatus.RESERVED, "due_back": too_far_date}
        form = BaseBookInstanceForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("due_back", form.errors)
        self.assertEqual(form.errors["due_back"][0], "Invalid date - renewal more than 2 weeks ahead!")


class ChangeBookStatusFormTest(TestCase):
    def test_available_status_must_have_empty_due_date(self):
        data = {"status": InstanceStatus.AVAILABLE, "due_back": datetime.date.today()}
        form = ChangeBookStatusForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("due_back", form.errors)
        self.assertEqual(form.errors["due_back"][0], "The due back field must be empty for this status!")

    def test_available_status_success(self):
        data = {"status": InstanceStatus.AVAILABLE, "due_back": None}
        form = ChangeBookStatusForm(data=data)
        self.assertTrue(form.is_valid())

    def test_loan_status_success(self):
        date = datetime.date.today() + datetime.timedelta(weeks=4)

        data = {"status": InstanceStatus.ON_LOAN, "due_back": date}
        form = ChangeBookStatusForm(data=data)
        self.assertTrue(form.is_valid())


class BorrowOrReserveBookFormTest(TestCase):
    def test_cannot_borrow_unavailable_book(self):
        form_data = {
            "status": InstanceStatus.ON_LOAN,
            "due_back": datetime.date.today() + datetime.timedelta(weeks=1),
        }
        unavailable_instance = OnLoanBookInstanceFactory()
        form = BorrowOrReserveBookForm(data=form_data, instance=unavailable_instance)

        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
        self.assertEqual(form.non_field_errors()[0], "This book is not available!")

    def test_can_borrow_available_book(self):
        user = UserFactory()
        available_instance = AvailableBookInstanceFactory()

        form_data = {
            "status": InstanceStatus.ON_LOAN,
            "due_back": datetime.date.today() + datetime.timedelta(weeks=1),
        }

        form = BorrowOrReserveBookForm(data=form_data, instance=available_instance)
        form.user = user

        self.assertTrue(form.is_valid())

        saved_instance = form.save()

        self.assertEqual(saved_instance.status, InstanceStatus.ON_LOAN)

        self.assertEqual(available_instance.status, InstanceStatus.ON_LOAN)
        self.assertEqual(available_instance.borrower, user)

        history_exists = Loan.objects.filter(
            book_instance=available_instance, 
            borrower=user
        ).exists()
        self.assertTrue(history_exists, "Запис в історії позичань має бути створений")
