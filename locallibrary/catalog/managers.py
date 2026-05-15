from __future__ import annotations
from typing import TYPE_CHECKING
from django.db.models import (
    Q, QuerySet,
    Manager
)

from utils.choices import InstanceStatus
from user.models import CustomUser

if TYPE_CHECKING:
    from catalog.models import BookInstance

class BookInstanceManager(Manager):
    def active_loans(self) -> QuerySet[BookInstance]:
        return (
            self.filter(
                Q(status=InstanceStatus.ON_LOAN) 
                | 
                Q(status=InstanceStatus.RESERVED)
            )
        )
    
    def active_loans_by_user(self, user: CustomUser) -> QuerySet[BookInstance]:
        return self.active_loans().filter(borrower=user)

    
    def available_book_instances(self) -> QuerySet[BookInstance]:
        return self.filter(status=InstanceStatus.AVAILABLE)