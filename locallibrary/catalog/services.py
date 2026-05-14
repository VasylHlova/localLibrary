from datetime import date
from django.db import transaction

from user.models import CustomUser
from utils.choices import InstanceStatus, LoanStatus
from catalog.models import Loan, BookInstance

@transaction.atomic
def borrow_book(
    book_instance: BookInstance, 
    user: CustomUser, 
    due_back: int, 
    status: InstanceStatus
) -> None:
    if status not in [InstanceStatus.ON_LOAN, InstanceStatus.RESERVED]:
        return
    
    book_instance.status = status
    book_instance.borrower = user
    book_instance.due_back = due_back
    book_instance.save()
    
    if status == InstanceStatus.ON_LOAN:
        Loan.objects.create(book_instance=book_instance, borrower=user, status=LoanStatus.ACTIVE)

@transaction.atomic
def return_book(book_instance: BookInstance) -> None:
    if book_instance.status not in [InstanceStatus.ON_LOAN, InstanceStatus.RESERVED]:
        return
    
    if book_instance.status == InstanceStatus.ON_LOAN:
        active_loan = (
            Loan.objects.filter(book_instance=book_instance, returned_at__isnull=True).select_for_update().first()
        )

        if active_loan:
            _close_loan(loan=active_loan)

    book_instance.status = InstanceStatus.AVAILABLE
    book_instance.borrower = None
    book_instance.due_back = None
    book_instance.save()


def _close_loan(loan: Loan) -> None:
    loan.status = LoanStatus.RETURNED
    loan.returned_at = date.today()

    if loan.book_instance.due_back < loan.returned_at:
        delta = loan.returned_at - loan.book_instance.due_back

        loan.is_overdue = True
        loan.overdue_days = delta.days
    else:
        loan.is_overdue = False

    loan.save()