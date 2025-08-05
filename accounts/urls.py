from django.urls import path, include
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
)

urlpatterns = [
    # Template Views
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    
    # API Views
    path('api/', include([
        path('', api_root, name='api-root'),
        path('register/', RegisterAPIView.as_view(), name='register'),
        path('token/', CustomTokenObtainPairView.as_view(), name='token-obtain'),
        path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
        path('profile/', ProfileAPIView.as_view(), name='profile'),
    ])),
]