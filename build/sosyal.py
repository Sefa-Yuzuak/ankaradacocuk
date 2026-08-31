# -*- coding: utf-8 -*-
"""Instagram/Facebook icin hazir gonderi gorselleri + metin uretir.

Sitedeki gercek veriden (data/mekanlar.json, data/foto.json) uretir; uydurma yok.
Wikimedia fotograflarinda telif kunyesi hem gorsele hem metne konur (CC-BY-SA geregi).
Cikti: sosyal/gonderiler/*.jpg + sosyal/metinler.md + sosyal/profil/*
Kullanim: python build/sosyal.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8")
KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "build"))
from ikon import yuz  # marka amblemi (konum ignesi + cocuk yuzu)

CIK = KOK / "sosyal"
GON = CIK / "gonderiler"
PRO = CIK / "profil"
IMG = KOK / "static" / "img" / "mekan"

TURUNCU = (255, 122, 89)
TKOYU = (230, 96, 63)
SARI = (255, 201, 77)
KOYU = (43, 43, 52)
BEYAZ = (255, 255, 255)
KREM = (255, 250, 243)
KATRENK = {"park": (58, 166, 109), "muze": (138, 99, 210), "bilim": (47, 125, 225),
           "hayvanat": (217, 130, 43), "sanat": (201, 74, 140), "oyun": (232, 85, 61),
           "spor": (31, 162, 166), "atolye": (184, 134, 43), "kutuphane": (95, 111, 143),
           "avm": (122, 92, 255), "yemek": (224, 116, 47), "gezi": (43, 138, 94)}
KATIK = {"park": "\U0001F333", "muze": "\U0001F3DB\uFE0F", "bilim": "\U0001F52D",
         "hayvanat": "\U0001F992", "sanat": "\U0001F3AD", "oyun": "\U0001F3AA",
         "spor": "\u26F8\uFE0F", "atolye": "\U0001F3A8", "kutuphane": "\U0001F4DA",
         "avm": "\U0001F6CD\uFE0F", "yemek": "\U0001F37D\uFE0F", "gezi": "\U0001F697"}
KATAD = {"park": "Park", "muze": "Muze", "bilim": "Bilim", "hayvanat": "Hayvanlar", "sanat": "Sanat",
         "oyun": "Oyun", "spor": "Spor", "atolye": "Atolye", "kutuphane": "Kutuphane", "avm": "AVM",
         "yemek": "Kafe/Restoran", "gezi": "Gezi"}
EN_IYI = [("score_bebek", "0-3"), ("score_okul_oncesi", "3-6"),
          ("score_ilkokul", "6-11"), ("score_ergen", "11-16")]


def font(px, kalin=True):
    adlar = (["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"] if kalin
             else ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"])
    for a in adlar:
        try:
            return ImageFont.truetype(a, px)
        except OSError:
            continue
    return ImageFont.load_default()


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


def kapak_foto(m, w, h):
    f = m.get("foto")
    if not f:
        return None
    yol = IMG / f["lg"]
    if not yol.exists():
        return None
    im = Image.open(yol).convert("RGB")
    g, y = im.size
    if g / y > w / h:
        ng = int(y * w / h); sol = (g - ng) // 2; im = im.crop((sol, 0, sol + ng, y))
    else:
        ny = int(g * h / w); ust = int((y - ny) * 0.3); im = im.crop((0, ust, g, ust + ny))
    return im.resize((w, h), Image.LANCZOS)


def alt_gradyan(w, h, bas=0.4):
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = ov.load()
    by = int(h * bas)
    for yy in range(by, h):
        a = int(235 * ((yy - by) / (h - by)) ** 1.3)
        for xx in range(w):
            px[xx, yy] = (15, 12, 10, a)
    return ov


def marka_seridi(im, d):
    logo = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
    yuz(ImageDraw.Draw(logo), 0, 0, 96 / 64)
    im.paste(logo, (40, 36), logo)
    d.text((150, 44), "ankarada", font=font(40), fill=BEYAZ)
    w = d.textlength("ankarada", font=font(40))
    d.text((150 + w, 44), "cocuk", font=font(40), fill=SARI)


def en_iyi_yas(m):
    return max(EN_IYI, key=lambda t: m.get(t[0]) or 0)[1]


def mekan_gonderi(m):
    W, H = 1080, 1350
    kr = KATRENK.get(m["category"], TURUNCU)
    foto = kapak_foto(m, W, H)
    if foto:
        im = foto.convert("RGBA")
    else:
        base = Image.new("RGB", (W, H), kr)
        d0 = ImageDraw.Draw(base)
        for yy in range(H):
            fr = yy / H
            d0.line([(0, yy), (W, yy)], fill=tuple(int(c * (1 - .35 * fr)) for c in kr))
        d0.text((W / 2, H * 0.34), KATIK.get(m["category"], "\U0001F4CD"), font=font(360), anchor="mm")
        im = base.convert("RGBA")
    im.alpha_composite(alt_gradyan(W, H))
    d = ImageDraw.Draw(im)
    marka_seridi(im, d)
    # Puan rozeti
    px, py, pr = W - 96, 88, 64
    d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=TURUNCU)
    d.text((px, py - 14), f"{m['puan']}", font=font(54), fill=BEYAZ, anchor="mm")
    d.text((px, py + 28), "/10", font=font(24), fill=BEYAZ, anchor="mm")
    # Alt icerik (asagidan yukari)
    y = H - 72
    d.text((48, y), "ankaradacocuk.com", font=font(38), fill=SARI, anchor="ls")
    y -= 64
    yas = en_iyi_yas(m)
    ortam = "Kapali alan" if m.get("indoor") else "Acik hava"
    meta = f"{yas} yas  |  {ortam}  |  {m.get('district') or 'Ankara'}"
    d.text((48, y), meta, font=font(34, False), fill=(238, 238, 238), anchor="ls")
    y -= 58
    isim_f = font(76)
    for s in reversed(sar(d, m["name"], isim_f, W - 96)[:3]):
        d.text((48, y), s, font=isim_f, fill=BEYAZ, anchor="ls")
        y -= 84
    cip = f"{KATAD.get(m['category'], '')}"
    cw = d.textlength(cip, font=font(32)) + 36
    d.rounded_rectangle([48, y - 46, 48 + cw, y - 4], radius=21, fill=kr)
    d.text((48 + 18, y - 25), cip, font=font(32), fill=BEYAZ, anchor="lm")
    if m.get("foto"):
        k = f"Foto: {(m['foto'].get('yazar') or '')[:26]} / {m['foto'].get('lisans', '')} - Wikimedia"
        d.text((W - 28, H - 16), k, font=font(20, False), fill=(220, 220, 220), anchor="rs")
    return im.convert("RGB")


def metin(m):
    yas = en_iyi_yas(m)
    ac = (m.get("description") or "").strip().split(". ")[0][:150].rstrip(".") + "."
    ortam = "\U0001F3E0 Kapali alan" if m.get("indoor") else "\u2600\uFE0F Acik hava"
    fiyat = {"ucretsiz": "Ucretsiz", "uygun": "Uygun", "orta": "Orta butce",
             "yuksek": "Yuksek"}.get(m.get("price") or "", "")
    tags = ["#ankara", "#ankaradacocuk", "#ankaraetkinlik", "#cocuklagezi", "#ankaragezilecekyerler",
            "#ailece", "#cocukaktiviteleri", "#ankarabebek", "#haftasonu", "#ankaraanne"]
    kattag = {"park": "#park", "muze": "#muze", "yemek": "#cocukdostukafe", "oyun": "#oyunalani",
              "bilim": "#bilimmerkezi", "hayvanat": "#hayvanatbahcesi", "spor": "#buzpateni",
              "atolye": "#atolye", "gezi": "#gunubirlik", "sanat": "#cocuktiyatrosu",
              "kutuphane": "#kutuphane", "avm": "#avm"}.get(m["category"])
    if kattag:
        tags.insert(3, kattag)
    satir = [f"\U0001F4CD {m['name']} - {m.get('district') or 'Ankara'}", "", ac, "",
             f"\u2B50 Ankarada Cocuk Puani: {m['puan']}/10",
             f"\U0001F476 En uygun yas: {yas}",
             ortam + (f" | \U0001F4B8 {fiyat}" if fiyat else ""), "",
             "Detayli puan, ucret, ulasim ve aile ipuclari \U0001F449 ankaradacocuk.com", ""]
    if m.get("foto"):
        satir += [f"\U0001F4F7 {m['foto'].get('yazar', '')} / {m['foto'].get('lisans', '')}, Wikimedia Commons", ""]
    satir += [" ".join(tags)]
    return "\n".join(satir)


def avatar():
    W = 1080
    im = Image.new("RGB", (W, W), TURUNCU)
    d = ImageDraw.Draw(im)
    for yy in range(W):
        fr = yy / W
        d.line([(0, yy), (W, yy)], fill=tuple(int(c * (1 - .28 * fr)) for c in TURUNCU))
    logo = Image.new("RGBA", (660, 660), (0, 0, 0, 0))
    yuz(ImageDraw.Draw(logo), 0, 0, 660 / 64)
    im.paste(logo, ((W - 660) // 2, 150), logo)
    d.text((W / 2, W - 150), "ankaradacocuk", font=font(78), fill=BEYAZ, anchor="mm")
    return im


def kapak():
    W, H = 1640, 624
    im = Image.new("RGB", (W, H), KREM)
    d = ImageDraw.Draw(im)
    d.ellipse([W - 360, -180, W + 180, 360], fill=(255, 230, 217))
    logo = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    yuz(ImageDraw.Draw(logo), 0, 0, 300 / 64)
    im.paste(logo, (90, 150), logo)
    d.text((420, 185), "Ankara'da cocukla", font=font(76), fill=KOYU)
    d.text((420, 278), "gidilecek yerler", font=font(76), fill=TURUNCU)
    d.text((420, 398), "196 mekan | yasa gore puanli | kaynakli | ankaradacocuk.com",
           font=font(36, False), fill=(90, 90, 104))
    return im


def main():
    GON.mkdir(parents=True, exist_ok=True)
    PRO.mkdir(parents=True, exist_ok=True)
    # derlenmis hafif veri: puan + foto zaten iceride
    mekanlar = json.loads((KOK / "dist" / "static" / "mekanlar.json").read_text("utf-8"))
    aday = [m for m in mekanlar if m.get("foto") and m.get("status") != "kapali"]
    aday.sort(key=lambda m: -m["puan"])
    sec = aday[:12]
    metinler = ["# Instagram / Facebook - hazir gonderiler", "",
                "Her gorsel `sosyal/gonderiler/` icinde; metni kopyala-yapistir.", ""]
    for i, m in enumerate(sec, 1):
        img = mekan_gonderi(m)
        ad = f"{i:02d}-" + "".join(c for c in m["name"].lower() if c.isalnum())[:24]
        img.save(GON / f"{ad}.jpg", "JPEG", quality=88)
        metinler += [f"## {i:02d}. {m['name']}", "", "```", metin(m), "```", ""]
        print(f"{i:02d} {m['name'][:44]}")
    avatar().save(PRO / "avatar.jpg", "JPEG", quality=92)
    kapak().save(PRO / "kapak.jpg", "JPEG", quality=90)
    (PRO / "profil-metni.md").write_text(
        "# Profil kiti\n\n"
        "**Kullanici adi:** @ankaradacocuk\n\n"
        "**Ad:** Ankarada Cocuk - Ankara Aile Rehberi\n\n"
        "**Bio (Instagram):**\n"
        "Ankara'da cocukla gidilecek yerler\n"
        "196 mekan - yasa gore puanli - etkinlik takvimi\n"
        "Tumu sitede >> ankaradacocuk.com\n\n"
        "**Facebook Sayfa aciklamasi:**\n"
        "Ankara'da cocuklu aileler icin parklar, oyun alanli kafeler, muzeler, bilim merkezleri ve "
        "etkinlikler; her mekan 0-3 / 3-6 / 6-11 / 11-16 yas icin ayri puanli. Kaynakli ve guncel. "
        "ankaradacocuk.com\n", encoding="utf-8")
    (CIK / "metinler.md").write_text("\n".join(metinler), encoding="utf-8")
    print(f"\n{len(sec)} gonderi + profil kiti -> {CIK}")


if __name__ == "__main__":
    raise SystemExit(main())
