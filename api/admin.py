from django.contrib import admin
from .models import (
    Product,
    Price,
    Store,
    Category,
    ProductChangeRequest,
    UserProfile,
    ProductViewLog,
)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'ean', 'brand', 'is_approved')
    list_filter = ('is_approved',)
    search_fields = ('name', 'ean')


@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ('product', 'price', 'store', 'currency', 'user', 'is_approved')
    list_filter = ('is_approved', 'currency')
    search_fields = ('product__name', 'store__name')


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'store_type', 'verified')
    list_filter = ('verified', 'store_type')
    search_fields = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_approved')
    list_filter = ('is_approved',)



@admin.register(ProductChangeRequest)
class ProductChangeRequestAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'is_approved', 'is_rejected', 'created_at')
    list_filter = ('is_approved', 'is_rejected')
    search_fields = ('product__name',)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # Applica le modifiche solo se è stato approvato e non ancora rifiutato
        if obj.is_approved and not obj.is_rejected:
            product = obj.product

            if obj.proposed_name:
                product.name = obj.proposed_name
            if obj.proposed_brand:
                product.brand = obj.proposed_brand
            if obj.proposed_quantity:
                product.quantity = obj.proposed_quantity
            if obj.proposed_unit:
                product.unit = obj.proposed_unit
            if obj.proposed_categories.exists():
                product.categories.set(obj.proposed_categories.all())

            product.save()



@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'preferred_currency', 'preferred_language', 'location')


@admin.register(ProductViewLog)
class ProductViewLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'device_info', 'timestamp')
    list_filter = ('user', 'product')
    readonly_fields = ('user', 'product', 'device_info', 'timestamp')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
