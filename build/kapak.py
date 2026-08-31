# -*- coding: utf-8 -*-
"""Gercek fotografi olmayan mekanlar icin markali, tasarlanmis kapak gorseli uretir.

Sahte foto DEGIL; kategori rengi + dekor + mekan adi + puan + logo tasiyan tasarim kapagi.
Boylece her mekan kartinin ve detay hero'sunun bir gorseli olur (16:9 webp, foto ile ayni bicim).
Cikti: static/img/mekan/<slug>-kapak.webp + data/kapak.json ({name: dosya})
Kullanim: python build/kapak.py   (derle.py'den ONCE calistirilir)
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8")
KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "build"))
from derle import hazirla, yukle, KATEGORILER, YAS_GRUPLARI
from ikon import yuz

IMG = KOK / "static" / "img" / "mekan"
BEYAZ = (255, 255, 255)
SARI = (255, 201, 77)


def _rgb(hx):
    hx = hx.lstrip("#")
    return tuple(int(hx[i:i + 2], 16) for i in (0, 2, 4))


def font(px, kalin=True):
    adlar = (["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"] if kalin
             else ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"])
    for a in adlar:
        try:
            return ImageFont.truetype(a, px)
        except OSError:
            continue
    return ImageFont.load_default()


def emoji_font(px):
    try:
        return ImageFont.truetype("C:/Windows/Fonts/seguiemj.ttf", px)
    except OSError:
        return None


def sar(d, metin, fnt, en_fazla):
    satirlar, cur = [], ""
    for k in metin.split():
        dene = (cur + " " + k).strip()
        if d.textlength(dene, font=fnt) <= en_fazla:
            cur = dene
        else:
            if cur:
                satirlar.append(cur)
            cur = k
    if cur:
        satirlar.append(cur)
    return satirlar


def koyult(rgb, f):
    return tuple(int(c * f) for c in rgb)


def en_iyi_yas(m):
    çift = [("score_bebek", "0-3"), ("score_okul_oncesi", "3-6"),
            ("score_ilkokul", "6-11"), ("score_ergen", "11-16")]
    return max(çift, key=lambda t: m.get(t[0]) or 0)[1]


def kapak(m):
    W, H = 1080, 675
    kat = m["kategori"]
    kr = _rgb(kat["renk"])
    im = Image.new("RGB", (W, H), kr)
    d = ImageDraw.Draw(im)
    # capraz gradyan
    for y in range(H):
        f = y / H
        d.line([(0, y), (W, y)], fill=koyult(kr, 1 - 0.42 * f))
    # dekor daireler (OG stili)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    do = ImageDraw.Draw(ov)
    do.ellipse([W - 300, -160, W + 220, 360], fill=(255, 255, 255, 26))
    do.ellipse([-180, H - 260, 260, H + 200], fill=(0, 0, 0, 26))
    im = Image.alpha_composite(im.convert("RGBA"), ov)
    d = ImageDraw.Draw(im)
    # buyuk, soluk kategori emojisi (varsa)
    ef = emoji_font(300)
    ik = kat.get("ikon", "")
    if ef and ik:
        try:
            kat_l = Image.new("RGBA", (360, 360), (0, 0, 0, 0))
            ImageDraw.Draw(kat_l).text((180, 180), ik, font=ef, anchor="mm", embedded_color=True)
            kat_l.putalpha(kat_l.getchannel("A").point(lambda a: int(a * 0.22)))
            im.alpha_composite(kat_l, (W - 400, 60))
        except Exception:
            pass
    # logo + marka (sol ust)
    logo = Image.new("RGBA", (78, 78), (0, 0, 0, 0))
    yuz(ImageDraw.Draw(logo), 0, 0, 78 / 64)
    im.paste(logo, (36, 30), logo)
    d.text((124, 38), "ankarada", font=font(34), fill=BEYAZ)
    w = d.textlength("ankarada", font=font(34))
    d.text((124 + w, 38), "cocuk", font=font(34), fill=SARI)
    # puan rozeti (sag ust)
    px, py, pr = W - 78, 74, 52
    d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=BEYAZ)
    d.text((px, py - 10), f"{m['puan']}", font=font(42), fill=koyult(kr, 0.8), anchor="mm")
    d.text((px, py + 26), "/10", font=font(20), fill=koyult(kr, 0.8), anchor="mm")
    # kategori cipi
    cip = kat["kisa"]
    cf = font(30)
    cw = d.textlength(cip, font=cf) + 34
    d.rounded_rectangle([44, H - 250, 44 + cw, H - 250 + 46], radius=22, fill=koyult(kr, 0.5))
    d.text((44 + 17, H - 250 + 23), cip, font=cf, fill=BEYAZ, anchor="lm")
    # mekan adi (buyuk, alt)
    isim_f = font(66)
    satir = sar(d, m["name"], isim_f, W - 88)[:3]
    y = H - 180
    for s in satir:
        d.text((44, y), s, font=isim_f, fill=BEYAZ)
        y += 74
    # alt bilgi
    yas = en_iyi_yas(m)
    ortam = "Kapali alan" if m.get("indoor") else "Acik hava"
    d.text((44, H - 44), f"{yas} yas  |  {ortam}  |  {m.get('district') or 'Ankara'}",
           font=font(28, False), fill=(255, 255, 255))
    return im.convert("RGB")


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    mekanlar = hazirla(yukle("mekanlar.json"))
    foto = json.loads((KOK / "data" / "foto.json").read_text("utf-8")) if (KOK / "data" / "foto.json").exists() else {}
    kayit = {}
    n = 0
    for m in mekanlar:
        if foto.get(m["name"]):
            continue  # gercek foto var, kapak uretme
        dosya = f"{m['slug']}-kapak.webp"
        kapak(m).save(IMG / dosya, "WEBP", quality=80, method=6)
        kayit[m["name"]] = dosya
        n += 1
    (KOK / "data" / "kapak.json").write_text(json.dumps(kayit, ensure_ascii=False, indent=1), "utf-8")
    print(f"{n} markali kapak uretildi -> {IMG}")


if __name__ == "__main__":
    raise SystemExit(main())
