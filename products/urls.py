from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductViewSet, 
    CategoryViewSet,
    product_detail,
    product_create,
    product_update,
    product_delete
)

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'categories', CategoryViewSet)

urlpatterns = [
    # API URLs
    path('api/', include(router.urls)),
    
    # Template URLs
    path('products/<int:pk>/', product_detail, name='product-detail'),
    path('products/create/', product_create, name='product-create'),
    path('products/<int:pk>/update/', product_update, name='product-update'),
    path('products/<int:pk>/delete/', product_delete, name='product-delete'),
]