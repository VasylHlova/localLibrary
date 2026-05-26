import pytest
from django.urls import reverse
from rest_framework import status

from catalog.tests.helper.factories import AuthorFactory, BookFactory

pytestmark = pytest.mark.django_db


class TestAuthorViewSet:
    def test_list_returns_all_authors(self, api_client):
        AuthorFactory.create_batch(4)
        response = api_client.get(reverse("api-author-list"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 4

    def test_retrieve_uses_base_serializer(self, api_client):
        author = AuthorFactory()
        response = api_client.get(reverse("api-author-detail", args=[author.pk]))
        assert response.status_code == status.HTTP_200_OK
        assert "first_name" in response.data

    def test_create_staff(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        response = api_client.post(
            reverse("api-author-list"),
            {"first_name": "Jane", "last_name": "Doe"},
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_anonymous_returns_401(self, api_client):
        response = api_client.post(
            reverse("api-author-list"),
            {"first_name": "Jane", "last_name": "Doe"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_destroy_returns_204(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        author = AuthorFactory()
        response = api_client.delete(reverse("api-author-detail", args=[author.pk]))
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_destroy_with_related_books_returns_409(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        author = AuthorFactory()
        BookFactory(author=author)
        response = api_client.delete(reverse("api-author-detail", args=[author.pk]))
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "related books" in response.data["detail"]

    def test_list_uses_base_serializer_for_list_action(self, api_client):
        AuthorFactory()
        response = api_client.get(reverse("api-author-list"))
        assert response.status_code == status.HTTP_200_OK
        assert "first_name" in response.data["results"][0]
