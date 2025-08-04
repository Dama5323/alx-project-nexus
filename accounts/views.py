from django.contrib.auth import get_user_model
from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import UserSerializer, CustomTokenObtainPairSerializer
from rest_framework.permissions import AllowAny
from .serializers import RegisterSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.views import APIView
from drf_yasg import openapi


# Get the custom user model
User = get_user_model()

@api_view(['GET'])
def auth_root(request):
    return Response({
        'register': request.build_absolute_uri('register/'),
        'token_obtain': request.build_absolute_uri('token/'),
        'token_refresh': request.build_absolute_uri('token/refresh/'),
        'login': request.build_absolute_uri('login/'),
        'logout': request.build_absolute_uri('logout/'),
    })

class RegisterView(generics.CreateAPIView):
    """
    View for user registration.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token obtain view that includes additional user data in the response.
    """
    serializer_class = CustomTokenObtainPairSerializer

class ProfileView(generics.RetrieveUpdateAPIView):
    """
    View to retrieve and update user profile.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """
        Returns the user object associated with the request.
        """
        return self.request.user
    
    def get_queryset(self):
        """
        Explicitly define queryset for better IDE support.
        """
        return User.objects.all()
    

class UserRegistrationView(APIView):
    @swagger_auto_schema(
        operation_description="Register a new user account",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password', 'password2'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format='password'),
                'password2': openapi.Schema(type=openapi.TYPE_STRING, format='password'),
            },
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="User created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'email': openapi.Schema(type=openapi.TYPE_STRING),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            status.HTTP_400_BAD_REQUEST: "Invalid input data",
        }
    )
    def post(self, request):
        # registration logic here
        pass