from django.contrib import admin
from django import forms
from .models import Category, Product, Review

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'inline' in kwargs.get('prefix', ''):
            self.fields['price'].required = False
            self.fields['stock'].required = False

class ProductInline(admin.TabularInline):
    form = ProductForm
    model = Product
    extra = 1
    min_num = 0
    fields = ('name', 'description', 'price', 'stock', 'available', 'image')
    verbose_name_plural = "Products in this category"
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.validate_min = False
        return formset

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at', 'get_product_count', 'description_preview')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductInline]
    search_fields = ('name', 'description')
    list_filter = ('created_at',)
    
    def get_product_count(self, obj):
        return obj.products.count()
    get_product_count.short_description = '# Products'
    
    def description_preview(self, obj):
        return obj.description[:50] + '...' if obj.description else ''
    description_preview.short_description = 'Description Preview'
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if instance.name and instance.price is not None and instance.stock is not None:
                instance.save()
        formset.save_m2m()

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductForm
    list_display = ('name', 'category', 'price', 'stock', 'available', 'created_at')
    list_editable = ('price', 'stock', 'available')
    list_filter = ('category', 'available', 'created_at')
    search_fields = ('name', 'description')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'category', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'stock')
        }),
        ('Status', {
            'fields': ('available', 'image')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('get_product_name', 'user', 'rating', 'created_at', 'short_comment')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__username', 'comment')
    raw_id_fields = ('product', 'user')
    date_hierarchy = 'created_at'
    
    def get_product_name(self, obj):
        return obj.product.name
    get_product_name.short_description = 'Product'
    get_product_name.admin_order_field = 'product__name'
    
    def short_comment(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    short_comment.short_description = 'Comment Preview'