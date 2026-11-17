"""Build the optimised images and web fonts used by the root index.html.

Run from the repository root:  python assets/tools/build_home_assets.py
Needs Pillow (WebP support) and fontTools with brotli. Source files are never
modified; full-resolution originals stay where they are and are linked from the
page for enlargement and download.
"""
from pathlib import Path

from PIL import Image
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[2]
OUT_IMG = ROOT / "assets" / "img"
OUT_FONT = ROOT / "assets" / "fonts"

PHOTO = "easy-food-kitchen-package/visualizations/photoreal-2026-11-16/images/"
PLANS = "easy-food-kitchen-package/plans/"
RENDERS = "easy-food-kitchen-package/renders/ar/"
BRAND = "easy-food-identity-v2-green/generated/"

# name -> (source, widths, quality)
IMAGES = {
    "shopfront-site": (PHOTO + "05-A-exterior-site-matched-2026-11-17.png", (1448, 1100, 720), 80),
    "interior-door": (PHOTO + "03-A-interior-from-door.png", (1587, 1000, 640), 80),
    "interior-back": (PHOTO + "04-A-interior-from-back.png", (1587, 1000, 640), 80),
    "topdown": (PHOTO + "02-A-top-down-cutaway.png", (1585, 1000, 640), 80),
    "equipment": (PHOTO + "09-A-equipment-detail.png", (1586, 1000, 640), 80),
    "cutaway": (PHOTO + "01-A-cutaway-3d.png", (1587, 1000, 640), 82),
    "plan-a": (PLANS + "layout-A.png", (1200, 700), 88),
    "plan-b": (PLANS + "layout-B.png", (1200, 700), 88),
    "flow-a": (RENDERS + "06-A-staff-and-food-flow.png", (1000, 640), 86),
    "wc-a": (RENDERS + "11-A-retained-wc-accordion.png", (1000, 640), 86),
    "brandboard": (BRAND + "easy-food-brandboard.png", (1536, 1000, 640), 82),
    "food": (BRAND + "easy-food-menu-hero.png", (1536, 1000, 640), 80),
}


def build_images():
    OUT_IMG.mkdir(parents=True, exist_ok=True)
    for name, (src, widths, quality) in IMAGES.items():
        im = Image.open(ROOT / src).convert("RGB")
        for w in widths:
            w = min(w, im.width)
            h = round(im.height * w / im.width)
            out = OUT_IMG / f"{name}-{w}.webp"
            im.resize((w, h), Image.LANCZOS).save(out, "WEBP", quality=quality, method=6)
            print(f"{out.relative_to(ROOT)}  {w}x{h}  {out.stat().st_size // 1024} KB")

    # Social preview: 1200 x 630 crop of the shopfront, centred on the fascia.
    im = Image.open(ROOT / IMAGES["shopfront-site"][0]).convert("RGB")
    scale = 1200 / im.width
    im = im.resize((1200, round(im.height * scale)), Image.LANCZOS)
    top = round(im.height * 0.12)
    im.crop((0, top, 1200, top + 630)).save(OUT_IMG / "og-shopfront-site.jpg", "JPEG", quality=84, optimize=True)


def build_fonts():
    OUT_FONT.mkdir(parents=True, exist_ok=True)
    src_dir = ROOT / "easy-food-identity-v2-green" / "assets" / "fonts"
    for family in ("Cairo", "Manrope"):
        font = TTFont(src_dir / f"{family}-Variable.ttf")
        font.flavor = "woff2"
        out = OUT_FONT / f"{family}-Variable.woff2"
        font.save(out)
        (OUT_FONT / f"{family}-OFL.txt").write_bytes((src_dir / f"{family}-OFL.txt").read_bytes())
        print(f"{out.relative_to(ROOT)}  {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    build_images()
    build_fonts()
