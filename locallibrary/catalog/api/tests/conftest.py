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
    ImageFactory,
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
register(ImageFactory)
register(ReservedBookInstanceFactory)
register(AvailableBookInstanceFactory)
register(MaintenanceBookInstanceFactory)
register(LibrarianUserFactory)
register(BookInstanceFactory)

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_user(username="testuser", password="123")
    api_client.force_authenticate(user=user)
    return api_client