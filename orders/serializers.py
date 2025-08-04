from rest_framework import serializers
from products.serializers import ProductSerializer
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'price', 'quantity', 
            'product_name', 'product_sku', 'subtotal'
        ]
        read_only_fields = fields

    def get_subtotal(self, obj):
        return obj.price * obj.quantity

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(
        source='get_status_display', 
        read_only=True
    )
    payment_method_display = serializers.CharField(
        source='get_payment_method_display', 
        read_only=True
    )

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'status', 'status_display',
            'payment_method', 'payment_method_display',
            'total_price', 'created_at', 'updated_at',
            'shipping_address', 'billing_address',
            'tracking_number', 'items'
        ]
        read_only_fields = fields