import pytest
from common.validators import validate_file_size
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile


def test_validate_file_size_valid():
    file = ContentFile(b"0" * (1024 * 1024), name="test.jpg")
    validate_file_size(file)


def test_validate_file_size_invalid():
    file = ContentFile(b"0" * (21 * 1024 * 1024), name="test_large.jpg")
    with pytest.raises(ValidationError, match="Exceeded max file size"):
        validate_file_size(file)
