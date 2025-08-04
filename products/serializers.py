from rest_framework import serializers
from .models import Product, Category, Review
from django.contrib.auth import get_user_model

User = get_user_model()

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description']


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    
    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'comment', 'created_at']
        read_only_fields = ['user', 'created_at']


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False
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
            'image': {'required': False}
        }