import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from user.tests.helper.factories import UserFactory, ProfileFactory

pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    return APIClient()

class TestUserViewSet:
    def test_list_users_anonymous_forbidden(self, api_client):
        response = api_client.get(reverse("api-user-list"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_users_staff(self, api_client):
        user = UserFactory(is_staff=True, is_superuser=True)
        api_client.force_authenticate(user=user)
        UserFactory()
        response = api_client.get(reverse("api-user-list"))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

    def test_retrieve_user(self, api_client):
        user = UserFactory(is_staff=True, is_superuser=True)
        api_client.force_authenticate(user=user)
        target = UserFactory()
        response = api_client.get(reverse("api-user-detail", args=[target.pk]))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == target.username

    def test_me_unauthenticated(self, api_client):
        url = reverse("api-user-me")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_authenticated(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        url = reverse("api-user-me")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == user.username

    def test_update_my_profile(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        url = reverse("api-user-update-my-profile")
        response = api_client.patch(url, {"date_of_birth": "1995-05-05"})
        assert response.status_code == status.HTTP_200_OK
        user.profile.refresh_from_db()
        assert str(user.profile.date_of_birth) == "1995-05-05"

    def test_update_my_account(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        url = reverse("api-user-update-my-account")
        response = api_client.patch(url, {"first_name": "NewName"})
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.first_name == "NewName"
