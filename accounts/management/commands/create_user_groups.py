from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from accounts.models import CustomUser

class Command(BaseCommand):
    help = 'Creates Customers, Guest_Users, and Premium_Members groups'

    def handle(self, *args, **options):
        groups = [
            ('Customers', [
                'view_product',
                'add_order',
                'view_order'
            ]),
            ('Guest_Users', [
                'view_product'
            ]),
            ('Premium_Members', [
                'view_product',
                'add_order',
                'view_order',
                'early_access',
                'exclusive_content'
            ])
        ]

        for group_name, perms in groups:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                permissions = Permission.objects.filter(codename__in=perms)
                group.permissions.set(permissions)  
                self.stdout.write(
                    self.style.SUCCESS(f'Created group: {group_name}')
                )  
            else:
                self.stdout.write(
                    self.style.WARNING(f'Group {group_name} already exists')
                )  
