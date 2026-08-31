"""PNG ikonlar (192/512) ve Open Graph görseli (1200x630) üretir -> static/"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

STATIC = Path(__file__).resolve().parent.parent / "static"
TURUNCU, SARI, KOYU, BEYAZ = (255, 122, 89), (255, 201, 77), (43, 43, 52), (255, 255, 255)
KENAR, YANAK = (230, 96, 63), (255, 208, 194)


def yuz(d: ImageDraw.ImageDraw, x, y, s):
    """Konum iğnesi + gülen çocuk yüzü (marka). s = 64 birimlik tuvale ölçek."""
    cx, cyh, R = x + 32 * s, y + 25 * s, 21 * s
    # iğne gövdesi: alt uç üçgeni + baş dairesi (koyu kenar sonra ince orange üstüne)
    def pin(renk, k=0.0):
        d.polygon([(x + (17 + k) * s, y + (37 + k) * s), (cx, y + (61 - k) * s),
                   (x + (47 - k) * s, y + (37 + k) * s)], fill=renk)
        d.ellipse([cx - R + k * s, cyh - R + k * s, cx + R - k * s, cyh + R - k * s], fill=renk)
    pin(KENAR, 0.0)
    pin(TURUNCU, 1.4)
    # yüz
    fr = 12 * s
    d.ellipse([cx - fr, cyh - fr, cx + fr, cyh + fr], fill=BEYAZ)
    er = 2.2 * s
    for ex in (-4.6, 4.6):
        gx = cx + ex * s
        d.ellipse([gx - er, cyh - 2 * s - er, gx + er, cyh - 2 * s + er], fill=KOYU)
    d.arc([cx - 6 * s, cyh - 1 * s, cx + 6 * s, cyh + 7 * s], 20, 160, fill=KOYU, width=max(2, int(2.4 * s)))
    cr = 1.7 * s
    for cxo in (-7.6, 7.6):
        px = cx + cxo * s
        d.ellipse([px - cr, cyh + 2 * s - cr, px + cr, cyh + 2 * s + cr], fill=YANAK)
    # keşif kıvılcımı (öneri/rehber)
    sx, sy, r1, r2 = x + 51 * s, y + 11 * s, 5 * s, 1.9 * s
    d.polygon([(sx, sy - r1), (sx + r2, sy - r2), (sx + r1, sy), (sx + r2, sy + r2),
               (sx, sy + r1), (sx - r2, sy + r2), (sx - r1, sy), (sx - r2, sy - r2)], fill=SARI)


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
