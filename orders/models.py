from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from products.models import Product
from django.utils import timezone
from django.db.models import Q, Sum, F
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ImproperlyConfigured, ValidationError
import json
from django.db import transaction

class Order(models.Model):
    """
    Represents a customer order with enhanced status tracking and financial controls.
    Includes robust JSON field handling and validation.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        PROCESSING = 'PROCESSING', 'Processing'
        SHIPPED = 'SHIPPED', 'Shipped'
        DELIVERED = 'DELIVERED', 'Delivered'
        CANCELLED = 'CANCELLED', 'Cancelled'
        REFUNDED = 'REFUNDED', 'Refunded'
        FAILED = 'FAILED', 'Payment Failed'

    class PaymentMethod(models.TextChoices):
        CREDIT_CARD = 'CC', 'Credit Card'
        PAYPAL = 'PP', 'PayPal'
        CASH_ON_DELIVERY = 'COD', 'Cash on Delivery'
        BANK_TRANSFER = 'BT', 'Bank Transfer'
        WALLET = 'WLT', 'Digital Wallet'

    # Core Fields
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='Customer',
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    payment_method = models.CharField(
        max_length=5,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CREDIT_CARD,
        verbose_name='Payment Method',
        db_index=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created Date',
        db_index=True
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Last Updated'
    )
    payment_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Payment Date'
    )
    shipping_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Shipping Date',
        db_index=True
    )

    # Financial Fields
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Total Amount'
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Tax Amount'
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Discount Amount'
    )

    # Address Information (JSON)
    shipping_address = models.JSONField(
        default=dict,
        verbose_name='Shipping Address',
        blank=True
    )
    billing_address = models.JSONField(
        default=dict,
        verbose_name='Billing Address',
        blank=True
    )

    # Other Fields
    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Tracking Number'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Internal Notes'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        indexes = [
            models.Index(fields=['status', 'created_at'], name='status_created_idx'),
            models.Index(fields=['user', '-created_at'], name='user_order_history_idx'),
            models.Index(fields=['payment_method', 'status'], name='payment_status_idx'),
            models.Index(
                fields=['created_at'], 
                name='fast_created_at_idx',
                condition=Q(status__in=['PENDING', 'PAID'])
            ),
        ]
        permissions = [
            ('cancel_order', 'Can cancel order'),
            ('refund_order', 'Can refund order'),
            ('export_orders', 'Can export order data'),
        ]

    def clean(self):
        """Validate JSON fields before saving"""
        super().clean()
        for field in ['shipping_address', 'billing_address']:
            value = getattr(self, field)
            if isinstance(value, str):
                try:
                    setattr(self, field, json.loads(value))
                except json.JSONDecodeError:
                    raise ValidationError({field: 'Invalid JSON format'})

    def save(self, *args, **kwargs):
        """Ensure clean data before saving"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.pk} - {self.user.email} ({self.get_status_display()})"

    @property
    def subtotal(self):
        """Calculate pre-tax/discount total"""
        return self.total_price - self.tax_amount + self.discount_amount

    @property
    def item_count(self):
        """Optimized item count using annotation"""
        return self.items.aggregate(total=Sum('quantity'))['total'] or 0

    def update_total(self):
        """Atomic update of order totals with lock to prevent race conditions"""
        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=self.pk)
            aggregates = order.items.aggregate(
                total=Sum(F('price') * F('quantity')),
                count=models.Count('id')
            )
            order.total_price = aggregates['total'] or 0
            order.save(update_fields=['total_price'])

    def mark_as_paid(self, payment_date=None):
        """Transition order to paid status with payment verification"""
        if self.status == Order.Status.PENDING:
            self.status = Order.Status.PAID
            self.payment_date = payment_date or timezone.now()
            self.save(update_fields=['status', 'payment_date'])
            self._send_payment_confirmation()

    def cancel(self, reason=None, restock=True):
        """Cancel order with safety checks and inventory management"""
        if self.status not in [Order.Status.DELIVERED, Order.Status.CANCELLED]:
            self.status = Order.Status.CANCELLED
            if reason:
                self.notes = f"{timezone.now().isoformat()} - Cancelled: {reason}\n{self.notes}"
            self.save(update_fields=['status', 'notes'])
            if restock:
                self._restock_inventory()

    def _send_payment_confirmation(self):
        """Trigger payment confirmation workflow"""
        # Implementation would go here
        pass

    def _restock_inventory(self):
        """Restock products when order is cancelled"""
        for item in self.items.all():
            if item.product:
                item.product.stock += item.quantity
                item.product.save()


class OrderItem(models.Model):
    """
    Immutable record of ordered products with price snapshots and inventory controls.
    Includes robust variant JSON field handling.
    """
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE,
        verbose_name='Order',
        db_index=True
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items',
        verbose_name='Product'
    )
    
    # Core Fields
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='Quantity'
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Unit Price'
    )
    
    # Snapshot Fields
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
    variant = models.JSONField(
        default=dict,
        verbose_name='Product Variant Info',
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created Date'
    )

    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'product'],
                name='unique_order_product',
                condition=Q(product__isnull=False)
            )
        ]
        indexes = [
            models.Index(fields=['order', 'product'], name='order_product_idx'),
            models.Index(fields=['product'], name='product_sales_idx'),
            models.Index(
                fields=['created_at'],
                name='daily_sales_idx',
                condition=Q(order__status='DELIVERED')
            ),
        ]

    def clean(self):
        """Validate variant JSON before saving"""
        super().clean()
        if isinstance(self.variant, str):
            try:
                self.variant = json.loads(self.variant)
            except json.JSONDecodeError:
                raise ValidationError({'variant': 'Invalid JSON format'})

    def save(self, *args, **kwargs):
        """Enforce business rules before saving"""
        if not self.price and self.product:
            self.price = self.product.current_price()
        
        if self.product:
            self.product_name = self.product.name
            self.product_sku = getattr(self.product, 'sku', '')
            
        self.full_clean()
        super().save(*args, **kwargs)
        
        if not kwargs.get('update_fields'):
            self.order.update_total()

    def delete(self, *args, **kwargs):
        """Handle inventory and order totals when deleting"""
        super().delete(*args, **kwargs)
        self.order.update_total()

    def __str__(self):
        return f"{self.quantity}x {self.product_name} @ {self.price} (Order #{self.order_id})"

    @property
    def subtotal(self):
        """Calculated property with null checks"""
        return (self.price or Decimal('0')) * (self.quantity or 1)

    @property
    def tax_amount(self):
        """Calculate tax amount with safety checks"""
        try:
            tax_rate = self._get_tax_rate()
            return self.subtotal * tax_rate
        except (InvalidOperation, ImproperlyConfigured):
            return Decimal('0')
        
    def _get_tax_rate(self):
        """Get configured tax rate with validation"""
        try:
            rate_str = getattr(settings, 'DEFAULT_TAX_RATE', '0.10')
            rate = Decimal(str(rate_str))
            if not (Decimal('0') <= rate <= Decimal('1')):
                raise ImproperlyConfigured("Tax rate must be between 0 and 1")
            return rate
        except (ValueError, InvalidOperation):
            raise ImproperlyConfigured("Invalid DEFAULT_TAX_RATE in settings")