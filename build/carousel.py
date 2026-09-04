# -*- coding: utf-8 -*-
"""Instagram carousel (kaydırmalı liste) üretir — rakiplerin en çok 'kaydet' getiren türü.
Bizim farkımız: YAŞA GÖRE puanı öne çıkarır. 1080x1350 kareler (kapak + N mekân + CTA).
Site verisinden (gerçek foto + puan), uydurma yok.
Çıktı: static/medya/carousel/<tema>/NN.jpg  +  carousel-metin.md
Kullanım: python build/carousel.py   (önce: python build/derle.py)
"""
from __future__ import annotations
import json
import math
import sys
from pathlib import Path
from PIL import Image, ImageDraw

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "build"))
import reels as R  # yardımcıları yeniden kullan (font, efont, sar, kirp_doldur, yildiz, koyult, IMG, marka)

CW, CH = 1080, 1350
CIK = KOK / "static" / "medya" / "carousel"
BEYAZ, KOYU, SARI = (255, 255, 255), (28, 28, 36), (255, 201, 77)


def vgrad(kr):
    im = Image.new("RGB", (CW, CH), kr)
    d = ImageDraw.Draw(im)
    for yy in range(CH):
        d.line([(0, yy), (CW, yy)], fill=R.koyult(kr, 1 - 0.42 * (yy / CH)))
    return im


def foto_of(m):
    for anahtar in ("foto", "kapak"):
        v = m.get(anahtar)
        if not v:
            continue
        yol = R.IMG / (v["lg"] if isinstance(v, dict) else v)
        if yol.exists():
            return Image.open(yol)
    return None


def kapak(tema, kr):
    im = vgrad(kr)
    d = ImageDraw.Draw(im)
    ef = R.efont(170)
    if ef:
        el = Image.new("RGBA", (230, 230), (0, 0, 0, 0))
        ImageDraw.Draw(el).text((115, 115), tema["emoji"], font=ef, anchor="mm", embedded_color=True)
        im.paste(el, (CW // 2 - 115, 210), el)
    # üst küçük + vurgu büyük
    y = 500
    fb = R.font(72)
    for s in R.sar(d, tema["ust"], fb, CW - 140):
        d.text((CW // 2, y), s, font=fb, fill=BEYAZ, anchor="mm")
        y += 88
    y += 24
    fh = R.font(128)
    for s in R.sar(d, tema["vur"], fh, CW - 110):
        d.text((CW // 2, y), s, font=fh, fill=SARI, anchor="mm")
        y += 142
    # şerit
    y += 34
    d.rounded_rectangle([CW // 2 - 340, y, CW // 2 + 340, y + 108], radius=54, fill=BEYAZ)
    d.text((CW // 2, y + 54), "YAŞA GÖRE PUANLI · KAYDET", font=R.font(44), fill=R.koyult(kr, 0.7), anchor="mm")
    # kaydır oku (carousel'de doğru metafor)
    d.text((CW - 96, CH // 2), "›", font=R.font(150), fill=(255, 255, 255, 220), anchor="mm")
    # marka
    lg = R.marka()
    im.paste(lg, (CW // 2 - 150, CH - 130), lg)
    d.text((CW // 2 - 66, CH - 112), "ankaradaçocuk", font=R.font(42), fill=BEYAZ, anchor="lm")
    return im


def mekan(m, sira, alan, rozet_ust, tam, kr):
    im = Image.new("RGB", (CW, CH), KOYU)
    ust = 820
    f = foto_of(m)
    if f:
        im.paste(R.kirp_doldur(f, CW, ust), (0, 0))
    d = ImageDraw.Draw(im, "RGBA")
    d.rectangle([0, 0, CW, 220], fill=(0, 0, 0, 90))
    for i in range(200):
        d.line([(0, ust - 200 + i), (CW, ust - 200 + i)], fill=(28, 28, 36, int(255 * i / 200)))
    d.rectangle([0, ust, CW, CH], fill=(28, 28, 36, 255))
    # sıra rozeti
    d.ellipse([48, 54, 190, 196], fill=kr)
    d.text((119, 118), f"{sira}", font=R.font(92), fill=BEYAZ, anchor="mm")
    # yaş-puan rozeti (BİZİM FARK) sağ üst
    puan = m.get(alan)
    if puan is not None:
        d.rounded_rectangle([CW - 340, 54, CW - 48, 200], radius=40, fill=(255, 255, 255, 240))
        d.text((CW - 194, 96), rozet_ust, font=R.font(38), fill=R.koyult(kr, 0.6), anchor="mm")
        R.yildiz(d, CW - 254, 158, 24, (245, 180, 60))
        d.text((CW - 222, 158), f"{puan}/{tam}", font=R.font(52), fill=R.koyult(kr, 0.55), anchor="lm")
    # isim
    isf = R.font(72)
    y = ust + 44
    for s in R.sar(d, m["name"], isf, CW - 110)[:2]:
        d.text((56, y), s, font=isf, fill=BEYAZ)
        y += 84
    # bilgi
    ortam = "Kapalı alan" if m.get("indoor") else "Açık hava"
    fiyat = {"ücretsiz": "Ücretsiz", "uygun": "Uygun", "orta": "Orta", "yüksek": "Yüksek"}.get(m.get("price") or "", "")
    bilgi = f"{m.get('district') or 'Ankara'}   ·   {ortam}" + (f"   ·   {fiyat}" if fiyat else "")
    d.text((56, y + 16), bilgi, font=R.font(42, False), fill=(220, 220, 232), anchor="lm")
    # kısa açıklama
    ac = (m.get("description") or "").strip().split(". ")[0].strip()
    if ac:
        if len(ac) > 120:
            ac = ac[:120].rsplit(" ", 1)[0] + "…"
        for i, s in enumerate(R.sar(d, ac, R.font(40, False), CW - 110)[:3]):
            d.text((56, y + 96 + i * 52), s, font=R.font(40, False), fill=(178, 178, 194))
    return im


def cta(kr):
    im = vgrad(kr)
    d = ImageDraw.Draw(im)
    lg = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    from ikon import yuz
    yuz(ImageDraw.Draw(lg), 0, 0, 160 / 64)
    im.paste(lg, (CW // 2 - 80, 300), lg)
    d.text((CW // 2, 560), "ankaradaçocuk.com", font=R.font(84), fill=BEYAZ, anchor="mm")
    for i, s in enumerate(["Tüm liste puanı, ücreti ve", "ulaşımıyla sitede.", "196 mekân · yaşa göre puanlı"]):
        d.text((CW // 2, 680 + i * 66), s, font=R.font(44, False), fill=(255, 246, 236), anchor="mm")
    d.rounded_rectangle([CW // 2 - 320, 940, CW // 2 + 320, 1060], radius=60, fill=SARI)
    d.text((CW // 2, 1000), "KAYDET · PAYLAŞ", font=R.font(50), fill=KOYU, anchor="mm")
    d.text((CW // 2, 1150), "Takip et  @ankaradacocuk", font=R.font(46), fill=BEYAZ, anchor="mm")
    return im


def uret(tema, mekanlar):
    kr = tuple(int(tema["renk"].lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    sec = [m for m in mekanlar if tema["filt"](m) and foto_of(m)]
    sec.sort(key=lambda m: -((m.get(tema["alan"]) or 0) * 1.0
                             + 0.3 * math.log10(((m.get("google") or {}).get("count") or 0) + 1)))
    top, gor = [], set()
    for m in sec:
        if m["name"] in gor:
            continue
        top.append(m); gor.add(m["name"])
        if len(top) >= tema["adet"]:
            break
    if len(top) < 4:
        print(f"  ! {tema['slug']}: yetersiz ({len(top)})")
        return None
    kls = CIK / tema["slug"]
    kls.mkdir(parents=True, exist_ok=True)
    for eski in kls.glob("*.jpg"):
        eski.unlink()
    n = 1
    kapak(tema, kr).save(kls / f"{n:02d}.jpg", quality=90); n += 1
    for i, m in enumerate(top, 1):
        mekan(m, i, tema["alan"], tema["rozet_ust"], tema["tam"], kr).save(kls / f"{n:02d}.jpg", quality=90); n += 1
    cta(kr).save(kls / f"{n:02d}.jpg", quality=90)
    print(f"  ✓ {tema['slug']}: {len(top)} mekân -> {n} kare")
    return {"tema": tema, "mekanlar": top, "kare": n}


TEMALAR = [
    {"slug": "bebek-0-3", "ust": "Ankara'da 0-3 bebekle", "vur": "EN İYİ 7 YER", "emoji": "👶", "renk": "#e8739b",
     "alan": "score_bebek", "rozet_ust": "0-3 yaş", "tam": 5, "adet": 7,
     "filt": lambda m: (m.get("score_bebek") or 0) >= 4,
     "caption": "Ankara'da 0-3 yaş bebekle gidilecek en iyi 7 yer 👶 Bebek arabası rahat, sakin ve güvenli. Kaydet 👇"},
    {"slug": "ucretsiz", "ust": "Ankara'da çocukla", "vur": "ÜCRETSİZ 8 MEKÂN", "emoji": "🆓", "renk": "#2f9e6f",
     "alan": "puan", "rozet_ust": "PUAN", "tam": 10, "adet": 8,
     "filt": lambda m: m.get("price") == "ücretsiz",
     "caption": "Ankara'da çocukla ücretsiz gidilecek 8 mekân 🆓 Cebe dokunmadan koca bir gün. Kaydet, lazım olur 👇"},
    {"slug": "okul-oncesi-3-6", "ust": "Ankara'da 3-6 yaş", "vur": "EN İYİ 7 YER", "emoji": "🧒", "renk": "#e0822b",
     "alan": "score_okul_oncesi", "rozet_ust": "3-6 yaş", "tam": 5, "adet": 7,
     "filt": lambda m: (m.get("score_okul_oncesi") or 0) >= 4,
     "caption": "Ankara'da 3-6 yaş çocukla en iyi 7 yer 🧒 Oyun, keşif, ilk müze deneyimi. Kaydet 👇"},
    {"slug": "yagmurlu", "ust": "Yağmurlu günde çocukla", "vur": "7 KAPALI MEKÂN", "emoji": "☔", "renk": "#2f7de1",
     "alan": "puan", "rozet_ust": "PUAN", "tam": 10, "adet": 7,
     "filt": lambda m: m.get("indoor"),
     "caption": "Yağmurlu günde Ankara'da çocukla 7 kapalı mekân ☔ Islanmadan eğlence. Kaydet, lazım olur 👇"},
]


def main():
    CIK.mkdir(parents=True, exist_ok=True)
    mekanlar = json.loads((KOK / "dist" / "static" / "mekanlar.json").read_text("utf-8"))
    mekanlar = [m for m in mekanlar if m.get("status") != "kapali"]
    print(f"{len(TEMALAR)} carousel tema, {len(mekanlar)} mekân...\n")
    md = ["# Instagram Carousel — hazır kaydırmalı listeler", ""]
    for tema in TEMALAR:
        s = uret(tema, mekanlar)
        if s:
            liste = "\n".join(f"{i}. {m['name']} ({m.get('district') or 'Ankara'})"
                              for i, m in enumerate(s["mekanlar"], 1))
            md.append(f"## {tema['ust']} {tema['vur']}\n\n{s['kare']} kare · `static/medya/carousel/{tema['slug']}/`\n\n"
                      f"**Açıklama:**\n```\n{tema['caption']}\n\n{liste}\n\nHepsi 👉 ankaradacocuk.com\n```\n")
    (CIK / "carousel-metin.md").write_text("\n".join(md), encoding="utf-8")
    print(f"\n-> {CIK}")


if __name__ == "__main__":
    main()
