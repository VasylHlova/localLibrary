from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status

from catalog.choices import InstanceStatus
from catalog.tests.helper.factories import (
    AvailableBookInstanceFactory,
    BookFactory,
    MaintenanceBookInstanceFactory,
    OnLoanBookInstanceFactory,
    UserFactory,
)

pytestmark = pytest.mark.django_db


class TestGetBookInstanceQueryset:
    def test_anonymous_sees_only_available(self, api_client):
        AvailableBookInstanceFactory.create_batch(2)
        OnLoanBookInstanceFactory()
        MaintenanceBookInstanceFactory()
        response = api_client.get(reverse("api-instance-list"))
        assert response.status_code == status.HTTP_200_OK
        statuses = {item["status"] for item in response.data["results"]}
        assert InstanceStatus.AVAILABLE in statuses
        assert InstanceStatus.ON_LOAN not in statuses
        assert InstanceStatus.MAINTENANCE not in statuses

    def test_staff_user_sees_all_statuses(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        AvailableBookInstanceFactory()
        OnLoanBookInstanceFactory()
        MaintenanceBookInstanceFactory()
        response = api_client.get(reverse("api-instance-list"))
        assert response.status_code == status.HTTP_200_OK
        statuses = {item["status"] for item in response.data["results"]}
        assert InstanceStatus.AVAILABLE in statuses
        assert InstanceStatus.ON_LOAN in statuses
        assert InstanceStatus.MAINTENANCE in statuses

    def test_regular_user_sees_available_and_own_loans(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        own_loan = OnLoanBookInstanceFactory(borrower=user)
        other_loan = OnLoanBookInstanceFactory()
        available = AvailableBookInstanceFactory()
        response = api_client.get(reverse("api-instance-list"))
        assert response.status_code == status.HTTP_200_OK
        ids = {item["id"] for item in response.data["results"]}
        assert str(own_loan.id) in ids
        assert str(available.id) in ids
        assert str(other_loan.id) not in ids


class TestBookInstanceViewSet:
    def test_list_anonymous_returns_200_with_available_only(self, api_client):
        AvailableBookInstanceFactory.create_batch(2)
        OnLoanBookInstanceFactory()
        response = api_client.get(reverse("api-instance-list"))
        assert response.status_code == status.HTTP_200_OK
        statuses = {item["status"] for item in response.data["results"]}
        assert InstanceStatus.AVAILABLE in statuses
        assert InstanceStatus.ON_LOAN not in statuses

    def test_list_regular_user_returns_200(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        AvailableBookInstanceFactory.create_batch(2)
        OnLoanBookInstanceFactory()
        response = api_client.get(reverse("api-instance-list"))
        assert response.status_code == status.HTTP_200_OK

    def test_list_staff_user_returns_200(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        AvailableBookInstanceFactory.create_batch(2)
        OnLoanBookInstanceFactory()
        response = api_client.get(reverse("api-instance-list"))
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_anonymous_returns_200_for_available_instance(self, api_client):
        instance = AvailableBookInstanceFactory()
        response = api_client.get(reverse("api-instance-detail", args=[instance.pk]))
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_staff_can_access_any_instance(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        instance = OnLoanBookInstanceFactory()
        response = api_client.get(reverse("api-instance-detail", args=[instance.pk]))
        assert response.status_code == status.HTTP_200_OK

    def test_create_requires_permission(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        response = api_client.post(reverse("api-instance-list"), {})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_staff(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        book = BookFactory()
        payload = {
            "book": book.pk,
            "imprint": "First Edition",
            "status": InstanceStatus.AVAILABLE,
        }
        response = api_client.post(reverse("api-instance-list"), payload)
        assert response.status_code == status.HTTP_201_CREATED

    def test_partial_update_requires_can_change_status(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        instance = OnLoanBookInstanceFactory(borrower=user)
        response = api_client.patch(
            reverse("api-instance-detail", args=[instance.pk]),
            {"status": InstanceStatus.AVAILABLE},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_partial_update_with_can_change_status(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        instance = OnLoanBookInstanceFactory()
        response = api_client.patch(
            reverse("api-instance-detail", args=[instance.pk]),
            {"status": InstanceStatus.AVAILABLE, "due_back": None},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        instance.refresh_from_db()
        assert instance.status == InstanceStatus.AVAILABLE

    def test_my_action_requires_authentication(self, api_client):
        response = api_client.get(reverse("api-instance-my"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_my_action_returns_own_loans_only(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        own = OnLoanBookInstanceFactory(borrower=user)
        other = OnLoanBookInstanceFactory()
        response = api_client.get(reverse("api-instance-my"))
        assert response.status_code == status.HTTP_200_OK
        ids = {i["id"] for i in response.data["results"]}
        assert str(own.id) in ids
        assert str(other.id) not in ids

    def test_my_action_unpaginated_when_no_results(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        with patch.object(
            __import__("catalog.api.views", fromlist=["BookInstanceViewSet"]).BookInstanceViewSet,
            "paginate_queryset",
            return_value=None,
        ):
            response = api_client.get(reverse("api-instance-my"))
        assert response.status_code == status.HTTP_200_OK
