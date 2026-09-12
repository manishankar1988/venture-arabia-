from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse


class SingletonModel(models.Model):
    """Base class for models that must have exactly one row (site settings)."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):  # pragma: no cover - guard only
        raise ValueError("The site settings record cannot be deleted.")

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class SiteSettings(SingletonModel):
    """Company details and store configuration - editable from the admin panel."""

    company_name = models.CharField(max_length=120, default="Venture Arabia Trading Services")
    tagline = models.CharField(
        max_length=200,
        default="Authorised Trodat stamp dealer in Doha since 2009 - rubber stamps, toners, printing & office services.",
    )
    logo = models.ImageField(upload_to="branding/", blank=True, help_text="PNG or SVG, ideally with a transparent background.")

    # Legal identity (required for e-commerce transparency under Qatar Law No. 16 of 2010)
    legal_name = models.CharField(max_length=200, default="Venture Arabia Trading Services")
    commercial_registration = models.CharField(
        "Commercial Registration (CR) number",
        max_length=50,
        blank=True,
        help_text="Shown in the footer and on invoices. Required for online trading in Qatar.",
    )
    trade_licence = models.CharField("Trade licence number", max_length=50, blank=True)

    # Address
    po_box = models.CharField("P.O. Box", max_length=30, default="201678")
    building = models.CharField(max_length=60, default="Building No. 441, Office No. 2, First Floor")
    zone = models.CharField(max_length=20, default="Zone 56")
    street = models.CharField(max_length=60, default="Street 340")
    landmark = models.CharField(max_length=120, default="Near Al Ahli Bank building")
    area = models.CharField(max_length=120, default="Salwa Road")
    city = models.CharField(max_length=60, default="Doha")
    country = models.CharField(max_length=60, default="Qatar")
    google_maps_embed_url = models.URLField(
        blank=True, help_text="Optional 'Embed a map' URL from Google Maps (the src of the iframe)."
    )
    google_maps_link = models.URLField(blank=True, help_text="Optional 'Share' link to open the location in Google Maps.")

    # Contact
    phone = models.CharField(max_length=30, default="+974 4468 9269")
    mobile_1 = models.CharField(max_length=30, default="+974 5588 3587")
    mobile_2 = models.CharField(max_length=30, blank=True, default="+974 3390 5158")
    whatsapp_number = models.CharField(
        max_length=20,
        default="97455883587",
        help_text="Digits only, with country code and no plus sign, e.g. 97455883587.",
    )
    email = models.EmailField(default="venture@venture.com.qa")
    email_secondary = models.EmailField(blank=True, default="venstationery@gmail.com")
    opening_hours = models.TextField(
        default="Saturday - Thursday: 8:00 AM - 1:00 PM, 4:00 PM - 9:00 PM\nFriday: Closed",
        help_text="One line per entry.",
    )

    # Social
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)

    # Store configuration
    currency_code = models.CharField(max_length=3, default="QAR")
    delivery_fee = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("20.00"), validators=[MinValueValidator(0)]
    )
    free_delivery_threshold = models.DecimalField(
        "Free delivery for orders above",
        max_digits=8,
        decimal_places=2,
        default=Decimal("200.00"),
        validators=[MinValueValidator(0)],
        help_text="Set to 0 to disable free delivery.",
    )
    tax_rate_percent = models.DecimalField(
        "Tax / VAT rate (%)",
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(0)],
        help_text="Qatar currently applies no VAT on these goods. Update here if legislation changes.",
    )
    enable_cash_on_delivery = models.BooleanField(default=True)
    enable_bank_transfer = models.BooleanField(default=True)
    enable_card_on_delivery = models.BooleanField(
        "Enable card payment on delivery (POS machine)", default=True
    )
    bank_name = models.CharField(max_length=120, blank=True)
    bank_account_name = models.CharField(max_length=120, blank=True)
    bank_iban = models.CharField("IBAN", max_length=40, blank=True)
    bank_instructions = models.TextField(
        blank=True,
        default="Please transfer the total amount and send the transfer receipt to our WhatsApp with your order number.",
    )

    # Content
    announcement_bar = models.CharField(
        max_length=200,
        blank=True,
        default="Free collection & delivery within Doha | Special photocopy rates for schools, colleges and corporate offices",
    )
    about_text = models.TextField(
        default=(
            "Venture Arabia Trading Services has been an authorised Trodat stamps dealer in Qatar since 2009. "
            "We manufacture all types of rubber and self-inking stamps, supply computer toners and accessories, "
            "and provide printing, photocopying, laminating and binding services with free collection and delivery."
        )
    )
    footer_text = models.CharField(max_length=250, blank=True, default="All prices are in Qatari Riyal (QAR).")
    meta_description = models.CharField(
        max_length=160,
        default="Trodat stamps, rubber stamps, toners, printing, photocopying, laminating and binding in Doha, Qatar. Free collection and delivery.",
    )

    class Meta:
        verbose_name = "Site settings"
        verbose_name_plural = "Site settings"

    def __str__(self):
        return self.company_name

    @property
    def full_address(self):
        parts = [self.building, self.zone, self.street, self.landmark, self.area, self.city, self.country]
        return ", ".join(p for p in parts if p)

    @property
    def whatsapp_link(self):
        return f"https://wa.me/{self.whatsapp_number}" if self.whatsapp_number else ""

    @property
    def opening_hours_lines(self):
        return [line.strip() for line in self.opening_hours.splitlines() if line.strip()]


class Page(models.Model):
    """A CMS page such as About, Privacy Policy, Terms & Conditions."""

    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True)
    body = models.TextField(help_text="HTML is allowed. Only trusted staff should edit this content.")
    meta_description = models.CharField(max_length=160, blank=True)
    is_published = models.BooleanField(default=True)
    show_in_footer = models.BooleanField(default=True)
    show_in_nav = models.BooleanField("Show in main navigation", default=False)
    sort_order = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("cms:page", args=[self.slug])


class HomeBanner(models.Model):
    """Hero slides on the home page."""

    title = models.CharField(max_length=120)
    subtitle = models.CharField(max_length=250, blank=True)
    image = models.ImageField(upload_to="banners/", blank=True, help_text="Recommended 1600 x 700 px.")
    button_text = models.CharField(max_length=40, blank=True, default="Shop now")
    button_url = models.CharField(max_length=200, blank=True, default="/products/")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title


class Testimonial(models.Model):
    author = models.CharField(max_length=100)
    organisation = models.CharField(max_length=120, blank=True)
    quote = models.TextField()
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.author} - {self.organisation}" if self.organisation else self.author


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    subject = models.CharField(max_length=150)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} ({self.name})"
