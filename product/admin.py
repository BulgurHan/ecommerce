from django.contrib import admin
from django.db.models import Sum 
from .models import Category, Product, ParentCategory, Collection, ProductVariant


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['parent_categories','name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


class ParentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}



class ProductVariantInline(admin.TabularInline):  
    model = ProductVariant
    extra = 1  # Yeni ürün eklerken 1 boş satır göster



class ProductAdmin(admin.ModelAdmin):
    list_display = ['id','name', 'price', 'total_stock', 'avaible', 'created', 'updated']
    list_editable = ['price', 'avaible']
    list_filter = ('category',)
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 20
    inlines = [ProductVariantInline]  # Ürün detayında bedenleri göster

    def total_stock(self, obj):
        total = obj.variants.aggregate(total_stock=Sum('stock'))['total_stock']
        return total if total else 0  # Eğer None dönerse 0 olarak göster
    total_stock.short_description = "Toplam Stok"



class CollectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}


admin.site.register(Collection,CollectionAdmin)
admin.site.register(Category,CategoryAdmin)
admin.site.register(ParentCategory,ParentCategoryAdmin)
admin.site.register(Product,ProductAdmin)


