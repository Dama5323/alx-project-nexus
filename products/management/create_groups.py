from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from products.models import Product

class Command(BaseCommand):
    help = 'Creates default user groups with product permissions'

    def handle(self, *args, **options):
        # Get or create permissions
        content_type = ContentType.objects.get_for_model(Product)
        
        permissions_map = {
            'can_view_product': 'Can view product details',
            'can_create_product': 'Can create new products',
            'can_edit_product': 'Can edit existing products',
            'can_delete_product': 'Can remove products',
        }

        # Create permissions if they don't exist
        for codename, name in permissions_map.items():
            Permission.objects.get_or_create(
                codename=codename,
                name=name,
                content_type=content_type
            )

        # Create Groups with permissions
        groups = {
            'Viewers': ['can_view_product'],
            'Editors': ['can_view_product', 'can_create_product', 'can_edit_product'],
            'Admins': list(permissions_map.keys()) + ['can_manage_users']
        }

        for group_name, permission_codenames in groups.items():
            group, created = Group.objects.get_or_create(name=group_name)
            for codename in permission_codenames:
                try:
                    permission = Permission.objects.get(codename=codename)
                    group.permissions.add(permission)
                except Permission.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f'Permission {codename} not found, skipping'
                    ))
            
            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(
                f'{action} group "{group_name}" with {len(permission_codenames)} permissions'
            ))