from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from django.db import transaction
from django.db import models

from typing import Type, Any


@receiver(post_delete, sender='catalog.Author')
@receiver(post_delete, sender='catalog.Book')
def cleanup_photo_on_delete(sender: type[models.Model], instance:models.Model, **kwargs:Any) -> None:
    if instance.photo:
        transaction.on_commit(lambda: instance.photo.delete(save=False))

@receiver(pre_save, sender='catalog.Author')
@receiver(pre_save, sender='catalog.Book')
def cleanup_old_photo_on_update(sender: type[models.Model], instance:models.Model, **kwargs:Any) -> None:
    if not instance.pk:
        return
    
    old_instance = sender.objects.get(pk=instance.pk)

    if old_instance.photo and old_instance.photo != instance.photo:
        transaction.on_commit(lambda: old_instance.photo.delete(save=False))

