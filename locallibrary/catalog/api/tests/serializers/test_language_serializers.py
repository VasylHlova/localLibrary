import pytest

from catalog.api.serializers.language import LanguageSerializer
from catalog.tests.helper.factories import LanguageFactory

pytestmark = pytest.mark.django_db


def test_language_serialization():
    language = LanguageFactory(name="Ukrainian")
    serializer = LanguageSerializer(instance=language)
    expected_data = {
        "id": language.id,
        "name": "Ukrainian",
    }
    assert serializer.data == expected_data


def test_language_validation_success():
    data = {"name": "English"}
    serializer = LanguageSerializer(data=data)
    assert serializer.is_valid()
    assert serializer.validated_data == {"name": "English"}


def test_language_validation_empty_name():
    data = {"name": ""}
    serializer = LanguageSerializer(data=data)
    assert not serializer.is_valid()
    assert "name" in serializer.errors


def test_language_validation_missing_name():
    data = {}
    serializer = LanguageSerializer(data=data)
    assert not serializer.is_valid()
    assert "name" in serializer.errors


def test_language_validation_name_too_long():
    data = {"name": "a" * 201}
    serializer = LanguageSerializer(data=data)
    assert not serializer.is_valid()
    assert "name" in serializer.errors
