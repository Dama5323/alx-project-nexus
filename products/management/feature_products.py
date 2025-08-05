from django.core.management.base import BaseCommand
from products.models import Product

class Command(BaseCommand):
    help = 'Mark specific products as featured'

    def add_arguments(self, parser):
        parser.add_argument('product_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        Product.objects.filter(id__in=options['product_ids']).update(featured=True)
        self.stdout.write(self.style.SUCCESS('Successfully featured products'))