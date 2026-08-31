# -*- coding: utf-8 -*-
"""Her mekan icin Google puani + yorum sayisi + harita linkini ceker (KURALLARA UYGUN).

Google Maps sartlari yorum METNINI kalici saklamaya izin vermez; place_id saklanabilir,
puan/sayi kisa sureli onbelleklenip her derlemede tazelenir, yoruma link verilir.
Bu script YALNIZCA rating + user_ratings_total + url + place_id saklar (yorum metni DEGIL).
Sonuc: data/google.json {name: {place_id, rating, count, url}}
Kullanim: python build/google.py
"""
from __future__ import annotations
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "build"))
from foto import _norm, _cekirdek

KEY = (KOK / "build" / ".places.key").read_text().strip()
UA = {"User-Agent": "ankaradacocuk.com/1.0"}
BASE = "https://maps.googleapis.com/maps/api/place/"
BIAS = "circle:45000@39.925,32.837"
HEDEF = KOK / "data" / "google.json"


def _json(path, par):
    par["key"] = KEY
    with urllib.request.urlopen(urllib.request.Request(BASE + path + "?" + urllib.parse.urlencode(par),
                                                       headers=UA), timeout=40) as r:
        return json.loads(r.read())


def cek(m):
    par = {"input": f"{_cekirdek(m['name'])} {m.get('district') or 'Ankara'} Ankara",
           "inputtype": "textquery", "fields": "place_id,name",
           "locationbias": (f"point:{m['lat']},{m['lng']}" if m.get("lat") and m.get("lng") else BIAS)}
    d = _json("findplacefromtext/json", par)
    if d.get("status") != "OK" or not d.get("candidates"):
        return None
    c = d["candidates"][0]
    if not any(len(t) >= 4 for t in (_norm(m["name"]) & _norm(c.get("name", "")))):
        return None
    pid = c["place_id"]
    dd = _json("details/json", {"place_id": pid, "fields": "rating,user_ratings_total,url"})
    if dd.get("status") != "OK":
        return None
    r = dd.get("result", {})
    if not r.get("rating"):
        return None
    return {"place_id": pid, "rating": r.get("rating"),
            "count": r.get("user_ratings_total") or 0, "url": r.get("url") or ""}


def main():
    mekanlar = json.loads((KOK / "data" / "mekanlar.json").read_text("utf-8"))
    sonuc = json.loads(HEDEF.read_text("utf-8")) if HEDEF.exists() else {}
    yeni = 0
    for i, m in enumerate(mekanlar, 1):
        if m["name"] in sonuc:
            continue
        try:
            g = cek(m)
            sonuc[m["name"]] = g  # None da yazilir: tekrar sorulmaz
            if g:
                yeni += 1
                print(f"{i:3}/{len(mekanlar)} {g['rating']}  ({g['count']:>4}) {m['name'][:40]}")
        except Exception as ex:
            print(f"{i:3}/{len(mekanlar)} !  {m['name'][:38]} {type(ex).__name__}")
        HEDEF.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), "utf-8")
        time.sleep(0.12)
    print(f"\nGoogle puani: {sum(1 for v in sonuc.values() if v)}/{len(mekanlar)} mekanda")


if __name__ == "__main__":
    raise SystemExit(main())
