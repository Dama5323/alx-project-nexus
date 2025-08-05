from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q
import re
import os

def user_profile_photo_path(instance, filename):
    """Generate secure upload path with timestamp to prevent filename collisions"""
    ext = os.path.splitext(filename)[1].lower()
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    return f'users/{instance.id}/profile_photos/{timestamp}{ext}'

class CustomUserManager(BaseUserManager):
    def normalize_email(self, email):
        """Ensure all emails are lowercase and properly normalized"""
        email = super().normalize_email(email)
        return email.lower()

    def create_user(self, email, password=None, **extra_fields):
        """Create user with email validation and case normalization"""
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        """Create superuser with additional validations"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not extra_fields.get('is_staff'):
            raise ValueError(_('Superuser must have is_staff=True.'))
        if not extra_fields.get('is_superuser'):
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

def validate_date_of_birth(value):
    """Enhanced date validation with configurable age limits"""
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
            code='underage'
        )
    if age > max_age:
        raise ValidationError(
            _('Please enter a valid date of birth. Maximum age is %(max_age)d.'),
            params={'max_age': max_age},
            code='invalid_age'
        )
    if value > today:
        raise ValidationError(
            _('Date of birth cannot be in the future.'),
            code='future_date'
        )

class User(AbstractUser):
    # Remove username completely (not just setting to None)
    username = None
    
    email = models.EmailField(
        _('email address'),
        unique=True,
        db_index=True,  # Added for performance
        help_text=_('Email will be automatically converted to lowercase.')
    )
    
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        validators=[validate_date_of_birth],
        help_text=_('Format: YYYY-MM-DD. Must be at least 13 years old.')
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
    
    # Security fields
    failed_login_attempts = models.PositiveIntegerField(
        default=0,
        help_text=_('Number of consecutive failed login attempts')
    )
    last_failed_login = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Timestamp of last failed login attempt')
    )
    account_locked_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Timestamp until account is locked')
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
            ('can_unlock_accounts', _('Can unlock user accounts')),
        ]

        indexes = [
            # Single field indexes
            models.Index(fields=['email'], name='user_email_idx'),
            models.Index(fields=['date_joined'], name='user_joined_idx'),
            
            # Composite indexes
            models.Index(fields=['is_active', 'date_joined'], name='user_active_joined_idx'),
            models.Index(fields=['first_name', 'last_name'], name='user_name_search_idx'),
            
            # Conditional indexes
            models.Index(
                fields=['date_of_birth'],
                name='user_dob_idx',
                condition=Q(date_of_birth__isnull=False)
            ),
            models.Index(
                fields=['email'],
                name='active_user_email_idx',
                condition=Q(is_active=True)
            ),
        ]

    def clean(self):
        """Enhanced validation with strict email format checking"""
        super().clean()
        
        if self.email:
            self.email = self.__class__.objects.normalize_email(self.email)
            if not re.match(r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$", self.email):
                raise ValidationError(
                    {'email': _('Enter a valid email address.')},
                    code='invalid_email'
                )

    def save(self, *args, **kwargs):
        """Ensure consistent data before saving"""
        self.email = self.email.lower()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

    @property
    def age(self):
        """Calculate user age from date_of_birth"""
        if not self.date_of_birth:
            return None
            
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < 
            (self.date_of_birth.month, self.date_of_birth.day)
        )

    def lock_account(self, duration_minutes=30):
        """Lock user account for specified duration"""
        self.account_locked_until = timezone.now() + timezone.timedelta(
            minutes=duration_minutes
        )
        self.save(update_fields=['account_locked_until'])

    def reset_login_attempts(self):
        """Reset failed login counter"""
        self.failed_login_attempts = 0
        self.last_failed_login = None
        self.save(update_fields=[
            'failed_login_attempts', 
            'last_failed_login'
        ])