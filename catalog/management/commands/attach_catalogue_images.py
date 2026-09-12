"""
Links the product photos cropped from the Trodat dealer catalogue (media/products/)
to the seeded products, categories and home banner. Safe to re-run.
"""
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from catalog.models import Category, Product, ProductImage
from cms.models import HomeBanner

# Products whose photo and imprint sample share their own SKU-named file
OWN_PHOTO = [
    "4911", "4912", "4913", "4914", "4915", "4916", "4917", "4918", "4925", "4926", "4927", "4928", "4929",
    "4931", "4941", "4921", "4922", "4923", "4924", "4933", "4612", "46019", "46025", "4630", "4638", "4642",
    "4911-TEXTILE", "4726", "4727", "4729", "4645", "46050", "44045", "44055", "4730", "4731", "4750",
    "4750/L1", "4750/L2", "4750/L9",
]
# Products that use a shared/generic catalogue photo
SHARED_PHOTO = {
    "9051": "pads-9051", "9052": "pads-9052", "9053": "pads-9053", "9054": "pads-9054",
    "7011": "ink-bottles",
    # Professional models are shown in the range photo only
    "5460": "daters-group", "5211": "printy-range",
}
CATEGORY_IMAGES = {
    "trodat-self-inking-stamps": "printy-range",
    "text-stamps-rectangular": "4912",
    "square-stamps": "4924",
    "round-stamps": "4630",
    "oval-stamps": "44045",
    "date-stamps": "daters-group",
    "ink-cartridges-stamp-pads": "pads-and-inks",
}


def fname(sku):
    return sku.replace("/", "-").lower() + ".jpg"


class Command(BaseCommand):
    help = "Attach catalogue images in media/products to products, categories and the home banner."

    def handle(self, *args, **options):
        media = Path(settings.MEDIA_ROOT)
        products_dir = media / "products"
        gallery_dir = products_dir / "gallery"
        attached = 0

        def set_image(product, rel):
            nonlocal attached
            if (media / rel).exists():
                product.image.name = rel
                product.save(update_fields=["image"])
                attached += 1
            else:
                self.stderr.write(f"missing {rel} for {product.sku}")

        for sku in OWN_PHOTO:
            product = Product.objects.filter(sku=sku).first()
            if not product:
                self.stderr.write(f"product {sku} not found")
                continue
            set_image(product, f"products/{fname(sku)}")
            imprint = gallery_dir / (fname(sku)[:-4] + "-imprint.jpg")
            if imprint.exists():
                ProductImage.objects.get_or_create(
                    product=product,
                    image=f"products/gallery/{imprint.name}",
                    defaults={"alt_text": f"Sample impression of Trodat {sku}", "sort_order": 1},
                )

        for sku, name in SHARED_PHOTO.items():
            product = Product.objects.filter(sku=sku).first()
            if product:
                set_image(product, f"products/{name}.jpg")

        # Every 1- and 2-colour ink cartridge gets the cartridge photo
        for product in Product.objects.filter(sku__startswith="6/"):
            set_image(product, "products/cartridges.jpg")

        # Category images
        cat_dir = media / "categories"
        cat_dir.mkdir(exist_ok=True)
        for slug, name in CATEGORY_IMAGES.items():
            cat = Category.objects.filter(slug=slug).first()
            src = products_dir / f"{name}.jpg"
            if cat and src.exists():
                dst = cat_dir / f"{slug}.jpg"
                shutil.copyfile(src, dst)
                cat.image.name = f"categories/{slug}.jpg"
                cat.save(update_fields=["image"])

        # Home banner
        banner = HomeBanner.objects.order_by("sort_order", "id").first()
        src = products_dir / "printy-range.jpg"
        if banner and src.exists() and not banner.image:
            (media / "banners").mkdir(exist_ok=True)
            shutil.copyfile(src, media / "banners" / "printy-range.jpg")
            banner.image.name = "banners/printy-range.jpg"
            banner.save(update_fields=["image"])

        without = Product.objects.filter(image="").count()
        self.stdout.write(self.style.SUCCESS(f"Attached {attached} product images; {without} products still without a photo."))
        for p in Product.objects.filter(image=""):
            self.stdout.write(f"  no photo: {p.sku} - {p.name}")
