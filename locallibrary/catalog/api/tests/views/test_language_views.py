import pytest
from django.urls import reverse
from rest_framework import status

from catalog.models import Language
from catalog.tests.helper.factories import LanguageFactory

pytestmark = pytest.mark.django_db


class TestLanguageViewSet:

    def test_list_anonymous(self, api_client):
        LanguageFactory.create_batch(2)
        response = api_client.get(reverse("api-language-list"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_retrieve(self, api_client):
        lang = LanguageFactory()
        response = api_client.get(reverse("api-language-detail", args=[lang.pk]))
        assert response.status_code == status.HTTP_200_OK

    def test_create_anonymous_forbidden(self, api_client):
        response = api_client.post(reverse("api-language-list"), {"name": "Polish"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_staff(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        response = api_client.post(reverse("api-language-list"), {"name": "Polish"})
        assert response.status_code == status.HTTP_201_CREATED
        assert Language.objects.filter(name="Polish").exists()

    def test_delete_staff(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        lang = LanguageFactory()
        response = api_client.delete(reverse("api-language-detail", args=[lang.pk]))
        assert response.status_code == status.HTTP_204_NO_CONTENT
