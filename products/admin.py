from django.contrib import admin
from .models import Category, Product, Review, ProductImage  
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Avg
from django.utils.html import format_html, mark_safe

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'product_count', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    ordering = ('name',)
    readonly_fields = ('created_at', 'old_slug')
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'old_slug')
        }),
        ('Details', {
            'fields': ('description', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'is_featured', 'image_preview')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100" />')
        return "No image"
    image_preview.short_description = 'Preview'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]  # Added this line
    list_display = ('image_thumb', 'name', 'price', 'category', 'available', 'featured', 
                   'average_rating', 'created_at')
    list_filter = ('available', 'featured', 'category', 'created_at')
    list_editable = ('price', 'available', 'featured')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description', 'category__name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'view_reviews_link')
    exclude = ('old_slug',)
    list_select_related = ('category', 'created_by')  # Added for performance
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'category', 'price')
        }),
        ('Inventory', {
            'fields': ('stock', 'available', 'featured'),
            'classes': ('collapse',)
        }),
        ('Details', {
            'fields': ('description', 'image', 'created_by'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def average_rating(self, obj):
        avg = obj.reviews.aggregate(Avg('rating'))['rating__avg']
        return f"{avg:.1f}" if avg else "No ratings"
    average_rating.short_description = 'Avg Rating'

    def view_reviews_link(self, obj):
        count = obj.reviews.count()
        url = reverse('admin:products_review_changelist') + f'?product__id__exact={obj.id}'
        return format_html('<a href="{}">{} Reviews</a>', url, count)
    view_reviews_link.short_description = 'Reviews'

    def image_thumb(self, obj):
        try:
            if obj.image:
                return mark_safe(f'<img src="{obj.image.url}" width="50" />')
            first_extra = obj.images.first()
            if first_extra and first_extra.image:
                return mark_safe(f'<img src="{first_extra.image.url}" width="50" />')
        except Exception:
            pass
        return "No image"
    image_thumb.short_description = 'Image'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at', 'short_comment')
    list_filter = ('rating', 'created_at', 'product__category')
    search_fields = ('user__email', 'product__name', 'comment')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    list_select_related = ('product', 'user')
    date_hierarchy = 'created_at'
    raw_id_fields = ('user',)  # Added for better user selection

    def short_comment(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    short_comment.short_description = 'Comment Preview'