from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import QuoteRequestForm
from .models import Category, Product, Service

SORT_OPTIONS = {
    "featured": ("Featured", ["-is_featured", "sort_order", "name"]),
    "name": ("Name A-Z", ["name"]),
    "price_asc": ("Price: low to high", ["price", "name"]),
    "price_desc": ("Price: high to low", ["-price", "name"]),
    "newest": ("Newest", ["-created_at"]),
}


def _product_listing(request, base_qs, extra_context):
    query = request.GET.get("q", "").strip()[:100]
    sort = request.GET.get("sort", "featured")
    if sort not in SORT_OPTIONS:
        sort = "featured"

    qs = base_qs.filter(is_active=True).select_related("category")
    if query:
        qs = qs.filter(
            Q(name__icontains=query)
            | Q(sku__icontains=query)
            | Q(short_description__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
        )
    qs = qs.order_by(*SORT_OPTIONS[sort][1])

    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    params = request.GET.copy()
    params.pop("page", None)

    context = {
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "query": query,
        "sort": sort,
        "sort_options": [(k, v[0]) for k, v in SORT_OPTIONS.items()],
        "categories": Category.objects.filter(is_active=True, parent__isnull=True),
        "querystring": params.urlencode(),
        "total": paginator.count,
    }
    context.update(extra_context)
    return render(request, "catalog/product_list.html", context)


def product_list(request):
    return _product_listing(request, Product.objects.all(), {"title": "All products", "current_category": None})


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    qs = Product.objects.filter(Q(category=category) | Q(category__parent=category))
    return _product_listing(request, qs, {"title": category.name, "current_category": category})


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related("category"), slug=slug, is_active=True)
    related = (
        Product.objects.filter(is_active=True, category=product.category)
        .exclude(pk=product.pk)
        .order_by("?")[:4]
    )
    return render(request, "catalog/product_detail.html", {"product": product, "related": related})


def service_list(request):
    services = Service.objects.filter(is_active=True)
    return render(request, "catalog/service_list.html", {"services": services})


def service_detail(request, slug):
    service = get_object_or_404(Service, slug=slug, is_active=True)
    others = Service.objects.filter(is_active=True).exclude(pk=service.pk)[:5]
    return render(request, "catalog/service_detail.html", {"service": service, "others": others})


def quote_request(request):
    initial = {}
    service_slug = request.GET.get("service")
    if service_slug:
        service = Service.objects.filter(slug=service_slug, is_active=True).first()
        if service:
            initial["service"] = service

    if request.method == "POST":
        form = QuoteRequestForm(request.POST, request.FILES)
        if form.is_valid():
            quote = form.save()
            send_mail(
                subject=f"[Quote request #{quote.pk}] {quote.service or 'General'} - {quote.name}",
                message=(
                    f"Name: {quote.name}\nCompany: {quote.company}\nEmail: {quote.email}\nPhone: {quote.phone}\n"
                    f"Quantity: {quote.quantity}\n\n{quote.details}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ORDER_NOTIFICATION_EMAIL],
                fail_silently=True,
            )
            messages.success(
                request,
                f"Thank you, your quote request #{quote.pk} has been received. We will contact you within one working day.",
            )
            return redirect("catalog:service_list")
    else:
        form = QuoteRequestForm(initial=initial)
    return render(request, "catalog/quote_request.html", {"form": form})
