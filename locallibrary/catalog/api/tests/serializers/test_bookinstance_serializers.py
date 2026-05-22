import pytest
from datetime import date, timedelta
from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import ValidationError
from catalog.choices import InstanceStatus
from catalog.api.serializers.book_instance import (
    BookInstanceListSerializer,
    BookInstanceDetailSerializer,
    BookInstanceCreateSerializer,
    BorrowOrReserveSerializer,
    ChangeStatusSerializer,
    RenewDueBackSerializer,
    BorrowReservedSerializer,
)
from catalog.tests.helper.factories import BookInstanceFactory, BookFactory, UserFactory, OnLoanBookInstanceFactory

pytestmark = pytest.mark.django_db

def test_book_instance_list_serialization():
    borrower = UserFactory()
    book = BookFactory()
    instance = BookInstanceFactory(status=InstanceStatus.ON_LOAN, borrower=borrower, book=book, due_back=date.today())
    serializer = BookInstanceListSerializer(instance=instance)
    assert serializer.data["borrower"] == str(borrower)
    assert serializer.data["book"] == str(book)
    assert serializer.data["status"] == InstanceStatus.ON_LOAN

def test_book_instance_detail_serialization():
    borrower = UserFactory()
    book = BookFactory()
    instance = BookInstanceFactory(status=InstanceStatus.ON_LOAN, borrower=borrower, book=book, due_back=date.today())
    
    factory = APIRequestFactory()
    request = factory.get("/api/catalog/instances/")
    serializer = BookInstanceDetailSerializer(instance=instance, context={"request": request})
    assert serializer.data["book"]["title"] == book.title
    assert serializer.data["borrower"]["first_name"] == borrower.first_name
    assert serializer.data["borrower"]["last_name"] == borrower.last_name

def test_book_instance_create_validation_success():
    book = BookFactory()
    data = {
        "book": book.pk,
        "imprint": "First edition",
        "status": InstanceStatus.AVAILABLE,
    }
    serializer = BookInstanceCreateSerializer(data=data)
    assert serializer.is_valid()

def test_book_instance_create_validation_invalid_status():
    book = BookFactory()
    data = {
        "book": book.pk,
        "imprint": "First edition",
        "status": InstanceStatus.ON_LOAN,
    }
    serializer = BookInstanceCreateSerializer(data=data)
    assert not serializer.is_valid()
    assert "status" in serializer.errors

def test_borrow_or_reserve_validation_success():
    data = {
        "status": InstanceStatus.ON_LOAN,
        "due_back": str(date.today() + timedelta(weeks=3)),
    }
    serializer = BorrowOrReserveSerializer(data=data)
    assert serializer.is_valid()

def test_borrow_or_reserve_validation_past_date():
    data = {
        "status": InstanceStatus.ON_LOAN,
        "due_back": str(date.today() - timedelta(days=1)),
    }
    serializer = BorrowOrReserveSerializer(data=data)
    assert not serializer.is_valid()
    assert "due_back" in serializer.errors

def test_borrow_or_reserve_validation_loan_limit_exceeded():
    data = {
        "status": InstanceStatus.ON_LOAN,
        "due_back": str(date.today() + timedelta(weeks=5)),
    }
    serializer = BorrowOrReserveSerializer(data=data)
    assert not serializer.is_valid()
    assert "due_back" in serializer.errors

def test_borrow_or_reserve_validation_reserve_limit_exceeded():
    data = {
        "status": InstanceStatus.RESERVED,
        "due_back": str(date.today() + timedelta(weeks=3)),
    }
    serializer = BorrowOrReserveSerializer(data=data)
    assert not serializer.is_valid()
    assert "due_back" in serializer.errors

def test_change_status_validation_success():
    data = {
        "status": InstanceStatus.ON_LOAN,
        "due_back": str(date.today() + timedelta(weeks=3)),
    }
    serializer = ChangeStatusSerializer(data=data)
    assert serializer.is_valid()

def test_change_status_validation_available_with_due_date_fails():
    data = {
        "status": InstanceStatus.AVAILABLE,
        "due_back": str(date.today() + timedelta(weeks=1)),
    }
    serializer = ChangeStatusSerializer(data=data)
    assert not serializer.is_valid()
    assert "due_back" in serializer.errors
    assert "The due back field must be empty for this status!" in serializer.errors["due_back"][0]

def test_change_status_validation_available_no_due_date_success():
    data = {
        "status": InstanceStatus.AVAILABLE,
    }
    serializer = ChangeStatusSerializer(data=data)
    assert serializer.is_valid()

def test_change_status_validation_partial_no_status_success():
    data = {
        "due_back": str(date.today() + timedelta(weeks=3)),
    }
    serializer = ChangeStatusSerializer(data=data)
    assert serializer.is_valid()

def test_renew_due_back_serializer_no_instance_fails():
    data = {
        "due_back": str(date.today() + timedelta(weeks=3)),
    }
    serializer = RenewDueBackSerializer(data=data)
    assert not serializer.is_valid()
    assert "non_field_errors" in serializer.errors
    assert "Cannot renew due back date without an instance." in serializer.errors["non_field_errors"][0]

def test_renew_due_back_serializer_success():
    instance = OnLoanBookInstanceFactory()
    data = {
        "due_back": str(date.today() + timedelta(weeks=3)),
    }
    serializer = RenewDueBackSerializer(instance=instance, data=data)
    assert serializer.is_valid()

def test_renew_due_back_serializer_loan_limit_exceeded():
    instance = OnLoanBookInstanceFactory()
    data = {
        "due_back": str(date.today() + timedelta(weeks=5)),
    }
    serializer = RenewDueBackSerializer(instance=instance, data=data)
    assert not serializer.is_valid()
    assert "due_back" in serializer.errors

def test_borrow_reserved_serializer_success():
    data = {
        "due_back": str(date.today() + timedelta(weeks=3)),
    }
    serializer = BorrowReservedSerializer(data=data)
    assert serializer.is_valid()

def test_borrow_reserved_serializer_limit_exceeded():
    data = {
        "due_back": str(date.today() + timedelta(weeks=5)),
    }
    serializer = BorrowReservedSerializer(data=data)
    assert not serializer.is_valid()
    assert "due_back" in serializer.errors
