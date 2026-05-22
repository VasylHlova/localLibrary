from django.core.exceptions import ValidationError
from django.core.files.base import File

MAX_UPLOAD_SIZE_BYTES = 20 * 1024 * 1024


def validate_file_size(file: File) -> None:
    if file.size > MAX_UPLOAD_SIZE_BYTES:
        raise ValidationError("Exceeded max file size(20MB)")
