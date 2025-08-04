from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CategoryViewSet, ReviewViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'', ProductViewSet, basename='product')  # Changed from 'products' to ''

# Nested reviews
router.register(
    r'(?P<product_slug>[^/.]+)/reviews', 
    ReviewViewSet, 
    basename='product-reviews'
)

urlpatterns = router.urls