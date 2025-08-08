from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    OrderListView,
    OrderCreateView,
    OrderDetailView,
    OrderPayView,
    OrderCancelView,
    OrderTrackView,
    OrderInvoicePDFView,  
    AddOrderItemView,
    OrderViewSet,
    StatusTransitionView
)

app_name = 'orders'

# Traditional Django URLs
traditional_urlpatterns = [
    path('', OrderListView.as_view(), name='list'),
    path('create/', OrderCreateView.as_view(), name='create'),
    path('<int:pk>/', OrderDetailView.as_view(), name='detail'),
    path('<int:order_id>/add-item/', AddOrderItemView.as_view(), name='add-item'),
    path('<int:pk>/pay/', OrderPayView.as_view(), name='pay'),
    path('<int:pk>/cancel/', OrderCancelView.as_view(), name='cancel'),
    path('<int:pk>/track/', OrderTrackView.as_view(), name='track'),
    path('<int:pk>/invoice/', OrderInvoicePDFView.as_view(), name='invoice'),
    path('orders/<int:pk>/transitions/', StatusTransitionView.as_view(), name='order-status-transitions'),
    

]

# DRF API URLs
router = DefaultRouter()
router.register(r'', OrderViewSet, basename='order')

# Combine both URL patterns
urlpatterns = traditional_urlpatterns + router.urls