from django.apps import AppConfig

class ProductsConfig(AppConfig):
    name = 'products'

    def ready(self):
        try:
            from django.core.cache import cache
            from django.core.cache.backends.base import InvalidCacheBackendError
            from django.db.utils import OperationalError, ProgrammingError

            if not cache.get('jwt_content_types_cached'):
                from django.contrib.contenttypes.models import ContentType
                from django.apps import apps

                try:
                    ContentType.objects.get_for_models(
                        apps.get_model('token_blacklist', 'BlacklistedToken'),
                        apps.get_model('token_blacklist', 'OutstandingToken'),
                    )
                    cache.set('jwt_content_types_cached', True, timeout=None)
                except (LookupError, OperationalError, ProgrammingError):
                    # Tables might not exist yet
                    pass
        except (InvalidCacheBackendError, ConnectionError):
            # Silently fail if cache isn't available
            pass
