from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse

from .models import ContactMessage, HomeBanner, Page, SiteSettings, Testimonial


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Company", {"fields": ("company_name", "tagline", "logo", "about_text", "meta_description")}),
        (
            "Legal identity",
            {
                "fields": ("legal_name", "commercial_registration", "trade_licence"),
                "description": "Qatar's E-Commerce Law (No. 16 of 2010) requires online sellers to clearly identify themselves. "
                "These details are shown in the website footer and on order confirmations.",
            },
        ),
        (
            "Address",
            {
                "fields": (
                    "po_box", "building", "zone", "street", "landmark", "area", "city", "country",
                    "google_maps_embed_url", "google_maps_link",
                )
            },
        ),
        ("Contact", {"fields": ("phone", "mobile_1", "mobile_2", "whatsapp_number", "email", "email_secondary", "opening_hours")}),
        ("Social media", {"fields": ("facebook_url", "instagram_url", "linkedin_url"), "classes": ("collapse",)}),
        (
            "Store & payments",
            {
                "fields": (
                    "currency_code", "delivery_fee", "free_delivery_threshold", "tax_rate_percent",
                    "enable_cash_on_delivery", "enable_card_on_delivery", "enable_bank_transfer",
                    "bank_name", "bank_account_name", "bank_iban", "bank_instructions",
                )
            },
        ),
        ("Website text", {"fields": ("announcement_bar", "footer_text")}),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = SiteSettings.load()
        return redirect(reverse("admin:cms_sitesettings_change", args=[obj.pk]))


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published", "show_in_footer", "show_in_nav", "sort_order", "updated_at")
    list_editable = ("is_published", "show_in_footer", "show_in_nav", "sort_order")
    list_filter = ("is_published", "show_in_footer", "show_in_nav")
    search_fields = ("title", "slug", "body")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("title", "slug", "body")}),
        ("Visibility", {"fields": ("is_published", "show_in_footer", "show_in_nav", "sort_order")}),
        ("SEO", {"fields": ("meta_description",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(HomeBanner)
class HomeBannerAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("author", "organisation", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "name", "email", "phone", "created_at", "is_read")
    list_filter = ("is_read", "created_at")
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = ("name", "email", "phone", "subject", "message", "created_at")
    actions = ["mark_read"]

    @admin.action(description="Mark selected messages as read")
    def mark_read(self, request, queryset):
        queryset.update(is_read=True)

    def has_add_permission(self, request):
        return False
