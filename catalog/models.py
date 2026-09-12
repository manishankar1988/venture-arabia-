from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from .validators import validate_upload


class Category(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True)
    icon = models.CharField(
        max_length=40,
        blank=True,
        help_text="Optional emoji or short label shown when no image is set, e.g. 🖃",
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return f"{self.parent} › {self.name}" if self.parent else self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:category", args=[self.slug])

    @property
    def active_products(self):
        return self.products.filter(is_active=True)


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    sku = models.CharField("SKU / model number", max_length=60, unique=True, help_text="e.g. 4912")
    brand = models.CharField(max_length=60, blank=True, default="Trodat")
    short_description = models.CharField(max_length=250, blank=True)
    description = models.TextField(blank=True, help_text="Plain text. Blank lines start a new paragraph.")

    price = models.DecimalField(
        "Price (QAR)",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Leave empty to show 'Price on request' - the price is then confirmed with the customer before production.",
    )
    compare_at_price = models.DecimalField(
        "Compare-at price (QAR)",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Optional. Shown crossed out to indicate a discount.",
    )

    track_stock = models.BooleanField(default=False, help_text="Untick for made-to-order items such as custom stamps.")
    stock_quantity = models.PositiveIntegerField(default=0)

    # Stamp-specific attributes (all optional)
    plate_size = models.CharField("Max. text plate size", max_length=60, blank=True, help_text="e.g. 47 mm x 18 mm")
    ink_cartridge = models.CharField("Replacement ink cartridge", max_length=60, blank=True, help_text="e.g. 6/4912")
    date_size = models.CharField(max_length=30, blank=True, help_text="For daters, e.g. 4 mm")
    available_colours = models.CharField(
        "Body colours", max_length=200, blank=True, help_text="Comma separated, e.g. Black, Blue, Red"
    )
    ink_colours = models.CharField(
        max_length=200, blank=True, default="Black, Blue, Red, Green, Violet", help_text="Comma separated"
    )

    is_customisable = models.BooleanField(
        "Requires custom text / artwork",
        default=False,
        help_text="If ticked, customers must enter the stamp text or upload artwork when ordering.",
    )
    customisation_help = models.CharField(
        max_length=250,
        blank=True,
        default="Enter the exact text for your stamp (line by line). We will send you a proof before production.",
    )

    image = models.ImageField(upload_to="products/", blank=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]
        indexes = [models.Index(fields=["is_active", "is_featured"])]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.sku}")
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:product_detail", args=[self.slug])

    @property
    def in_stock(self):
        return not self.track_stock or self.stock_quantity > 0

    @property
    def has_price(self):
        return self.price is not None

    @property
    def is_on_sale(self):
        return bool(self.has_price and self.compare_at_price and self.compare_at_price > self.price)

    @property
    def discount_percent(self):
        if not self.is_on_sale:
            return 0
        return int(round((1 - self.price / self.compare_at_price) * 100))

    @property
    def colour_list(self):
        return [c.strip() for c in self.available_colours.split(",") if c.strip()]

    @property
    def ink_colour_list(self):
        return [c.strip() for c in self.ink_colours.split(",") if c.strip()]

    @property
    def spec_rows(self):
        rows = [
            ("Model", self.sku),
            ("Brand", self.brand),
            ("Max. text plate size", self.plate_size),
            ("Date size", self.date_size),
            ("Replacement ink cartridge", self.ink_cartridge),
            ("Body colours", self.available_colours),
            ("Ink colours", self.ink_colours),
        ]
        return [(k, v) for k, v in rows if v]


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/gallery/")
    alt_text = models.CharField(max_length=150, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"Image for {self.product}"


class Service(models.Model):
    class Icon(models.TextChoices):
        STAMP = "stamp", "Stamp"
        PRINT = "print", "Printer"
        COPY = "copy", "Photocopier"
        LAMINATE = "laminate", "Laminating"
        BIND = "bind", "Binding"
        TONER = "toner", "Toner"
        DELIVERY = "delivery", "Delivery van"
        DESIGN = "design", "Design"

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True)
    icon = models.CharField(max_length=20, choices=Icon.choices, default=Icon.PRINT)
    short_description = models.CharField(max_length=250)
    description = models.TextField(help_text="Plain text. Blank lines start a new paragraph.")
    starting_price = models.DecimalField(
        "Starting price (QAR)", max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    price_unit = models.CharField(max_length=40, blank=True, help_text="e.g. per page, per stamp, per document")
    turnaround = models.CharField(max_length=80, blank=True, help_text="e.g. Same day, 1-2 working days")
    image = models.ImageField(upload_to="services/", blank=True)
    is_featured = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:service_detail", args=[self.slug])


class QuoteRequest(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        QUOTED = "quoted", "Quote sent"
        WON = "won", "Won"
        CLOSED = "closed", "Closed"

    service = models.ForeignKey(Service, null=True, blank=True, on_delete=models.SET_NULL, related_name="quotes")
    name = models.CharField(max_length=100)
    company = models.CharField(max_length=120, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    quantity = models.CharField(max_length=60, blank=True, help_text="e.g. 500 pages, 3 stamps")
    details = models.TextField()
    attachment = models.FileField(upload_to="quotes/%Y/%m/", blank=True, validators=[validate_upload])
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    internal_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Quote #{self.pk} - {self.name}"
