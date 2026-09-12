"""End-to-end tests for the storefront, checkout, tracking, forms, admin and security headers.

Run with:  python manage.py test
"""
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.html import escape

from catalog.models import Product, Service
from cms.models import Page
from shop.models import Order


@override_settings(
    SECURE_SSL_REDIRECT=False,
    AXES_ENABLED=False,
    # Tests must not depend on a collectstatic run having produced the WhiteNoise manifest.
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
)
class SiteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)
        cls.stamp = Product.objects.get(sku="4912")
        cls.cartridge = Product.objects.get(sku="6/4912")
        cls.service = Service.objects.first()
        cls.admin = get_user_model().objects.create_superuser("admin", "admin@example.com", "Adm1n-Passw0rd!")

    # -- public pages ------------------------------------------------------
    def test_public_pages_render(self):
        urls = [
            "/", "/products/", "/products/?q=4912", "/products/?sort=price_desc",
            "/products/category/trodat-self-inking-stamps/", "/products/category/round-stamps/",
            self.stamp.get_absolute_url(), "/services/", self.service.get_absolute_url(),
            "/services/request-quote/", "/contact/", "/shop/cart/", "/shop/track/",
            "/accounts/login/", "/accounts/register/", "/accounts/password-reset/",
            "/sitemap.xml", "/robots.txt",
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        for page in Page.objects.filter(is_published=True):
            self.assertContains(self.client.get(page.get_absolute_url()), escape(page.title))

    def test_404_and_protected_pages(self):
        self.assertEqual(self.client.get("/does-not-exist/").status_code, 404)
        self.assertEqual(self.client.get("/shop/my-orders/").status_code, 302)
        self.assertEqual(self.client.get("/" + settings.ADMIN_URL).status_code, 302)

    def test_security_headers(self):
        response = self.client.get("/")
        for header in ("Content-Security-Policy", "X-Frame-Options", "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy"):
            self.assertIn(header, response)
        self.assertEqual(response["X-Frame-Options"], "DENY")

    # -- cart & checkout ---------------------------------------------------
    def _fill_cart(self):
        self.client.post(reverse("shop:cart_add", args=[self.stamp.pk]), {"quantity": 2, "custom_text": "VENTURE ARABIA\nDoha"})
        self.client.post(reverse("shop:cart_add", args=[self.cartridge.pk]), {"quantity": 3})

    def test_custom_stamp_requires_text(self):
        response = self.client.post(reverse("shop:cart_add", args=[self.stamp.pk]), {"quantity": 1}, follow=True)
        self.assertContains(response, "required")
        self.assertContains(self.client.get("/shop/cart/"), "empty")

    def test_checkout_rejects_invalid_qatar_phone(self):
        self._fill_cart()
        response = self.client.post("/shop/checkout/", {
            "full_name": "Test", "email": "t@example.com", "phone": "12345", "delivery_method": "delivery",
            "building": "1", "zone": "56", "street": "340", "area": "Salwa", "city": "Doha",
            "payment_method": "cod", "accepted_terms": "on",
        })
        self.assertContains(response, "valid Qatar phone")

    def test_delivery_requires_address(self):
        self._fill_cart()
        response = self.client.post("/shop/checkout/", {
            "full_name": "Test", "email": "t@example.com", "phone": "55883587", "delivery_method": "delivery",
            "payment_method": "cod", "accepted_terms": "on",
        })
        self.assertContains(response, "Required for delivery")

    def test_full_checkout_pickup_bank_transfer(self):
        self._fill_cart()
        stock_before = self.cartridge.stock_quantity
        response = self.client.post("/shop/checkout/", {
            "full_name": "Test Customer", "email": "test@example.com", "phone": "5588 3587",
            "delivery_method": "pickup", "payment_method": "bank_transfer", "accepted_terms": "on",
            "create_account": "on",
        })
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get()
        self.assertTrue(order.number.startswith("VA"))
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.subtotal, Decimal("176.00"))
        self.assertEqual(order.delivery_fee, Decimal("0.00"))
        self.assertEqual(order.total, Decimal("176.00"))
        self.assertEqual(order.phone, "+97455883587")
        self.assertTrue(order.accepted_terms)
        self.assertEqual(order.items.get(sku="4912").custom_text, "VENTURE ARABIA\nDoha")
        self.cartridge.refresh_from_db()
        self.assertEqual(self.cartridge.stock_quantity, stock_before - 3)
        # confirmation to the customer + notification to the shop + account email
        self.assertGreaterEqual(len(mail.outbox), 3)
        self.assertTrue(any(order.number in m.body for m in mail.outbox))
        self.assertIn("test@example.com", [m.to[0] for m in mail.outbox])
        # success page, cart cleared, account created and logged in
        self.assertContains(self.client.get(response["Location"]), "Thank you")
        self.assertContains(self.client.get("/shop/cart/"), "empty")
        self.assertContains(self.client.get("/shop/my-orders/"), order.number)
        self.assertEqual(order.user.email, "test@example.com")

    def test_delivery_fee_and_free_delivery_threshold(self):
        self.client.post(reverse("shop:cart_add", args=[self.cartridge.pk]), {"quantity": 1})
        response = self.client.post("/shop/checkout/", {
            "full_name": "Test", "email": "t@example.com", "phone": "33905158", "delivery_method": "delivery",
            "building": "1", "zone": "56", "street": "340", "area": "Salwa", "city": "Doha",
            "payment_method": "cod", "accepted_terms": "on",
        })
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get()
        self.assertEqual(order.delivery_fee, Decimal("20.00"))  # below the free-delivery threshold
        self.assertEqual(order.total, order.subtotal + Decimal("20.00"))

    def test_order_tracking(self):
        self._fill_cart()
        self.client.post("/shop/checkout/", {
            "full_name": "Test", "email": "t@example.com", "phone": "55883587", "delivery_method": "pickup",
            "payment_method": "bank_transfer", "accepted_terms": "on",
        })
        order = Order.objects.get()
        found = self.client.post("/shop/track/", {"number": order.number.lower(), "phone": "+974 5588 3587"})
        self.assertContains(found, order.number)
        self.assertContains(found, "Bank transfer details")
        wrong = self.client.post("/shop/track/", {"number": order.number, "phone": "33333333"})
        self.assertContains(wrong, "No order found")
        # success page is not accessible to strangers
        self.client.logout()
        self.client.session.flush()
        self.assertEqual(self.client.get(f"/shop/order/{order.number}/success/").status_code, 302)

    # -- forms -------------------------------------------------------------
    def test_contact_form_and_honeypot(self):
        ok = self.client.post("/contact/", {"name": "A", "email": "a@b.com", "subject": "Hi", "message": "Hello", "website": ""})
        self.assertEqual(ok.status_code, 302)
        spam = self.client.post("/contact/", {"name": "A", "email": "a@b.com", "subject": "Hi", "message": "Hello", "website": "http://spam"})
        self.assertEqual(spam.status_code, 200)

    def test_quote_request(self):
        response = self.client.post("/services/request-quote/", {
            "service": self.service.pk, "name": "B", "email": "b@b.com", "phone": "33905158", "details": "500 copies",
        })
        self.assertEqual(response.status_code, 302)

    def test_registration(self):
        response = self.client.post("/accounts/register/", {
            "first_name": "Sara", "email": "sara@example.com",
            "password1": "Strong-Passw0rd-2026", "password2": "Strong-Passw0rd-2026", "consent": "on",
        })
        self.assertEqual(response.status_code, 302)
        self.assertContains(self.client.get("/accounts/profile/"), "Sara")

    # -- admin -------------------------------------------------------------
    def test_admin_pages(self):
        self._fill_cart()
        self.client.post("/shop/checkout/", {
            "full_name": "Test", "email": "t@example.com", "phone": "55883587", "delivery_method": "pickup",
            "payment_method": "cod", "accepted_terms": "on",
        })
        order = Order.objects.get()
        self.client.force_login(self.admin)
        admin = "/" + settings.ADMIN_URL
        for path in [
            "", "catalog/product/", "catalog/product/add/", "catalog/category/", "catalog/service/",
            "catalog/quoterequest/", "cms/page/", "cms/homebanner/", "cms/contactmessage/",
            "cms/sitesettings/1/change/", "shop/order/", f"shop/order/{order.pk}/change/",
        ]:
            with self.subTest(url=admin + path):
                self.assertEqual(self.client.get(admin + path).status_code, 200)
        export = self.client.post(admin + "shop/order/", {"action": "export_csv", "_selected_action": [order.pk]})
        self.assertIn(order.number.encode(), export.content)
        self.client.post(admin + "shop/order/", {"action": "mark_confirmed", "_selected_action": [order.pk]})
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CONFIRMED)
