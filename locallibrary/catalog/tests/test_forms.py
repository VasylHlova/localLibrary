import datetime

from django.test import TestCase

from utils.choices import InstanceStatus
from catalog.forms import (
    ChangeBookInstanceStatusDueBackBaseForm,
    BorrowOrReserveBookForm,
    ChangeBookStatusForm,
    ChangeBookInstanceDueBackBaseForm,
)
from catalog.tests.helper.factories import (
    AvailableBookInstanceFactory,
)


class ChangeBookInstanceDueBackBaseFormTest(TestCase):
    def test_no_date_is_invalid(self):
        form = ChangeBookInstanceDueBackBaseForm(data={"due_back": None})
        self.assertFalse(form.is_valid())

    def test_past_date_is_invalid(self):
        past_date = datetime.date.today() - datetime.timedelta(days=1)
        form = ChangeBookInstanceDueBackBaseForm(data={"due_back": past_date})
        self.assertFalse(form.is_valid())
        self.assertIn("due_back", form.errors)
        self.assertEqual(form.errors["due_back"][0], "Invalid date - renewal in past!")

    def test_date_too_far_in_future_is_invalid(self):
        too_far = datetime.date.today() + datetime.timedelta(weeks=4) + datetime.timedelta(days=1)
        form = ChangeBookInstanceDueBackBaseForm(data={"due_back": too_far})
        self.assertFalse(form.is_valid())
        self.assertIn("due_back", form.errors)
        self.assertEqual(form.errors["due_back"][0], "Invalid date - renewal more than 4 weeks ahead!")

    def test_today_is_valid(self):
        form = ChangeBookInstanceDueBackBaseForm(data={"due_back": datetime.date.today()})
        self.assertTrue(form.is_valid())

    def test_max_date_is_valid(self):
        max_date = datetime.date.today() + datetime.timedelta(weeks=4)
        form = ChangeBookInstanceDueBackBaseForm(data={"due_back": max_date})
        self.assertTrue(form.is_valid())


class ChangeBookInstanceStatusDueBackBaseFormTest(TestCase):
    def test_past_due_date_is_invalid(self):
        past_date = datetime.date.today() - datetime.timedelta(days=1)
        form = ChangeBookInstanceStatusDueBackBaseForm(
            data={"status": InstanceStatus.ON_LOAN, "due_back": past_date}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("due_back", form.errors)
        self.assertEqual(form.errors["due_back"][0], "Invalid date - renewal in past!")

    def test_term_limit_exceeded_for_loan_status(self):
        too_far = datetime.date.today() + datetime.timedelta(weeks=4) + datetime.timedelta(days=1)
        form = ChangeBookInstanceStatusDueBackBaseForm(
            data={"status": InstanceStatus.ON_LOAN, "due_back": too_far}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("due_back", form.errors)
        self.assertEqual(form.errors["due_back"][0], "Invalid date - renewal more than 4 weeks ahead!")

    def test_term_limit_exceeded_for_reserve_status(self):
        too_far = datetime.date.today() + datetime.timedelta(weeks=2) + datetime.timedelta(days=1)
        form = ChangeBookInstanceStatusDueBackBaseForm(
            data={"status": InstanceStatus.RESERVED, "due_back": too_far}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("due_back", form.errors)
        self.assertEqual(form.errors["due_back"][0], "Invalid date - renewal more than 2 weeks ahead!")


class ChangeBookStatusFormTest(TestCase):
    def test_available_status_with_due_back_is_invalid(self):
        form = ChangeBookStatusForm(
            data={"status": InstanceStatus.AVAILABLE, "due_back": datetime.date.today()}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("due_back", form.errors)
        self.assertEqual(form.errors["due_back"][0], "The due back field must be empty for this status!")

    def test_available_status_without_due_back_is_valid(self):
        form = ChangeBookStatusForm(data={"status": InstanceStatus.AVAILABLE, "due_back": None})
        self.assertTrue(form.is_valid())

    def test_loan_status_with_valid_date_is_valid(self):
        valid_date = datetime.date.today() + datetime.timedelta(weeks=4)
        form = ChangeBookStatusForm(data={"status": InstanceStatus.ON_LOAN, "due_back": valid_date})
        self.assertTrue(form.is_valid())


class BorrowOrReserveBookFormTest(TestCase):
    def setUp(self):
        self.valid_data = {
            "status": InstanceStatus.ON_LOAN,
            "due_back": datetime.date.today() + datetime.timedelta(weeks=1),
        }

    def test_valid_data_is_valid(self):
        instance = AvailableBookInstanceFactory()
        form = BorrowOrReserveBookForm(data=self.valid_data, instance=instance)
        self.assertTrue(form.is_valid())

    def test_reserve_with_valid_date_is_valid(self):
        instance = AvailableBookInstanceFactory()
        form = BorrowOrReserveBookForm(
            data={"status": InstanceStatus.RESERVED, "due_back": datetime.date.today() + datetime.timedelta(weeks=1)},
            instance=instance
        )
        self.assertTrue(form.is_valid())

    def test_past_due_back_is_invalid(self):
        instance = AvailableBookInstanceFactory()
        form = BorrowOrReserveBookForm(
            data={"status": InstanceStatus.ON_LOAN, "due_back": datetime.date.today() - datetime.timedelta(days=1)},
            instance=instance
        )
        self.assertFalse(form.is_valid())
        self.assertIn("due_back", form.errors)
