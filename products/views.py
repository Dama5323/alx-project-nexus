from django.shortcuts import render, get_object_or_404
from django.core.cache import cache
from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from django.db.models import Prefetch, Avg, Count
from django.contrib.admin.views.decorators import staff_member_required
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from .models import Product, Category, Review
from .serializers import ProductSerializer, CategorySerializer, ReviewSerializer
from .filters import ProductFilter

# ======================
# Template Views (HTML)
# ======================

@staff_member_required
def dashboard(request):
    """Admin product dashboard with key metrics"""
    context = {
        'product_count': Product.objects.count(),
        'category_count': Category.objects.count(),
        'recent_products': Product.objects.order_by('-created_at')[:5],
        'top_products': Product.objects.annotate(
            avg_rating=Avg('reviews__rating')
        ).order_by('-avg_rating')[:3]
    }
    return render(request, 'products/dashboard.html', context)

def product_list_view(request):
    """Product listing page with optimized queryset"""
    products = Product.objects.select_related('category').order_by('-created_at')
    return render(request, 'products/list.html', {
        'products': products,
        'categories': Category.objects.all()
    })

def product_detail_view(request, slug):
    """Product detail page with reviews"""
    product = get_object_or_404(
        Product.objects.prefetch_related(
            Prefetch('reviews', queryset=Review.objects.select_related('user'))
        ),
        slug=slug
    )
    return render(request, 'products/detail.html', {
        'product': product,
        'similar_products': Product.objects.filter(
            category=product.category
        ).exclude(id=product.id)[:4]
    })

def home_view(request):
    """Homepage with featured and recent products"""
    context = {
        'featured_products': Product.objects.filter(featured=True)[:4],
        'recent_products': Product.objects.order_by('-created_at')[:8],
        'top_rated': Product.objects.annotate(
            avg_rating=Avg('reviews__rating')
        ).order_by('-avg_rating')[:3]
    }
    return render(request, 'home.html', context)

# ==================
# API Views (JSON)
# ==================

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    last_page_strings = ('last',)

class IsOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners to edit their reviews"""
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user

class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint for products with:
    - Advanced filtering
    - Dual lookup (ID and slug)
    - Cached statistics
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    @extend_schema(
    parameters=[
        OpenApiParameter(
            name='category',
            type=str,
            description='Filter by category slug'
        ),
        OpenApiParameter(
            name='search',
            type=str,
            description='Search query'
        )
    ],
    examples=[
        OpenApiExample(
            'Filter Example',
            value={},
            description='Example: /products/?category=electronics&search=phone',
            parameter_only=('category', 'search')  # ← Changed to tuple
        )
    ]
)
    def list(self, request):
        return super().list(request)

    
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    pagination_class = StandardResultsSetPagination
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['price', 'created_at', 'name', 'stock', 'rating']
    ordering = ['-created_at']

    def get_permissions(self):
        """Dynamic permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        """Optimized queryset with related data"""
        return super().get_queryset().select_related(
            'category', 'created_by'
        ).prefetch_related(
            Prefetch('reviews', queryset=Review.objects.select_related('user'))
        ).annotate(
            rating=Avg('reviews__rating')
        )

    def get_object(self):
        """Support both slug and ID lookups"""
        if 'pk' in self.kwargs:
            return get_object_or_404(self.get_queryset(), pk=self.kwargs['pk'])
        return super().get_object()

    def perform_create(self, serializer):
        """Attach the creating user"""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def stats(self, request, slug=None):
        """Cached product statistics endpoint"""
        cache_key = f'product_stats_{slug}'
        stats = cache.get(cache_key)
        
        if not stats:
            product = self.get_object()
            stats = {
                'review_count': product.reviews.count(),
                'average_rating': product.reviews.aggregate(
                    avg=Avg('rating'))['avg'],
                'rating_distribution': product.reviews.values(
                    'rating').annotate(count=Count('id'))
            }
            cache.set(cache_key, stats, timeout=3600)  # Cache for 1 hour
        
        return Response(stats)

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for product categories"""
    queryset = Category.objects.annotate(
        product_count=Count('products')
    )
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'product_count']
    ordering = ['name']

class ReviewViewSet(viewsets.ModelViewSet):
    """API endpoint for product reviews with owner permissions"""
    serializer_class = ReviewSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    lookup_field = 'id'

    def get_queryset(self):
        """Reviews for a specific product with user details"""
        return Review.objects.filter(
            product__slug=self.kwargs['product_slug']
        ).select_related('user', 'product')

    def perform_create(self, serializer):
        """Set the product and author before saving"""
        product = get_object_or_404(Product, slug=self.kwargs['product_slug'])
        serializer.save(product=product, user=self.request.user)