from datetime import date
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from user.models import CustomUser
from catalog.choices import InstanceStatus, LoanStatus
from catalog.models import Loan, BookInstance

@transaction.atomic
def borrow_or_reserve_book(
    book_instance: BookInstance, 
    user: CustomUser, 
    due_back: int, 
    status: InstanceStatus
) -> None:
    
    locked_instance = BookInstance.objects.get_locked(pk=book_instance.pk)
    
    if status not in [InstanceStatus.ON_LOAN, InstanceStatus.RESERVED]:
        raise ValueError(f"Bad status: {status}")
    
    if locked_instance.status != InstanceStatus.AVAILABLE:
            raise ValueError("Book is not available")

    locked_instance.status = status
    locked_instance.borrower = user
    locked_instance.due_back = due_back
    locked_instance.save()
    
    if status == InstanceStatus.ON_LOAN:
        Loan.objects.create(book_instance=locked_instance, borrower=user, status=LoanStatus.ACTIVE)

@transaction.atomic
def return_book(book_instance: BookInstance) -> None:
    locked_instance = BookInstance.objects.get_locked(pk=book_instance.pk)

    if locked_instance.status not in [InstanceStatus.ON_LOAN, InstanceStatus.RESERVED]:
        raise ValueError(f"Bad status: {locked_instance.status}")
    
    if locked_instance.status == InstanceStatus.ON_LOAN:
        active_loan = (
            Loan.objects.filter(book_instance=locked_instance, returned_at__isnull=True).select_for_update().first()
        )

        if active_loan:
            _close_loan(loan=active_loan, book_instance=locked_instance)

    locked_instance.status = InstanceStatus.AVAILABLE
    locked_instance.borrower = None
    locked_instance.due_back = None
    locked_instance.save()

def _close_loan(loan: Loan, book_instance: BookInstance) -> None:
    loan.status = LoanStatus.RETURNED
    loan.returned_at = date.today()
    loan.save()

def renew_book(book_instance, due_back):
    if book_instance.status not in [InstanceStatus.ON_LOAN, InstanceStatus.RESERVED]:
        raise ValueError(_(f"This book has bad status({book_instance.status}) for this action!"))
    book_instance.due_back = due_back
    book_instance.save()

@transaction.atomic
def borrow_reserved_book(book_instance, user, due_back) -> None:
    locked_instance = BookInstance.objects.get_locked(pk=book_instance.pk)

    if locked_instance.status != InstanceStatus.RESERVED:
        raise ValueError(_(f"This book has bad status({locked_instance.status}) for this action!"))
    locked_instance.status = InstanceStatus.ON_LOAN
    locked_instance.borrower = user
    locked_instance.due_back = due_back
    locked_instance.save()
    
    Loan.objects.create(book_instance=locked_instance, borrower=user, status=LoanStatus.ACTIVE)