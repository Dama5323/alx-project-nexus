from drf_yasg.inspectors import FieldInspector
from drf_yasg import openapi
from rest_framework import serializers

class SerializerMetaclassInspector(FieldInspector):
    def process_result(self, result, method_name, obj, **kwargs):
        """Modify schema content for all fields"""
        if isinstance(result, openapi.Schema):
        
            if hasattr(result, 'serializer'):
                del result.serializer
            
            
            if isinstance(obj, serializers.Field):
                self._enhance_field_schema(result, obj)
            
            
            if isinstance(obj, serializers.ChoiceField):
                result.enum = [choice[0] for choice in obj.choices.items()]
                result.description = f"Available choices: {', '.join(result.enum)}"
            
            if isinstance(obj, serializers.DecimalField):
                result.format = 'decimal'
                result.example = "99.99"
                
            if isinstance(obj, serializers.DateTimeField):
                result.format = 'date-time'
                result.example = "2023-01-01T00:00:00Z"
        
        return result
    
    def _enhance_field_schema(self, schema, field):
        """Apply common schema enhancements"""
        if field.help_text:
            schema.description = field.help_text
        if field.label:
            schema.title = field.label
        if field.default != serializers.empty:
            schema.default = field.default
        if field.required:
            schema.min_length = 1 if isinstance(field, serializers.CharField) else None