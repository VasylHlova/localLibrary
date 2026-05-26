import pytest
from django.urls import reverse
from rest_framework import status

from catalog.tests.helper.factories import LoanFactory, UserFactory

pytestmark = pytest.mark.django_db


class TestLoanReadViewSet:
    def test_list_requires_view_loan_permission(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        response = api_client.get(reverse("api-loan-list"))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_anonymous_returns_401(self, api_client):
        response = api_client.get(reverse("api-loan-list"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_with_permission(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        LoanFactory.create_batch(3)
        response = api_client.get(reverse("api-loan-list"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3

    def test_retrieve_with_permission(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        loan = LoanFactory()
        response = api_client.get(reverse("api-loan-detail", args=[loan.pk]))
        assert response.status_code == status.HTTP_200_OK

    def test_create_not_allowed(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        response = api_client.post(reverse("api-loan-list"), {})
        assert response.status_code in (status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_403_FORBIDDEN)
