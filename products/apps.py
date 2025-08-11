from django.apps import AppConfig
import os

class ProductsConfig(AppConfig):
    name = 'products'

    def ready(self):
        # Skip during management commands and tests
        if (os.environ.get('RUN_MAIN') != 'true' and 
            not os.environ.get('RUNNING_TESTS')):
            self._initialize_content_types()

    def _initialize_content_types(self):
        """Delayed initialization after app registry is ready"""
        from django.db.models.signals import post_migrate
        from django.apps import apps
        
        def callback(sender, **kwargs):
            try:
                from django.contrib.contenttypes.models import ContentType
                ContentType.objects.get_for_models(
                    apps.get_model('token_blacklist', 'BlacklistedToken'),
                    apps.get_model('token_blacklist', 'OutstandingToken'),
                )
            except Exception as e:
                pass
                
        post_migrate.connect(callback, sender=self)