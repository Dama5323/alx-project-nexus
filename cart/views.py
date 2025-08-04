from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from products.models import Product
from .models import Cart, CartItem
from .serializers import CartSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404

class CartViewSet(viewsets.ModelViewSet):
    """
    API endpoint for cart operations
    """
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete']  # Limit available methods

    def get_queryset(self):
        """Always return the current user's cart"""
        return Cart.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Get current user's cart",
        responses={
            200: CartSerializer,
            401: "Unauthorized"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """Get or create cart for the current user"""
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Add item to cart",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['product_id'],
            properties={
                'product_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Product ID"),
                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, default=1, description="Quantity to add")
            }
        ),
        responses={
            201: openapi.Response('Item added', CartSerializer),
            400: "Invalid input",
            404: "Product not found"
        }
    )
    @action(detail=True, methods=['post'], url_path='add-item')
    def add_item(self, request, pk=None):
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        
        product = get_object_or_404(Product, id=product_id)
        cart = self.get_object()  # Gets the user's cart
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        serializer = self.get_serializer(cart)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Remove item from cart",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['product_id'],
            properties={
                'product_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Product ID to remove"),
                'remove_all': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False, 
                                           description="Remove all quantities if True")
            }
        ),
        responses={
            200: openapi.Response('Item removed', CartSerializer),
            404: "Product not found in cart"
        }
    )
    @action(detail=True, methods=['post'], url_path='remove-item')
    def remove_item(self, request, pk=None):
        product_id = request.data.get('product_id')
        remove_all = request.data.get('remove_all', False)
        product = get_object_or_404(Product, id=product_id)
        cart = self.get_object()
        
        try:
            cart_item = CartItem.objects.get(cart=cart, product=product)
            if remove_all or cart_item.quantity <= 1:
                cart_item.delete()
            else:
                cart_item.quantity -= 1
                cart_item.save()
                
            serializer = self.get_serializer(cart)
            return Response(serializer.data)
            
        except CartItem.DoesNotExist:
            return Response(
                {"detail": "Product not found in cart"}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @swagger_auto_schema(
        operation_description="Clear entire cart",
        responses={
            204: "Cart cleared successfully",
            401: "Unauthorized"
        }
    )
    @action(detail=True, methods=['delete'], url_path='clear')
    def clear_cart(self, request, pk=None):
        """Remove all items from cart"""
        cart = self.get_object()
        cart.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)