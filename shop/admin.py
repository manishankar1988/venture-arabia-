import csv

from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("product", "product_name", "sku", "unit_price", "quantity", "custom_text", "line_total")
    readonly_fields = ("line_total",)

    @admin.display(description="Line total")
    def line_total(self, obj):
        if not obj.pk or obj.unit_price is None:
            return "-"
        return f"{obj.line_total} {obj.order.currency}"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "created_at", "full_name", "phone", "delivery_method", "payment_method", "total_display", "payment_status", "status_badge")
    list_filter = ("status", "payment_status", "payment_method", "delivery_method", "created_at")
    search_fields = ("number", "full_name", "email", "phone", "company")
    date_hierarchy = "created_at"
    readonly_fields = ("number", "subtotal", "delivery_fee", "tax_rate_percent", "tax_amount", "total", "currency", "accepted_terms", "created_at", "updated_at", "user")
    inlines = [OrderItemInline]
    actions = ["mark_confirmed", "mark_processing", "mark_out_for_delivery", "mark_delivered", "mark_paid", "export_csv"]
    list_per_page = 30
    fieldsets = (
        ("Order", {"fields": ("number", "status", "payment_status", "created_at", "updated_at", "user")}),
        ("Customer", {"fields": ("full_name", "email", "phone", "company")}),
        ("Delivery", {"fields": ("delivery_method", "building", "zone", "street", "area", "city", "delivery_notes")}),
        ("Payment & totals", {"fields": ("payment_method", "subtotal", "delivery_fee", "tax_rate_percent", "tax_amount", "total", "currency")}),
        ("Internal", {"fields": ("staff_notes", "accepted_terms")}),
    )

    @admin.display(description="Total", ordering="total")
    def total_display(self, obj):
        return f"{obj.total} {obj.currency}"

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        colours = {
            "pending": "#b45309", "confirmed": "#1d4ed8", "processing": "#6d28d9", "ready": "#0e7490",
            "out_for_delivery": "#0369a1", "delivered": "#15803d", "cancelled": "#b91c1c",
        }
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px">{}</span>',
            colours.get(obj.status, "#374151"), obj.get_status_display(),
        )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.recalculate()
        form.instance.save()

    def _set_status(self, queryset, status):
        queryset.update(status=status)

    @admin.action(description="Mark as Confirmed")
    def mark_confirmed(self, request, queryset):
        self._set_status(queryset, Order.Status.CONFIRMED)

    @admin.action(description="Mark as In production / processing")
    def mark_processing(self, request, queryset):
        self._set_status(queryset, Order.Status.PROCESSING)

    @admin.action(description="Mark as Out for delivery")
    def mark_out_for_delivery(self, request, queryset):
        self._set_status(queryset, Order.Status.OUT_FOR_DELIVERY)

    @admin.action(description="Mark as Delivered")
    def mark_delivered(self, request, queryset):
        self._set_status(queryset, Order.Status.DELIVERED)

    @admin.action(description="Mark as Paid")
    def mark_paid(self, request, queryset):
        queryset.update(payment_status=Order.PaymentStatus.PAID)

    @admin.action(description="Export selected orders to CSV")
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="orders.csv"'
        writer = csv.writer(response)
        writer.writerow(["Order", "Date", "Customer", "Phone", "Email", "Delivery", "Payment", "Payment status", "Status", "Subtotal", "Delivery fee", "Tax", "Total"])
        for o in queryset:
            writer.writerow([o.number, o.created_at.strftime("%Y-%m-%d %H:%M"), o.full_name, o.phone, o.email, o.get_delivery_method_display(), o.get_payment_method_display(), o.get_payment_status_display(), o.get_status_display(), o.subtotal, o.delivery_fee, o.tax_amount, o.total])
        return response

    def has_add_permission(self, request):
        return False
