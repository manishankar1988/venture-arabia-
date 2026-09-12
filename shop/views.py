from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_POST

from catalog.models import Product
from cms.models import SiteSettings

from .cart import Cart
from .forms import AddToCartForm, CheckoutForm, OrderTrackForm
from .models import Order, OrderItem


def _delivery_fee(site, subtotal, delivery_method):
    if delivery_method == Order.DeliveryMethod.PICKUP:
        return Decimal("0.00")
    if site.free_delivery_threshold and subtotal >= site.free_delivery_threshold:
        return Decimal("0.00")
    return site.delivery_fee


def cart_detail(request):
    cart = Cart(request)
    site = SiteSettings.load()
    subtotal = cart.subtotal
    fee = _delivery_fee(site, subtotal, Order.DeliveryMethod.DELIVERY)
    return render(
        request,
        "shop/cart.html",
        {"cart": cart, "subtotal": subtotal, "delivery_fee": fee, "estimated_total": subtotal + fee, "has_unpriced": cart.has_unpriced},
    )


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    form = AddToCartForm(request.POST, product=product)
    if form.is_valid():
        if not product.in_stock:
            messages.error(request, f"Sorry, {product.name} is currently out of stock.")
            return redirect(product.get_absolute_url())
        cart = Cart(request)
        cart.add(product, form.cleaned_data["quantity"], form.cleaned_data.get("custom_text", ""))
        messages.success(request, f"{product.name} was added to your cart.")
        return redirect("shop:cart")
    for error in form.errors.values():
        messages.error(request, error.as_text().lstrip("* "))
    return redirect(product.get_absolute_url())


@require_POST
def cart_update(request, key):
    cart = Cart(request)
    try:
        qty = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        qty = 1
    cart.update(key, qty)
    return redirect("shop:cart")


@require_POST
def cart_remove(request, key):
    Cart(request).remove(key)
    messages.info(request, "Item removed from your cart.")
    return redirect("shop:cart")


def checkout(request):
    cart = Cart(request)
    if cart.is_empty:
        messages.info(request, "Your cart is empty.")
        return redirect("catalog:product_list")

    site = SiteSettings.load()
    subtotal = cart.subtotal

    if request.method == "POST":
        form = CheckoutForm(request.POST, site=site)
        if form.is_valid():
            order = _create_order(request, cart, form, site)
            cart.clear()
            request.session["last_order_number"] = order.number
            messages.success(request, f"Thank you! Your order {order.number} has been placed.")
            return redirect("shop:order_success", number=order.number)
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {
                "full_name": request.user.get_full_name() or request.user.username,
                "email": request.user.email,
            }
            last = request.user.orders.first()
            if last:
                for f in ("phone", "company", "building", "zone", "street", "area", "city"):
                    initial[f] = getattr(last, f)
        form = CheckoutForm(initial=initial, site=site)

    tax = (subtotal * site.tax_rate_percent / Decimal("100")).quantize(Decimal("0.01"))
    context = {
        "form": form,
        "cart": cart,
        "subtotal": subtotal,
        "delivery_fee": _delivery_fee(site, subtotal, Order.DeliveryMethod.DELIVERY),
        "tax": tax,
        "has_unpriced": cart.has_unpriced,
    }
    return render(request, "shop/checkout.html", context)


def _create_order(request, cart, form, site):
    with transaction.atomic():
        order = form.save(commit=False)
        order.currency = site.currency_code
        if request.user.is_authenticated:
            order.user = request.user
        elif form.cleaned_data.get("create_account"):
            order.user = _create_customer_account(request, order)
        order.save()

        for item in cart:
            product = item["product"]
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                sku=product.sku,
                unit_price=item["unit_price"],
                quantity=item["quantity"],
                custom_text=item["custom_text"],
            )
            if product.track_stock:
                Product.objects.filter(pk=product.pk, stock_quantity__gte=item["quantity"]).update(
                    stock_quantity=F("stock_quantity") - item["quantity"]
                )

        order.recalculate(
            delivery_fee=_delivery_fee(site, cart.subtotal, order.delivery_method),
            tax_rate=site.tax_rate_percent,
        )
        order.save()

    _send_order_emails(order, site)
    return order


def _create_customer_account(request, order):
    User = get_user_model()
    if User.objects.filter(email__iexact=order.email).exists():
        messages.info(request, "An account with this email already exists. Log in to see your orders.")
        return None
    username = order.email.lower()
    password = get_random_string(14)
    user = User.objects.create_user(username=username, email=order.email, password=password)
    name_parts = order.full_name.split(" ", 1)
    user.first_name = name_parts[0]
    user.last_name = name_parts[1] if len(name_parts) > 1 else ""
    user.save()
    send_mail(
        subject="Your Venture Arabia account",
        message=(
            f"Hello {order.full_name},\n\nAn account has been created for you.\n"
            f"Username: {username}\nTemporary password: {password}\n\n"
            "Please log in and change your password from your account page."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.email],
        fail_silently=True,
    )
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return user


def _send_order_emails(order, site):
    body = render_to_string("shop/emails/order_confirmation.txt", {"order": order, "site": site})
    send_mail(
        subject=f"Order {order.number} received - {site.company_name}",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.email],
        fail_silently=True,
    )
    send_mail(
        subject=f"[New order] {order.number} - {order.full_name} - {order.total} {order.currency}",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.ORDER_NOTIFICATION_EMAIL],
        fail_silently=True,
    )


def order_success(request, number):
    order = get_object_or_404(Order, number=number)
    allowed = (
        request.session.get("last_order_number") == number
        or (request.user.is_authenticated and (order.user_id == request.user.id or request.user.is_staff))
    )
    if not allowed:
        return redirect("shop:order_track")
    return render(request, "shop/order_success.html", {"order": order})


def order_track(request):
    order = None
    if request.method == "POST":
        form = OrderTrackForm(request.POST)
        if form.is_valid():
            order = Order.objects.filter(
                number=form.cleaned_data["number"], phone=form.cleaned_data["phone"]
            ).first()
            if order is None:
                messages.error(request, "No order found with that number and phone combination.")
    else:
        form = OrderTrackForm()
    return render(request, "shop/order_track.html", {"form": form, "order": order})


@login_required
def my_orders(request):
    orders = request.user.orders.prefetch_related("items")
    return render(request, "shop/my_orders.html", {"orders": orders})


@login_required
def my_order_detail(request, number):
    order = get_object_or_404(Order, number=number, user=request.user)
    return render(request, "shop/order_detail.html", {"order": order})
