# -*- coding: utf-8 -*-
"""2. gecis: gercek fotografi olmayan mekanlar icin Wikimedia Commons'ta daha genis arama.

Wikipedia madde on gorseli (foto.py) disinda, dogrudan Commons'ta:
  1) dosya adi aramasi (namespace 6)
  2) koordinata gore geosearch (yakindaki cogtag'li dosyalar)
Kati isim eslesmesi + logo/harita/svg filtresi + serbest lisans zorunlu; belirsizse ATLA.
Sonuclari data/foto.json'a EKLER (mevcut None kayitlarini gunceller). Kullanim: python build/foto2.py
"""
from __future__ import annotations
import json
import sys
import time
import urllib.parse
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "build"))
from foto import _get, _norm, _temiz, _cekirdek, kirp_kaydet, LOGO_RE, HEDEF, IMG
from derle import slugify

COMMONS = "https://commons.wikimedia.org/w/api.php?"


def _meta(ii):
    meta = ii.get("extmetadata") or {}
    m = lambda k: _temiz((meta.get(k) or {}).get("value"))
    lisans = m("LicenseShortName") or "Wikimedia Commons"
    if "all rights" in lisans.lower():
        return None
    return {"yazar": m("Artist") or "Bilinmiyor", "lisans": lisans,
            "lisans_url": m("LicenseUrl")}


def _uygun(p, vtok):
    title = p.get("title", "")
    dosya = title.split("File:")[-1]
    if LOGO_RE.search(dosya) or dosya.lower().rsplit(".", 1)[-1] in ("svg", "pdf", "gif", "tif", "tiff"):
        return None
    ii = (p.get("imageinfo") or [{}])[0]
    if not str(ii.get("mime", "")).startswith("image/"):
        return None
    ptok = _norm(dosya)
    if not ptok:
        return None
    ortak = vtok & ptok
    # kati: uzun ortak token + (madde adi mekan adinda ya da >=2 ortak)
    if not (any(len(t) >= 5 for t in ortak) and (ptok <= vtok or len(ortak) >= 2)):
        return None
    mm = _meta(ii)
    if not mm:
        return None
    return {"indir": ii.get("thumburl") or ii.get("url"), "wiki": dosya,
            "sayfa": ii.get("descriptionurl") or f"https://commons.wikimedia.org/wiki/{title}", **mm}


def commons_bul(m):
    vtok = _norm(m["name"])
    if not vtok:
        return None
    ortak_par = {"prop": "imageinfo", "iiprop": "url|extmetadata|mime", "iiurlwidth": "1600"}
    # 1) isim aramasi
    q = urllib.parse.urlencode({"action": "query", "format": "json", "formatversion": "2",
                                "generator": "search", "gsrsearch": _cekirdek(m["name"]) + " Ankara",
                                "gsrnamespace": "6", "gsrlimit": "6", **ortak_par})
    try:
        pages = _get(COMMONS + q).get("query", {}).get("pages", [])
    except Exception:
        pages = []
    pages.sort(key=lambda p: p.get("index", 99))
    for p in pages:
        r = _uygun(p, vtok)
        if r:
            return r
    # 2) koordinat geosearch
    if m.get("lat") and m.get("lng"):
        q2 = urllib.parse.urlencode({"action": "query", "format": "json", "formatversion": "2",
                                     "generator": "geosearch", "ggscoord": f"{m['lat']}|{m['lng']}",
                                     "ggsradius": "300", "ggsnamespace": "6", "ggslimit": "12", **ortak_par})
        try:
            pages2 = _get(COMMONS + q2).get("query", {}).get("pages", [])
        except Exception:
            pages2 = []
        for p in pages2:
            r = _uygun(p, vtok)
            if r:
                return r
    return None


def main():
    import urllib.request
    from foto import UA
    IMG.mkdir(parents=True, exist_ok=True)
    mekanlar = json.loads((KOK / "data" / "mekanlar.json").read_text("utf-8"))
    sonuc = json.loads(HEDEF.read_text("utf-8")) if HEDEF.exists() else {}
    yeni = 0
    for i, mk in enumerate(mekanlar, 1):
        ad = mk["name"]
        if sonuc.get(ad):
            continue  # zaten gercek foto var
        try:
            g = commons_bul(mk)
            if not g:
                continue
            with urllib.request.urlopen(urllib.request.Request(g["indir"], headers=UA), timeout=60) as r:
                ham = r.read()
            dosyalar = kirp_kaydet(ham, slugify(ad))
            g.pop("indir")
            sonuc[ad] = {**g, **dosyalar}
            yeni += 1
            print(f"{i:3} + {ad[:38]:38} <- {g['wiki'][:34]} [{g['lisans'][:16]}]")
        except Exception as ex:
            print(f"{i:3} ! {ad[:38]} {type(ex).__name__}")
        time.sleep(0.3)
    HEDEF.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), "utf-8")
    print(f"\n2. gecis: +{yeni} yeni gercek foto. Toplam: {sum(1 for v in sonuc.values() if v)}")


if __name__ == "__main__":
    raise SystemExit(main())
