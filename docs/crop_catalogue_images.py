"""Requires: pip install pymupdf pillow
Crop product photos + imprint samples out of the scanned Trodat catalogue.
Coordinates are in the 120-dpi page space (992 x 1403 px); pages are rendered at 300 dpi.
"""
import os
import pymupdf
from PIL import Image, ImageOps

PDF = "trodat-catalogue.pdf"  # run this script from the docs/ folder: python crop_catalogue_images.py
OUT = "../media"
SCALE = 300 / 120

# sku: (page, photo box, imprint box or None)   boxes = (x0, y0, x1, y1) in 120-dpi px
PRODUCTS = {
    "4911":  (4, (150, 150, 275, 278), (285, 148, 478, 221)),
    "4912":  (4, (135, 405, 268, 532), (275, 410, 502, 507)),
    "4913":  (4, (125, 680, 258, 818), (262, 685, 542, 796)),
    "4914":  (4, (100, 945, 238, 1082), (245, 945, 562, 1077)),
    "4915":  (5, (110, 130, 248, 268), (255, 120, 602, 246)),
    "4916":  (5, (95, 400, 258, 532), (260, 385, 602, 442)),
    "4917":  (5, (110, 630, 243, 772), (255, 620, 502, 672)),
    "4918":  (5, (95, 860, 248, 992), (255, 850, 612, 927)),
    "4925":  (5, (95, 1130, 248, 1262), (255, 1120, 648, 1247)),
    "4926":  (6, (160, 145, 298, 312), (305, 160, 668, 347)),
    "4927":  (6, (150, 470, 288, 642), (300, 480, 592, 672)),
    "4928":  (6, (140, 790, 278, 962), (288, 800, 578, 962)),
    "4929":  (6, (130, 1110, 268, 1277), (275, 1120, 528, 1262)),
    "4931":  (7, (130, 120, 278, 272), (285, 130, 622, 284)),
    "4941":  (7, (130, 470, 262, 632), (280, 480, 482, 591)),
    "4921":  (7, (115, 770, 218, 882), (258, 775, 328, 842)),
    "4922":  (7, (100, 1090, 213, 1217), (243, 1105, 348, 1207)),
    "4923":  (8, (150, 130, 268, 287), (298, 145, 452, 297)),
    "4924":  (8, (140, 495, 263, 662), (288, 505, 492, 702)),
    "4933":  (8, (120, 870, 263, 1002), (283, 875, 412, 997)),
    "4612":  (8, (100, 1180, 213, 1292), (273, 1185, 342, 1239)),
    "46019": (9, (105, 110, 233, 262), (263, 115, 367, 217)),
    "46025": (9, (105, 110, 233, 262), (458, 110, 592, 227)),
    "4630":  (9, (95, 345, 186, 502), (243, 320, 412, 477)),
    "4638":  (9, (90, 590, 198, 747), (238, 575, 437, 751)),
    "4642":  (9, (65, 864, 213, 1042), (223, 830, 447, 1032)),
    "4911-TEXTILE": (9, (55, 1130, 213, 1262), (213, 1140, 407, 1212)),
    "4726":  (10, (105, 505, 238, 642), (253, 500, 602, 682)),
    "4727":  (10, (95, 790, 238, 952), (243, 790, 527, 987)),
    "4729":  (10, (90, 1085, 218, 1237), (228, 1090, 472, 1232)),
    "4645":  (11, (120, 150, 283, 332), (293, 140, 522, 372)),
    "46050": (11, (100, 480, 283, 652), (288, 470, 527, 702)),
    "44045": (11, (120, 830, 238, 977), (283, 855, 492, 987)),
    "44055": (11, (120, 1120, 238, 1267), (273, 1140, 537, 1292)),
    "4730":  (12, (165, 155, 293, 327), (298, 150, 582, 315)),
    "4731":  (12, (160, 490, 298, 642), (303, 480, 642, 627)),
    "4750":  (12, (165, 820, 268, 962), (298, 810, 507, 932)),
    "4750/L1": (12, (165, 1140, 268, 1292), (298, 1120, 502, 1242)),
}
# Same photo/imprint reused for stock-text variants
PRODUCTS["4750/L2"] = PRODUCTS["4750/L1"]
PRODUCTS["4750/L9"] = PRODUCTS["4750/L1"]

# Generic / supporting images (page, box, trim?)
EXTRAS = {
    "pads-9054": (3, (55, 655, 385, 855), False),
    "pads-9053": (3, (25, 825, 335, 1005), False),
    "pads-9052": (3, (195, 950, 415, 1085), False),
    "pads-9051": (3, (105, 1020, 335, 1145), False),
    "ink-bottles": (3, (395, 675, 705, 985), False),
    "cartridges": (3, (325, 1015, 725, 1235), False),
    "pads-and-inks": (3, (20, 640, 730, 1250), False),
    "printy-range": (2, (40, 568, 905, 1290), False),
    "daters-group": (10, (75, 50, 375, 305), True),
}


def trim(img, thresh=228, margin=10):
    """Trim near-white borders from a scanned crop."""
    gray = ImageOps.grayscale(img)
    bw = gray.point(lambda p: 255 if p < thresh else 0)
    bbox = bw.getbbox()
    if not bbox:
        return img
    x0, y0, x1, y1 = bbox
    x0 = max(0, x0 - margin); y0 = max(0, y0 - margin)
    x1 = min(img.width, x1 + margin); y1 = min(img.height, y1 + margin)
    return img.crop((x0, y0, x1, y1))


def square(img, size=900, bg=(255, 255, 255)):
    """Fit the image on a square white canvas."""
    img = img.convert("RGB")
    ratio = min((size - 80) / img.width, (size - 80) / img.height)
    if ratio < 1 or True:
        img = img.resize((max(1, int(img.width * ratio)), max(1, int(img.height * ratio))), Image.LANCZOS)
    canvas = Image.new("RGB", (size, size), bg)
    canvas.paste(img, ((size - img.width) // 2, (size - img.height) // 2))
    return canvas


def render(doc, page_no, cache={}):
    if page_no not in cache:
        pix = doc[page_no - 1].get_pixmap(dpi=300)
        cache[page_no] = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    return cache[page_no]


def crop(doc, page_no, box):
    img = render(doc, page_no)
    x0, y0, x1, y1 = [int(v * SCALE) for v in box]
    return img.crop((x0, y0, x1, y1))


def safe(sku):
    return sku.replace("/", "-").lower()


def main():
    doc = pymupdf.open(PDF)
    os.makedirs(f"{OUT}/products", exist_ok=True)
    os.makedirs(f"{OUT}/products/gallery", exist_ok=True)
    os.makedirs(f"{OUT}/categories", exist_ok=True)
    os.makedirs(f"{OUT}/banners", exist_ok=True)
    thumbs = []
    for sku, (page, photo, imprint) in PRODUCTS.items():
        p = square(trim(crop(doc, page, photo)))
        p.save(f"{OUT}/products/{safe(sku)}.jpg", quality=88)
        thumbs.append((sku, p))
        if imprint:
            i = square(trim(crop(doc, page, imprint)), size=900)
            i.save(f"{OUT}/products/gallery/{safe(sku)}-imprint.jpg", quality=88)
            thumbs.append((sku + " imprint", i))
    for name, (page, box, do_trim) in EXTRAS.items():
        img = crop(doc, page, box)
        if do_trim:
            img = trim(img)
        if name.startswith("pads-") or name in ("ink-bottles", "cartridges"):
            img = square(img, bg=(255, 255, 255))
        img.save(f"{OUT}/products/{name}.jpg", quality=88)
        thumbs.append((name, img))

    # contact sheet for visual verification
    cell = 220
    cols = 8
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * (cell + 24)), (240, 240, 240))
    from PIL import ImageDraw
    d = ImageDraw.Draw(sheet)
    for n, (label, im) in enumerate(thumbs):
        t = im.copy(); t.thumbnail((cell - 10, cell - 10))
        x = (n % cols) * cell + 5; y = (n // cols) * (cell + 24) + 5
        sheet.paste(t, (x, y)); d.text((x, y + cell - 6), label, fill=(0, 0, 0))
    sheet.save("contact_sheet.jpg", quality=80)
    print("done", len(thumbs), "images")


if __name__ == "__main__":
    main()
