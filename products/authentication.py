from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.cache import cache

class CachedJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user_id = validated_token.get('user_id')
        cache_key = f'jwt_user_{user_id}'
        user = cache.get(cache_key)
        
        if user is None:
            user = super().get_user(validated_token)
            cache.set(cache_key, user, timeout=300)  # Cache for 5 minutes
        
        return user