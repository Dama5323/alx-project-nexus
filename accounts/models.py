from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
import re

def user_profile_photo_path(instance, filename):
    return f'users/{instance.id}/profile_photos/{filename}'

class CustomUserManager(BaseUserManager):
    def normalize_email(self, email):
        """
        Override normalize_email to ensure all emails are lowercase
        """
        email = super().normalize_email(email)
        return email.lower()

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not extra_fields.get('is_staff'):
            raise ValueError(_('Superuser must have is_staff=True.'))
        if not extra_fields.get('is_superuser'):
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

def validate_date_of_birth(value):
    """
    Validator for date_of_birth field
    """
    if value is None:
        return
    
    min_age = 13
    max_age = 120
    
    today = timezone.now().date()
    age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
    
    if age < min_age:
        raise ValidationError(
            _('User must be at least %(min_age)d years old.'),
            params={'min_age': min_age},
        )
    if age > max_age:
        raise ValidationError(
            _('Please enter a valid date of birth. Maximum age is %(max_age)d.'),
            params={'max_age': max_age},
        )
    if value > today:
        raise ValidationError(_('Date of birth cannot be in the future.'))

class User(AbstractUser):
    username = None
    email = models.EmailField(
        _('email address'), 
        unique=True,
        help_text=_('Email will be automatically converted to lowercase.')
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        validators=[validate_date_of_birth],
        help_text=_('Format: DD/MM/YYYY. Must be at least 13 years old.')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_users'
    )
    profile_photo = models.ImageField(
        upload_to=user_profile_photo_path,
        null=True,
        blank=True,
        verbose_name=_('Profile Photo')
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        permissions = [
            ('can_view_dashboard', _('Can view admin dashboard')),
            ('can_manage_users', _('Can manage other users')),
        ]

    def clean(self):
        """
        Additional model-wide validation
        """
        super().clean()
        if self.email:
            self.email = self.__class__.objects.normalize_email(self.email)
            
        # You could add additional email format validation here if needed
        if self.email and not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", self.email):
            raise ValidationError({'email': _('Enter a valid email address.')})

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        """
        Ensure email is always saved in lowercase
        """
        self.email = self.email.lower()
        self.full_clean()  
        super().save(*args, **kwargs)