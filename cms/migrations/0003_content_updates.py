"""Content corrections requested by the company (Sept 2026):
- no 'Authorised' wording anywhere
- 'delivery across Doha'
- working hours 9-1 / 4-8
- delivery is free (no fee, no threshold)
Applied to rows that already exist; new installs get the same values from the model defaults / seed.
"""
from decimal import Decimal

from django.db import migrations

REPLACEMENTS = [
    ("Authorised Trodat stamp dealer", "Trodat stamp dealer"),
    ("Authorised Trodat dealer", "Trodat dealer"),
    ("an authorised Trodat stamps dealer", "a Trodat stamps dealer"),
    ("an authorised dealer of", "a dealer of"),
    ("Authorised dealer", "Trodat dealer"),
    ("authorised dealer", "dealer"),
    ("within Doha", "across Doha"),
    ("anywhere in Doha", "across Doha"),
    ("Free collection and delivery.", "Delivery across Doha."),
]


def fix_text(value):
    for old, new in REPLACEMENTS:
        value = value.replace(old, new)
    return value


def update_content(apps, schema_editor):
    SiteSettings = apps.get_model("cms", "SiteSettings")
    Page = apps.get_model("cms", "Page")
    HomeBanner = apps.get_model("cms", "HomeBanner")

    for s in SiteSettings.objects.all():
        s.tagline = fix_text(s.tagline)
        s.about_text = fix_text(s.about_text)
        s.announcement_bar = fix_text(s.announcement_bar)
        s.meta_description = fix_text(s.meta_description)
        if "8:00 AM - 1:00 PM, 4:00 PM - 9:00 PM" in s.opening_hours:
            s.opening_hours = s.opening_hours.replace("8:00 AM - 1:00 PM, 4:00 PM - 9:00 PM", "9:00 AM - 1:00 PM, 4:00 PM - 8:00 PM")
        s.delivery_fee = Decimal("0.00")
        s.free_delivery_threshold = Decimal("0.00")
        s.save()

    for p in Page.objects.all():
        body = fix_text(p.body)
        body = body.replace(
            "Orders above the amount shown at checkout qualify for free delivery.",
            "Delivery across Doha is free of charge.",
        )
        if body != p.body:
            p.body = body
            p.save(update_fields=["body"])

    for b in HomeBanner.objects.all():
        title, subtitle = fix_text(b.title), fix_text(b.subtitle)
        if (title, subtitle) != (b.title, b.subtitle):
            b.title, b.subtitle = title, subtitle
            b.save(update_fields=["title", "subtitle"])


class Migration(migrations.Migration):
    dependencies = [("cms", "0002_price_optional_and_content")]
    operations = [migrations.RunPython(update_content, migrations.RunPython.noop)]
