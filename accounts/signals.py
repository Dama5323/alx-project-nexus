from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import DatabaseError
from .models import User  # Changed from UserProfile to User
from django.conf import settings


if 'accounts' in settings.INSTALLED_APPS:
    @receiver(post_save, sender=settings.AUTH_USER_MODEL)  # Using settings reference
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            try:
                from .models import UserProfile
                UserProfile.objects.create(user=instance)
            except (DatabaseError, ImportError):
                # Handle cases where model doesn't exist
                pass

    @receiver(post_save, sender=settings.AUTH_USER_MODEL)
    def save_user_profile(sender, instance, **kwargs):
        if hasattr(instance, 'profile'):
            instance.profile.save()