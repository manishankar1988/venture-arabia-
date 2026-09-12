"""
Loads the initial catalogue (Trodat stamps from the dealer catalogue), services,
site settings and the legal/CMS pages required for trading online in Qatar.

Safe to run more than once: existing records (matched by slug / SKU) are kept
and only missing ones are created. Prices are INDICATIVE placeholders in QAR
and must be updated from the admin panel before going live.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from catalog.models import Category, Product, Service
from cms.models import HomeBanner, Page, SiteSettings

from ._legal_pages import LEGAL_PAGES

INK = "Black, Blue, Red, Green, Violet"
BODY_STD = "Black, Blue, Red, Grey"
BODY_WIDE = "Black, Blue, Red, Grey, Green, Yellow, White, Pink, Light blue, Violet"

# (sku, name, plate size, cartridge, body colours, price, featured, extra description)
TEXT_STAMPS = [
    ("4911", "Trodat Printy 4911 self-inking text stamp", "38 mm x 14 mm", "6/4911", BODY_WIDE, "45.00", True, "Ideal for 1-3 lines of text such as name and phone number, 'PAID', 'COPY' or 'ORIGINAL'. Optional protective cap."),
    ("4912", "Trodat Printy 4912 self-inking text stamp", "47 mm x 18 mm", "6/4912", BODY_WIDE, "55.00", True, "Our most popular size - suitable for 3-4 lines: company name, address and phone number. Optional protective cap."),
    ("4913", "Trodat Printy 4913 self-inking text stamp", "58 mm x 22 mm", "6/4913", BODY_WIDE, "65.00", True, "Room for up to 5 lines including a small logo. Optional protective cap."),
    ("4914", "Trodat Printy 4914 self-inking text stamp", "64 mm x 26 mm", "6/4914", BODY_WIDE, "75.00", False, "Large address stamp with space for a logo and up to 6 lines of text. Optional protective cap."),
    ("4915", "Trodat Printy 4915 self-inking text stamp", "70 mm x 25 mm", "6/4915", BODY_WIDE, "85.00", False, "Wide-format text stamp for letterheads, company details and signatures."),
    ("4916", "Trodat Printy 4916 self-inking text stamp", "70 mm x 10 mm", "6/4916", "Black", "55.00", False, "Slim single-line stamp for names, signatures or reference numbers."),
    ("4917", "Trodat Printy 4917 self-inking text stamp", "50 mm x 10 mm", "6/4817", "Black", "50.00", False, "Compact single-line stamp - perfect for signature stamps."),
    ("4918", "Trodat Printy 4918 self-inking text stamp", "75 mm x 15 mm", "6/4918", BODY_STD, "70.00", False, "Wide two-line stamp for company name and contact line."),
    ("4925", "Trodat Printy 4925 self-inking text stamp", "82 mm x 25 mm", "6/4925", BODY_STD, "95.00", False, "Extra-wide text stamp for long company names and addresses."),
    ("4926", "Trodat Printy 4926 self-inking text stamp", "75 mm x 38 mm", "6/4926", BODY_STD, "110.00", True, "Large-format stamp for detailed company information, logos and multi-line text."),
    ("4927", "Trodat Printy 4927 self-inking text stamp", "60 mm x 40 mm", "6/4927", BODY_STD + ", Green", "100.00", False, "Tall rectangular stamp suitable for logos with several lines of text."),
    ("4928", "Trodat Printy 4928 self-inking text stamp", "60 mm x 33 mm", "6/4928", BODY_STD, "95.00", False, "Rectangular stamp for company details with logo."),
    ("4929", "Trodat Printy 4929 self-inking text stamp", "50 mm x 30 mm", "6/4929", BODY_STD, "85.00", False, "Medium rectangular stamp for company details or approval stamps."),
    ("4931", "Trodat Printy 4931 self-inking text stamp", "70 mm x 30 mm", "6/4931", BODY_STD, "100.00", False, "Wide rectangular stamp for company details and logos."),
    ("4941", "Trodat Printy 4941 self-inking text stamp", "41 mm x 24 mm", "6/4750", "Black", "80.00", False, "Compact stamp with the same plate size as the 4750 dater."),
]

SQUARE_STAMPS = [
    ("4921", "Trodat Printy 4921 square stamp", "12 mm x 12 mm", "6/4921", "Black, Blue, Red", "40.00", False, "Tiny square stamp for initials, tick marks or 'OK'. Optional protective cap."),
    ("4922", "Trodat Printy 4922 square stamp", "20 mm x 20 mm", "6/4922", "Black, Blue, Red", "50.00", False, "Small square stamp for symbols and short marks. Optional protective cap."),
    ("4923", "Trodat Printy 4923 square stamp", "30 mm x 30 mm", "6/4923", "Black, Blue, Red", "60.00", False, "Square stamp for approval marks, logos and control stamps."),
    ("4924", "Trodat Printy 4924 square stamp", "40 mm x 40 mm", "6/4924", BODY_STD + ", White, Green", "75.00", True, "Large square stamp - ideal for logos and company seals."),
    ("4933", "Trodat Printy 4933 square stamp", "25 mm x 25 mm", "6/4933", "Black, Blue, Red", "60.00", False, "Square stamp supplied with protective cap - great for pocket use."),
]

ROUND_STAMPS = [
    ("4612", "Trodat Printy 4612 round stamp", "Ø 12 mm", "6/4612", "Black", "45.00", False, "Miniature round stamp with protective cap."),
    ("46019", "Trodat Printy 46019 round stamp", "Ø 19 mm", "6/46019", BODY_STD, "50.00", False, "Small round stamp with protective cap - logos and monograms."),
    ("46025", "Trodat Printy 46025 round stamp", "Ø 25 mm", "6/46025", BODY_STD, "60.00", False, "Round stamp with protective cap for logos and short circular text."),
    ("4630", "Trodat Printy 4630 round stamp", "Ø 30 mm", "6/4630", BODY_STD, "65.00", True, "Popular round stamp size for company seals. Optional protective cap."),
    ("4638", "Trodat Printy 4638 round stamp", "Ø 38 mm", "6/4638", "Black, Blue, Red", "75.00", False, "Round stamp for official company seals. Optional protective cap."),
    ("4642", "Trodat Printy 4642 round stamp", "Ø 42 mm", "6/4642", BODY_STD, "85.00", True, "Large round company seal supplied with protective cap."),
    ("4645", "Trodat Printy 4645 round stamp", "Ø 45 mm", "6/4645", BODY_STD, "95.00", False, "Large round stamp for detailed circular seals."),
    ("46050", "Trodat Printy 46050 round stamp", "Ø 50 mm", "6/46050", "Black", "110.00", False, "Extra-large round stamp with protective cap."),
]

OVAL_STAMPS = [
    ("44045", "Trodat Printy 44045 oval stamp", "45 mm x 30 mm", "6/44045", BODY_STD, "85.00", False, "Oval stamp for elegant logos and seals."),
    ("44055", "Trodat Printy 44055 oval stamp", "55 mm x 35 mm", "6/44055", BODY_STD, "95.00", False, "Large oval stamp for logos with surrounding text."),
]

DATERS = [
    ("4726", "Trodat Printy 4726 dater with text", "75 mm x 38 mm", "6/4926 (1-colour) or 6/4926/2 (2-colour)", "4 mm", "Black", "150.00", True, "Large dater with custom text above and below the date. Ideal for 'RECEIVED', 'APPROVED' or delivery stamps."),
    ("4727", "Trodat Printy 4727 dater with text", "60 mm x 40 mm", "6/4927 (1-colour) or 6/4927/2 (2-colour)", "4 mm", "Black", "140.00", False, "Dater with generous space for text and logo around the date."),
    ("4729", "Trodat Printy 4729 dater with text", "50 mm x 30 mm", "6/4929 (1-colour) or 6/4929/2 (2-colour)", "3 mm", "Red", "120.00", False, "Compact dater with custom text, 3 mm date."),
    ("4730", "Trodat Printy 4730 dater with text", "56 mm x 33 mm", "6/4927 (1-colour) or 6/4927/2 (2-colour)", "4 mm", "Black", "130.00", False, "Dater with custom text - a favourite for accounts departments."),
    ("4731", "Trodat Printy 4731 dater with text", "70 mm x 30 mm", "6/4931 (1-colour) or 6/4931/2 (2-colour)", "3 mm", "Red", "150.00", False, "Wide dater with custom text on either side of the date."),
    ("4750", "Trodat Printy 4750 dater with text", "41 mm x 24 mm", "6/4750 (1-colour) or 6/4750/2 (2-colour)", "4 mm", "Black", "110.00", True, "The classic office dater with one line of custom text above and below the date."),
]

INK_CARTRIDGES = [
    ("6/4911", "4911", "22.00"), ("6/4912", "4912", "22.00"), ("6/4913", "4913", "24.00"), ("6/4914", "4914", "25.00"),
    ("6/4915", "4915", "25.00"), ("6/4916", "4916", "22.00"), ("6/4817", "4917", "22.00"), ("6/4918", "4918", "25.00"),
    ("6/4925", "4925", "28.00"), ("6/4926", "4926 / 4726", "30.00"), ("6/4927", "4927 / 4727 / 4730", "30.00"),
    ("6/4928", "4928", "28.00"), ("6/4929", "4929 / 4729", "28.00"), ("6/4931", "4931 / 4731", "30.00"),
    ("6/4750", "4750 / 4941", "25.00"), ("6/4921", "4921", "20.00"), ("6/4922", "4922", "20.00"), ("6/4923", "4923", "22.00"),
    ("6/4924", "4924", "25.00"), ("6/4933", "4933", "22.00"), ("6/4612", "4612", "20.00"), ("6/46019", "46019", "20.00"),
    ("6/46025", "46025", "22.00"), ("6/4630", "4630", "22.00"), ("6/4638", "4638", "24.00"), ("6/4642", "4642", "25.00"),
    ("6/4645", "4645", "25.00"), ("6/46050", "46050", "28.00"), ("6/44045", "44045", "25.00"), ("6/44055", "44055", "26.00"),
]
TWO_COLOUR_CARTRIDGES = [
    ("6/4926/2", "4726", "38.00"), ("6/4927/2", "4727 / 4730", "38.00"), ("6/4929/2", "4729", "35.00"),
    ("6/4931/2", "4731", "38.00"), ("6/4750/2", "4750 / 4750/L", "32.00"),
]

STAMP_PADS = [
    ("9051", "Trodat 9051 stamp pad", "90 mm x 50 mm", "25.00"),
    ("9052", "Trodat 9052 stamp pad", "110 mm x 70 mm", "35.00"),
    ("9053", "Trodat 9053 stamp pad", "160 mm x 90 mm", "50.00"),
    ("9054", "Trodat 9054 stamp pad", "210 mm x 130 mm", "70.00"),
]

SERVICES = [
    ("Custom rubber stamp making", "stamp", "All types of rubber, self-inking and pre-inked stamps made to order - company seals, signature stamps, daters, Arabic & English text and logos.", "Send us your text or artwork and we will prepare a proof for approval before production. We stock the complete Trodat Printy and Professional ranges and can also make traditional wooden-handle rubber stamps, pocket stamps and heavy-duty metal-frame stamps.\n\nTypical turnaround is the same or next working day. Bulk orders for schools, clinics, ministries and corporate offices are welcome.", None, "", "Same / next working day"),
    ("Photocopying (B&W and colour)", "copy", "High-volume black & white and colour photocopying with special rates for schools, colleges and corporate offices.", "A4 and A3 photocopying in black & white or full colour, single or double sided, with optional stapling, hole punching and sorting.\n\nWe offer special contract rates for schools, colleges, training centres and corporate offices, and collect and deliver documents free of charge across Doha.", None, "", "Same day for most jobs"),
    ("Printing", "print", "Digital printing of documents, letterheads, business cards, flyers, certificates, labels and more.", "Short-run digital printing on a range of paper stocks. We print reports, proposals, training manuals, letterheads, business cards, invitation cards, flyers, certificates and stickers.\n\nSend us your files (PDF preferred) or let us help with the layout. Free collection and delivery across Doha.", None, "", "1-2 working days"),
    ("Laminating", "laminate", "Protect documents, certificates, ID cards and menus with gloss or matt lamination.", "Pouch lamination from ID-card size up to A3, in gloss or matt finish. Ideal for certificates, notices, menus, name badges and classroom materials.", None, "", "Same day"),
    ("Binding", "bind", "Spiral, comb, thermal and hard-cover binding for reports, theses, manuals and proposals.", "Choose from plastic comb binding, metal spiral (wire-o) binding, thermal binding and hard-cover binding with clear or coloured covers. Suitable for reports, dissertations, tender documents, training manuals and presentations.", None, "", "Same / next working day"),
    ("Computer toners & accessories", "toner", "Original and compatible toner cartridges plus printer accessories for HP, Canon, Brother, Samsung, Kyocera and more.", "We supply original and high-quality compatible toner and ink cartridges for all major printer brands, along with drums, fusers, paper and other consumables.\n\nTell us your printer model and we will quote the best available option with free delivery to your office.", None, "", "Same / next working day"),
    ("Collection & delivery across Doha", "delivery", "We collect your documents and deliver finished work across Doha at no extra charge.", "For photocopying, printing, laminating and binding jobs we collect your originals from your school, college or office and return the finished work - free of charge, across Doha. Simply call, WhatsApp or request a quote and our driver will be in touch.", None, "", "Scheduled with your order"),
]


class Command(BaseCommand):
    help = "Seed the database with site settings, the Trodat catalogue, services and legal pages."

    @transaction.atomic
    def handle(self, *args, **options):
        SiteSettings.load()
        self.stdout.write("Site settings ready.")

        cat_stamps = self._category("Trodat Self-Inking Stamps", 1, "Original Trodat Printy 4.0 self-inking stamps - the world's best-selling stamp range, climate-neutral and made in Austria. Every stamp is made to order with your own text or logo.", "🖃")
        cat_text = self._category("Text Stamps (Rectangular)", 1, "Rectangular self-inking text stamps for addresses, signatures and company details.", "▭", parent=cat_stamps)
        cat_square = self._category("Square Stamps", 2, "Square self-inking stamps for logos, approval marks and control stamps.", "◻", parent=cat_stamps)
        cat_round = self._category("Round Stamps", 3, "Round self-inking stamps for company seals and logos.", "◯", parent=cat_stamps)
        cat_oval = self._category("Oval Stamps", 4, "Oval self-inking stamps.", "⬭", parent=cat_stamps)
        cat_dater = self._category("Date Stamps", 2, "Self-inking daters with custom text, stock text (RECEIVED, PAID, FAXED) and professional heavy-duty daters.", "📅")
        cat_ink = self._category("Ink Cartridges & Stamp Pads", 3, "Replacement ink cartridges for every Trodat model, hand stamp pads and refill inks. Printy 4.0 cartridges also fit older Printy models.", "🧴")
        cat_toner = self._category("Computer Toners & Accessories", 4, "Original and compatible toner cartridges and printer accessories for all major brands. Contact us with your printer model for a quote.", "🖨")

        for sku, name, plate, cart, colours, price, featured, desc in TEXT_STAMPS:
            self._stamp(cat_text, sku, name, plate, cart, colours, price, featured, desc)
        for sku, name, plate, cart, colours, price, featured, desc in SQUARE_STAMPS:
            self._stamp(cat_square, sku, name, plate, cart, colours, price, featured, desc)
        for sku, name, plate, cart, colours, price, featured, desc in ROUND_STAMPS:
            self._stamp(cat_round, sku, name, plate, cart, colours, price, featured, desc)
        for sku, name, plate, cart, colours, price, featured, desc in OVAL_STAMPS:
            self._stamp(cat_oval, sku, name, plate, cart, colours, price, featured, desc)

        self._product(
            cat_text, "4911-TEXTILE", "Trodat Printy 4911 clothing marker", "38 mm x 14 mm", "6/4911 Textile", "Red", None, False,
            "Self-inking stamp with black textile ink for marking school uniforms, sports kits, towels and workwear. Withstands washing.",
            ink_colours="Black (textile)", customisable=True, short="Mark clothing and fabric with a permanent name stamp.",
        )

        for sku, name, plate, cart, date_size, colours, price, featured, desc in DATERS:
            self._product(cat_dater, sku, name, plate, cart, colours, None, featured, desc, date_size=date_size, customisable=True, short=f"Self-inking dater with custom text, {date_size} date, {plate} plate.")
        for suffix, text in (("L1", "RECEIVED"), ("L2", "PAID"), ("L9", "FAXED")):
            self._product(
                cat_dater, f"4750/{suffix}", f"Trodat Printy 4750/{suffix} '{text}' dater", "41 mm x 24 mm", "6/4750/2", "Black", None, False,
                f"Ready-made two-colour dater with the stock text '{text}' in blue and the date in red. No custom text required - ready to ship.",
                date_size="4 mm", customisable=False, ink_colours="Blue / Red (2-colour)", short=f"Stock-text dater: {text} + date. Ready to ship.",
            )
        self._product(cat_dater, "5460", "Trodat Professional 5460 dater with text", "56 mm x 33 mm", "6/56", "Black / Silver", None, True,
                      "Heavy-duty metal-frame self-inking dater for high-volume use in banks, ministries and accounts departments. Custom text above and below the date.", date_size="4 mm", customisable=True, short="Heavy-duty professional dater for high-volume use.")
        self._product(cat_stamps, "5211", "Trodat Professional 5211 text stamp", "85 mm x 55 mm", "6/5211", "Black / Silver", None, False,
                      "Extra-large heavy-duty text stamp with metal frame - for detailed company seals, delivery stamps and forms.", customisable=True, short="Extra-large heavy-duty text stamp.")

        for sku, fits, price in INK_CARTRIDGES:
            self._product(cat_ink, sku, f"Trodat ink cartridge {sku}", "", "", "", price, False,
                          f"Genuine Trodat replacement ink cartridge {sku} for Printy {fits}. Available in black, blue, red, green and violet. Simply press down the stamp and slide out the old pad to replace. Printy 4.0 cartridges also fit older Printy models.",
                          short=f"Replacement pad for Printy {fits}.", ink_colours=INK, track_stock=True, stock=25)
        for sku, fits, price in TWO_COLOUR_CARTRIDGES:
            self._product(cat_ink, sku, f"Trodat 2-colour ink cartridge {sku}", "", "", "", price, False,
                          f"Genuine Trodat two-colour replacement cartridge {sku} (blue text / red date) for Printy {fits} daters.",
                          short=f"Two-colour pad for Printy {fits}.", ink_colours="Blue / Red", track_stock=True, stock=10)
        for sku, name, size, price in STAMP_PADS:
            self._product(cat_ink, sku, name, size, "", "", price, False,
                          f"Trodat {sku} felt hand stamp pad, {size}, for traditional rubber stamps. Awarded the Austrian Ecolabel. Available in black, blue, red, green and violet.",
                          short=f"Hand stamp pad {size}.", ink_colours=INK, track_stock=True, stock=10)
        self._product(cat_ink, "7011", "Trodat 7011 stamp ink 28 ml", "", "", "", "20.00", False,
                      "Water-based refill ink for Trodat self-inking stamps and felt pads, 28 ml bottle. Available in black, blue, red, green and violet.",
                      short="Refill ink bottle for stamps and pads.", ink_colours=INK, track_stock=True, stock=20)

        self._product(cat_toner, "TONER-HP", "Toner cartridge for HP LaserJet printers", "", "", "", "150.00", False,
                      "Original and compatible toner cartridges for HP LaserJet and LaserJet Pro printers (e.g. 85A, 12A, 05A, 26A, 30A, 79A). Please state your printer model in the customisation box and we will confirm the exact cartridge and price before delivery.",
                      customisable=True, short="Original & compatible - tell us your printer model.", ink_colours="Black, Cyan, Magenta, Yellow", help="Enter your printer model (e.g. HP LaserJet Pro M404) and whether you need original or compatible.")
        self._product(cat_toner, "TONER-CANON", "Toner cartridge for Canon printers", "", "", "", "150.00", False,
                      "Original and compatible toner cartridges for Canon i-SENSYS and imageCLASS printers. State your printer model and we will confirm the exact cartridge and price.",
                      customisable=True, short="Original & compatible - tell us your printer model.", ink_colours="Black, Cyan, Magenta, Yellow", help="Enter your printer model and whether you need original or compatible.")
        self._product(cat_toner, "TONER-OTHER", "Toner / ink cartridge for other brands", "", "", "", "120.00", False,
                      "Toner and ink cartridges for Brother, Samsung, Kyocera, Xerox, Ricoh, Epson and other brands. State your printer model and we will confirm availability and price.",
                      customisable=True, short="Brother, Samsung, Kyocera, Xerox, Ricoh, Epson…", ink_colours="Black, Cyan, Magenta, Yellow", help="Enter your printer brand and model number.")
        self._product(cat_toner, "PAPER-A4", "A4 copy paper 80 gsm (ream of 500)", "", "", "", "22.00", False,
                      "Premium white A4 80 gsm multipurpose copier paper, 500 sheets per ream. Bulk discounts for boxes of 5 reams.",
                      short="500 sheets, 80 gsm.", ink_colours="", track_stock=True, stock=50)
        self.stdout.write(f"Products: {Product.objects.count()}")

        for i, (name, icon, short, desc, price, unit, turnaround) in enumerate(SERVICES):
            Service.objects.get_or_create(
                slug=slugify(name),
                defaults={
                    "name": name, "icon": icon, "short_description": short, "description": desc,
                    "starting_price": Decimal(price) if price else None, "price_unit": unit,
                    "turnaround": turnaround, "sort_order": i, "is_featured": True,
                },
            )
        self.stdout.write(f"Services: {Service.objects.count()}")

        for i, (slug, title, body) in enumerate(LEGAL_PAGES):
            Page.objects.get_or_create(
                slug=slug,
                defaults={"title": title, "body": body, "sort_order": i, "show_in_nav": slug == "about-us"},
            )
        self.stdout.write(f"Pages: {Page.objects.count()}")

        if not HomeBanner.objects.exists():
            HomeBanner.objects.create(
                title="Trodat stamps, toners and print services - delivered across Doha",
                subtitle="Trodat stamps dealer in Doha since 2009. Custom rubber stamps made the same day, genuine toners, and printing, photocopying, laminating and binding with free collection and delivery across Doha.",
                button_text="Shop stamps",
                button_url="/products/",
            )
        self.stdout.write(self.style.SUCCESS("Seed complete. Remember to review prices and legal pages in the admin panel."))

    # -- helpers -----------------------------------------------------------
    def _category(self, name, order, description, icon, parent=None):
        obj, _ = Category.objects.get_or_create(
            slug=slugify(name), defaults={"name": name, "sort_order": order, "description": description, "icon": icon, "parent": parent}
        )
        return obj

    def _stamp(self, category, sku, name, plate, cartridge, colours, price, featured, desc):
        # Stamps are shown without a price (price on request, confirmed before production)
        self._product(
            category, sku, name, plate, cartridge, colours, None, featured, desc,
            customisable=True, short=f"Self-inking text stamp, max. plate {plate}.",
        )

    def _product(self, category, sku, name, plate, cartridge, colours, price, featured, desc, *,
                 short="", date_size="", customisable=False, ink_colours=INK, track_stock=False, stock=0, help=""):
        defaults = {
            "category": category, "name": name, "plate_size": plate, "ink_cartridge": cartridge,
            "available_colours": colours, "price": Decimal(price) if price is not None else None, "is_featured": featured,
            "description": desc, "short_description": short, "date_size": date_size,
            "is_customisable": customisable, "ink_colours": ink_colours,
            "track_stock": track_stock, "stock_quantity": stock,
        }
        if help:
            defaults["customisation_help"] = help
        Product.objects.get_or_create(sku=sku, defaults=defaults)
