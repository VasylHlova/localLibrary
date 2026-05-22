import pytest
from django.urls import reverse
from rest_framework import status

from catalog.models import Genre
from catalog.tests.helper.factories import GenreFactory

pytestmark = pytest.mark.django_db


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

    def test_create_staff(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        response = api_client.post(reverse("api-genre-list"), {"name": "Horror"})
        assert response.status_code == status.HTTP_201_CREATED
        assert Genre.objects.filter(name="Horror").exists()

    def test_update_staff(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        genre = GenreFactory(name="Old")
        response = api_client.put(
            reverse("api-genre-detail", args=[genre.pk]), {"name": "New"}
        )
        assert response.status_code == status.HTTP_200_OK
        genre.refresh_from_db()
        assert genre.name == "New"

    def test_delete_staff(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
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
