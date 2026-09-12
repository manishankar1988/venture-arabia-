"""Business decision (Sept 2026): stamps and services are shown without prices.
Prices are confirmed with the customer before production. Consumables keep their prices.
"""
from django.db import migrations


def remove_prices(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    Category = apps.get_model("catalog", "Category")
    Service = apps.get_model("catalog", "Service")

    stamp_roots = Category.objects.filter(slug__in=["trodat-self-inking-stamps", "date-stamps"])
    stamp_categories = list(stamp_roots) + list(Category.objects.filter(parent__in=stamp_roots))
    Product.objects.filter(category__in=stamp_categories).update(price=None, compare_at_price=None)

    Service.objects.update(starting_price=None, price_unit="")
    for old, new in (
        ("Free collection & delivery", "Collection & delivery across Doha"),
    ):
        Service.objects.filter(name=old).update(name=new)
    for s in Service.objects.all():
        changed = False
        for old, new in (("within Doha", "across Doha"), ("anywhere in Doha", "across Doha")):
            if old in s.description:
                s.description = s.description.replace(old, new); changed = True
            if old in s.short_description:
                s.short_description = s.short_description.replace(old, new); changed = True
        if changed:
            s.save(update_fields=["description", "short_description"])


class Migration(migrations.Migration):
    dependencies = [("catalog", "0002_price_optional_and_content")]
    operations = [migrations.RunPython(remove_prices, migrations.RunPython.noop)]
