from django.urls import path, include
from django.contrib.auth.views import LogoutView
from django.views.generic.base import RedirectView  
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
from accounts.views import (
    login_view,
    register_view,
    logout_view,
    AuthTokenObtainPairView,
    AuthRegisterAPIView,
    AccountDetailAPIView,
    AccountProfileAPIView,
    AccountViewSet,
    api_root
)

router = DefaultRouter()
router.register(r'accounts', AccountViewSet, basename='accounts')

urlpatterns = [
    # Template Views (for web browser access)
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    
    # API Views (for programmatic access)
    path('', api_root, name='api-root'),
    
    # Authentication Endpoints
    path('auth/register/', AuthRegisterAPIView.as_view(), name='auth-register'),
    path('auth/token/', AuthTokenObtainPairView.as_view(), name='auth-token'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='auth-token-refresh'),
    
    # Account Endpoints (consistent naming)
    path('accounts/me/', AccountDetailAPIView.as_view(), name='account-detail'),
    path('accounts/profile/', AccountProfileAPIView.as_view(), name='account-profile'),
    
    # Include DRF router URLs
    path('api/', include(router.urls)),
    
    # Redirect for old /users/ endpoints (temporary)
    path('users/', include([
        path('', RedirectView.as_view(url='/accounts/'), name='users-redirect'),
        path('me/', RedirectView.as_view(url='/accounts/me/'), name='users-me-redirect'),
        path('profile/', RedirectView.as_view(url='/accounts/profile/'), name='users-profile-redirect'),
    ])),
]