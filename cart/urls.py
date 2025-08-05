from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartViewSet, cart_view

app_name = 'cart' 

router = DefaultRouter()
router.register(r'api', CartViewSet, basename='cart-api')  

urlpatterns = [
    path('api/', include(router.urls)),  # API routes
    path('', cart_view, name='view'),   # Regular view
]