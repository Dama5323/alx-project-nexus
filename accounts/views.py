from django.contrib.auth import get_user_model, login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import UserSerializer, CustomTokenObtainPairSerializer, RegisterSerializer
from django.contrib.auth import login, authenticate
from .forms import CustomUserCreationForm, CustomAuthenticationForm

User = get_user_model()

# Template Views
def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


def logout_view(request):
    """Handle traditional Django template logout"""
    logout(request)
    return redirect('home')

# API Views
class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token obtain view with additional user data"""
    serializer_class = CustomTokenObtainPairSerializer

class RegisterAPIView(generics.CreateAPIView):
    """API endpoint for user registration"""
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

class ProfileAPIView(generics.RetrieveUpdateAPIView):
    """API endpoint for user profile"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_queryset(self):
        return User.objects.none()  # Required for DRF but not used

@api_view(['GET'])
def api_root(request):
    """API root endpoint with URL listings"""
    return Response({
        'register': request.build_absolute_uri('register/'),
        'login': request.build_absolute_uri('login/'),
        'token_obtain': request.build_absolute_uri('token/'),
        'token_refresh': request.build_absolute_uri('token/refresh/'),
        'profile': request.build_absolute_uri('profile/'),
    })