from typing import Any
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError as DjangoValidationError

from catalog.models import BookInstance
from catalog.api.serializers.book import BookShortSerializer
from user.api.serializers import UserShortSerializer
from catalog.choices import InstanceStatus
from catalog.validators import validate_term_limit, validate_future_date


class BookInstanceStatusDueBackValidationMixin:
    def validate_due_back(self, value) -> Any:
        if value:
            validate_future_date(value)
        return value

    def validate(self, data) -> dict:
        status = data.get("status")
        due_back = data.get("due_back")
        if status and due_back:
            if status in [InstanceStatus.ON_LOAN, InstanceStatus.RESERVED]:
                try:
                    validate_term_limit(due_back, status=status)
                except DjangoValidationError as e:
                    raise serializers.ValidationError({"due_back": e.message})
        return data
    
    
class ChangeDueBackBaseSerializer(serializers.ModelSerializer):
    due_back = serializers.DateField(
        validators=[validate_future_date]
    )

    class Meta:
        model = BookInstance
        fields = ["due_back"]

    def get_status(self) -> str:
        raise NotImplementedError("Subclasses must implement get_status()")
    
    def validate(self, data) -> dict:
        due_back = data.get("due_back")
        if due_back:
            try:
                validate_term_limit(due_back, status=self.get_status())
            except DjangoValidationError as e:
                raise serializers.ValidationError({"due_back": e.message})
        return data
    

class BookInstanceReadBaseSerializer(serializers.ModelSerializer):
    is_overdue = serializers.BooleanField(read_only=True, required=False, allow_null=True)

    class Meta:
        model = BookInstance
        fields = ['id', 'book', 'status', 'imprint', 'due_back', 'borrower', 'is_overdue']

            
class BookInstanceListSerializer(BookInstanceReadBaseSerializer):
    borrower = serializers.StringRelatedField()
    book = serializers.StringRelatedField()
    

class BookInstanceDetailSerializer(BookInstanceReadBaseSerializer):
    book = BookShortSerializer(read_only=True)
    borrower = UserShortSerializer(read_only=True)
    
    
class BookInstanceCreateSerializer(serializers.ModelSerializer):
    STATUS_CHOICES = (
        (InstanceStatus.AVAILABLE, "Available"),
        (InstanceStatus.MAINTENANCE, "Maintenance"),
    )
    
    status = serializers.ChoiceField(choices=STATUS_CHOICES)
    
    class Meta:
        model = BookInstance
        fields = ['book', 'imprint', 'status']
        

class BorrowOrReserveSerializer(
    BookInstanceStatusDueBackValidationMixin, 
    serializers.Serializer
):
    STATUS_CHOICES = (
        (InstanceStatus.ON_LOAN, "Borrow"),
        (InstanceStatus.RESERVED, "Reserve"),
    )

    status = serializers.ChoiceField(choices=STATUS_CHOICES)
    due_back = serializers.DateField(
        help_text="Enter a date when you going to return the book (reservetion max - 2 weeks; borrowing - 4 weeks).",
    )


class ChangeStatusSerializer(
    BookInstanceStatusDueBackValidationMixin, 
    serializers.ModelSerializer
):
    class Meta:
        model = BookInstance
        fields = ["status", "due_back"]

    def validate(self, data) -> dict:
        data = super().validate(data) 

        status = data.get("status")
        due_back = data.get("due_back")

        if status == InstanceStatus.AVAILABLE and due_back:
            raise serializers.ValidationError(
                {"due_back": _("The due back field must be empty for this status!")}
            )
        return data
    

class RenewDueBackSerializer(ChangeDueBackBaseSerializer):
    def get_status(self) -> str:
        if self.instance is None:
            raise serializers.ValidationError("Cannot renew due back date without an instance.")
        return self.instance.status
    
class BorrowReservedSerializer(ChangeDueBackBaseSerializer):
    def get_status(self) -> str:
        return InstanceStatus.ON_LOAN