import csv

from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html

from .models import Category, Product, ProductImage, QuoteRequest, Service


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "product_count", "sort_order", "is_active")
    list_editable = ("sort_order", "is_active")
    list_filter = ("is_active", "parent")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="Products")
    def product_count(self, obj):
        return obj.products.count()


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "alt_text", "sort_order")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("thumbnail", "name", "sku", "category", "price", "stock_status", "is_customisable", "is_featured", "is_active")
    list_display_links = ("thumbnail", "name")
    list_editable = ("price", "is_featured", "is_active")
    list_filter = ("is_active", "is_featured", "is_customisable", "category", "brand")
    search_fields = ("name", "sku", "short_description", "description")
    prepopulated_fields = {"slug": ("name", "sku")}
    inlines = [ProductImageInline]
    readonly_fields = ("created_at", "updated_at")
    actions = ["make_active", "make_inactive", "export_csv"]
    list_per_page = 40
    fieldsets = (
        ("Basic information", {"fields": ("category", "name", "slug", "sku", "brand", "short_description", "description", "image")}),
        ("Pricing", {"fields": ("price", "compare_at_price")}),
        ("Stock", {"fields": ("track_stock", "stock_quantity")}),
        ("Stamp specifications", {"fields": ("plate_size", "date_size", "ink_cartridge", "available_colours", "ink_colours")}),
        ("Customisation", {"fields": ("is_customisable", "customisation_help")}),
        ("Visibility", {"fields": ("is_active", "is_featured", "sort_order")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(description="")
    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:40px;width:40px;object-fit:cover;border-radius:4px">', obj.image.url)
        return format_html('<span style="display:inline-block;height:40px;width:40px;border-radius:4px;background:#e5e7eb"></span>')

    @admin.display(description="Stock")
    def stock_status(self, obj):
        if not obj.track_stock:
            return "Made to order"
        return f"{obj.stock_quantity} in stock" if obj.stock_quantity else "Out of stock"

    @admin.action(description="Publish selected products")
    def make_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Hide selected products")
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description="Export selected products to CSV")
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="products.csv"'
        writer = csv.writer(response)
        writer.writerow(["SKU", "Name", "Category", "Price (QAR)", "Plate size", "Ink cartridge", "Active"])
        for p in queryset:
            writer.writerow([p.sku, p.name, p.category, p.price, p.plate_size, p.ink_cartridge, p.is_active])
        return response


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "starting_price", "price_unit", "turnaround", "is_featured", "is_active", "sort_order")
    list_editable = ("is_featured", "is_active", "sort_order")
    list_filter = ("is_active", "is_featured")
    search_fields = ("name", "short_description", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "company", "service", "phone", "status", "created_at")
    list_editable = ("status",)
    list_filter = ("status", "service", "created_at")
    search_fields = ("name", "company", "email", "phone", "details")
    readonly_fields = ("service", "name", "company", "email", "phone", "quantity", "details", "attachment", "created_at")
    fieldsets = (
        ("Request", {"fields": ("service", "name", "company", "email", "phone", "quantity", "details", "attachment", "created_at")}),
        ("Follow-up", {"fields": ("status", "internal_notes")}),
    )

    def has_add_permission(self, request):
        return False
