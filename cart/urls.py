from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views  

app_name = 'cart' 

router = DefaultRouter()
router.register(r'cart', views.CartViewSet, basename='cart')  

urlpatterns = [
    # Web Interface URLs
    path('', views.cart_detail, name='detail'), 
    path('add/<int:product_id>/', views.add_to_cart, name='add'),
    
    # API Endpoints (via ViewSet)
    path('', include(router.urls)),
]