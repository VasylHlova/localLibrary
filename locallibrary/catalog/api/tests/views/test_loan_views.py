import pytest
from django.urls import reverse
from django.contrib.auth.models import Permission
from rest_framework import status

from catalog.models import Loan
from catalog.tests.helper.factories import LoanFactory, UserFactory, LibrarianUserFactory

pytestmark = pytest.mark.django_db

def _staff_user():
    user = LibrarianUserFactory()
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
    user.user_permissions.set(perms)
    return user.__class__.objects.get(pk=user.pk)

class TestLoanReadViewSet:

    def test_list_requires_view_loan_permission(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        response = api_client.get(reverse("api-loan-list"))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_anonymous_forbidden(self, api_client):
        response = api_client.get(reverse("api-loan-list"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_with_permission(self, api_client):
        user = _staff_user()
        api_client.force_authenticate(user=user)
        LoanFactory.create_batch(3)
        response = api_client.get(reverse("api-loan-list"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3

    def test_retrieve_with_permission(self, api_client):
        user = _staff_user()
        api_client.force_authenticate(user=user)
        loan = LoanFactory()
        response = api_client.get(reverse("api-loan-detail", args=[loan.pk]))
        assert response.status_code == status.HTTP_200_OK

    def test_create_not_allowed(self, api_client):
        user = _staff_user()
        api_client.force_authenticate(user=user)
        response = api_client.post(reverse("api-loan-list"), {})
        assert response.status_code in (status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_403_FORBIDDEN)
