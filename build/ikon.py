"""PNG ikonlar (192/512) ve Open Graph görseli (1200x630) üretir -> static/"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

STATIC = Path(__file__).resolve().parent.parent / "static"
TURUNCU, SARI, KOYU, BEYAZ = (255, 122, 89), (255, 201, 77), (34, 34, 42), (255, 255, 255)


def yuz(d: ImageDraw.ImageDraw, x, y, s):
    """Basit gülen çocuk yüzü + gövde; s = ölçek (64 birimlik tuvale göre)."""
    d.rounded_rectangle([x, y, x + 64 * s, y + 64 * s], radius=16 * s, fill=TURUNCU)
    d.ellipse([x + 22 * s, y + 14 * s, x + 42 * s, y + 34 * s], fill=BEYAZ)
    d.ellipse([x + 26 * s, y + 21 * s, x + 30 * s, y + 25 * s], fill=KOYU)
    d.ellipse([x + 34 * s, y + 21 * s, x + 38 * s, y + 25 * s], fill=KOYU)
    d.arc([x + 26 * s, y + 22 * s, x + 38 * s, y + 31 * s], 20, 160, fill=KOYU, width=max(1, int(2 * s)))
    d.pieslice([x + 16 * s, y + 36 * s, x + 48 * s, y + 68 * s], 180, 360, fill=SARI)


def ikon(boyut):
    im = Image.new("RGBA", (boyut, boyut), (0, 0, 0, 0))
    yuz(ImageDraw.Draw(im), 0, 0, boyut / 64)
    im.save(STATIC / f"icon-{boyut}.png")


def font(boyut):
    for ad in ("C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(ad, boyut)
        except OSError:
            continue
    return ImageFont.load_default()


def og():
    im = Image.new("RGB", (1200, 630), (255, 250, 243))
    d = ImageDraw.Draw(im)
    d.ellipse([850, -200, 1400, 350], fill=(255, 230, 217))
    d.ellipse([-200, 400, 300, 900], fill=(255, 243, 198))
    yuz(d, 80, 90, 2.6)
    d.text((280, 100), "ankarada", font=font(72), fill=KOYU)
    d.text((280, 175), "çocuk", font=font(72), fill=TURUNCU)
    d.text((80, 330), "Ankara'da çocukla gidilecek yerler", font=font(48), fill=KOYU)
    d.text((80, 400), "Parklar · kafeler · müzeler · oyun alanları · geziler", font=font(32), fill=(90, 90, 104))
    d.text((80, 470), "Her mekân 0-3 / 3-6 / 6-11 / 11-16 yaş için ayrı puanlı", font=font(32), fill=(90, 90, 104))
    d.rounded_rectangle([80, 540, 420, 600], radius=30, fill=TURUNCU)
    d.text((110, 552), "ankaradacocuk.com", font=font(28), fill=BEYAZ)
    im.save(STATIC / "og.png", optimize=True)


if __name__ == "__main__":
    ikon(192)
    ikon(512)
    og()
    print("ikonlar üretildi")
