from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError  
from decimal import Decimal
from products.models import Product
from django.utils import timezone


class Cart(models.Model):
    """
    Represents a user's shopping cart with enhanced functionality.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name='Owner'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Creation Date'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Last Update'
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text='Is this cart currently active?'
    )

    class Meta:
        verbose_name = 'Shopping Cart'
        verbose_name_plural = 'Shopping Carts'
        indexes = [
            models.Index(fields=['user'], name='cart_user_idx'),
            models.Index(fields=['created_at'], name='cart_created_idx'),
            models.Index(
                fields=['is_active'],
                name='active_carts_idx',
                condition=models.Q(is_active=True)
            ),
        ]

    def __str__(self):
        return f"Cart #{self.id} - {self.user.email}"

    @property
    def item_count(self):
        """Optimized count using aggregation"""
        return self.items.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0

    @property
    def total(self):
        """Calculates total with Decimal precision and null checks"""
        from django.db.models import Sum, F
        result = self.items.aggregate(
            total=Sum(F('product__price') * F('quantity'))
        )['total'] or Decimal('0')
        return Decimal(result).quantize(Decimal('0.01'))

    def clear(self):
        """Efficiently clears all items from cart"""
        self.items.all().delete()

    def merge_from_session(self, session_cart):
        """
        Merges items from session-based cart into user cart
        Handles duplicate products by summing quantities
        """
        from collections import defaultdict
        items_map = defaultdict(int)
        
        # Add existing cart items
        for item in self.items.all():
            items_map[item.product_id] += item.quantity
        
        # Add session items
        for session_item in session_cart:
            items_map[session_item['product_id']] += session_item['quantity']
        
        # Rebuild cart
        self.clear()
        for product_id, quantity in items_map.items():
            try:
                product = Product.objects.get(pk=product_id)
                self.items.create(
                    product=product,
                    quantity=min(quantity, product.stock)
                )
            except Product.DoesNotExist:
                continue


class CartItem(models.Model):
    """
    Represents an item in the shopping cart with inventory controls.
    """
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        db_index=True
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name='Product'
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='Quantity'
    )
    added_at = models.DateTimeField(
    auto_now_add=True,
    verbose_name='Added Date'
    )
    price_at_addition = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Price When Added'
    )

    class Meta:
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'product'],
                name='unique_cart_product'
            )
        ]
        indexes = [
            models.Index(fields=['cart', 'product'], name='cartitem_composite_idx'),
            models.Index(fields=['added_at'], name='cartitem_added_idx'),
        ]
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.quantity}x {self.product.name} in Cart #{self.cart_id}"

    def clean(self):
        """Validate quantity doesn't exceed available stock"""
        if self.quantity > self.product.stock:
            raise ValidationError(
                f'Only {self.product.stock} items available in stock'
            )

    def save(self, *args, **kwargs):
        """Snapshot product price and validate before saving"""
        if not self.price_at_addition:
            self.price_at_addition = self.product.price
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        """Calculates line item total with price snapshot"""
        price = self.price_at_addition or self.product.price
        return Decimal(price) * Decimal(self.quantity)

    def increase_quantity(self, amount=1, save=True):
        """Safely increase quantity with stock validation"""
        new_quantity = self.quantity + amount
        if new_quantity > self.product.stock:
            raise ValidationError(
                f'Cannot add {amount} items. Only {self.product.stock - self.quantity} available'
            )
        self.quantity = new_quantity
        if save:
            self.save()

    def decrease_quantity(self, amount=1, save=True):
        """Safely decrease quantity with minimum validation"""
        new_quantity = self.quantity - amount
        if new_quantity < 1:
            raise ValidationError('Quantity cannot be less than 1')
        self.quantity = new_quantity
        if save:
            self.save()