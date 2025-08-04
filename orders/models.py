from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from products.models import Product
from django.utils import timezone

class Order(models.Model):
    """
    Represents a customer order in the e-commerce system.
    Tracks the order lifecycle from creation to fulfillment.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]

    PAYMENT_METHODS = [
        ('CC', 'Credit Card'),
        ('PP', 'PayPal'),
        ('COD', 'Cash on Delivery'),
        ('BT', 'Bank Transfer'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='Customer'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        db_index=True
    )
    payment_method = models.CharField(
        max_length=3,
        choices=PAYMENT_METHODS,
        default='CC',
        verbose_name='Payment Method'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created Date'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Last Updated'
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Total Amount'
    )
    shipping_address = models.TextField(
        blank=True,
        verbose_name='Shipping Address'
    )
    billing_address = models.TextField(
        blank=True,
        verbose_name='Billing Address'
    )
    tracking_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Tracking Number'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Internal Notes'
    )
    payment_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Payment Date'
    )
    shipping_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Shipping Date'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user']),
            models.Index(fields=['payment_method']),
        ]
        permissions = [
            ('cancel_order', 'Can cancel order'),
            ('refund_order', 'Can refund order'),
        ]

    def __str__(self):
        return f"Order #{self.pk} - {self.user.email} ({self.get_status_display()})"

    @property
    def item_count(self):
        """Returns total quantity of items in the order"""
        return sum(item.quantity for item in self.items.all())

    def update_total(self):
        """Safely update order total"""
        try:
            self.total_price = sum(
                item.subtotal for item in self.items.all() 
                if hasattr(item, 'subtotal')
            )
            self.save(update_fields=['total_price'])
        except (TypeError, AttributeError):
            self.total_price = 0
            self.save(update_fields=['total_price'])

    def mark_as_paid(self):
        """Transition order to paid status"""
        if self.status == 'PENDING':
            self.status = 'PAID'
            self.payment_date = timezone.now()
            self.save(update_fields=['status', 'payment_date'])
            # Add payment notification logic here

    def cancel(self, reason=None):
        """Cancel the order with optional reason"""
        if self.status not in ['DELIVERED', 'CANCELLED', 'REFUNDED']:
            self.status = 'CANCELLED'
            if reason:
                self.notes = f"Cancellation reason: {reason}\n\n{self.notes}"
            self.save(update_fields=['status', 'notes'])
            # Add inventory restocking logic here

class OrderItem(models.Model):
    """
    Represents an individual item within an order.
    Contains product details at the time of purchase.
    """
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE,
        verbose_name='Order'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items',
        verbose_name='Product'
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='Quantity'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Unit Price'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created Date'
    )
    product_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Product Name (Snapshot)'
    )
    product_sku = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Product SKU (Snapshot)'
    )

    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'product'],
                name='unique_order_product',
                condition=models.Q(product__isnull=False)
            )
        ]
        ordering = ['created_at']

    def __str__(self):
        product_name = self.product_name or (self.product.name if self.product else "[Deleted Product]")
        return f"{self.quantity} x {product_name} (Order #{self.order.id})"

    def save(self, *args, **kwargs):
        """Save product snapshot data before saving"""
        if self.product:
            self.product_name = self.product.name
            self.product_sku = self.product.sku if hasattr(self.product, 'sku') else ''
        super().save(*args, **kwargs)
        self.order.update_total()

    def delete(self, *args, **kwargs):
        """Update order total when item is deleted"""
        order = self.order
        super().delete(*args, **kwargs)
        order.update_total()

    @property
    def subtotal(self):
        """Calculate line item total with null checks"""
        if self.price is None or self.quantity is None:
            return 0
        return self.price * self.quantitys
    
    def save(self, *args, **kwargs):
        """Auto-set price and product info if not set"""
        if self.product and not self.price:
            self.price = self.product.price
        if self.product and not self.product_name:
            self.product_name = self.product.name
        if self.product and not self.product_sku:
            self.product_sku = getattr(self.product, 'sku', '')
        super().save(*args, **kwargs)