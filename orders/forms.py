from django import forms
from django.core.exceptions import ValidationError
from .models import Order, OrderItem
from products.models import Product
from cart.models import Cart

class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['shipping_address', 'billing_address', 'payment_method']
        widgets = {
            'shipping_address': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Enter complete shipping address'
            }),
            'billing_address': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Enter complete billing address'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-select'
            })
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set initial values from user profile if available
        if self.user and hasattr(self.user, 'profile'):
            profile = self.user.profile
            self.fields['shipping_address'].initial = profile.shipping_address
            self.fields['billing_address'].initial = profile.billing_address

    def clean(self):
        cleaned_data = super().clean()
        
        # Verify the user has items in their cart
        if not Cart.objects.filter(user=self.user).exists():
            raise ValidationError("You cannot create an order with an empty cart")
            
        return cleaned_data

    def save(self, commit=True):
        order = super().save(commit=False)
        order.user = self.user
        
        if commit:
            order.save()
            self._create_order_items(order)
            
        return order

    def _create_order_items(self, order):
        """Create order items from user's cart"""
        cart = Cart.objects.get(user=self.user)
        
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                price=item.product.price,
                quantity=item.quantity,
                product_name=item.product.name,
                product_sku=item.product.sku
            )
        
        # Calculate and save total price
        order.total_price = sum(
            item.price * item.quantity 
            for item in order.items.all()
        )
        order.save()
        
        # Clear the cart
        cart.items.all().delete()