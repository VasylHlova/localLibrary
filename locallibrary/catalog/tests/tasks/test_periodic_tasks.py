from datetime import date, timedelta
from unittest.mock import patch
from django.test import TestCase

from catalog.tasks.periodic_tasks import (
    check_expiring_loans, 
    update_status_on_exipiring_reservation_date
)
from ..helper.factories import (
    OnLoanBookInstanceFactory, 
    BookInstanceFactory,
    UserFactory
)
from utils.choices import InstanceStatus

class PeriodicTasksTest(TestCase):

    @patch('catalog.tasks.periodic_tasks.send_return_reminder_email.delay')
    def test_check_expiring_loans_triggers_correct_dates(self, mock_delay):
        today = date.today()
        
        OnLoanBookInstanceFactory(due_back=today + timedelta(days=1))
        OnLoanBookInstanceFactory(due_back=today + timedelta(days=3))
        OnLoanBookInstanceFactory(due_back=today + timedelta(days=5))

        result = check_expiring_loans()

        self.assertEqual(mock_delay.call_count, 2)
        self.assertIn("Processed 2", result)

    def test_update_status_on_expired_reservations(self):
        today = date.today()
        user = UserFactory()

        expired = BookInstanceFactory(
            status=InstanceStatus.RESERVED,
            due_back=today - timedelta(days=1),
            borrower=user 
        )
        active = BookInstanceFactory(
            status=InstanceStatus.RESERVED,
            due_back=today + timedelta(days=1),
            borrower=user 
        )

        update_status_on_exipiring_reservation_date()

        expired.refresh_from_db()
        active.refresh_from_db()

        self.assertEqual(expired.status, InstanceStatus.AVAILABLE)
        self.assertIsNone(expired.borrower)
        self.assertEqual(active.status, InstanceStatus.RESERVED)