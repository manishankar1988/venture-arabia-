from decimal import Decimal

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending confirmation"
        CONFIRMED = "confirmed", "Confirmed"
        PROCESSING = "processing", "In production / processing"
        READY = "ready", "Ready for collection"
        OUT_FOR_DELIVERY = "out_for_delivery", "Out for delivery"
        DELIVERED = "delivered", "Delivered / collected"
        CANCELLED = "cancelled", "Cancelled"

    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", "Unpaid"
        PAID = "paid", "Paid"
        REFUNDED = "refunded", "Refunded"

    class PaymentMethod(models.TextChoices):
        COD = "cod", "Cash on delivery"
        CARD_ON_DELIVERY = "card_on_delivery", "Card on delivery (POS)"
        BANK_TRANSFER = "bank_transfer", "Bank transfer"

    class DeliveryMethod(models.TextChoices):
        DELIVERY = "delivery", "Home / office delivery"
        PICKUP = "pickup", "Collect from our office (Salwa Road)"

    number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders"
    )

    # Customer
    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    company = models.CharField(max_length=120, blank=True)

    # Delivery
    delivery_method = models.CharField(max_length=20, choices=DeliveryMethod.choices, default=DeliveryMethod.DELIVERY)
    building = models.CharField(max_length=120, blank=True)
    zone = models.CharField(max_length=20, blank=True)
    street = models.CharField(max_length=60, blank=True)
    area = models.CharField(max_length=120, blank=True)
    city = models.CharField(max_length=60, blank=True, default="Doha")
    delivery_notes = models.TextField(blank=True)

    # Payment
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.COD)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)

    # Money (snapshotted at checkout)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    tax_rate_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="QAR")

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    staff_notes = models.TextField(blank=True, help_text="Internal notes - never shown to the customer.")
    accepted_terms = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.number

    @staticmethod
    def generate_number():
        year = timezone.now().year
        prefix = f"VA{year}-"
        with transaction.atomic():
            last = Order.objects.select_for_update().filter(number__startswith=prefix).order_by("-number").first()
            seq = int(last.number.split("-")[-1]) + 1 if last else 1
        return f"{prefix}{seq:05d}"

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self.generate_number()
        super().save(*args, **kwargs)

    @property
    def delivery_address(self):
        if self.delivery_method == self.DeliveryMethod.PICKUP:
            return "Collection from Venture Arabia office"
        parts = [self.building, f"Zone {self.zone}" if self.zone else "", f"Street {self.street}" if self.street else "", self.area, self.city]
        return ", ".join(p for p in parts if p)

    @property
    def has_unpriced_items(self):
        return self.items.filter(unit_price__isnull=True).exists()

    @property
    def is_open(self):
        return self.status not in {self.Status.DELIVERED, self.Status.CANCELLED}

    def recalculate(self, delivery_fee=None, tax_rate=None):
        self.subtotal = sum((i.line_total for i in self.items.all()), Decimal("0.00"))
        if delivery_fee is not None:
            self.delivery_fee = delivery_fee
        if tax_rate is not None:
            self.tax_rate_percent = tax_rate
        self.tax_amount = (self.subtotal * self.tax_rate_percent / Decimal("100")).quantize(Decimal("0.01"))
        self.total = self.subtotal + self.delivery_fee + self.tax_amount


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("catalog.Product", null=True, on_delete=models.SET_NULL, related_name="order_items")
    product_name = models.CharField(max_length=200)
    sku = models.CharField(max_length=60)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Empty = price to be confirmed with the customer.")
    quantity = models.PositiveIntegerField(default=1)
    custom_text = models.TextField(blank=True, help_text="Stamp text or customisation instructions supplied by the customer.")

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

    @property
    def has_price(self):
        return self.unit_price is not None

    @property
    def line_total(self):
        if self.unit_price is None or self.quantity is None:
            return Decimal("0.00")
        return self.unit_price * self.quantity
