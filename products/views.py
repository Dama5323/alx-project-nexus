from django.shortcuts import render
from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets
from .models import Product
from .serializers import ProductSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly

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