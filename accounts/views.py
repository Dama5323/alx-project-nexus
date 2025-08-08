from django.contrib.auth import login as auth_login, logout as auth_logout
from django.shortcuts import render, redirect
from django.urls import reverse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import RegisterSerializer, UserSerializer, CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import api_view

# Template Views
def login_view(request):
    if request.method == 'POST':
        # Add your login logic here
        return redirect('home')
    return render(request, 'accounts/login.html')

def logout_view(request):
    auth_logout(request)
    return redirect('login')

def register_view(request):
    if request.method == 'POST':
        # Add your registration logic here
        return redirect('login')
    return render(request, 'accounts/register.html')

# API Views
# accounts/views.py
class RegisterAPIView(APIView):  # Changed from RegisterView to RegisterAPIView
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Register a new user account",
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response("User created", UserSerializer),
            400: "Invalid data"
        },
        tags=['Authentication']
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )
        

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
    @swagger_auto_schema(
        operation_description="Obtain JWT token pair",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={
            200: openapi.Response(
                description="Tokens",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                    },
                )
            ),
            401: "Invalid credentials"
        },
        tags=['Authentication']
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get current user details",
        responses={
            200: UserSerializer,
            401: "Unauthorized"
        },
        tags=['Users']
    )
    def get(self, request):
        return Response(UserSerializer(request.user).data)
    
# accounts/views.py
class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get or update user profile",
        responses={
            200: UserSerializer,
            401: "Unauthorized"
        },
        tags=['Users']
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Update user profile",
        request_body=UserSerializer,
        responses={
            200: UserSerializer,
            400: "Bad request",
            401: "Unauthorized"
        },
        tags=['Users']
    )
    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    

@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'register': reverse('auth-register', request=request, format=format),
        'token-obtain': reverse('auth-token', request=request, format=format),
        'token-refresh': reverse('auth-token-refresh', request=request, format=format),
        'user-detail': reverse('user-detail', request=request, format=format),
    })