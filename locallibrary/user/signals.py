from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.db import transaction
from django.contrib.auth import get_user_model

from .models import UserProfile

User = get_user_model()

@receiver(pre_save, sender=User)
def user_deactivation_handler(sender, instance, **kwargs):
    if not instance.pk:
        return

    old_instance = sender.objects.get(pk=instance.pk)

    if old_instance.is_active and not instance.is_active:

        if instance.profile.profile_picture:
             transaction.on_commit(lambda: instance.profile.profile_picture.delete(save=False))


@receiver(pre_save, sender='user.UserProfile')
def cleanup_old_profile_photo_on_update(sender, instance, **kwargs):
    if not instance.pk:
        return
    
    old_instance = sender.objects.get(pk=instance.pk)

    if old_instance.profile_picture and old_instance.profile_picture != instance.profile_picture:
        transaction.on_commit(lambda: old_instance.profile_picture.delete(save=False))

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)