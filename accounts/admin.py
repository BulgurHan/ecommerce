from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    ordering = ('first_name',)
    # Admin panelinde listelenecek alanlar
    list_display = ('first_name', 'last_name', 'email',  'cerezler')

    # Admin panelinde detay sayfasında gösterilecek alanlar ve alan grupları
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name',  'cerezler')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Admin panelinde düzenlenecek alanlar ve alan grupları
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2',  'cerezler', 'first_name', 'last_name'),
        }),
    )
    list_display_links = ('first_name', 'email')

# Yeni özelleştirilmiş UserAdmin sınıfını kaydediyoruz
admin.site.register(CustomUser, CustomUserAdmin)