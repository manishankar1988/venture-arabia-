from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from catalog.models import Category, Product, Service

from .forms import ContactForm
from .models import HomeBanner, Page, Testimonial


def home(request):
    context = {
        "banners": HomeBanner.objects.filter(is_active=True),
        "featured_products": Product.objects.filter(is_active=True, is_featured=True).select_related("category")[:8],
        "categories": Category.objects.filter(is_active=True, parent__isnull=True).order_by("sort_order", "name")[:8],
        "services": Service.objects.filter(is_active=True, is_featured=True)[:6],
        "testimonials": Testimonial.objects.filter(is_active=True)[:3],
    }
    return render(request, "cms/home.html", context)


def page_detail(request, slug):
    page = get_object_or_404(Page, slug=slug, is_published=True)
    return render(request, "cms/page.html", {"page": page})


@require_http_methods(["GET", "POST"])
def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            msg = form.save()
            try:
                send_mail(
                    subject=f"[Website enquiry] {msg.subject}",
                    message=(
                        f"From: {msg.name} <{msg.email}> {msg.phone}\n\n{msg.message}"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.ORDER_NOTIFICATION_EMAIL],
                    fail_silently=True,
                )
            except Exception:  # pragma: no cover - email must never break the request
                pass
            messages.success(request, "Thank you. Your message has been received and we will reply shortly.")
            return redirect("cms:contact")
    else:
        form = ContactForm()
    return render(request, "cms/contact.html", {"form": form})


def error_404(request, exception=None):
    return render(request, "404.html", status=404)


def error_500(request):
    return render(request, "500.html", status=500)
