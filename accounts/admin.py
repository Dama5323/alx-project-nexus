# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group, Permission
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    search_fields = ('email', 'username')
    ordering = ('-date_joined',)
    filter_horizontal = ('groups', 'user_permissions')  # Add this line
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('username', 'phone')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_staff'),
        }),
    )

# Custom Group Admin
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'permissions_count', 'users_count')
    filter_horizontal = ('permissions',)
    search_fields = ('name',)
    
    def permissions_count(self, obj):
        return obj.permissions.count()
    permissions_count.short_description = 'Permissions Count'
    
    def users_count(self, obj):
        return obj.user_set.count()
    users_count.short_description = 'Users Count'

# Unregister and re-register Group
admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)