from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from .models import Product, Category, Review
from .serializers import ProductSerializer, CategorySerializer, ReviewSerializer
from .filters import ProductFilter
from django.db.models import Prefetch


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    last_page_strings = ('last',)

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user

class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows products to be viewed or edited.
    """
    serializer_class = ProductSerializer
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    pagination_class = StandardResultsSetPagination
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['price', 'created_at', 'name', 'stock']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        # Optimized queryset with select_related and prefetch_related
        return Product.objects.select_related(
            'category',
            'created_by'
        ).prefetch_related(
            Prefetch('reviews', queryset=Review.objects.select_related('user'))
        ).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def stats(self, request, slug=None):
        """Get statistics for a product"""
        product = self.get_object()
        return Response({
            'review_count': product.reviews.count(),
            'average_rating': product.reviews.aggregate(
                avg_rating=models.Avg('rating')
            )['avg_rating'],
        })

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows categories to be viewed.
    """
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        return Category.objects.only(
            'name', 'slug', 'description'
        ).order_by('name')

class ReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows reviews to be viewed or edited.
    """
    serializer_class = ReviewSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    lookup_field = 'id'

    def get_queryset(self):
        return Review.objects.select_related(
            'user',
            'product'
        ).filter(
            product__slug=self.kwargs['product_slug']
        ).only(
            'rating', 'comment', 'created_at',
            'user__email', 'product__name'
        ).order_by('-created_at')

    def perform_create(self, serializer):
        product = get_object_or_404(Product.objects.only('id'), 
                                 slug=self.kwargs['product_slug'])
        serializer.save(product=product, user=self.request.user)