from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import Order, OrderItem, Cart, CartItem, Adress, PaymentModel




class OrderItemInline(admin.TabularInline):
    model = OrderItem
    fields = ['product', 'variant', 'quantity', 'price']
    readonly_fields = ['product', 'variant', 'quantity', 'price']
    can_delete = False
    max_num = 0  # Yeni ürün eklenmesini engelle
    def variant(self, obj):
        if obj.product_variant:
            return f"{obj.product_variant.product.name} - {obj.product_variant.get_size_display()}"
        return "-"
    
    variant.short_description = "Ürün Varyantı"

    

class OrderResource(resources.ModelResource):
    class Meta:
        model = Order
        exclude = ('status', 'kargo')  # İlgili alanları dışarı aktarmaya dahil etme


@admin.register(Order)
class OrderAdmin(ImportExportModelAdmin):
    resource_class = OrderResource
    list_display = ['id', 'billingName', 'tracking_number', 'status', 'kargo','total', 'created']
    list_display_links = ('id', 'billingName', 'tracking_number','total', 'created')
    list_editable = ('status', 'kargo')
    search_fields = ['id', 'billingName', 'emailAddress']
    readonly_fields = ['id', 'billingName', 'emailAddress', 'created']
    list_filter = ('status', 'created')
    inlines = [OrderItemInline]

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False



