# -*- coding: utf-8 -*-
"""Instagram/TikTok Reels: dikey (1080x1920) slayt videolari uretir (ffmpeg + PIL).

Sitedeki GERCEK foto + puandan uretir (uydurma yok). Her tema icin: intro (hook) +
5 mekan karti + outro (CTA). Kareler PIL ile, hareket (yumusak zoom) + birlestirme ffmpeg ile.
Ses YOK: trend sesi Instagram'da eklenir (algoritma icin daha iyi + telif guvenli).
Cikti: reels/<tema>.mp4 + reels/reels-metin.md
Kullanim: python build/reels.py            (once: python build/derle.py)
"""
from __future__ import annotations
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8")
KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "build"))
from ikon import yuz

W, H = 1080, 1920
CIK = KOK / "reels"
IMG = KOK / "static" / "img" / "mekan"
TURUNCU, TKOYU, SARI, KOYU, BEYAZ = (255, 122, 89), (230, 96, 63), (255, 201, 77), (30, 30, 38), (255, 255, 255)
EN_IYI = [("score_bebek", "0-3"), ("score_okul_oncesi", "3-6"), ("score_ilkokul", "6-11"), ("score_ergen", "11-16")]


def font(px, kalin=True):
    adlar = (["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"] if kalin
             else ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"])
    for a in adlar:
        try:
            return ImageFont.truetype(a, px)
        except OSError:
            continue
    return ImageFont.load_default()


def efont(px):
    try:
        return ImageFont.truetype("C:/Windows/Fonts/seguiemj.ttf", px)
    except OSError:
        return None


def sar(d, metin, fnt, en):
    sat, cur = [], ""
    for k in metin.split():
        t = (cur + " " + k).strip()
        if d.textlength(t, font=fnt) <= en:
            cur = t
        else:
            if cur:
                sat.append(cur)
            cur = k
    if cur:
        sat.append(cur)
    return sat


def koyult(rgb, f):
    return tuple(max(0, min(255, int(c * f))) for c in rgb)


def kirp_doldur(im, w, h):
    """cover-fit: hedef orana kirp, doldur."""
    im = im.convert("RGB")
    o_h = w / h
    o = im.width / im.height
    if o > o_h:
        yeni = int(im.height * o_h)
        x = (im.width - yeni) // 2
        im = im.crop((x, 0, x + yeni, im.height))
    else:
        yeni = int(im.width / o_h)
        y = (im.height - yeni) // 2
        im = im.crop((0, y, im.width, y + yeni))
    return im.resize((w, h), Image.LANCZOS)


def en_iyi_yas(m):
    return max(EN_IYI, key=lambda t: m.get(t[0]) or 0)[1]


def marka():
    logo = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    yuz(ImageDraw.Draw(logo), 0, 0, 1.0)
    return logo


def zemin(kr):
    im = Image.new("RGB", (W, H), kr)
    d = ImageDraw.Draw(im)
    for yy in range(H):
        f = yy / H
        d.line([(0, yy), (W, yy)], fill=koyult(kr, 1 - 0.5 * f))
    return im


def yildiz(d, cx, cy, r, kr):
    pts = []
    import math as _m
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.42
        a = -_m.pi / 2 + i * _m.pi / 5
        pts.append((cx + rr * _m.cos(a), cy + rr * _m.sin(a)))
    d.polygon(pts, fill=kr)


def intro_kare(baslik, emoji, kr):
    im = zemin(kr)
    d = ImageDraw.Draw(im)
    # emoji (renkli, üstte)
    ef = efont(190)
    if ef:
        el = Image.new("RGBA", (250, 250), (0, 0, 0, 0))
        ImageDraw.Draw(el).text((125, 125), emoji, font=ef, anchor="mm", embedded_color=True)
        im.paste(el, (W // 2 - 125, 300), el)
    # başlık: üst satır küçük, vurgu satırı büyük
    parts = baslik.split("\n")
    ust = parts[0] if len(parts) > 1 else ""
    vur = parts[-1]
    y = 640
    if ust:
        fb = font(84)
        for s in sar(d, ust, fb, W - 150):
            d.text((W // 2, y), s, font=fb, fill=(255, 255, 255), anchor="mm")
            y += 100
    y += 26
    fh = font(150)
    for s in sar(d, vur, fh, W - 110):
        d.text((W // 2, y), s, font=fh, fill=SARI, anchor="mm")
        y += 168
    # fayda şeridi (emoji yok — tofu olmasın)
    y += 40
    d.rounded_rectangle([W // 2 - 360, y, W // 2 + 360, y + 116], radius=58, fill=BEYAZ)
    d.text((W // 2, y + 58), "PUANLI LİSTE · KAYDET", font=font(52), fill=TKOYU, anchor="mm")
    # marka alt
    lg = marka()
    im.paste(lg, (W // 2 - 158, H - 158), lg)
    d.text((W // 2 - 74, H - 138), "ankaradaçocuk", font=font(48), fill=BEYAZ, anchor="lm")
    return im


def mekan_kare(m, sira):
    im = Image.new("RGB", (W, H), KOYU)
    foto = None
    if m.get("foto"):
        yol = IMG / m["foto"]["lg"]
        if yol.exists():
            foto = Image.open(yol)
    if foto is None and m.get("kapak"):
        yol = IMG / m["kapak"]
        if yol.exists():
            foto = Image.open(yol)
    ust_h = 1180
    if foto:
        im.paste(kirp_doldur(foto, W, ust_h), (0, 0))
    d = ImageDraw.Draw(im, "RGBA")
    # ust karartma (sira rozeti okunur)
    d.rectangle([0, 0, W, 260], fill=(0, 0, 0, 90))
    # alt gecis (foto -> kart)
    for i in range(220):
        a = int(255 * (i / 220))
        d.line([(0, ust_h - 220 + i), (W, ust_h - 220 + i)], fill=(30, 30, 38, a))
    d.rectangle([0, ust_h, W, H], fill=(30, 30, 38, 255))
    # sira rozeti
    d.ellipse([54, 60, 214, 220], fill=TURUNCU)
    d.text((134, 132), f"{sira}", font=font(104), fill=BEYAZ, anchor="mm")
    # puan rozeti (sag ust) — çizili yıldız (emoji tofu olmasın)
    kr = tuple(int((m.get("renk") or "#ff7a59").lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    d.rounded_rectangle([W - 258, 64, W - 54, 182], radius=56, fill=(255, 255, 255, 238))
    yildiz(d, W - 208, 110, 26, (245, 180, 60))
    d.text((W - 172, 110), f"{m['puan']}", font=font(60), fill=koyult(kr, 0.62), anchor="lm")
    d.text((W - 156, 158), "/10", font=font(30), fill=koyult(kr, 0.62), anchor="mm")
    # kategori cipi
    cip = (m.get("kat_ad") or "").upper()
    if cip:
        cf = font(38)
        cw = d.textlength(cip, font=cf) + 46
        d.rounded_rectangle([60, ust_h + 44, 60 + cw, ust_h + 116], radius=36, fill=kr)
        d.text((60 + 23, ust_h + 80), cip, font=cf, fill=BEYAZ, anchor="lm")
    # isim
    isf = font(78)
    sat = sar(d, m["name"], isf, W - 120)[:3]
    y = ust_h + 150
    for s in sat:
        d.text((60, y), s, font=isf, fill=BEYAZ)
        y += 90
    # bilgi satiri (emoji yok — tofu olmasın; nokta ayraç)
    yas = en_iyi_yas(m)
    ortam = "Kapalı alan" if m.get("indoor") else "Açık hava"
    bilgi = f"{m.get('district') or 'Ankara'}   ·   {yas} yaş   ·   {ortam}"
    d.text((60, y + 20), bilgi, font=font(46, False), fill=(228, 228, 238), anchor="lm")
    # aciklama (kisa)
    ac = (m.get("description") or "").strip().split(". ")[0].strip()
    if ac:
        if len(ac) > 110:
            ac = ac[:110].rsplit(" ", 1)[0] + "…"
        for i, s in enumerate(sar(d, ac, font(42, False), W - 120)[:2]):
            d.text((60, y + 100 + i * 54), s, font=font(42, False), fill=(180, 180, 195))
    return im


def outro_kare(toplam, kr):
    im = zemin(kr)
    d = ImageDraw.Draw(im)
    lg = Image.new("RGBA", (170, 170), (0, 0, 0, 0))
    yuz(ImageDraw.Draw(lg), 0, 0, 170 / 64)
    im.paste(lg, (W // 2 - 85, 430), lg)
    d.text((W // 2, 700), "ankaradaçocuk.com", font=font(92), fill=BEYAZ, anchor="mm")
    for i, s in enumerate([f"{toplam} mekân · yaşa göre puanlı",
                           "park · müze · oyun · etkinlik", "hepsi tek sitede"]):
        d.text((W // 2, 840 + i * 78), s, font=font(50, False), fill=(255, 245, 235), anchor="mm")
    d.rounded_rectangle([W // 2 - 340, 1160, W // 2 + 340, 1284], radius=62, fill=SARI)
    d.text((W // 2, 1222), "KAYDET · PAYLAŞ", font=font(54), fill=KOYU, anchor="mm")
    d.text((W // 2, 1372), "Takip et  @ankaradacocuk", font=font(50), fill=BEYAZ, anchor="mm")
    return im


def klip(kare_yolu, mp4_yolu, sure, zoom_in=True):
    """Tek kareden yumusak zoom'lu klip (ffmpeg zoompan)."""
    kf = int(sure * 30)
    if zoom_in:
        z = "min(zoom+0.0006,1.14)"
    else:
        z = "if(eq(on,0),1.14,max(zoom-0.0006,1.0))"
    vf = (f"scale=2160:3840,zoompan=z='{z}':d={kf}:x='iw/2-(iw/zoom/2)':"
          f"y='ih/2-(ih/zoom/2)':s={W}x{H}:fps=30,format=yuv420p")
    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", str(kare_yolu), "-t", f"{sure}",
                    "-vf", vf, "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                    "-r", "30", str(mp4_yolu)], check=True, capture_output=True)


MUZIK = KOK / "muzik"


def _synth_bed(sure, cikti):
    """Orijinal, TELİFSİZ yumuşak akor pad'i (C-majör). Gerçek müzik yoksa yedek.
    Instagram'da 'orijinal ses' olur, telif riski yok."""
    dur = f"{sure:.2f}"
    fout = f"{max(0.1, sure - 1.6):.2f}"
    girisler = []
    for frq in (261.63, 329.63, 392.00, 523.25):  # C4 E4 G4 C5
        girisler += ["-f", "lavfi", "-i", f"sine=frequency={frq}:duration={dur}"]
    fc = (f"[0][1][2][3]amix=inputs=4,tremolo=f=0.2:d=0.55,"
          f"aecho=0.8:0.85:130:0.35,lowpass=f=1050,highpass=f=90,"
          f"afade=t=in:st=0:d=1.2,afade=t=out:st={fout}:d=1.6,volume=1.5[a]")
    subprocess.run(["ffmpeg", "-y", *girisler, "-filter_complex", fc,
                    "-map", "[a]", "-c:a", "aac", "-b:a", "160k", str(cikti)],
                   check=True, capture_output=True)


def muzik_ekle(sessiz_mp4, cikti_mp4, idx, sure):
    """Videoya ses göm. muzik/ içinde gerçek telifsiz parça varsa onu (döngü+fade);
    yoksa orijinal synth pad. Sessiz reels Keşfet'te geri planda kalır — bunu çözer."""
    parcalar = sorted(p for e in ("*.mp3", "*.m4a", "*.wav", "*.aac", "*.ogg")
                      for p in MUZIK.glob(e)) if MUZIK.exists() else []
    fout = f"{max(0.1, sure - 1.6):.2f}"
    if parcalar:
        trk = parcalar[idx % len(parcalar)]
        fc = f"[1:a]afade=t=out:st={fout}:d=1.6,volume=0.85[a]"
        subprocess.run(["ffmpeg", "-y", "-i", str(sessiz_mp4),
                        "-stream_loop", "-1", "-i", str(trk),
                        "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                        "-t", f"{sure:.2f}", str(cikti_mp4)],
                       check=True, capture_output=True)
        return trk.name
    # yedek: synth
    import tempfile as _tf
    with _tf.TemporaryDirectory() as _t:
        bed = Path(_t) / "bed.m4a"
        _synth_bed(sure, bed)
        subprocess.run(["ffmpeg", "-y", "-i", str(sessiz_mp4), "-i", str(bed),
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "160k", "-shortest", str(cikti_mp4)],
                       check=True, capture_output=True)
    return "synth-pad (telifsiz)"


def reel_yap(tema, mekanlar):
    kr = tuple(int(tema["renk"].lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    sec = [m for m in mekanlar if tema["filt"](m) and (m.get("foto") or m.get("kapak"))]
    sec.sort(key=lambda m: -((m.get("puan") or 0) + 1.6 * math.log10(((m.get("google") or {}).get("count") or 0) + 1)))
    top, gorulen = [], set()
    for m in sec:
        if m["name"] in gorulen:
            continue
        top.append(m); gorulen.add(m["name"])
        if len(top) >= 5:
            break
    if len(top) < 3:
        print(f"  ! {tema['slug']}: yeterli mekân yok ({len(top)})")
        return None
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        klipler = []
        S_INTRO, S_KART, S_OUTRO = 2.0, 2.5, 2.6
        # intro (hızlı hook)
        intro_kare(tema["baslik"], tema["emoji"], kr).save(td / "k00.png")
        klip(td / "k00.png", td / "c00.mp4", S_INTRO, True)
        klipler.append(td / "c00.mp4")
        # mekanlar
        for i, m in enumerate(top, 1):
            mekan_kare(m, i).save(td / f"k{i:02d}.png")
            klip(td / f"k{i:02d}.png", td / f"c{i:02d}.mp4", S_KART, i % 2 == 1)
            klipler.append(td / f"c{i:02d}.mp4")
        # outro
        outro_kare(TOPLAM, kr).save(td / "k99.png")
        klip(td / "k99.png", td / "c99.mp4", S_OUTRO, False)
        klipler.append(td / "c99.mp4")
        toplam_sure = S_INTRO + len(top) * S_KART + S_OUTRO
        # birlestir (sessiz)
        liste = td / "liste.txt"
        liste.write_text("".join(f"file '{c.as_posix()}'\n" for c in klipler), encoding="utf-8")
        sessiz = td / "sessiz.mp4"
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(liste),
                        "-c", "copy", str(sessiz)], check=True, capture_output=True)
        # ses göm
        cikti = CIK / f"reel-{tema['slug']}.mp4"
        try:
            idx = TEMALAR.index(tema)
        except ValueError:
            idx = 0
        ses = muzik_ekle(sessiz, cikti, idx, toplam_sure)
    print(f"  ✓ {tema['slug']}: {len(top)} mekân, {toplam_sure:.1f}s, ses: {ses} -> {cikti.name}")
    return {"tema": tema, "mekanlar": top}


def metin(sonuc):
    tema = sonuc["tema"]
    tags = ("#ankara #ankaradacocuk #reels #ankaraetkinlik #cocuklagezi #ankaragezilecekyerler "
            "#ailece #cocukaktiviteleri #ankarabebek #haftasonu #ankaraanne #kesfet")
    liste = "\n".join(f"{i}. {m['name']} ({m.get('district') or 'Ankara'}) — {m['puan']}/10"
                      for i, m in enumerate(sonuc["mekanlar"], 1))
    return (f"## {tema['baslik'].replace(chr(10), ' ')}\n\n"
            f"**Video:** `reels/reel-{tema['slug']}.mp4` (sessiz — IG'de trend sesi ekle)\n\n"
            f"**Kapak:** ilk kare\n\n**Önerilen açıklama:**\n```\n{tema['caption']}\n\n{liste}\n\n"
            f"Detaylar 👉 ankaradacocuk.com\n\n{tags}\n```\n")


TEMALAR = [
    {"slug": "parklar", "baslik": "ANKARA'DA ÇOCUKLA\nEN İYİ 5 PARK", "emoji": "🌳", "renk": "#3aa66d",
     "filt": lambda m: m["category"] == "park",
     "caption": "Ankara'da çocukla en iyi 5 park! 🌳 Hangisine gittin? 👇"},
    {"slug": "yagmurlu-gun", "baslik": "YAĞMURLU GÜNDE\nÇOCUKLA 5 KAPALI MEKÂN", "emoji": "🌧️", "renk": "#2f7de1",
     "filt": lambda m: m.get("indoor") and m["category"] in ("bilim", "muze", "oyun", "spor"),
     "caption": "Yağmur mu var? Kapalı ama eğlenceli 5 yer ☔️ Kaydet, lazım olur!"},
    {"slug": "muzeler", "baslik": "ÇOCUKLA GEZİLECEK\n5 ANKARA MÜZESİ", "emoji": "🏛️", "renk": "#8a63d2",
     "filt": lambda m: m["category"] == "muze",
     "caption": "Çocukla öğrenmek eğlenceli! Ankara'nın en iyi 5 çocuk dostu müzesi 🏛️"},
    {"slug": "hayvanat", "baslik": "HAYVANLARI SEVEN\nÇOCUKLARA 5 YER", "emoji": "🦁", "renk": "#d9822b",
     "filt": lambda m: m["category"] == "hayvanat",
     "caption": "Akvaryum, çiftlik, hayvan parkı… Hayvan seven çocuklara 5 adres 🦁🐠"},
]


def main():
    CIK.mkdir(parents=True, exist_ok=True)
    global TOPLAM
    mekanlar = json.loads((KOK / "dist" / "static" / "mekanlar.json").read_text("utf-8"))
    mekanlar = [m for m in mekanlar if m.get("status") != "kapali"]
    TOPLAM = len(mekanlar)
    print(f"{len(TEMALAR)} tema, {TOPLAM} mekân...\n")
    md = ["# Instagram / TikTok Reels — hazır videolar", "",
          "Her video `reels/` içinde, 1080x1920 sessiz MP4. Instagram'da yükleyip **trend sesi** ekle.", ""]
    for tema in TEMALAR:
        s = reel_yap(tema, mekanlar)
        if s:
            md.append(metin(s))
    (CIK / "reels-metin.md").write_text("\n".join(md), encoding="utf-8")
    print(f"\n-> {CIK}")


if __name__ == "__main__":
    main()
