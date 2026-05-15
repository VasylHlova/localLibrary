from datetime import date
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from user.models import CustomUser
from utils.choices import InstanceStatus, LoanStatus
from catalog.models import Loan, BookInstance

@transaction.atomic
def borrow_or_reserve_book(
    book_instance: BookInstance, 
    user: CustomUser, 
    due_back: int, 
    status: InstanceStatus
) -> None:
    if status not in [InstanceStatus.ON_LOAN, InstanceStatus.RESERVED]:
        raise ValueError(f"Bad status: {status}")
    
    if book_instance.status != InstanceStatus.AVAILABLE:
            raise ValueError("Book is not available")

    book_instance.status = status
    book_instance.borrower = user
    book_instance.due_back = due_back
    book_instance.save()
    
    if status == InstanceStatus.ON_LOAN:
        Loan.objects.create(book_instance=book_instance, borrower=user, status=LoanStatus.ACTIVE)

@transaction.atomic
def return_book(book_instance: BookInstance) -> None:
    if book_instance.status not in [InstanceStatus.ON_LOAN, InstanceStatus.RESERVED]:
        raise ValueError(f"Bad status: {book_instance.status}")
    
    if book_instance.status == InstanceStatus.ON_LOAN:
        active_loan = (
            Loan.objects.filter(book_instance=book_instance, returned_at__isnull=True).select_for_update().first()
        )

        if active_loan:
            _close_loan(loan=active_loan, book_instance=book_instance)

    book_instance.status = InstanceStatus.AVAILABLE
    book_instance.borrower = None
    book_instance.due_back = None
    book_instance.save()


def _close_loan(loan: Loan, book_instance: BookInstance) -> None:
    loan.status = LoanStatus.RETURNED
    loan.returned_at = date.today()

    if book_instance.due_back < loan.returned_at:
        delta = loan.returned_at - book_instance.due_back

        loan.is_overdue = True
        loan.overdue_days = delta.days
    else:
        loan.is_overdue = False

    loan.save()

def renew_book(book_instance, due_back):
    if book_instance.status not in [InstanceStatus.ON_LOAN, InstanceStatus.RESERVED]:
        raise ValueError(_(f"This book has bad status({book_instance.status}) for this action!"))
    book_instance.due_back = due_back
    book_instance.save()

def borrow_reserved_book(book_instance, user, due_back):
    if book_instance.status != InstanceStatus.RESERVED:
        raise ValueError(_(f"This book has bad status({book_instance.status}) for this action!"))
    book_instance.status = InstanceStatus.ON_LOAN
    book_instance.borrower = user
    book_instance.due_back = due_back
    book_instance.save()