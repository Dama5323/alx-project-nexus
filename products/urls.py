from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductViewSet, 
    CategoryViewSet, 
    ReviewViewSet,
    ProductListView  
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
    path('', ProductListView.as_view(), name='list'),
    
    # API endpoints
    path('api/', include(router.urls)),
]