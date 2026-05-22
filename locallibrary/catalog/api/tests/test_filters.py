import pytest
from datetime import date, timedelta
from django.utils.timezone import now
from catalog.api.filters import BookFilter, LoanFilter, AuthorFilter, BookInstanceFilter
from catalog.models import Book, Loan, Author, BookInstance
from catalog.tests.helper.factories import (
    BookFactory,
    AuthorFactory,
    LoanFactory,
    BookInstanceFactory,
    UserFactory,
)
from catalog.choices import InstanceStatus

pytestmark = pytest.mark.django_db

def test_book_filter_by_title():
    b1 = BookFactory(title="Python Book")
    b2 = BookFactory(title="Django Guide")
    f = BookFilter(data={"title": "Python Book"}, queryset=Book.objects.all())
    assert b1 in f.qs
    assert b2 not in f.qs

def test_book_filter_by_author_full_name():
    a1 = AuthorFactory(first_name="Taras", last_name="Shevchenko")
    a2 = AuthorFactory(first_name="Lesya", last_name="Ukrainka")
    b1 = BookFactory(author=a1)
    b2 = BookFactory(author=a2)
    f = BookFilter(data={"author_name": "shevchenko"}, queryset=Book.objects.all())
    assert b1 in f.qs
    assert b2 not in f.qs

def test_book_filter_by_author_full_name_empty():
    b = BookFactory()
    f = BookFilter(data={"author_name": ""}, queryset=Book.objects.all())
    assert b in f.qs

def test_loan_filter_by_issued_at():
    loan = LoanFactory()
    f = LoanFilter(data={"issued_at": str(date.today())}, queryset=Loan.objects.all())
    assert loan in f.qs

def test_loan_filter_is_overdue_true():
    user = UserFactory()
    inst_active_overdue = BookInstanceFactory(status=InstanceStatus.ON_LOAN, borrower=user, due_back=date.today() - timedelta(days=2))
    loan_active_overdue = LoanFactory(book_instance=inst_active_overdue, borrower=user, returned_at=None)
    inst_active_ok = BookInstanceFactory(status=InstanceStatus.ON_LOAN, borrower=user, due_back=date.today() + timedelta(days=2))
    loan_active_ok = LoanFactory(book_instance=inst_active_ok, borrower=user, returned_at=None)
    inst_returned_overdue = BookInstanceFactory(status=InstanceStatus.AVAILABLE, borrower=None, due_back=date.today() - timedelta(days=5))
    loan_returned_overdue = LoanFactory(book_instance=inst_returned_overdue, borrower=user, returned_at=date.today() - timedelta(days=2))
    inst_returned_ok = BookInstanceFactory(status=InstanceStatus.AVAILABLE, borrower=None, due_back=date.today() - timedelta(days=2))
    loan_returned_ok = LoanFactory(book_instance=inst_returned_ok, borrower=user, returned_at=date.today() - timedelta(days=5))

    f = LoanFilter(data={"is_overdue": True}, queryset=Loan.objects.all())
    assert loan_active_overdue in f.qs
    assert loan_returned_overdue in f.qs
    assert loan_active_ok not in f.qs
    assert loan_returned_ok not in f.qs

def test_loan_filter_is_overdue_false():
    user = UserFactory()
    inst_active_overdue = BookInstanceFactory(status=InstanceStatus.ON_LOAN, borrower=user, due_back=date.today() - timedelta(days=2))
    loan_active_overdue = LoanFactory(book_instance=inst_active_overdue, borrower=user, returned_at=None)
    inst_active_ok = BookInstanceFactory(status=InstanceStatus.ON_LOAN, borrower=user, due_back=date.today() + timedelta(days=2))
    loan_active_ok = LoanFactory(book_instance=inst_active_ok, borrower=user, returned_at=None)
    inst_returned_overdue = BookInstanceFactory(status=InstanceStatus.AVAILABLE, borrower=None, due_back=date.today() - timedelta(days=5))
    loan_returned_overdue = LoanFactory(book_instance=inst_returned_overdue, borrower=user, returned_at=date.today() - timedelta(days=2))
    inst_returned_ok = BookInstanceFactory(status=InstanceStatus.AVAILABLE, borrower=None, due_back=date.today() - timedelta(days=2))
    loan_returned_ok = LoanFactory(book_instance=inst_returned_ok, borrower=user, returned_at=date.today() - timedelta(days=5))

    f = LoanFilter(data={"is_overdue": False}, queryset=Loan.objects.all())
    assert loan_active_ok in f.qs
    assert loan_returned_ok in f.qs
    assert loan_active_overdue not in f.qs
    assert loan_returned_overdue not in f.qs

def test_author_filter_by_first_name():
    a1 = AuthorFactory(first_name="Taras", last_name="Shevchenko")
    a2 = AuthorFactory(first_name="Lesya", last_name="Ukrainka")
    f = AuthorFilter(data={"first_name": "ara"}, queryset=Author.objects.all())
    assert a1 in f.qs
    assert a2 not in f.qs

def test_author_filter_by_last_name():
    a1 = AuthorFactory(first_name="Taras", last_name="Shevchenko")
    a2 = AuthorFactory(first_name="Lesya", last_name="Ukrainka")
    f = AuthorFilter(data={"last_name": "rain"}, queryset=Author.objects.all())
    assert a2 in f.qs
    assert a1 not in f.qs

def test_author_filter_by_full_name():
    a1 = AuthorFactory(first_name="Taras", last_name="Shevchenko")
    a2 = AuthorFactory(first_name="Lesya", last_name="Ukrainka")
    f = AuthorFilter(data={"name": "ras shev"}, queryset=Author.objects.all())
    assert a1 in f.qs
    assert a2 not in f.qs

def test_author_filter_by_full_name_empty():
    a = AuthorFactory()
    f = AuthorFilter(data={"name": ""}, queryset=Author.objects.all())
    assert a in f.qs

def test_book_instance_filter_by_book_title():
    book1 = BookFactory(title="Python For Beginners")
    book2 = BookFactory(title="Django Guide")
    inst1 = BookInstanceFactory(book=book1)
    inst2 = BookInstanceFactory(book=book2)
    f = BookInstanceFilter(data={"book_title": "python"}, queryset=BookInstance.objects.all())
    assert inst1 in f.qs
    assert inst2 not in f.qs

def test_book_instance_filter_by_status():
    inst1 = BookInstanceFactory(status=InstanceStatus.AVAILABLE)
    inst2 = BookInstanceFactory(status=InstanceStatus.MAINTENANCE)
    f = BookInstanceFilter(data={"status": InstanceStatus.AVAILABLE}, queryset=BookInstance.objects.all())
    assert inst1 in f.qs
    assert inst2 not in f.qs

def test_book_instance_filter_by_borrower():
    user1 = UserFactory()
    inst1 = BookInstanceFactory(status=InstanceStatus.RESERVED, borrower=user1, due_back=date.today())
    inst2 = BookInstanceFactory(status=InstanceStatus.AVAILABLE)
    f = BookInstanceFilter(data={"borrower": user1.pk}, queryset=BookInstance.objects.all())
    assert inst1 in f.qs
    assert inst2 not in f.qs
