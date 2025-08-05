from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views
from .views import OrderViewSet

app_name = 'orders' 

# Traditional URLs
urlpatterns = [
    path('', views.OrderListView.as_view(), name='list'),
    path('create/', views.OrderCreateView.as_view(), name='create'),
    path('<int:pk>/', views.OrderDetailView.as_view(), name='detail'),
    path('<int:pk>/pay/', views.OrderPayView.as_view(), name='pay'),
    path('<int:pk>/cancel/', views.OrderCancelView.as_view(), name='cancel'),
    path('<int:pk>/track/', views.OrderTrackView.as_view(), name='track'),
    path('<int:pk>/invoice/', views.OrderInvoicePDFView.as_view(), name='invoice'),
]

# API URLs
router = DefaultRouter()
router.register(r'', OrderViewSet, basename='order') 

urlpatterns = router.urls