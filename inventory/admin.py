from django.contrib import admin
from .models import WarehouseItem

@admin.register(WarehouseItem)
class WarehouseItemAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'category', 'quantity', 'unit_price', 'updated_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'sku', 'description')
    readonly_fields = ('created_at', 'updated_at')
