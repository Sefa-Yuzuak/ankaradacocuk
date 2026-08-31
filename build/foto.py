"""Mekânların GERÇEK, özgür lisanslı fotoğraflarını Wikipedia/Wikimedia'dan toplar.

İlke (bkz. kamu-misafirhaneleri/gorsel.py): stok/uydurma fotoğraf YOK. Yalnızca
Wikipedia maddesi mekânla KESİN eşleşen mekânların önde gelen serbest lisanslı
fotoğrafı alınır; yazar + lisans + kaynak saklanır ve sayfada künye gösterilir.
Eşleşme belirsizse foto konmaz (emoji kapak kalır).

Kullanım: python build/foto.py            -> data/foto.json + static/img/mekan/*.webp
"""
from __future__ import annotations
import io, json, re, sys, time, unicodedata, urllib.parse, urllib.request
from pathlib import Path
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
KOK = Path(__file__).resolve().parent.parent
IMG = KOK / "static" / "img" / "mekan"
HEDEF = KOK / "data" / "foto.json"
UA = {"User-Agent": "ankaradacocuk.com/1.0 (https://ankaradacocuk.com; merhaba@ankaradacocuk.com)"}
BOYUTLAR = {"lg": (1200, 675), "sm": (640, 360)}
KALITE = 72
LOGO_RE = __import__("re").compile(r"logo|seal|amblem|emblem|arma|coat|flag|bayrak|_map|harita|icon|afi[sş]|poster|banner", 2)
TR = str.maketrans("çğıöşüâîû", "cgiosuaiu")
STOP = {"ve", "ile", "ankara", "cocuk", "cocuklar", "cocuklu", "muzesi", "muze", "parki",
        "park", "merkezi", "merkez", "the", "ozel", "tarihi", "milli", "kir", "kafe",
        "cafe", "restaurant", "restoran", "bahcesi", "eski", "yeni", "buyuk", "kucuk"}


def _norm(s: str) -> set[str]:
    s = unicodedata.normalize("NFKD", (s or "").lower().translate(TR)).encode("ascii", "ignore").decode()
    return {t for t in re.findall(r"[a-z0-9]+", s) if len(t) > 2} - STOP


def _get(url: str) -> dict:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return json.load(r)


def _temiz(h: str | None) -> str:
    if not h:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", urllib.parse.unquote(h))).strip()


def _cekirdek(ad: str) -> str:
    return re.split(r"[(–\-]", ad)[0].strip()


def bul(ad: str) -> dict | None:
    """Wikipedia'da mekânı ara; KESİN eşleşen maddenin serbest lisanslı fotoğrafını döndür."""
    cekirdek = _cekirdek(ad)
    vtok = _norm(ad)
    if not vtok:
        return None
    q = urllib.parse.urlencode({
        "action": "query", "format": "json", "formatversion": "2",
        "generator": "search", "gsrsearch": cekirdek + " Ankara", "gsrlimit": "4",
        "gsrnamespace": "0", "prop": "pageimages|info", "piprop": "original|name",
        "pilicense": "free", "inprop": "url",
    })
    try:
        pages = _get("https://tr.wikipedia.org/w/api.php?" + q).get("query", {}).get("pages", [])
    except Exception:
        return None
    pages.sort(key=lambda p: p.get("index", 99))
    for p in pages:
        baslik = p.get("title", "")
        if "(anlam ayrımı)" in baslik or not (p.get("original") or {}).get("source"):
            continue
        ptok = _norm(baslik)
        if not ptok:
            continue
        # KATI eşleşme: madde tokenları mekân adında olmalı (ya da tersi), + uzun ortak token
        ortak = vtok & ptok
        uzun_ortak = any(len(t) >= 5 for t in ortak)
        kapsar = ptok <= vtok or vtok <= ptok or len(ortak) >= max(2, min(len(ptok), len(vtok)))
        if not (uzun_ortak and (ptok <= vtok or vtok <= ptok or len(ortak) >= 2)):
            continue
        dosya = p.get("pageimage")
        if not dosya or LOGO_RE.search(dosya):
            continue  # logo/amblem/harita: gerçek foto değil
        q2 = urllib.parse.urlencode({
            "action": "query", "format": "json", "formatversion": "2",
            "titles": f"File:{dosya}", "prop": "imageinfo",
            "iiprop": "extmetadata|url", "iiurlwidth": "1600",
        })
        try:
            bilgi = _get("https://commons.wikimedia.org/w/api.php?" + q2)["query"]["pages"][0]
        except Exception:
            continue
        ii = (bilgi.get("imageinfo") or [{}])[0]
        meta = ii.get("extmetadata") or {}
        m = lambda k: _temiz((meta.get(k) or {}).get("value"))
        lisans = m("LicenseShortName") or "Wikimedia Commons"
        if "all rights" in lisans.lower() or (meta.get("Copyrighted", {}).get("value") == "True" and not m("LicenseUrl")):
            continue
        return {
            "indir": ii.get("thumburl") or (p["original"]["source"]),
            "wiki": baslik,
            "yazar": m("Artist") or "Bilinmiyor",
            "lisans": lisans,
            "lisans_url": m("LicenseUrl"),
            "sayfa": ii.get("descriptionurl") or f"https://commons.wikimedia.org/wiki/File:{dosya}",
        }
    return None


def kirp_kaydet(veri: bytes, ad_slug: str) -> dict:
    im = Image.open(io.BytesIO(veri))
    if im.mode not in ("RGB", "L"):
        im = im.convert("RGB")
    g, y = im.size
    istenen = 16 / 9
    if g / y > istenen:
        yg = int(y * istenen); sol = (g - yg) // 2; im = im.crop((sol, 0, sol + yg, y))
    else:
        yy = int(g / istenen); ust = int((y - yy) * 0.32); im = im.crop((0, ust, g, ust + yy))
    out = {}
    for et, (bg, by) in BOYUTLAR.items():
        yol = IMG / f"{ad_slug}-{et}.webp"
        im.resize((bg, by), Image.LANCZOS).save(yol, "WEBP", quality=KALITE, method=6)
        out[et] = yol.name
    return out


def main() -> int:
    sys.path.insert(0, str(KOK / "build"))
    from derle import slugify
    mekanlar = json.loads((KOK / "data" / "mekanlar.json").read_text("utf-8"))
    IMG.mkdir(parents=True, exist_ok=True)
    sonuc = json.loads(HEDEF.read_text("utf-8")) if HEDEF.exists() else {}
    bulunan = 0
    for i, mk in enumerate(mekanlar, 1):
        ad = mk["name"]
        if ad in sonuc:
            if sonuc[ad]:
                bulunan += 1
            continue
        try:
            g = bul(ad)
            if not g:
                sonuc[ad] = None
                print(f"{i:3}/{len(mekanlar)} —  {ad[:45]}")
            else:
                with urllib.request.urlopen(urllib.request.Request(g["indir"], headers=UA), timeout=60) as r:
                    ham = r.read()
                dosyalar = kirp_kaydet(ham, slugify(ad))
                g.pop("indir")
                sonuc[ad] = {**g, **dosyalar}
                bulunan += 1
                print(f"{i:3}/{len(mekanlar)} ✓  {ad[:40]:40} <- {g['wiki'][:35]} [{g['lisans'][:18]}]")
        except Exception as ex:
            sonuc[ad] = None
            print(f"{i:3}/{len(mekanlar)} !  {ad[:40]} {type(ex).__name__}")
        HEDEF.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), "utf-8")
        time.sleep(0.3)
    print(f"\n{bulunan}/{len(mekanlar)} mekânda gerçek foto bulundu")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
