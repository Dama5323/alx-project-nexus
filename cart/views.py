from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiExample
from django.shortcuts import redirect, get_object_or_404, render
from .models import Cart, CartItem
from products.models import Product
from .serializers import CartSerializer, CartItemActionSerializer
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)

class CartViewSet(viewsets.ViewSet):
    """
    API endpoints for cart operations
    """
    permission_classes = [IsAuthenticated]

    def get_cart(self):
        """Get or create cart for the current user"""
        cart, created = Cart.objects.get_or_create(
            user=self.request.user,
            defaults={'is_active': True}
        )
        logger.debug(f"Cart {'created' if created else 'retrieved'}: {cart.id}")
        return cart

    def list(self, request):
        """Get cart summary"""
        cart = self.get_cart()
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    @extend_schema(
        request=CartItemActionSerializer,
        responses={200: CartSerializer},
        examples=[OpenApiExample('Example', value={'product_id': 1, 'quantity': 2})]
    )
    @action(detail=False, methods=['post'], url_path='add-item')
    def add_item(self, request):
        """Add item to cart with proper validation"""
        serializer = CartItemActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            product = Product.objects.get(id=serializer.validated_data['product_id'])
            quantity = serializer.validated_data.get('quantity', 1)
            
            if quantity > product.stock:
                return Response(
                    {'error': 'Not enough stock available'},  # Changed to match test
                    status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Check stock before attempting to add
            if quantity > product.stock:
                return Response(
                    {'error': f'Only {product.stock} items available'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            with transaction.atomic():
                cart = self.get_cart()
                try:
                    cart_item = CartItem.objects.get(cart=cart, product=product)
                    new_quantity = cart_item.quantity + quantity
                    if new_quantity > product.stock:
                        return Response(
                            {'error': f'Only {product.stock - cart_item.quantity} more available'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    cart_item.quantity = new_quantity
                    cart_item.save()
                except CartItem.DoesNotExist:
                    CartItem.objects.create(
                        cart=cart,
                        product=product,
                        quantity=quantity
                    )
                
                return Response(
                    CartSerializer(cart, context={'request': request}).data,
                    status=status.HTTP_200_OK
                )
                
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        request=CartItemActionSerializer,
        responses={200: CartSerializer},
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
        """Remove item from cart or reduce quantity"""
        serializer = CartItemActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            product = Product.objects.get(id=serializer.validated_data['product_id'])
            quantity = serializer.validated_data.get('quantity', 1)
            
            if quantity <= 0:
                return Response(
                    {'error': 'Quantity must be positive'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            with transaction.atomic():
                cart = self.get_cart()
                try:
                    cart_item = CartItem.objects.get(cart=cart, product=product)
                    if cart_item.quantity > quantity:
                        cart_item.quantity -= quantity
                        cart_item.save()
                    else:
                        cart_item.delete()
                        
                    return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)
                    
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

    @extend_schema(
        responses={
            200: OpenApiExample(
                'Success response',
                value={'message': 'Cart cleared successfully', 'items': []}
            )
        }
    )
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """Clear all items from the cart"""
        with transaction.atomic():
            cart = self.get_cart()
            cart.items.all().delete()
            return Response(
                {'message': 'Cart cleared successfully', 'items': []},
                status=status.HTTP_200_OK
            )

# HTML Views
@login_required
def cart_detail(request):
    """Render cart page with debug information"""
    try:
        cart = Cart.objects.select_related('user')\
                          .prefetch_related('items__product')\
                          .get(user=request.user)
        logger.debug(f"Rendering cart for user {request.user.id}")
        return render(request, 'cart/detail.html', {
            'cart': cart,
            'debug': True  
        })
    except Cart.DoesNotExist:
        logger.info(f"Creating new cart for user {request.user.id}")
        cart = Cart.objects.create(user=request.user)
        return render(request, 'cart/detail.html', {'cart': cart})

@login_required
@require_POST
def add_to_cart(request, product_id):
    """Add item to cart from web interface"""
    try:
        quantity = int(request.POST.get('quantity', 1))
        product = get_object_or_404(Product, id=product_id)
        
        with transaction.atomic():
            cart, _ = Cart.objects.get_or_create(user=request.user)
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            
        messages.success(request, f"Added {product.name} to cart")
        return redirect('cart:detail')
        
    except Exception as e:
        messages.error(request, f"Error adding to cart: {str(e)}")
        return redirect('products:detail', slug=product.slug)