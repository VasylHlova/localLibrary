from django.core.exceptions import ValidationError
from django.core.files.base import File


def validate_file_size(file: File) -> None:
    limit = 20 * 1024 * 1024

    if file.size > limit:
        raise ValidationError("Exceeded max file size(20MB)")
