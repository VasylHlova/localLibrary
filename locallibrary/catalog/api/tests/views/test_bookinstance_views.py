import pytest
from unittest.mock import patch
from django.urls import reverse
from django.contrib.auth.models import Permission
from rest_framework import status

from catalog.choices import InstanceStatus
from catalog.models import BookInstance
from catalog.tests.helper.factories import (
    BookFactory,
    UserFactory,
    LibrarianUserFactory,
    AvailableBookInstanceFactory,
    OnLoanBookInstanceFactory,
    MaintenanceBookInstanceFactory,
)

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

class TestGetBookInstanceQueryset:

    def test_anonymous_sees_only_available(self, api_client):
        AvailableBookInstanceFactory.create_batch(2)
        OnLoanBookInstanceFactory()
        MaintenanceBookInstanceFactory()
        response = api_client.get(reverse("api-instance-list"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_with_view_perm_sees_all(self, api_client):
        user = _staff_user()
        api_client.force_authenticate(user=user)
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
        OnLoanBookInstanceFactory(borrower=user)
        OnLoanBookInstanceFactory()
        AvailableBookInstanceFactory()
        response = api_client.get(reverse("api-instance-list"))
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestBookInstanceViewSet:

    def test_list_anonymous_returns_401(self, api_client):
        AvailableBookInstanceFactory.create_batch(2)
        OnLoanBookInstanceFactory()
        response = api_client.get(reverse("api-instance-list"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_with_view_perm_returns_200(self, api_client):
        user = _staff_user()
        api_client.force_authenticate(user=user)
        AvailableBookInstanceFactory.create_batch(2)
        OnLoanBookInstanceFactory()
        response = api_client.get(reverse("api-instance-list"))
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_anonymous_returns_401(self, api_client):
        instance = AvailableBookInstanceFactory()
        response = api_client.get(reverse("api-instance-detail", args=[instance.pk]))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_own_on_loan_instance(self, api_client):
        user = _staff_user()
        api_client.force_authenticate(user=user)
        instance = OnLoanBookInstanceFactory()
        response = api_client.get(reverse("api-instance-detail", args=[instance.pk]))
        assert response.status_code == status.HTTP_200_OK

    def test_create_requires_permission(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        response = api_client.post(reverse("api-instance-list"), {})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_staff(self, api_client):
        user = _staff_user()
        api_client.force_authenticate(user=user)
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

    def test_partial_update_with_can_change_status(self, api_client):
        user = _staff_user()
        api_client.force_authenticate(user=user)
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

    def test_my_action_returns_own_loans(self, api_client):
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
