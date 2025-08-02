from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, ProductListAPIView, ProductDetailAPIView

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')

urlpatterns = [
    # Include all ViewSet URLs
    path('', include(router.urls)),
    
    # Additional custom API endpoints
    path('products/list/', ProductListAPIView.as_view(), name='product-list'),
    path('products/<slug:slug>/', ProductDetailAPIView.as_view(), name='product-detail'),
]