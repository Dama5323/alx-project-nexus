from django.shortcuts import render, get_object_or_404, redirect
from django.core.cache import cache
from django.db.models import Prefetch, Avg, Count, Q
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import cache_page
from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
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
        'product_count': cache.get_or_set(
            'product_count', 
            Product.objects.count(), 
            3600
        ),
        'category_count': cache.get_or_set(
            'category_count',
            Category.objects.count(),
            3600
        ),
        'recent_products': Product.objects.order_by('-created_at')[:5],
        'top_products': Product.objects.annotate(
            avg_rating=Avg('reviews__rating')
        ).filter(avg_rating__isnull=False).order_by('-avg_rating')[:3]
    }
    return render(request, 'products/dashboard.html', context)

def product_list_view(request):
    """Optimized product listing with category filtering"""
    category_slug = request.GET.get('category')
    search_query = request.GET.get('q', '')
    
    products = Product.objects.select_related('category').order_by('-created_at')
    
    if category_slug:
        products = products.filter(category__slug=category_slug)
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    return render(request, 'products/list.html', {
        'products': products,
        'categories': Category.objects.all(),
        'current_category': category_slug,
        'search_query': search_query
    })

def product_detail_view(request, slug=None, pk=None):
    """
    Product detail page supporting both slug and ID lookups
    with related products and reviews
    """
    if pk:
        product = get_object_or_404(
            Product.objects.select_related('category'),
            pk=pk
        )
    else:
        product = get_object_or_404(
            Product.objects.select_related('category'),
            slug=slug
        )
    
    reviews = product.reviews.select_related('user')[:5]
    similar_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id)[:4]
    
    return render(request, 'products/detail.html', {
        'product': product,
        'reviews': reviews,
        'similar_products': similar_products,
        'average_rating': product.reviews.aggregate(
            avg_rating=Avg('rating')
        )['avg_rating']
    })

@cache_page(60 * 15)  # Cache for 15 minutes
def home_view(request):
    """Optimized homepage with cached queries"""
    context = {
        'featured_products': Product.objects.filter(
            featured=True
        ).select_related('category')[:4],
        'recent_products': Product.objects.order_by('-created_at')[
            :8
        ].select_related('category'),
        'top_rated': Product.objects.annotate(
            avg_rating=Avg('reviews__rating')
        ).filter(
            avg_rating__isnull=False
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
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user

class ProductViewSet(viewsets.ModelViewSet):
    """
    Enhanced Product API with:
    - Dual lookup (ID/slug)
    - Advanced filtering
    - Optimized queries
    - Cached statistics
    """
    serializer_class = ProductSerializer
    lookup_field = 'slug'
    filter_backends = [
        DjangoFilterBackend, 
        filters.SearchFilter, 
        filters.OrderingFilter
    ]
    filterset_class = ProductFilter
    pagination_class = StandardResultsSetPagination
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = [
        'price', 'created_at', 'name', 'stock', 'rating'
    ]
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        return Product.objects.annotate(
            rating=Avg('reviews__rating')
        ).select_related(
            'category', 'created_by'
        ).prefetch_related(
            Prefetch(
                'reviews',
                queryset=Review.objects.select_related('user')
            )
        )

    def get_object(self):
        if 'pk' in self.kwargs:
            return get_object_or_404(self.get_queryset(), pk=self.kwargs['pk'])
        return super().get_object()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

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
                description='Example: /products/?category=electronics&search=phone'
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def stats(self, request, slug=None):
        cache_key = f'product_stats_{slug}'
        stats = cache.get(cache_key)
        
        if not stats:
            product = self.get_object()
            stats = {
                'review_count': product.reviews.count(),
                'average_rating': product.reviews.aggregate(
                    avg=Avg('rating'))['avg'] or 0,
                'rating_distribution': product.reviews.values(
                    'rating').annotate(count=Count('id'))
            }
            cache.set(cache_key, stats, timeout=3600)
        
        return Response(stats)

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.annotate(
        product_count=Count('products')
    ).prefetch_related(
        Prefetch(
            'products',
            queryset=Product.objects.annotate(
                avg_rating=Avg('reviews__rating')
            )
        )
    )
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'product_count']
    ordering = ['name']

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly, 
        IsOwnerOrReadOnly
    ]

    def get_queryset(self):
        return Review.objects.filter(
            product__slug=self.kwargs['product_slug']
        ).select_related('user', 'product')

    def perform_create(self, serializer):
        product = get_object_or_404(
            Product, 
            slug=self.kwargs['product_slug']
        )
        serializer.save(
            product=product, 
            user=self.request.user
        )