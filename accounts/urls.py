from django.urls import path
from django.contrib.auth.views import LogoutView
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    login_view,
    register_view,
    logout_view,
    CustomTokenObtainPairView,
    RegisterAPIView,
    ProfileAPIView,
    api_root,
    UserDetailView,
)

urlpatterns = [
    # Template Views (for web browser access)
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    
    # API Views (for programmatic access)
    path('', api_root, name='api-root'),
    path('auth/register/', RegisterAPIView.as_view(), name='auth-register'),
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='auth-token'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='auth-token-refresh'),
    path('users/me/', UserDetailView.as_view(), name='user-detail'),
    path('users/profile/', ProfileAPIView.as_view(), name='user-profile'),
]