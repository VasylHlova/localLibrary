from datetime import timedelta, date
from celery import shared_task

from catalog.models import BookInstance
from catalog.tasks.notification_tasks import send_return_reminder_email 
from utils.choices import InstanceStatus

@shared_task(name='catalog.check_expiring_loans')
def check_expiring_loans():
    today = date.today()

    three_days_out = today + timedelta(days=3)
    one_day_out = today + timedelta(days=1)

    expiring_loan_ids = BookInstance.objects.filter(
        due_back__in=[three_days_out, one_day_out],
        status__in=[InstanceStatus.ON_LOAN, InstanceStatus.RESERVED]
    ).values_list('id', flat=True)

    for loan_id in expiring_loan_ids:
        send_return_reminder_email.delay(str(loan_id))
    
    return f"Processed {len(expiring_loan_ids)} reminders."

@shared_task(name='catalog.update_status_on_exipiring_reservetion_date')
def update_status_on_exipiring_reservation_date():
    overdue_reservation = BookInstance.objects.filter(
        status__exact=InstanceStatus.RESERVED, 
        due_back__lt=date.today()
    )

    updated_count = overdue_reservation.update(
        borrower=None,
        due_back=None,
        status=InstanceStatus.AVAILABLE,
    )

    return f"Cleaned up {updated_count} expired reservations."