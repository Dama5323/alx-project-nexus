import django_filters
from .models import Product
from django.db.models import Q

class ProductFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    category = django_filters.CharFilter(field_name='category__slug')
    available = django_filters.BooleanFilter(field_name='available')
    
    class Meta:
        model = Product
        fields = ['search', 'min_price', 'max_price', 'category', 'available']
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value)
        )