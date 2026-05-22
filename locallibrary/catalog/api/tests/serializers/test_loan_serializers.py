import pytest
from rest_framework.test import APIRequestFactory
from catalog.api.serializers.loan import LoanListSerializer, LoanDetailSerializer
from catalog.tests.helper.factories import LoanFactory, UserFactory, BookInstanceFactory

pytestmark = pytest.mark.django_db

def test_loan_list_serialization():
    borrower = UserFactory(first_name="Ivan", last_name="Petrenko")
    book_instance = BookInstanceFactory(imprint="First Edition")
    loan = LoanFactory(borrower=borrower, book_instance=book_instance)
    serializer = LoanListSerializer(instance=loan)
    assert serializer.data["borrower"] == str(borrower)
    assert serializer.data["book_instance"] == str(book_instance)
    assert "is_overdue" in serializer.data
    assert "overdue_days" in serializer.data

def test_loan_detail_serialization():
    borrower = UserFactory(first_name="Ivan", last_name="Petrenko")
    book_instance = BookInstanceFactory(imprint="First Edition")
    loan = LoanFactory(borrower=borrower, book_instance=book_instance)
    
    factory = APIRequestFactory()
    request = factory.get("/api/catalog/loans/")
    serializer = LoanDetailSerializer(instance=loan, context={"request": request})
    assert serializer.data["borrower"]["first_name"] == "Ivan"
    assert serializer.data["borrower"]["last_name"] == "Petrenko"
    assert serializer.data["book_instance"].endswith(f"/api/catalog/instances/{book_instance.pk}/")
    assert "is_overdue" in serializer.data
    assert "overdue_days" in serializer.data
