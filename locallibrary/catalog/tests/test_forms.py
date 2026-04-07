import datetime

from utils.choices import InstanceStatus
from django.test import TestCase

from catalog.models import  Loan
from catalog.forms import (
    ChangeBookInstanceStatusDueBackBaseForm,
    BorrowOrReserveBookForm,
    ChangeBookStatusForm,
    ChangeBookInstanceDueBackBaseForm,
    RenewBookForm,
    BorrowReservedBookForm,
)
from .helper.factories import (
    UserFactory, 
    AvailableBookInstanceFactory, 
    OnLoanBookInstanceFactory,
    ReservedBookInstanceFactory,
)


class ChangeBookInstanceDueBackBaseFormTest(TestCase):
    def test_renew_from_no_date(self):
        date = None
        form = ChangeBookInstanceDueBackBaseForm(data={"due_back": date})
        self.assertFalse(form.is_valid())

    def test_due_back_date_in_past(self):
        date = datetime.date.today() - datetime.timedelta(days=1)
        form = ChangeBookInstanceDueBackBaseForm(data={"due_back": date})
        self.assertFalse(form.is_valid())
        self.assertIn("due_back", form.errors)
        self.assertEqual(form.errors["due_back"][0], "Invalid date - renewal in past!")

    def test_due_back_date_too_far_in_future(self):
        date = datetime.date.today() + datetime.timedelta(weeks=4) + datetime.timedelta(days=1)
        form = ChangeBookInstanceDueBackBaseForm(data={"due_back": date})
        self.assertFalse(form.is_valid())
        self.assertIn("due_back", form.errors)
        self.assertEqual(form.errors["due_back"][0], "Invalid date - renewal more than 4 weeks ahead!")

    def test_due_back_date_today(self):
        date = datetime.date.today()
        form = ChangeBookInstanceDueBackBaseForm(data={"due_back": date})
        self.assertTrue(form.is_valid())

    def test_due_back_date_max(self):
        date = datetime.date.today() + datetime.timedelta(weeks=4)
        form = ChangeBookInstanceDueBackBaseForm(data={"due_back": date})
        self.assertTrue(form.is_valid())

    def test_book_instance_status_not_in_desired(self):
        book_instance = AvailableBookInstanceFactory()
        valid_date = datetime.date.today() + datetime.timedelta(days=5)

        form = ChangeBookInstanceDueBackBaseForm(
            data={"due_back": valid_date},
            instance=book_instance,
            desired_statuses=[InstanceStatus.RESERVED, InstanceStatus.ON_LOAN]
        )

        self.assertFalse(form.is_valid())

        self.assertIn("__all__", form.errors)
        self.assertIn(
            "This book has bad status(a) for this action!", 
            form.errors["__all__"][0]
        )        

    def test_book_instance_status_in_desired(self):
        book_instance = AvailableBookInstanceFactory()
        valid_date = datetime.date.today() + datetime.timedelta(days=5)

        form = ChangeBookInstanceDueBackBaseForm(
            data={"due_back": valid_date},
            instance=book_instance,
            desired_statuses=[InstanceStatus.AVAILABLE]
        )
        self.assertTrue(form.is_valid())
 

class RenewBookFormTest(TestCase):
    def setUp(self):
        self.valid_date = datetime.date.today() + datetime.timedelta(days=7)

    def test_renew_valid_status_on_loan(self):
        book_instance = OnLoanBookInstanceFactory()
        form = RenewBookForm(
            data={"due_back": self.valid_date}, 
            instance=book_instance
        )
        self.assertTrue(form.is_valid())

    def test_renew_invalid_status_available(self):
        book_instance = AvailableBookInstanceFactory()
        form = RenewBookForm(
            data={"due_back": self.valid_date}, 
            instance=book_instance
        )
        
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
        self.assertIn(
            "This book has bad status(a) for this action!", 
            form.errors["__all__"][0]
        )


class BorrowReservedBookFormTest(TestCase):
    def setUp(self):
        self.valid_date = datetime.date.today() + datetime.timedelta(days=7)
        self.user = UserFactory()
        
        self.reserved_instance = ReservedBookInstanceFactory()

    def test_valid_status_reserved(self):
        form = BorrowReservedBookForm(
            data={"due_back": self.valid_date}, 
            instance=self.reserved_instance
        )
        form.user = self.user 
        self.assertTrue(form.is_valid())

    def test_invalid_status_on_loan(self):
        book_instance = OnLoanBookInstanceFactory()
        form = BorrowReservedBookForm(
            data={"due_back": self.valid_date}, 
            instance=book_instance
        )
        
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
        self.assertIn(
            "This book has bad status(o) for this action!", 
            form.errors["__all__"][0]
        )

    def test_form_save_changes_status_and_creates_loan(self):
        form = BorrowReservedBookForm(
            data={"due_back": self.valid_date}, 
            instance=self.reserved_instance
        )
        form.user = self.user
        
        self.assertTrue(form.is_valid()) 
        
        saved_instance = form.save()

        self.assertEqual(saved_instance.status, InstanceStatus.ON_LOAN)
        self.assertEqual(saved_instance.due_back, self.valid_date)

        self.reserved_instance.refresh_from_db()
        self.assertEqual(self.reserved_instance.status, InstanceStatus.ON_LOAN)

        history_exists = Loan.objects.filter(
            book_instance=self.reserved_instance, 
            borrower=self.user
        ).exists()
        self.assertTrue(history_exists, "Запис в історії позичань має бути створений після видачі зарезервованої книги")


class ChangeBookInstanceStatusDueBackBaseFormTest(TestCase):
    def test_past_due_date_is_invalid(self):
        past_date = datetime.date.today() - datetime.timedelta(days=1)
        data = {"status": InstanceStatus.ON_LOAN, "due_back": past_date}
        form = ChangeBookInstanceStatusDueBackBaseForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("due_back", form.errors)
        self.assertEqual(form.errors["due_back"][0], "Invalid date - renewal in past!")

    def test_term_limit_exceeded_for_loan_status(self):
        too_far_date = datetime.date.today() + datetime.timedelta(weeks=4) + datetime.timedelta(days=1)
        data = {"status": InstanceStatus.ON_LOAN, "due_back": too_far_date}
        form = ChangeBookInstanceStatusDueBackBaseForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("due_back", form.errors)
        self.assertEqual(form.errors["due_back"][0], "Invalid date - renewal more than 4 weeks ahead!")

    def test_term_limit_exceeded_for_reserve_status(self):
        too_far_date = datetime.date.today() + datetime.timedelta(weeks=2) + datetime.timedelta(days=1)
        data = {"status": InstanceStatus.RESERVED, "due_back": too_far_date}
        form = ChangeBookInstanceStatusDueBackBaseForm(data=data)

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
