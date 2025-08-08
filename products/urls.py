from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductViewSet, 
    CategoryViewSet, 
    ReviewViewSet,
    product_list_view,
    product_detail_view,
    home_view,
)

app_name = 'products'

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(
    r'products/(?P<product_slug>[^/.]+)/reviews',
    ReviewViewSet,
    basename='product-reviews'
)

urlpatterns = [
    # HTML interface
    path('', home_view, name='home'),
    path('products/', product_list_view, name='list'),
    path('products/<slug:slug>/', product_detail_view, name='detail'),
    
    # API endpoints
    path('', include((router.urls, 'products-api'))),
    
    # Additional ID-based product endpoint
    path('products/by-id/<int:pk>/', 
         ProductViewSet.as_view({'get': 'retrieve'}), 
         name='product-by-id'),
]