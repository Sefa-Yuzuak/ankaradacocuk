"""Koordinatı olmayan mekânları OSM Nominatim ile geokodlar; sonuç data/koordinat.json'a
(önbellek) yazılır ve birlestir.py tarafından uygulanır. Nominatim kuralı: 1 istek/sn, UA zorunlu.
Yalnızca Ankara il sınırları (viewbox) içindeki sonuçlar kabul edilir.
Kullanım: python build/geokod.py
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
KOK = Path(__file__).resolve().parent.parent
ONBELLEK = KOK / "data" / "koordinat.json"
UA = "ankaradacocuk.com site derleyici (merhaba@ankaradacocuk.com)"
VIEWBOX = "30.8,41.2,34.0,38.6"  # lon_min,lat_max,lon_max,lat_min — Ankara ili + çevre


def sorgula(q: str):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": q, "format": "jsonv2", "limit": 1, "viewbox": VIEWBOX, "bounded": 1, "countrycodes": "tr"})
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "tr"})
    with urllib.request.urlopen(req, timeout=20) as r:
        sonuc = json.load(r)
    return sonuc[0] if sonuc else None


def main():
    mekanlar = json.loads((KOK / "data" / "mekanlar.json").read_text(encoding="utf-8"))
    cache = json.loads(ONBELLEK.read_text(encoding="utf-8")) if ONBELLEK.exists() else {}
    bulunan = 0
    for m in mekanlar:
        if m.get("lat") and m.get("lng") or m["name"] in cache:
            continue
        adaylar = [m.get("google_maps_query"), f"{m['name']}, {m.get('district')}, Ankara", m.get("address")]
        kayit = None
        for q in [a for a in adaylar if a]:
            try:
                r = sorgula(q)
            except Exception as e:
                print(f"  ! {m['name']}: {type(e).__name__}")
                r = None
            time.sleep(1.1)
            if r:
                kayit = {"lat": round(float(r["lat"]), 5), "lng": round(float(r["lon"]), 5),
                         "sorgu": q, "eslesme": r.get("display_name", "")[:120], "tur": r.get("type")}
                break
        cache[m["name"]] = kayit  # None da kaydedilir: tekrar sorulmaz
        if kayit:
            bulunan += 1
            print(f"  ✓ {m['name']} -> {kayit['lat']},{kayit['lng']} ({kayit['tur']})")
        else:
            print(f"  ✗ {m['name']}")
        ONBELLEK.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{bulunan} yeni koordinat; önbellekte {sum(1 for v in cache.values() if v)} / {len(cache)}")


if __name__ == "__main__":
    main()
