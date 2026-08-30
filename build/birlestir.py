"""data/raw/*.json dosyalarını tek data/mekanlar.json'da birleştirir.

- Aynı mekân birden çok kategoride geldiyse ilk kayıt tutulur, boş alanları
  diğer kayıttan doldurulur (lat/lng, telefon, saat, mesafe...).
- Şehre yakın "gezi" kayıtları park'a, festivaller sanat'a, kayak spor'a taşınır.
Kullanım: python build/birlestir.py
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

KOK = Path(__file__).resolve().parent.parent
RAW = KOK / "data" / "raw"
ZORUNLU = ["name", "category", "district", "description", "score_bebek", "score_okul_oncesi",
           "score_ilkokul", "score_ergen", "score_erisilebilirlik", "score_guvenlik", "score_fiyat_performans"]
SIRA = ["gezi", "muze", "park", "oyun", "yemek"]  # öncelik: önce gelen dosya kazanır
KOKLER = ["gordion", "mogan", "eymir", "beynam", "soguksu", "karagol", "camkoru", "mavigol", "elmadag",
          "ataturkcocuklari", "harikalardiyari", "genclikparki", "altinpark", "fezagursey", "aquavega",
          "ankarakalesi", "hamamonu", "anitkabir", "kartaltepe", "ahlatlibel", "tulumtas", "kizilcahamamtermal"]
TR = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def ilce(ad):
    if not ad:
        return "Ankara"
    ad = re.split(r"[/,(–-]", ad)[0].strip()
    return {"Tepebaşı": "Eskişehir", "Boğazkale": "Çorum"}.get(ad, ad) or "Ankara"


def anahtar(ad: str) -> str:
    k = re.sub(r"\(.*?\)", "", ad)
    k = re.sub(r"[^a-z0-9]", "", k.lower().translate(TR))
    for kok in KOKLER:
        if kok in k:
            return kok
    return k


def bos(v):
    return v in (None, "", [], {})


def yeniden_kategorile(m):
    alt = (m.get("subcategory") or "").lower()
    if m["category"] == "gezi":
        if alt == "festival":
            m["category"] = "sanat"
        elif alt == "kayak":
            m["category"] = "spor"
        elif alt == "çiftlik":
            m["category"] = "hayvanat"
        elif alt == "doğa" and (m.get("distance_km") or 999) <= 30:
            m["category"] = "park"
    return m


dosyalar = sorted(RAW.glob("*.json"), key=lambda p: SIRA.index(p.stem) if p.stem in SIRA else 99)
hepsi, indeks, uyarilar = [], {}, []
for dosya in dosyalar:
    for m in json.loads(dosya.read_text(encoding="utf-8")):
        k = anahtar(m["name"])
        if k in indeks:
            mevcut = indeks[k]
            doldurulan = [a for a, v in m.items() if bos(mevcut.get(a)) and not bos(v)]
            for a in doldurulan:
                if not a.startswith("score_") or a in ZORUNLU:
                    mevcut[a] = m[a]
            mevcut["sources"] = list(dict.fromkeys((mevcut.get("sources") or []) + (m.get("sources") or [])))
            uyarilar.append(f"BİRLEŞTİ: {m['name']} ({dosya.stem}) -> {mevcut['name']} (+{', '.join(doldurulan) or '-'})")
            continue
        eksik = [a for a in ZORUNLU if bos(m.get(a))]
        if eksik:
            uyarilar.append(f"EKSİK {m['name']}: {', '.join(eksik)}")
        m["district"] = ilce(m.get("district"))
        for a in ("lat", "lng", "distance_km"):
            if isinstance(m.get(a), str):
                try:
                    m[a] = float(m[a])
                except ValueError:
                    m[a] = None
        m.pop("score_notes", None)
        m.pop("score_guvenlik_note", None)
        yeniden_kategorile(m)
        indeks[k] = m
        hepsi.append(m)

KOORD = KOK / "data" / "koordinat.json"
if KOORD.exists():
    cache = json.loads(KOORD.read_text(encoding="utf-8"))
    for m in hepsi:
        k = cache.get(m["name"])
        if k and not (m.get("lat") and m.get("lng")):
            m["lat"], m["lng"], m["koordinat_kaynak"] = k["lat"], k["lng"], "osm"

(KOK / "data" / "mekanlar.json").write_text(json.dumps(hepsi, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{len(hepsi)} mekân yazıldı; {sum(1 for m in hepsi if m.get('lat'))} koordinatlı; "
      f"{sum(1 for m in hepsi if m.get('status') == 'kapalı')} kapalı")
for u in uyarilar:
    print(" -", u)
