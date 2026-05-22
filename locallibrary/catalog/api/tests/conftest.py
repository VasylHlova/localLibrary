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


@pytest.fixture(scope="session")
def setup_permissions(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        from catalog.models import BookInstance

        # Ensure custom permissions exist in test database
        ct = ContentType.objects.get_for_model(BookInstance)
        for codename, name in [
            ("can_mark_returned", "Set book as returned"),
            ("can_change_due_back", "Set due back date"),
            ("can_change_status", "Can change book status"),
        ]:
            Permission.objects.get_or_create(
                codename=codename,
                content_type=ct,
                defaults={"name": name}
            )

@pytest.fixture
def staff_user(db, setup_permissions):
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
    return librarian.__class__.objects.get(pk=librarian.pk)


@pytest.fixture
def staff_client(api_client, staff_user):
    api_client.force_authenticate(user=staff_user)
    return api_client, staff_user