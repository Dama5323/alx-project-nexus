from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils.crypto import get_random_string
from django.db.models import Index, UniqueConstraint, Q
from django.core.cache import cache
from rest_framework import viewsets
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django.db.models import Avg, Count
from django.db.models.signals import pre_save
from django.dispatch import receiver

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    old_slug = models.SlugField(
        max_length=200,
        blank=True,
        default='',
        help_text="Legacy slug field (can be ignored)"
    ) 
    slug = models.SlugField(max_length=200, unique=True, blank=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    def clean(self):
        if not self.name:
            raise ValidationError("Name is required")
        if not self.slug or self.slug == self.old_slug:
            self.slug = slugify(self.name)
        if Category.objects.filter(slug=self.slug).exclude(id=self.id).exists():
            raise ValidationError('This slug is already in use.')
    
    def save(self, *args, **kwargs):
        if not self.slug or self.slug == self.old_slug:
            base_slug = slugify(self.name)
            self.slug = base_slug
            counter = 1
            while Category.objects.filter(slug=self.slug).exclude(id=self.id).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
        indexes = [
            Index(fields=['name']),
            Index(fields=['slug']),
            Index(fields=['created_at']),
            Index(fields=['slug'], name='category_slug_idx'),
        ]
        constraints = [
            UniqueConstraint(fields=['slug'], name='unique_category_slug'),
        ]


class Product(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0.01)],
        db_index=True
    )
    category = models.ForeignKey(
        Category,
        related_name='products',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True
    )
    stock = models.PositiveIntegerField(default=0, db_index=True)
    available = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='products',
        null=True,
        blank=True,
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True, db_index=True)
    featured = models.BooleanField(default=False, verbose_name="Featured Product")

    def clean(self):
        if not self.name:
            raise ValidationError("Name is required")
        if not self.slug:
            self.slug = slugify(self.name)
        if Product.objects.filter(slug=self.slug).exclude(id=self.id).exists():
            raise ValidationError('This slug is already in use.')
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            self.slug = base_slug
            counter = 1
            while Product.objects.filter(slug=self.slug).exclude(id=self.id).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    @property
    def average_rating(self):
        """Calculate average product rating"""
        return self.reviews.aggregate(average=Avg('rating'))['average'] or 0

    @property
    def review_count(self):
        """Count number of reviews"""
        return self.reviews.count()

    class Meta:
        ordering = ['-created_at']
        permissions = [
            ('can_view_product', 'Can view product details'),
            ('can_create_product', 'Can create new products'),
            ('can_edit_product', 'Can edit existing products'),
            ('can_delete_product', 'Can remove products'),
        ]
        indexes = [
            Index(fields=['name', 'category']),
            Index(fields=['category', 'available']),
            Index(fields=['price', 'available']),
            Index(fields=['-created_at']),
            Index(fields=['stock']),
            Index(fields=['slug'], name='product_slug_idx'),
            Index(
                fields=['available'],
                name='idx_available_products',
                condition=Q(available=True)
            ),
            Index(
                fields=['price'],
                name='idx_price_gt_100',
                condition=Q(price__gt=100)
            ),
            Index(
                fields=['available', 'category'],
                name='idx_available_by_category',
                condition=Q(available=True)
            ),
        ]
        constraints = [
            UniqueConstraint(fields=['slug'], name='unique_product_slug'),
        ]


class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    ]
    
    product = models.ForeignKey(
        Product, 
        related_name='reviews', 
        on_delete=models.CASCADE,
        db_index=True
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        db_index=True
    )
    rating = models.PositiveIntegerField(choices=RATING_CHOICES, db_index=True)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    def __str__(self):
        return f"Review by {self.user.email} for {self.product.name}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            Index(fields=['product', 'created_at']),
            Index(fields=['product', 'rating']),
            Index(fields=['user', 'created_at']),
            Index(
                fields=['rating'],
                name='idx_high_ratings',
                condition=Q(rating__gte=4)
            ),
        ]
        constraints = [
            UniqueConstraint(
                fields=['product', 'user'],
                name='unique_user_review_per_product'
            ),
        ]


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    def list(self, request, *args, **kwargs):
        cache_key = 'all_categories'
        categories = cache.get(cache_key)
        if not categories:
            categories = self.get_queryset()
            cache.set(cache_key, categories, timeout=60*15)  # 15 minutes
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)
    
class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(
        upload_to='product_images/',
        verbose_name='Additional Image'
    )
    alt_text = models.CharField(
        max_length=100,
        blank=True,
        help_text='Alternative text for accessibility'
    )
    is_featured = models.BooleanField(
        default=False,
        help_text='Mark as featured image for this product'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_featured', 'created_at']
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'

    def __str__(self):
        return f"Image for {self.product.name}"

@receiver(pre_save, sender=Product)
def product_pre_save(sender, instance, **kwargs):
    """Auto-generate slug for products"""
    if not instance.slug:
        base_slug = slugify(instance.name)
        instance.slug = base_slug
        counter = 1
        while Product.objects.filter(slug=instance.slug).exclude(id=instance.id).exists():
            instance.slug = f"{base_slug}-{counter}"
            counter += 1
