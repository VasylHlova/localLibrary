from typing import Any

from .utils import processing_image


class ImageProcessingMixin:
    def save(self, *args: Any, **kwargs: Any) -> None:
        if hasattr(self, "photo") and self.photo:
            size: tuple[int, int] = getattr(self, "IMAGE_SIZE", (800, 800))

            processed = processing_image(self.photo, max_size=size)
            if processed:
                self.photo.save(self.photo.name, processed, save=False)

        super().save(*args, **kwargs)
