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
            cart, created = Cart.objects.get_or_create(
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
                cart_item.save()
            
        messages.success(request, f"Added {product.name} to your cart")
        return redirect('products:list')
    except Exception as e:
        messages.error(request, f"Error adding to cart: {str(e)}")
        return redirect('products:detail', product_id=product_id)


class CartViewSet(viewsets.ViewSet):
    """
    API endpoints for shopping cart operations.
    
    Requires authentication via JWT token.
    """
    permission_classes = [IsAuthenticated]
    
    def get_cart(self):
        """Get or create cart with select_related optimization"""
        cart, created = Cart.objects.get_or_create(
            user=self.request.user,
            defaults={'is_active': True}
        )
        return cart

    @extend_schema(
        summary="Get cart contents",
        description="Retrieves all items in the authenticated user's cart",
        responses={
            200: CartSerializer,
            401: "Unauthorized - Missing or invalid token"
        }
    )
    
    def list(self, request):
        cart = self.get_cart()
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Add item to cart",
        description="""
        Adds a product to the cart or updates quantity if already present.
        
        Example:
        ```json
        {
            "product_id": 42,
            "quantity": 2
          }
        ```
        """,
        request=CartItemActionSerializer,
        responses={
            200: CartSerializer,
            400: "Invalid product ID or quantity",
            401: "Unauthorized"
        }
    )


    @action(detail=False, methods=['get'], url_path='summary')
    def cart_summary(self, request):
        cart = self.get_cart()
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @extend_schema(
        request=CartItemActionSerializer,
        responses=CartSerializer,
        examples=[
            OpenApiExample(
                'Example Request',
                value={'product_id': 1, 'quantity': 2},
                request_only=True
            )
        ],
        description="Add item to cart with quantity validation"
    )
    @action(detail=False, methods=['post'], url_path='add-item')
    def add_item(self, request):
        serializer = CartItemActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            cart = self.get_cart()
            product_id = serializer.validated_data['product_id']
            quantity = serializer.validated_data['quantity']
            
            try:
                cart_item = CartItem.objects.select_for_update().get(
                    cart=cart,
                    product_id=product_id
                )
                cart_item.increase_quantity(quantity)
            except CartItem.DoesNotExist:
                try:
                    CartItem.objects.create(
                        cart=cart,
                        product_id=product_id,
                        quantity=quantity
                    )
                except Exception as e:
                    return Response(
                        {'detail': str(e)},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except ValidationError as e:
                return Response(
                    {'detail': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response(
                CartSerializer(cart).data,
                status=status.HTTP_200_OK
            )

    @extend_schema(
        request=CartItemActionSerializer,
        responses=CartSerializer,
        description="Remove item from cart or reduce quantity"
    )
    @action(detail=False, methods=['post'], url_path='remove-item')
    def remove_item(self, request):
        serializer = CartItemActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            cart = self.get_cart()
            product_id = serializer.validated_data['product_id']
            quantity = serializer.validated_data['quantity']
            
            try:
                cart_item = CartItem.objects.select_for_update().get(
                    cart=cart,
                    product_id=product_id
                )
                
                if cart_item.quantity <= quantity:
                    cart_item.delete()
                else:
                    cart_item.decrease_quantity(quantity)
                    
            except (CartItem.DoesNotExist, ValidationError) as e:
                return Response(
                    {'detail': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response(
                CartSerializer(cart).data,
                status=status.HTTP_200_OK
            )

    @extend_schema(
        responses=CartSerializer,
        description="Completely empty the cart"
    )
    @action(detail=False, methods=['delete'], url_path='clear')
    def clear_cart(self, request):
        cart = self.get_cart()
        cart.clear()
        return Response(
            CartSerializer(cart).data,
            status=status.HTTP_200_OK
        )
    

