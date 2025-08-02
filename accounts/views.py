from django.contrib.auth import get_user_model
from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import UserSerializer, CustomTokenObtainPairSerializer

# Get the custom user model
User = get_user_model()

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