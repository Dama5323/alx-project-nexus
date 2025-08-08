# orders/serializers.py
from drf_yasg import openapi
from rest_framework import serializers
from .models import Order, OrderItem
from products.serializers import ProductSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'price', 'quantity', 'product_name', 'product_sku', 'subtotal']
        swagger_schema_fields = {
            'type': openapi.TYPE_OBJECT,
            'title': "OrderItem",
            'properties': {
                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'product': openapi.Schema(type=openapi.TYPE_OBJECT),
                'price': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER),
                'product_name': openapi.Schema(type=openapi.TYPE_STRING),
                'product_sku': openapi.Schema(type=openapi.TYPE_STRING),
                'subtotal': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
            }
        }

    def get_subtotal(self, obj):
        return obj.price * obj.quantity

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    class Meta:
        model = Order
        fields = '__all__'
        swagger_schema_fields = {
            'type': openapi.TYPE_OBJECT,
            'title': "Order",
            'properties': {
                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                'status': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=[choice[0] for choice in Order.Status.choices]
                ),
                'status_display': openapi.Schema(type=openapi.TYPE_STRING),
                'payment_method': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=[choice[0] for choice in Order.PaymentMethod.choices]
                ),
                'payment_method_display': openapi.Schema(type=openapi.TYPE_STRING),
                'total_price': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
                'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                
            }
        }