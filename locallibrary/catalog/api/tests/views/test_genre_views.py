import pytest
from django.urls import reverse
from django.contrib.auth.models import Permission
from rest_framework import status

from catalog.models import Genre
from catalog.tests.helper.factories import GenreFactory, LibrarianUserFactory

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

class TestGenreViewSet:

    def test_list_anonymous(self, api_client):
        GenreFactory.create_batch(3)
        response = api_client.get(reverse("api-genre-list"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3

    def test_retrieve(self, api_client):
        genre = GenreFactory()
        response = api_client.get(reverse("api-genre-detail", args=[genre.pk]))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == genre.name

    def test_create_anonymous_forbidden(self, api_client):
        response = api_client.post(reverse("api-genre-list"), {"name": "Horror"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_staff(self, api_client):
        user = _staff_user()
        api_client.force_authenticate(user=user)
        response = api_client.post(reverse("api-genre-list"), {"name": "Horror"})
        assert response.status_code == status.HTTP_201_CREATED
        assert Genre.objects.filter(name="Horror").exists()

    def test_update_staff(self, api_client):
        user = _staff_user()
        api_client.force_authenticate(user=user)
        genre = GenreFactory(name="Old")
        response = api_client.put(
            reverse("api-genre-detail", args=[genre.pk]), {"name": "New"}
        )
        assert response.status_code == status.HTTP_200_OK
        genre.refresh_from_db()
        assert genre.name == "New"

    def test_delete_staff(self, api_client):
        user = _staff_user()
        api_client.force_authenticate(user=user)
        genre = GenreFactory()
        response = api_client.delete(reverse("api-genre-detail", args=[genre.pk]))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Genre.objects.filter(pk=genre.pk).exists()

    def test_filter_by_name(self, api_client):
        GenreFactory(name="Science Fiction")
        GenreFactory(name="Horror")
        response = api_client.get(reverse("api-genre-list"), {"name": "Horror"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "Horror"
