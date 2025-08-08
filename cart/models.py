from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model

def get_default_expiry():
    return timezone.now() + timezone.timedelta(days=30)

class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(
        default=get_default_expiry
    )
    is_active = models.BooleanField(default=True, db_index=True)
    # applied_coupon = models.ForeignKey(
    #     'discounts.Coupon',
    #     null=True,
    #     blank=True,
    #     on_delete=models.SET_NULL
    # )

    class Meta:
        indexes = [
            models.Index(fields=['user'], name='cart_user_idx'),
            models.Index(fields=['created_at'], name='cart_created_idx'),
            models.Index(
                fields=['is_active'],
                name='active_carts_idx',
                condition=models.Q(is_active=True)
            ),
        ]

    @property
    def total_items(self):
        """Optimized count using aggregation"""
        return self.items.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0

    @property
    def subtotal(self):
        """Calculates total before discounts"""
        from django.db.models import Sum, F
        result = self.items.aggregate(
            total=Sum(F('product__price') * F('quantity'))
        )['total'] or Decimal('0.00')
        return Decimal(result).quantize(Decimal('0.00'))

    @property
    def total(self):
        """Final total after discounts"""
        subtotal = self.subtotal
        if hasattr(self, 'applied_coupon') and self.applied_coupon:
            return max(Decimal('0.00'), 
                     subtotal - self.applied_coupon.calculate_discount(subtotal))
        return subtotal

    def clear(self):
        """Efficiently clears all items"""
        self.items.all().delete()

class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    added_at = models.DateTimeField(auto_now_add=True)
    price_at_addition = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    is_removed = models.BooleanField(default=False)
    removed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'product'],
                name='unique_cart_product',
                condition=models.Q(is_removed=False)
            )
        ]

    def clean(self):
        if self.quantity > self.product.stock:
            raise ValidationError(
                f'Only {self.product.stock} items available'
            )

    def save(self, *args, **kwargs):
        if not self.price_at_addition:
            self.price_at_addition = self.product.price
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        return (self.price_at_addition or self.product.price) * self.quantity