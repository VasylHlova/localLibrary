from typing import Any

from django.db import models
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from common.tasks import cleanup_storage_file
from common.cache import increment_model_cache_version

@receiver(post_delete, sender="catalog.Author")
@receiver(post_delete, sender="catalog.Book")
def cleanup_image_on_delete(sender: type[models.Model], instance: models.Model, **kwargs: Any) -> None:
    if instance.image:
        cleanup_storage_file.delay(file_path=instance.image.name)


@receiver(pre_save, sender="catalog.Author")
@receiver(pre_save, sender="catalog.Book")
def cleanup_old_image_on_update(sender: type[models.Model], instance: models.Model, **kwargs: Any) -> None:
    if not instance.pk:
        return

    if getattr(instance, '_original_image', None) and instance._original_image != instance.image.name:
        cleanup_storage_file.delay(file_path=instance._original_image)


@receiver([post_delete, post_save], sender="catalog.Genre")
@receiver([post_delete, post_save], sender="catalog.Language")
@receiver([post_delete, post_save], sender="catalog.Author")
@receiver([post_delete, post_save], sender="catalog.Book")
@receiver([post_delete, post_save], sender="catalog.BookInstance")
@receiver([post_delete, post_save], sender="catalog.loan")
def invalidate_cache(sender: type[models.Model], instance: models.Model, **kwargs: Any) -> None:
    model_name = sender._meta.model_name

    increment_model_cache_version(model_name)
