from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import Order, OrderItem, Cart, CartItem, Adress


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ['product', 'quantity', 'price']
    can_delete = False
    max_num = 0  # Yeni ürün eklenmesini engelle


class OrderResource(resources.ModelResource):
    class Meta:
        model = Order
        exclude = ('status', 'kargo')  # İlgili alanları dışarı aktarmaya dahil etme


@admin.register(Order)
class OrderAdmin(ImportExportModelAdmin):
    resource_class = OrderResource
    list_display = ['id', 'billingName', 'emailAddress', 'status', 'kargo', 'created']
    list_display_links = ('id', 'billingName')
    list_editable = ('status', 'kargo')
    search_fields = ['id', 'billingName', 'emailAddress']
    readonly_fields = ['id', 'billingName', 'emailAddress', 'created']
    list_filter = ('status', 'created')
    inlines = [OrderItemInline]

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Adress)