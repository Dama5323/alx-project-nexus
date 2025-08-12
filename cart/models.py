from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.utils import timezone

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
    expires_at = models.DateTimeField(default=get_default_expiry)
    is_active = models.BooleanField(default=True, db_index=True)

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
        return self.items.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0

    @property
    def subtotal(self):
        from django.db.models import Sum, F
        result = self.items.aggregate(
            total=Sum(F('price_at_addition') * F('quantity'))
        )['total'] or Decimal('0.00')
        return Decimal(result).quantize(Decimal('0.00'))

    @property
    def total(self):
        subtotal = self.subtotal
        if hasattr(self, 'applied_coupon') and self.applied_coupon:
            return max(Decimal('0.00'),
                       subtotal - self.applied_coupon.calculate_discount(subtotal))
        return subtotal

    def clear(self):
        self.items.all().delete()

    def __str__(self):
        return f"Cart for {self.user}"


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
        if self.quantity < 1:
            raise ValidationError({'quantity': 'Quantity must be at least 1'})
        if self.quantity > self.product.stock:
            raise ValidationError({'quantity': f'Only {self.product.stock} items available'})
        if self.price_at_addition is None:
            self.price_at_addition = self.product.price

    def save(self, *args, **kwargs):
        existing = CartItem.objects.filter(
            cart=self.cart,
            product=self.product,
            is_removed=False
        ).exclude(pk=self.pk).first()

        if existing:
            existing.quantity = self.quantity
            existing.price_at_addition = self.price_at_addition
            existing.is_removed = False
            existing.removed_at = None
            existing.save()
            return existing

        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def subtotal(self):
        price = self.price_at_addition or self.product.price
        return Decimal(price * self.quantity).quantize(Decimal('0.00'))

    @property
    def total(self):
        # Apply discounts here if needed
        return self.subtotal

    def increase_quantity(self, amount):
        self.quantity += amount
        self.save(update_fields=['quantity'])

    def decrease_quantity(self, amount):
        self.quantity = max(1, self.quantity - amount)
        self.save(update_fields=['quantity'])

    def __str__(self):
        return f"{self.quantity}x {self.product.name} (Cart: {self.cart.id})"
