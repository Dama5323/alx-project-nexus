from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.cache import cache
from drf_spectacular.extensions import OpenApiAuthenticationExtension

class CachedJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user_id = validated_token.get('user_id')
        cache_key = f'jwt_user_{user_id}'
        user = cache.get(cache_key)
        
        if user is None:
            user = super().get_user(validated_token)
            cache.set(cache_key, user, timeout=300)  # Cache for 5 minutes
        
        return user
    

class CachedJWTAuthScheme(OpenApiAuthenticationExtension):
    target_class = 'products.authentication.CachedJWTAuthentication'
    name = 'JWT Auth'
    
    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT'
        }