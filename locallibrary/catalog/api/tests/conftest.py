import pytest
from rest_framework.test import APIClient
from pytest_factoryboy import register

from catalog.tests.helper.factories import (
    BookFactory,
    AuthorFactory,
    LanguageFactory,
    GenreFactory,
    LoanFactory,
    OnLoanBookInstanceFactory,
    OverdueBookInstanceFactory,
    UserFactory,
    ReservedBookInstanceFactory,
    AvailableBookInstanceFactory,
    MaintenanceBookInstanceFactory,
    LibrarianUserFactory,
    BookInstanceFactory,
)

register(BookFactory)
register(AuthorFactory)
register(LanguageFactory)
register(GenreFactory)
register(LoanFactory)
register(OnLoanBookInstanceFactory)
register(OverdueBookInstanceFactory)
register(UserFactory)

register(ReservedBookInstanceFactory)
register(AvailableBookInstanceFactory)
register(MaintenanceBookInstanceFactory)
register(LibrarianUserFactory)
register(BookInstanceFactory)

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client, user


@pytest.fixture
def anon_client():
    return APIClient()


@pytest.fixture
def staff_client(api_client):
    from django.contrib.auth.models import Permission
    librarian = LibrarianUserFactory()
    perms = Permission.objects.filter(
        codename__in=[
            "view_bookinstance", "add_bookinstance", "change_bookinstance", "delete_bookinstance",
            "view_book", "add_book", "change_book", "delete_book",
            "view_author", "add_author", "change_author", "delete_author",
            "view_genre", "add_genre", "change_genre", "delete_genre",
            "view_language", "add_language", "change_language", "delete_language",
            "view_loan",
            "can_mark_returned", "can_change_due_back", "can_change_status",
        ]
    )
    librarian.user_permissions.set(perms)
    api_client.force_authenticate(user=librarian)
    return api_client, librarian