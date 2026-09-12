from django.conf import settings

from catalog.models import Category
from shop.cart import Cart

from .models import Page, SiteSettings


def site_context(request):
    site = SiteSettings.load()
    return {
        "site": site,
        "nav_categories": Category.objects.filter(is_active=True, parent__isnull=True).order_by("sort_order", "name"),
        "footer_pages": Page.objects.filter(is_published=True, show_in_footer=True),
        "nav_pages": Page.objects.filter(is_published=True, show_in_nav=True),
        "cart_item_count": Cart(request).item_count,
        "CURRENCY": site.currency_code or settings.CURRENCY,
        "DEBUG": settings.DEBUG,
    }
