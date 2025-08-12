from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from products.serializers import ProductSerializer
from .models import Cart, CartItem
from django.db.models import Sum


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
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_items', 'total_price', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_total_items(self, obj):
        return obj.items.aggregate(total=Sum('quantity'))['total'] or 0

    def get_total_price(self, obj):
        return obj.total

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
    product_id = serializers.IntegerField(
        help_text="ID of the product to add/remove"
    )
    quantity = serializers.IntegerField(
        help_text="Number of items to add/remove",
        min_value=1
    )

    def validate_product_id(self, value):
        from products.models import Product
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Product does not exist")
        return value
