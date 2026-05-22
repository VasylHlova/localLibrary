import pytest
from datetime import date
from rest_framework.test import APIRequestFactory
from catalog.api.serializers.author import (
    AuthorBaseSerializer,
    AuthorShortSerializer,
    AuthorWriteSerializer,
)
from catalog.tests.helper.factories import AuthorFactory

pytestmark = pytest.mark.django_db

def test_author_base_serialization():
    author = AuthorFactory(
        first_name="Taras",
        last_name="Shevchenko",
        date_of_birth=date(1814, 3, 9),
        date_of_death=date(1861, 3, 10),
    )
    serializer = AuthorBaseSerializer(instance=author)
    expected_fields = {"id", "first_name", "last_name", "date_of_birth", "date_of_death", "image"}
    assert set(serializer.data.keys()) == expected_fields
    assert serializer.data["first_name"] == "Taras"
    assert serializer.data["last_name"] == "Shevchenko"
    assert serializer.data["date_of_birth"] == "1814-03-09"
    assert serializer.data["date_of_death"] == "1861-03-10"

def test_author_short_serialization():
    author = AuthorFactory(first_name="Lesya", last_name="Ukrainka")
    factory = APIRequestFactory()
    request = factory.get("/api/catalog/authors/")
    serializer = AuthorShortSerializer(instance=author, context={"request": request})
    assert serializer.data["first_name"] == "Lesya"
    assert serializer.data["last_name"] == "Ukrainka"
    assert "detail_url" in serializer.data
    assert serializer.data["detail_url"].endswith(f"/api/catalog/authors/{author.pk}/")

def test_author_write_validation_success():
    data = {
        "first_name": "Ivan",
        "last_name": "Franko",
        "date_of_birth": "1856-08-27",
        "date_of_death": "1916-05-28",
    }
    serializer = AuthorWriteSerializer(data=data)
    assert serializer.is_valid()

def test_author_write_validation_success_no_death_date():
    data = {
        "first_name": "Ivan",
        "last_name": "Franko",
        "date_of_birth": "1856-08-27",
    }
    serializer = AuthorWriteSerializer(data=data)
    assert serializer.is_valid()

def test_author_write_validation_death_before_birth():
    data = {
        "first_name": "Ivan",
        "last_name": "Franko",
        "date_of_birth": "1916-05-28",
        "date_of_death": "1856-08-27",
    }
    serializer = AuthorWriteSerializer(data=data)
    assert not serializer.is_valid()
    assert "non_field_errors" in serializer.errors
    assert "Author could not die earlier than was born!" in serializer.errors["non_field_errors"][0]

def test_author_write_validation_no_birth_date():
    data = {
        "first_name": "Ivan",
        "last_name": "Franko",
        "date_of_death": "1916-05-28",
    }
    serializer = AuthorWriteSerializer(data=data)
    assert serializer.is_valid()
