from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext as _

from .models import Ingredient, Recipe, Tag, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'name']
    ordering = ['email']
    add_fieldsets = [
        [None, {'classes': ['wide'], 'fields': ['email', 'name', 'password', 'password2']}],
        [_('permissions'), {'fields': ['is_active', 'is_staff', 'is_superuser']}]
    ]

    fieldsets = [
        [None, {'fields': ['email', 'password']}],
        [_('permissions'), {'fields': ['is_active', 'is_staff', 'is_superuser']}],
        [_('important dates'), {'fields': ['last_login']}]

    ]

    readonly_fields = ['last_login']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass

admin.site.register(Recipe)
admin.site.register(Ingredient)