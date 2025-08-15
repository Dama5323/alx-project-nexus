from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.cache import cache
from drf_spectacular.extensions import OpenApiAuthenticationExtension


class CachedJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if auth_header:
            # Cache key based on the token
            cache_key = f'auth_{auth_header}'
            user = cache.get(cache_key)
            
            if user is None:
                user = super().authenticate(request)
                if user:
                    cache.set(cache_key, user, timeout=300)  # Cache for 5 minutes
            return user
        return None
    

class CachedJWTAuthScheme(OpenApiAuthenticationExtension):
    target_class = 'products.authentication.CachedJWTAuthentication'
    name = 'JWT Auth'
    
    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT'
        }