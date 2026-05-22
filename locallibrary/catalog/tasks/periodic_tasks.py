from datetime import date, timedelta

from celery import shared_task

from catalog.choices import InstanceStatus
from catalog.models import BookInstance
from catalog.services import return_book
from catalog.tasks.notification_tasks import send_return_reminder_email


@shared_task(name="catalog.check_expiring_loans")
def check_expiring_loans():
    today = date.today()

    three_days_out = today + timedelta(days=3)
    one_day_out = today + timedelta(days=1)

    expiring_loan_ids = list(
        BookInstance.objects.filter(
            due_back__in=[three_days_out, one_day_out],
            status__in=[InstanceStatus.ON_LOAN, InstanceStatus.RESERVED],
        ).values_list("id", flat=True)
    )

    for loan_id in expiring_loan_ids:
        send_return_reminder_email.delay(str(loan_id))

    return f"Processed {len(expiring_loan_ids)} reminders."


@shared_task(name="catalog.update_status_on_expiring_reservation_date")
def update_status_on_expiring_reservation_date():
    overdue = BookInstance.objects.filter(status=InstanceStatus.RESERVED, due_back__lt=date.today())
    count = 0
    for instance in overdue.select_for_update():
        return_book(book_instance=instance)
        count += 1
    return f"Cleaned up {count} expired reservations."
