from django.shortcuts import render
from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets
from .models import Product
from .serializers import ProductSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, filters
from rest_framework.pagination import PageNumberPagination


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

@login_required
@permission_required('products.can_view_product', raise_exception=True)
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'products/detail.html', {'product': product})

@permission_required('products.can_create_product', raise_exception=True)
def product_create(request):
    # Product creation logic
    pass

@permission_required('products.can_edit_product', raise_exception=True)
def product_update(request, pk):
    # Product update logic
    pass

@permission_required('products.can_delete_product', raise_exception=True)
def product_delete(request, pk):
    # Product deletion logic
    pass


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class ProductListAPIView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    pagination_class = StandardResultsSetPagination
    
    filterset_fields = {
        'category': ['exact'],
        'price': ['gte', 'lte', 'exact'],
        'available': ['exact'],
    }
    
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']

class ProductDetailAPIView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'slug'

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category__name', 'price', 'stock']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']
