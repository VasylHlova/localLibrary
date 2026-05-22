import pytest
from catalog.api.serializers.genre import GenreSerializer
from catalog.tests.helper.factories import GenreFactory

pytestmark = pytest.mark.django_db

def test_genre_serialization():
    genre = GenreFactory(name="Sci-Fi")
    serializer = GenreSerializer(instance=genre)
    expected_data = {
        "id": genre.id,
        "name": "Sci-Fi",
    }
    assert serializer.data == expected_data

def test_genre_validation_success():
    data = {"name": "Fantasy"}
    serializer = GenreSerializer(data=data)
    assert serializer.is_valid()
    assert serializer.validated_data == {"name": "Fantasy"}

def test_genre_validation_empty_name():
    data = {"name": ""}
    serializer = GenreSerializer(data=data)
    assert not serializer.is_valid()
    assert "name" in serializer.errors

def test_genre_validation_missing_name():
    data = {}
    serializer = GenreSerializer(data=data)
    assert not serializer.is_valid()
    assert "name" in serializer.errors

def test_genre_validation_name_too_long():
    data = {"name": "a" * 201}
    serializer = GenreSerializer(data=data)
    assert not serializer.is_valid()
    assert "name" in serializer.errors
