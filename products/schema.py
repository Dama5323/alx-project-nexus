import graphene
from graphene_django import DjangoObjectType, DjangoListField
from graphene_django.filter import DjangoFilterConnectionField
from django_filters import FilterSet, NumberFilter, CharFilter
from graphql_jwt.decorators import login_required, staff_member_required
from .models import Category, Product, Review, ProductImage

# --------------------------
# FILTER SETS (REQUIRED FOR ALL FILTERED TYPES)
# --------------------------

class CategoryFilterSet(FilterSet):
    class Meta:
        model = Category
        fields = {
            'name': ['exact', 'icontains'],
            'slug': ['exact']
        }

class ProductFilterSet(FilterSet):
    min_price = NumberFilter(field_name="price", lookup_expr='gte')
    max_price = NumberFilter(field_name="price", lookup_expr='lte')
    
    class Meta:
        model = Product
        fields = {
            'name': ['exact', 'icontains'],
            'category__id': ['exact'],
            'available': ['exact']
        }

class ReviewFilterSet(FilterSet):
    class Meta:
        model = Review
        fields = {
            'rating': ['exact', 'gte', 'lte'],
            'product__id': ['exact']
        }

# --------------------------
# TYPES (WITH EXPLICIT FIELD DECLARATIONS)
# --------------------------

class CategoryType(DjangoObjectType):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'created_at')
        filterset_class = CategoryFilterSet
        interfaces = (graphene.relay.Node,)

class ProductImageType(DjangoObjectType):
    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'alt_text', 'is_featured')

class ProductType(DjangoObjectType):
    average_rating = graphene.Float()
    review_count = graphene.Int()
    images = graphene.List(ProductImageType)
    
    class Meta:
        model = Product
        fields = (
            'id', 'name', 'description', 'price', 
            'category', 'stock', 'available', 'featured'
        )
        filterset_class = ProductFilterSet
        interfaces = (graphene.relay.Node,)
    
    def resolve_images(self, info):
        return self.images.all()

class ReviewType(DjangoObjectType):
    class Meta:
        model = Review
        fields = ('id', 'product', 'user', 'rating', 'comment', 'created_at')
        filterset_class = ReviewFilterSet
        interfaces = (graphene.relay.Node,)

# --------------------------
# QUERIES (WITH PROPER RESOLVERS)
# --------------------------

class Query(graphene.ObjectType):
    all_categories = DjangoFilterConnectionField(CategoryType)
    all_products = DjangoFilterConnectionField(ProductType)
    all_reviews = DjangoFilterConnectionField(ReviewType)
    
    product_by_slug = graphene.Field(ProductType, slug=graphene.String(required=True))
    featured_products = graphene.List(ProductType)

    def resolve_all_categories(self, info, **kwargs):
        return Category.objects.all()

    def resolve_all_products(self, info, **kwargs):
        return Product.objects.select_related('category').prefetch_related('images')

    def resolve_all_reviews(self, info, **kwargs):
        return Review.objects.select_related('user', 'product')

    def resolve_product_by_slug(self, info, slug):
        return Product.objects.get(slug=slug)

    def resolve_featured_products(self, info):
        return Product.objects.filter(featured=True)

# --------------------------
# MUTATIONS
# --------------------------

class CreateCategory(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String()

    category = graphene.Field(CategoryType)

    @staff_member_required
    def mutate(self, info, name, description=None):
        category = Category.objects.create(
            name=name,
            description=description
        )
        return CreateCategory(category=category)

class ProductMutations(graphene.ObjectType):
    create_category = CreateCategory.Field()

# --------------------------
# SCHEMA DEFINITION
# --------------------------

schema = graphene.Schema(
    query=Query,
    mutation=ProductMutations
)