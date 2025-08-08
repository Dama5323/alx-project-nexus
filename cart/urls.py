from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartViewSet, cart_detail  
from drf_spectacular.views import SpectacularSwaggerView

app_name = 'cart'

# API Router Configuration
router = DefaultRouter()
router.register(r'', CartViewSet, basename='cart')  

urlpatterns = [
    # Web interface routes
    path('', cart_detail, name='detail'),  
    
    # API routes 
    path('', include(router.urls)), 
    
    # Action endpoints
    path('add/<int:product_id>/', CartViewSet.as_view({'post': 'add_item'}), name='add'),
    path('api/add-item/', CartViewSet.as_view({'post': 'add_item'}), name='api-add-item'),
    path('api/remove-item/', CartViewSet.as_view({'post': 'remove_item'}), name='api-remove-item'),
    path('api/clear/', CartViewSet.as_view({'delete': 'clear_cart'}), name='api-clear'),
    path('api/summary/', CartViewSet.as_view({'get': 'cart_summary'}), name='api-summary'),

    # Custom docs view
    path('api/docs/cart/', SpectacularSwaggerView.as_view(
        url_name='schema',
        template_name='swagger_ui.html',
        title="Cart API Documentation"
    ), name='cart-docs'),
]

