from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from django.contrib.auth.models import AnonymousUser
from django.db.models import Manager, Q, QuerySet
from user.models import CustomUser

from catalog.choices import InstanceStatus

if TYPE_CHECKING:
    from catalog.models import BookInstance


class BookInstanceManager(Manager["BookInstance"]):
    def active_loans(self) -> QuerySet[BookInstance]:
        return self.filter(Q(status=InstanceStatus.ON_LOAN) | Q(status=InstanceStatus.RESERVED))

    def active_loans_by_user(self, user: CustomUser | AnonymousUser | None) -> QuerySet[BookInstance]:
        if not isinstance(user, CustomUser):
            return self.none()
        return self.active_loans().filter(borrower=user)

    def available_book_instances(self) -> QuerySet[BookInstance]:
        return self.filter(status=InstanceStatus.AVAILABLE)

    def get_locked(self, pk: uuid.UUID | str) -> BookInstance:
        return self.select_for_update().get(pk=pk)
