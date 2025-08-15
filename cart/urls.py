from django.urls import path
from .views import CartViewSet
from drf_spectacular.views import SpectacularSwaggerView

app_name = 'cart'

urlpatterns = [
    path('add-item', CartViewSet.as_view({'post': 'add_item'}), name='cart-add-item'),
    path('remove-item', CartViewSet.as_view({'post': 'remove_item'}), name='remove-item'),
    path('clear', CartViewSet.as_view({'delete': 'clear_cart'}), name='clear'),
    path('summary', CartViewSet.as_view({'get': 'list'}), name='summary'),

    # Swagger documentation
    path(
        'api/docs/cart/',
        SpectacularSwaggerView.as_view(
            url_name='schema',
            template_name='swagger_ui.html',
            title="Cart API Documentation"
        ),
        name='cart-docs'
    ),
]
