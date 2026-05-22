import pytest
from django.urls import reverse
from django.contrib.auth.models import Permission
from rest_framework import status

from catalog.models import Author
from catalog.tests.helper.factories import AuthorFactory, BookFactory, LibrarianUserFactory

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

    def test_create_staff(self, api_client):
        user = _staff_user()
        api_client.force_authenticate(user=user)
        response = api_client.post(
            reverse("api-author-list"),
            {"first_name": "Jane", "last_name": "Doe"},
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_anonymous_forbidden(self, api_client):
        response = api_client.post(
            reverse("api-author-list"),
            {"first_name": "Jane", "last_name": "Doe"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_destroy_returns_204(self, api_client):
        user = _staff_user()
        api_client.force_authenticate(user=user)
        author = AuthorFactory()
        response = api_client.delete(reverse("api-author-detail", args=[author.pk]))
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_destroy_with_related_books_returns_409(self, api_client):
        user = _staff_user()
        api_client.force_authenticate(user=user)
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
