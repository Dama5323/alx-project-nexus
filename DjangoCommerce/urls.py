from django.contrib import admin
from django.urls import path, include, re_path
from django.contrib.auth import views as auth_views
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.routers import DefaultRouter
from products.views import home_view

# Initialize router
router = DefaultRouter()

# Schema View for Swagger/OpenAPI
schema_view = get_schema_view(
    openapi.Info(
        title="DjangoCommerce API",
        default_version='v1',
        description="API documentation for DjangoCommerce",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Home page
    path('', home_view, name='home'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # Template views (non-API)
    path('accounts/', include('accounts.urls')),  # For template views
    
    # API Endpoints
    path('api/', include([
        # API version of accounts (for DRF)
        path('accounts/', include('accounts.urls')),
        path('products/', include('products.urls')),
        path('cart/', include('cart.urls')),
        path('orders/', include('orders.urls')),
    ])),
    
    # DRF authentication URLs (important for Swagger)
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    
    # Password reset URLs
    path('password-reset/', 
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset.html',
            email_template_name='accounts/password_reset_email.html',
            subject_template_name='accounts/password_reset_subject.txt'
        ), 
        name='password_reset'),
    path('password-reset/done/', 
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html'
        ), 
        name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html'
        ), 
        name='password_reset_confirm'),
    path('password-reset-complete/', 
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html'
        ), 
        name='password_reset_complete'),
    
    # Documentation URLs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', 
        schema_view.without_ui(cache_timeout=0), 
        name='schema-json'),
    path('swagger/', 
        schema_view.with_ui('swagger', cache_timeout=0), 
        name='schema-swagger-ui'),
    path('redoc/', 
        schema_view.with_ui('redoc', cache_timeout=0), 
        name='schema-redoc'),
]