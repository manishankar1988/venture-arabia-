"""Session-based shopping cart.

Stored in the session as {"<product_id>:<hash>": {"product_id", "quantity", "custom_text"}}
so the same product can appear twice with different stamp text.
"""
from decimal import Decimal
import hashlib

from django.conf import settings

from catalog.models import Product

MAX_QTY = 99


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_KEY)
        if cart is None:
            cart = self.session[settings.CART_SESSION_KEY] = {}
        self.cart = cart

    # -- helpers ---------------------------------------------------------
    @staticmethod
    def _key(product_id, custom_text):
        digest = hashlib.sha1(custom_text.strip().encode("utf-8")).hexdigest()[:8] if custom_text else "0"
        return f"{product_id}:{digest}"

    def save(self):
        self.session.modified = True

    # -- mutations -------------------------------------------------------
    def add(self, product, quantity=1, custom_text=""):
        quantity = max(1, min(int(quantity), MAX_QTY))
        custom_text = (custom_text or "").strip()[:500]
        key = self._key(product.pk, custom_text)
        if key in self.cart:
            self.cart[key]["quantity"] = min(self.cart[key]["quantity"] + quantity, MAX_QTY)
        else:
            self.cart[key] = {"product_id": product.pk, "quantity": quantity, "custom_text": custom_text}
        self.save()

    def update(self, key, quantity):
        if key in self.cart:
            quantity = int(quantity)
            if quantity <= 0:
                del self.cart[key]
            else:
                self.cart[key]["quantity"] = min(quantity, MAX_QTY)
            self.save()

    def remove(self, key):
        if key in self.cart:
            del self.cart[key]
            self.save()

    def clear(self):
        self.session[settings.CART_SESSION_KEY] = {}
        self.save()

    # -- reads -----------------------------------------------------------
    def __iter__(self):
        ids = {item["product_id"] for item in self.cart.values()}
        products = {p.pk: p for p in Product.objects.filter(pk__in=ids, is_active=True)}
        for key, item in list(self.cart.items()):
            product = products.get(item["product_id"])
            if product is None:  # product was removed or hidden by staff
                del self.cart[key]
                self.save()
                continue
            yield {
                "key": key,
                "product": product,
                "quantity": item["quantity"],
                "custom_text": item.get("custom_text", ""),
                "unit_price": product.price,
                "line_total": product.price * item["quantity"],
            }

    @property
    def items(self):
        return list(self)

    @property
    def item_count(self):
        return sum(item["quantity"] for item in self.cart.values())

    @property
    def is_empty(self):
        return not self.cart

    @property
    def subtotal(self):
        return sum((item["line_total"] for item in self), Decimal("0.00"))
