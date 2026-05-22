import hashlib
import logging
import os
from io import BytesIO

from PIL import Image, ImageOps

from django.core.files.base import ContentFile, File
from django.db import models
from django.utils.deconstruct import deconstructible

logger = logging.getLogger(__name__)


class ImageProcessingMixin:
    IMAGE_FIELD = "image"

    def save(self, *args, **kwargs):
        field_name = getattr(self, "IMAGE_FIELD", "image")
        image_field = getattr(self, field_name, None)
        if image_field:
            size = getattr(self, "IMAGE_SIZE", (800, 800))
            processed = processing_image(image_field, max_size=size)
            if processed:
                image_field.save(image_field.name, processed, save=False)
        super().save(*args, **kwargs)


@deconstructible
class GeneratePath:
    def __init__(self, path: str) -> None:
        self.path = path

    def __call__(self, instance: models.Model, filename: str) -> str:
        hashed_name = hashlib.sha256(filename.encode("utf-8")).hexdigest()

        file_ext = ".webp"
        new_filename = f"{hashed_name}{file_ext}"

        return os.path.join(self.path, new_filename)


def processing_image(image: File, max_size: tuple[int, int] = (800, 800)) -> File | None:
    if not image:
        return None

    try:
        img = Image.open(image)
        img = ImageOps.exif_transpose(img)

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        img = ImageOps.fit(img, max_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))

        output = BytesIO()
        img.save(output, format="WEBP", quality=85, optimize=True)
        output.seek(0)

        return ContentFile(output.read())

    except Exception:
        logger.exception(
            "Image processing failed for '%s'. File will be saved unprocessed.",
            getattr(image, 'name', repr(image)),
        )
        return None
