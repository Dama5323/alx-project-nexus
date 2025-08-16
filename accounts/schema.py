# schema.py
from drf_spectacular.utils import extend_schema, OpenApiExample
from drf_spectacular.plumbing import build_object_type

def custom_preprocessing_hook(endpoints):
    # Rename "Users" to "Accounts" in schema
    for endpoint in endpoints:
        if endpoint[2] == 'users':
            endpoint[2] = 'accounts'
    return endpoints