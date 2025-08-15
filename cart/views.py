from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiExample
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, get_object_or_404, render
from .models import Cart, CartItem
from products.models import Product
from .serializers import CartSerializer, CartItemActionSerializer
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages


def cart_detail(request):
    cart = get_object_or_404(Cart, user=request.user)
    return render(request, 'cart/detail.html', {'cart': cart})


@login_required
@require_POST
def add_to_cart(request, product_id):
    """Traditional form-based view for adding to cart"""
    try:
        quantity = int(request.POST.get('quantity', 1))
        product = get_object_or_404(Product, id=product_id)
        
        with transaction.atomic():
            cart, _ = Cart.objects.get_or_create(
                user=request.user,
                defaults={'is_active': True}
            )
            
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.save(update_fields=['quantity'])
            
        messages.success(request, f"Added {product.name} to your cart")
        return redirect('products:list')
    except Exception as e:
        messages.error(request, f"Error adding to cart: {str(e)}")
        return redirect('products:detail', product_id=product_id)


class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_cart(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart

    def list(self, request):
        """Handles GET /cart/summary/"""
        cart = self.get_cart()
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @extend_schema(
        request=CartItemActionSerializer,
        examples=[
            OpenApiExample(
                'Example request',
                value={'product_id': 1, 'quantity': 2},
                request_only=True
            )
        ]
    )
    @action(detail=False, methods=['post'], url_path='add-item')
    def add_item(self, request):
        serializer = CartItemActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            product = Product.objects.get(id=serializer.validated_data['product_id'])
            quantity = serializer.validated_data.get('quantity', 1)
            
            with transaction.atomic():
                cart = self.get_cart()
                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    product=product,
                    defaults={'quantity': quantity}
                )
                
                if not created:
                    cart_item.quantity += quantity
                    cart_item.save()
                
                serializer = CartSerializer(cart)
                return Response(serializer.data, status=status.HTTP_200_OK)
                
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        request=CartItemActionSerializer,
        examples=[
            OpenApiExample(
                'Example request',
                value={'product_id': 1, 'quantity': 1},
                request_only=True
            )
        ]
    )
    @action(detail=False, methods=['post'], url_path='remove-item')
    def remove_item(self, request):
        serializer = CartItemActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            product = Product.objects.get(id=serializer.validated_data['product_id'])
            quantity = serializer.validated_data.get('quantity', 1)
            
            with transaction.atomic():
                cart = self.get_cart()
                try:
                    cart_item = CartItem.objects.get(cart=cart, product=product)
                    if cart_item.quantity > quantity:
                        cart_item.quantity -= quantity
                        cart_item.save()
                    else:
                        cart_item.delete()
                        
                    serializer = CartSerializer(cart)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                    
                except CartItem.DoesNotExist:
                    return Response(
                        {'error': 'Item not in cart'}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
                    
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['delete'], url_path='clear')
    def clear_cart(self, request):
        with transaction.atomic():
            cart = self.get_cart()
            cart.items.all().delete()
            return Response(
                {'message': 'Cart cleared successfully', 'items': []},
                status=status.HTTP_200_OK
            )