from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from catalog.tasks.notification_tasks import send_return_reminder_email
from catalog.tests.helper.factories import (
    AvailableBookInstanceFactory,
    OnLoanBookInstanceFactory,
    OverdueBookInstanceFactory,
)


class SendReturnReminderEmailTaskTest(TestCase):
    @patch("catalog.tasks.notification_tasks.send_mail")
    def test_sends_email_successfully(self, mock_send_mail):
        due_date = timezone.now().date() + timedelta(days=3)
        instance = OnLoanBookInstanceFactory(due_back=due_date)

        send_return_reminder_email(str(instance.id))

        mock_send_mail.assert_called_once()
        _, kwargs = mock_send_mail.call_args
        self.assertEqual(kwargs["recipient_list"], [instance.borrower.email])
        self.assertIn("Days left: 3", kwargs["html_message"])

    @patch("catalog.tasks.notification_tasks.send_mail")
    def test_handles_overdue_days_text(self, mock_send_mail):
        instance = OverdueBookInstanceFactory()

        send_return_reminder_email(str(instance.id))

        _, kwargs = mock_send_mail.call_args
        self.assertIn("deadline has already passed", kwargs["html_message"])

    @patch("catalog.tasks.notification_tasks.send_mail")
    def test_aborts_if_status_is_available(self, mock_send_mail):
        instance = AvailableBookInstanceFactory()

        result = send_return_reminder_email(str(instance.id))

        mock_send_mail.assert_not_called()
        self.assertIn("Email aborted", result)
