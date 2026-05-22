import pytest
from django.urls import reverse
from rest_framework import status

from catalog.tests.helper.factories import (
    AuthorFactory,
    BookFactory,
    BookInstanceFactory,
    GenreFactory,
    LanguageFactory,
)

pytestmark = pytest.mark.django_db


class TestBookViewSet:
    def test_list_anonymous(self, api_client):
        BookFactory.create_batch(3)
        response = api_client.get(reverse("api-book-list"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3

    def test_retrieve_anonymous(self, api_client):
        book = BookFactory()
        response = api_client.get(reverse("api-book-detail", args=[book.pk]))
        assert response.status_code == status.HTTP_200_OK

    def test_list_queryset_selects_related_author(self, api_client):
        BookFactory.create_batch(2)
        response = api_client.get(reverse("api-book-list"))
        assert response.status_code == status.HTTP_200_OK
        for item in response.data["results"]:
            assert "title" in item

    def test_retrieve_queryset_selects_related_language_and_prefetches_genre(self, api_client):
        book = BookFactory()
        response = api_client.get(reverse("api-book-detail", args=[book.pk]))
        assert response.status_code == status.HTTP_200_OK

    def test_create_staff(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        author = AuthorFactory()
        lang = LanguageFactory()
        genre = GenreFactory()
        payload = {
            "title": "New Book",
            "author": author.pk,
            "summary": "A summary",
            "isbn": "1234567890123",
            "language": lang.pk,
            "genre": [genre.pk],
        }
        response = api_client.post(reverse("api-book-list"), payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_anonymous_forbidden(self, api_client):
        response = api_client.post(reverse("api-book-list"), {})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_destroy_returns_204(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        book = BookFactory()
        book.instances.all().delete()
        response = api_client.delete(reverse("api-book-detail", args=[book.pk]))
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_destroy_with_related_instances_returns_409(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        book = BookFactory()
        BookInstanceFactory(book=book)
        response = api_client.delete(reverse("api-book-detail", args=[book.pk]))
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "related instances" in response.data["detail"]
