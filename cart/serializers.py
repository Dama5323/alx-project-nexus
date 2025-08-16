from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from products.serializers import ProductSerializer
from .models import Cart, CartItem
from django.db.models import Sum
from products.models import Product


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'added_at', 'price_at_addition', 'subtotal']
        read_only_fields = ['added_at', 'price_at_addition']

    def get_subtotal(self, obj):
        return obj.subtotal


class CartSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ['id', 'user', 'created_at', 'updated_at', 'items']
    
    def get_items(self, obj):
        items = []
        for item in obj.items.all():
            items.append({
                'id': item.id,
                'product': item.product.id,
                'quantity': item.quantity,
                'price': str(item.price_at_addition or item.product.price)
            })
        return items

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Add Item Example',
            value={
                'product_id': 42,
                'quantity': 2
            },
            request_only=True,
            description='Example request for adding an item to cart'
        )
    ]
)
class CartItemActionSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(default=1, min_value=1)

    def validate_product_id(self, value):
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError("Product does not exist")
        return value
