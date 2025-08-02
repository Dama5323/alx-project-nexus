from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import DatabaseError
from .models import UserProfile

@receiver(post_save, sender='accounts.CustomUser')
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        try:
            UserProfile.objects.create(user=instance)
        except DatabaseError:
            # Table doesn't exist yet or other DB issue
            pass

@receiver(post_save, sender='accounts.CustomUser')
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()