# -*- coding: utf-8 -*-
"""Google Places'tan mekanlarin GERCEK fotografini ceker (Wikimedia'da olmayanlar icin).

Anahtar build/.places.key'den okunur (git'e gitmez). Her mekan icin:
  Find Place (ad + ilce + Ankara konum yanliligi) -> place_id
  Place Details -> en iyi (manzara) foto + html_attributions + harita url
  Place Photo -> gorsel; 16:9 webp (foto.kirp_kaydet)
Kati ad kontrolu ile yanlis eslesme elenir. Sonuc data/foto.json'a EKLENIR (kaynak: google).
Google sartlari: fotograf attribution GOSTERILIR; site her derlemede tazelenir.
Kullanim: python build/places.py
"""
from __future__ import annotations
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "build"))
from foto import _norm, kirp_kaydet, HEDEF, IMG, _cekirdek
from derle import slugify

KEY = (KOK / "build" / ".places.key").read_text().strip()
UA = {"User-Agent": "ankaradacocuk.com/1.0 photo fetch"}
BASE = "https://maps.googleapis.com/maps/api/place/"
ANKARA_BIAS = "circle:45000@39.925,32.837"


def _get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
        return r.status, r.read()


def _json(path, par):
    par["key"] = KEY
    s, b = _get(BASE + path + "?" + urllib.parse.urlencode(par))
    return json.loads(b)


def bul(m):
    ad = m["name"]
    ilce = m.get("district") or "Ankara"
    sorgu = f"{_cekirdek(ad)} {ilce} Ankara"
    par = {"input": sorgu, "inputtype": "textquery", "fields": "place_id,name",
           "locationbias": (f"point:{m['lat']},{m['lng']}" if m.get("lat") and m.get("lng") else ANKARA_BIAS)}
    d = _json("findplacefromtext/json", par)
    if d.get("status") != "OK" or not d.get("candidates"):
        return None, d.get("status")
    c = d["candidates"][0]
    # kati ad kontrolu: en az bir ayirt edici ortak token (uzunluk>=4)
    vtok, ptok = _norm(ad), _norm(c.get("name", ""))
    ortak = vtok & ptok
    if not any(len(t) >= 4 for t in ortak):
        return None, f"AD-UYUSMAZ({c.get('name','')[:24]})"
    return c["place_id"], "OK"


def foto_sec(fotolar):
    """16:9 kapaga uygun: once genis (manzara) olani sec."""
    if not fotolar:
        return None
    manzara = [p for p in fotolar if p.get("width", 0) >= p.get("height", 1) * 1.2]
    return (manzara or fotolar)[0]


def cek(m):
    pid, durum = bul(m)
    if not pid:
        return None, durum
    dd = _json("details/json", {"place_id": pid, "fields": "name,photos,url"})
    if dd.get("status") != "OK":
        return None, "DETAILS-" + dd.get("status", "?")
    res = dd.get("result", {})
    p = foto_sec(res.get("photos") or [])
    if not p:
        return None, "FOTO-YOK"
    attr = re.sub("<[^>]+>", "", (p.get("html_attributions") or ["Google"])[0]).strip() or "Google"
    q = urllib.parse.urlencode({"maxwidth": "1600", "photo_reference": p["photo_reference"], "key": KEY})
    s, ham = _get(BASE + "photo?" + q)
    if not (ham[:3] == b"\xff\xd8\xff" or ham[:4] == b"\x89PNG" or ham[:4] == b"RIFF"):
        return None, "GORSEL-DEGIL"
    return {"ham": ham, "yazar": attr, "lisans": "Google", "sayfa": res.get("url") or "",
            "kaynak": "google", "wiki": ""}, "OK"


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    mekanlar = json.loads((KOK / "data" / "mekanlar.json").read_text("utf-8"))
    sonuc = json.loads(HEDEF.read_text("utf-8")) if HEDEF.exists() else {}
    yeni = 0
    hedefler = [m for m in mekanlar if not sonuc.get(m["name"])]
    print(f"Google Places: {len(hedefler)} mekan (fotografi olmayan) denenecek\n")
    for i, m in enumerate(hedefler, 1):
        ad = m["name"]
        try:
            g, durum = cek(m)
            if not g:
                print(f"{i:3}/{len(hedefler)} -  {ad[:40]:40} [{durum}]")
                continue
            dosyalar = kirp_kaydet(g.pop("ham"), slugify(ad))
            sonuc[ad] = {**g, **dosyalar}
            yeni += 1
            print(f"{i:3}/{len(hedefler)} OK {ad[:40]:40} <- {g['yazar'][:26]}")
        except Exception as ex:
            print(f"{i:3}/{len(hedefler)} !  {ad[:40]} {type(ex).__name__}: {str(ex)[:40]}")
        HEDEF.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), "utf-8")
        time.sleep(0.12)
    print(f"\nGoogle Places: +{yeni} gercek foto. Toplam gercek: {sum(1 for v in sonuc.values() if v)}/{len(mekanlar)}")


if __name__ == "__main__":
    raise SystemExit(main())
