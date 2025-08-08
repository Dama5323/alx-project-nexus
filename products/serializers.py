from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, extend_schema_field, OpenApiExample
from .models import Product, Category, Review
from django.contrib.auth import get_user_model

User = get_user_model()

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Category Example',
            value={
                'id': 1,
                'name': 'Electronics',
                'slug': 'electronics',
                'description': 'All electronic devices'
            },
            response_only=True
        )
    ]
)
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description']
        read_only_fields = ['slug']

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Review Example',
            value={
                'id': 1,
                'rating': 5,
                'comment': 'Excellent product!',
                'created_at': '2023-01-01T12:00:00Z'
            },
            response_only=True
        )
    ]
)
class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    
    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'comment', 'created_at']
        read_only_fields = ['user', 'created_at']

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Product Create Example',
            value={
                'name': 'Smartphone X',
                'description': 'Latest smartphone model',
                'price': 999.99,
                'category_id': 1,
                'stock': 100,
                'available': True
            },
            request_only=True
        ),
        OpenApiExample(
            'Product Response Example',
            value={
                'id': 1,
                'name': 'Smartphone X',
                'description': 'Latest smartphone model',
                'price': '999.99',
                'category': {
                    'id': 1,
                    'name': 'Electronics',
                    'slug': 'electronics'
                },
                'stock': 100,
                'available': True,
                'created_by': 'admin',
                'created_at': '2023-01-01T12:00:00Z',
                'image': '/media/products/smartphone_x.jpg',
                'slug': 'smartphone-x',
                'reviews': []
            },
            response_only=True
        )
    ]
)
class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False,
        help_text="ID of the product category"
    )
    reviews = ReviewSerializer(many=True, read_only=True)
    created_by = serializers.StringRelatedField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'category', 'category_id',
            'stock', 'available', 'created_by', 'created_at', 'updated_at',
            'image', 'slug', 'reviews'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'slug']
        extra_kwargs = {
            'image': {
                'required': False,
                'help_text': "Product image file upload"
            },
            'price': {
                'help_text': "Product price in decimal format (e.g. 19.99)"
            },
            'stock': {
                'help_text': "Available quantity in inventory",
                'min_value': 0
            }
        }

    @extend_schema_field(serializers.CharField())
    def get_created_by(self, obj):
        return str(obj.created_by)