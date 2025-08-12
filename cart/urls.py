from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartViewSet
from drf_spectacular.views import SpectacularSwaggerView

app_name = 'cart'

# API Router Configuration
router = DefaultRouter()
router.register(r'', CartViewSet, basename='cart')



urlpatterns = [
    # Include all router-generated URLs first
    path('', include(router.urls)),
    
    # Custom action endpoints
    path('add/<int:product_id>/', CartViewSet.as_view({'post': 'add_item'}), name='add-item'),
    path('add-item/', CartViewSet.as_view({'post': 'add_item'}), name='add-item'),
    path('remove-item/', CartViewSet.as_view({'post': 'remove_item'}), name='remove-item'),
    path('clear/', CartViewSet.as_view({'delete': 'clear_cart'}), name='clear'),
    path('summary/', CartViewSet.as_view({'get': 'cart_summary'}), name='summary'),

      
    
    # swagger documentation
    path('api/docs/cart/', SpectacularSwaggerView.as_view(
        url_name='schema',
        template_name='swagger_ui.html',
        title="Cart API Documentation"
    ), name='cart-docs'),
]