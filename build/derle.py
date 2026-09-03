"""ankaradacocuk.com statik site üreteci.

Kullanım:  python build/derle.py            -> dist/ klasörüne tüm siteyi yazar
Girdi:     data/site.json, data/mekanlar.json, data/rehberler.json
"""
from __future__ import annotations

import json
import sys
sys.stdout.reconfigure(encoding='utf-8')
import re
import shutil
import statistics
import unicodedata
from datetime import date, timedelta, datetime, timezone
from math import radians, sin, cos, asin, sqrt
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

KOK = Path(__file__).resolve().parent.parent
DATA = KOK / "data"
DIST = KOK / "dist"
TEMPLATES = KOK / "templates"
STATIC = KOK / "static"

TR_MAP = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def slugify(metin: str) -> str:
    metin = metin.translate(TR_MAP)
    metin = unicodedata.normalize("NFKD", metin).encode("ascii", "ignore").decode()
    metin = re.sub(r"[^a-zA-Z0-9]+", "-", metin).strip("-").lower()
    return re.sub(r"-{2,}", "-", metin)


KATEGORILER = {
    "park": {"ad": "Parklar & Açık Hava", "kisa": "Park", "ikon": "🌳", "renk": "#3aa66d",
             "aciklama": "Oyun alanları, millet bahçeleri, göl kenarları ve piknik yerleri.",
             "schema": "Park"},
    "muze": {"ad": "Müzeler & Kültür", "kisa": "Müze", "ikon": "🏛️", "renk": "#8a63d2",
             "aciklama": "Çocuklarla keşfedilecek müzeler, tarihî mekânlar ve sergiler.",
             "schema": "Museum"},
    "bilim": {"ad": "Bilim & Keşif", "kisa": "Bilim", "ikon": "🔭", "renk": "#2f7de1",
              "aciklama": "Bilim merkezleri, planetaryumlar ve deney atölyeleri.",
              "schema": "Museum"},
    "hayvanat": {"ad": "Hayvanlar & Akvaryum", "kisa": "Hayvanlar", "ikon": "🦒", "renk": "#d9822b",
                 "aciklama": "Akvaryum, hayvan parkı ve hayvan besleme çiftlikleri.",
                 "schema": "TouristAttraction"},
    "sanat": {"ad": "Tiyatro & Sanat", "kisa": "Sanat", "ikon": "🎭", "renk": "#c94a8c",
              "aciklama": "Çocuk tiyatroları, opera, sinema ve sanat atölyeleri.",
              "schema": "PerformingArtsTheater"},
    "oyun": {"ad": "Oyun & Eğlence Merkezleri", "kisa": "Oyun", "ikon": "🎪", "renk": "#e8553d",
             "aciklama": "Kapalı oyun alanları, trambolin parkları, lunapark ve eğlence merkezleri.",
             "schema": "AmusementPark"},
    "spor": {"ad": "Spor & Macera", "kisa": "Spor", "ikon": "⛸️", "renk": "#1fa2a6",
             "aciklama": "Buz pisti, kayak, karting, tırmanma, binicilik ve yüzme.",
             "schema": "SportsActivityLocation"},
    "atolye": {"ad": "Atölyeler & Kurslar", "kisa": "Atölye", "ikon": "🎨", "renk": "#b8862b",
               "aciklama": "Seramik, robotik, mutfak, lego ve yaratıcı atölyeler.",
               "schema": "LocalBusiness"},
    "kutuphane": {"ad": "Kütüphaneler", "kisa": "Kütüphane", "ikon": "📚", "renk": "#5f6f8f",
                  "aciklama": "Çocuk bölümü olan kütüphaneler ve okuma alanları.",
                  "schema": "Library"},
    "avm": {"ad": "AVM Çocuk Alanları", "kisa": "AVM", "ikon": "🛍️", "renk": "#7a5cff",
            "aciklama": "Alışveriş merkezlerindeki oyun ve eğlence alanları.",
            "schema": "ShoppingCenter"},
    "yemek": {"ad": "Çocuk Dostu Kafe & Restoran", "kisa": "Yemek", "ikon": "🍽️", "renk": "#e0742f",
              "aciklama": "Oyun alanlı kafeler, kahvaltı bahçeleri ve aile restoranları.",
              "schema": "Restaurant"},
    "gezi": {"ad": "Günübirlik Geziler & Doğa", "kisa": "Gezi", "ikon": "🚗", "renk": "#2b8a5e",
             "aciklama": "Ankara çevresinde günübirlik doğa, tarih, çiftlik ve kaplıca rotaları.",
             "schema": "TouristAttraction"},
}

YAS_GRUPLARI = [
    {"slug": "0-3-yas", "ad": "0-3 yaş (bebek)", "kisa": "0-3", "alan": "score_bebek", "ikon": "🍼",
     "aciklama": "Bebek arabasıyla rahat gezilen, sakin, güvenli ve bebek bakım imkânı olan mekânlar."},
    {"slug": "3-6-yas", "ad": "3-6 yaş (okul öncesi)", "kisa": "3-6", "alan": "score_okul_oncesi", "ikon": "🧸",
     "aciklama": "Oyun alanı, top havuzu, hayvan besleme ve kısa dikkat süresine uygun aktiviteler."},
    {"slug": "6-11-yas", "ad": "6-11 yaş (ilkokul)", "kisa": "6-11", "alan": "score_ilkokul", "ikon": "🚲",
     "aciklama": "Bilim merkezleri, trambolin, macera parkurları ve keşif temelli müzeler."},
    {"slug": "11-16-yas", "ad": "11-16 yaş (ergen)", "kisa": "11-16", "alan": "score_ergen", "ikon": "🛹",
     "aciklama": "Karting, tırmanma, buz pateni, kayak, kaçış odası ve derin içerikli müzeler."},
]

FIYAT_ETIKET = {"ücretsiz": "Ücretsiz", "uygun": "₺ Uygun", "orta": "₺₺ Orta", "yüksek": "₺₺₺ Yüksek"}

ETKINLIK_TIP = {
    "tiyatro": {"ad": "Çocuk Tiyatrosu", "ikon": "🎭"},
    "konser": {"ad": "Konser", "ikon": "🎵"},
    "muzikal": {"ad": "Müzikal", "ikon": "🎼"},
    "atolye": {"ad": "Atölye", "ikon": "🎨"},
    "festival": {"ad": "Festival", "ikon": "🎉"},
    "gosteri": {"ad": "Gösteri", "ikon": "🎪"},
    "sinema": {"ad": "Çocuk Sineması", "ikon": "🎬"},
    "bilim": {"ad": "Bilim Etkinliği", "ikon": "🔬"},
}

AYLAR_TR = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
            "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]


def yukle(ad: str):
    with open(DATA / ad, encoding="utf-8") as f:
        return json.load(f)


def puanla(m: dict) -> dict:
    """Ankarada Çocuk Puanı (10 üzerinden) ve yaş rozetleri."""
    alanlar = ["score_bebek", "score_okul_oncesi", "score_ilkokul", "score_ergen"]
    araliklar = [(0, 3), (3, 6), (6, 11), (11, 16)]
    amin, amax = m.get("age_min") or 0, m.get("age_max") or 99
    var = lambda a: m.get(a) is not None  # 0 geçerli bir puan ("uygun değil")
    uygun = [m[a] for a, (lo, hi) in zip(alanlar, araliklar) if var(a) and hi > amin and lo < amax]
    hepsi = [m[a] for a in alanlar if var(a)]
    yas_ort = statistics.mean(uygun or hepsi or [3])
    puan = lambda a: m[a] if var(a) else 3
    genel = (0.5 * yas_ort + 0.2 * puan("score_erisilebilirlik")
             + 0.15 * puan("score_guvenlik") + 0.15 * puan("score_fiyat_performans")) * 2
    m["puan"] = round(genel, 1)
    m["puan_yildiz"] = round(genel / 2)
    m["en_iyi_yas"] = max(YAS_GRUPLARI, key=lambda y: m.get(y["alan"]) or 0)["kisa"]
    m["yas_puanlari"] = [{"kisa": y["kisa"], "ad": y["ad"], "puan": m.get(y["alan"]) or 0, "slug": y["slug"]}
                         for y in YAS_GRUPLARI]
    return m


def hazirla(mekanlar: list[dict]) -> list[dict]:
    goruldu = set()
    sonuc = []
    for m in mekanlar:
        if m.get("category") not in KATEGORILER:
            raise SystemExit(f"Bilinmeyen kategori: {m.get('category')} ({m.get('name')})")
        slug = slugify(m["name"])
        if slug in goruldu:
            slug = f"{slug}-{slugify(m.get('district') or 'ankara')}"
        goruldu.add(slug)
        m["slug"] = slug
        m["url"] = f"/mekan/{slug}/"
        m["kategori"] = KATEGORILER[m["category"]]
        m["ilce_slug"] = slugify(m.get("district") or "ankara")
        m["fiyat_etiket"] = FIYAT_ETIKET.get(m.get("price") or "", "")
        def _liste(v, boluml=False):
            if isinstance(v, list):
                return [x for x in v if x]
            if not v:
                return []
            if boluml and isinstance(v, str):
                return [p.strip() for p in re.split(r"(?<=[.!?])\s+", v) if p.strip()]
            return [v]
        m["features"] = _liste(m.get("features"))
        m["tips"] = _liste(m.get("tips"), boluml=True)
        m["sources"] = _liste(m.get("sources"))
        m["status"] = m.get("status") or "belirsiz"
        m["maps_url"] = ("https://www.google.com/maps/search/?api=1&query="
                         + (f"{m['lat']},{m['lng']}" if m.get("lat") and m.get("lng")
                            else re.sub(r"\s+", "+", m.get("google_maps_query") or m["name"] + " Ankara")))
        puanla(m)
        sonuc.append(m)
    sonuc.sort(key=lambda x: (-x["puan"], x["name"]))
    return sonuc


def schema_mekan(m: dict, site: dict) -> dict:
    s = {
        "@context": "https://schema.org",
        "@type": sorted({m["kategori"]["schema"], "TouristAttraction"}),
        "name": m["name"],
        "touristType": ["Aileler", "Çocuklu aileler"],
        "dateModified": site["guncelleme"],
        "url": site["url"] + m["url"],
        "description": m.get("description") or "",
        "address": {"@type": "PostalAddress", "addressLocality": m.get("district") or "Ankara",
                    "addressRegion": "Ankara", "addressCountry": "TR",
                    **({"streetAddress": m["address"]} if m.get("address") else {})},
        "isAccessibleForFree": m.get("price") == "ücretsiz",
        "publicAccess": True,
    }
    if m.get("lat") and m.get("lng"):
        s["geo"] = {"@type": "GeoCoordinates", "latitude": m["lat"], "longitude": m["lng"]}
        s["hasMap"] = m["maps_url"]
    if m.get("website"):
        s["sameAs"] = m["website"]
    if m.get("phone"):
        s["telephone"] = m["phone"]
    if m.get("hours"):
        s["openingHours"] = m["hours"]
    if m.get("features"):
        s["amenityFeature"] = [{"@type": "LocationFeatureSpecification", "name": f, "value": True}
                               for f in m["features"]]
    s["audience"] = {"@type": "PeopleAudience", "suggestedMinAge": m.get("age_min") or 0,
                     "suggestedMaxAge": m.get("age_max") or 16, "audienceType": "Aileler ve çocuklar"}
    return s


def kirintilar(site, *parcalar):
    liste = [{"@type": "ListItem", "position": 1, "name": "Ana Sayfa", "item": site["url"] + "/"}]
    for i, (ad, url) in enumerate(parcalar, start=2):
        liste.append({"@type": "ListItem", "position": i, "name": ad, "item": site["url"] + url})
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": liste}


def liste_schema(site, ad, url, mekanlar):
    return {"@context": "https://schema.org", "@type": "ItemList", "name": ad, "url": site["url"] + url,
            "numberOfItems": len(mekanlar),
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": m["name"],
                                 "url": site["url"] + m["url"]} for i, m in enumerate(mekanlar)]}


def sss_schema(sorular):
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": s["soru"],
                            "acceptedAnswer": {"@type": "Answer", "text": s["cevap"]}} for s in sorular]}


def mekan_sss(m):
    """Mekan verisinden SSS uretir (FAQPage + GEO icin, hepsi gercek veriye dayali)."""
    yas_txt = f"{m.get('age_min') or 0}-{m['age_max'] if m.get('age_max') and m['age_max'] < 99 else '16+'}"
    sss = [{"soru": f"{m['name']} kaç yaş çocuk için uygun?",
            "cevap": f"{m['name']} {yas_txt} yaş aralığındaki çocuklara uygundur; en çok {m['en_iyi_yas']} "
                     f"yaş grubuna hitap eder. Ankarada Çocuk Puanı 10 üzerinden {m['puan']}."}]
    if m.get("aile_fiyat") and (m["aile_fiyat"].get("aile_tl")):
        a = m["aile_fiyat"]["aile_tl"]
        sss.append({"soru": f"{m['name']} 3-4 kişilik aileye kaça gelir?",
                    "cevap": f"Yorumlardan yaklaşık hesap: 2 yetişkin + 1-2 çocuk için ~{a[0]:.0f}–{a[1]:.0f} ₺. "
                             "Güncel fiyat için gitmeden teyit edin."})
    elif m.get("price_note"):
        sss.append({"soru": f"{m['name']} ücretli mi?", "cevap": m["price_note"]})
    elif m.get("fiyat_etiket"):
        sss.append({"soru": f"{m['name']} ücretli mi?",
                    "cevap": f"Bütçe düzeyi: {m['fiyat_etiket']}. Güncel ücret için gitmeden önce teyit edin."})
    sss.append({"soru": f"{m['name']} kapalı alan mı?",
                "cevap": "Kapalı alan; yağmurlu ve soğuk günlerde de uygundur." if m.get("indoor")
                         else "Açık hava mekânı; ziyareti hava durumuna göre planlamak iyi olur."})
    if m.get("transport"):
        sss.append({"soru": f"{m['name']} nasıl gidilir?",
                    "cevap": f"{m.get('district') or 'Ankara'} ilçesinde. {m['transport']}"})
    if m.get("google") and m["google"].get("rating"):
        sss.append({"soru": f"{m['name']} Google puanı kaç?",
                    "cevap": f"Google'da {m['google']['rating']} puan"
                             + (f" ({m['google']['count']} değerlendirme)" if m['google'].get('count') else "")
                             + ". Yorumları Google haritalar sayfasından okuyabilirsiniz."})
    bs = m.get("best_season")
    if bs:
        if bs == "her mevsim":
            nzc = ("Her mevsim ziyaret edilebilir; kapalı alan olduğu için hava koşullarından etkilenmez."
                   if m.get("indoor") else
                   "Her mevsim gidilebilir; açık hava olduğu için en keyifli dönem ilkbahar ve sonbahar, "
                   "yaz öğlenleri sıcak, kış rüzgârlı olabilir.")
        else:
            nzc = f"En uygun dönem: {bs}." + (" Kapalı alan olduğundan yağmur/soğukta da uygundur." if m.get("indoor") else "")
        sss.append({"soru": f"{m['name']} ne zaman gidilir, en iyi mevsim hangisi?", "cevap": nzc})
    er = m.get("score_erisilebilirlik")
    if er is not None:
        if er >= 4:
            erc = (f"Erişim rahat ({er}/5): düz ve geniş alanlar; bebek arabası ile ve büyük ölçüde "
                   "tekerlekli sandalye ile gezilebilir.")
        elif er == 3:
            erc = (f"Erişim orta düzeyde ({er}/5): bebek arabasıyla gezilebilir; kot farkı ve zemin durumu "
                   "için gitmeden önce teyit etmeniz önerilir.")
        else:
            erc = (f"Erişim sınırlı olabilir ({er}/5): bebek arabası veya tekerlekli sandalye ile ziyaret "
                   "öncesi mekândan bilgi almanız iyi olur.")
        sss.append({"soru": f"{m['name']} bebek arabasıyla gezilir mi, erişim nasıl?", "cevap": erc})
    return sss[:7]


def _tarih(x):
    """'YYYY-MM-DD' ya da 'YYYY-MM-DDTHH:MM' -> (date|None, saat|None)."""
    if not x:
        return None, None
    try:
        g = date.fromisoformat(str(x)[:10])
    except ValueError:
        return None, None
    saat = str(x)[11:16] if "T" in str(x) else None
    return g, saat


def etkinlik_hazirla(etkinlikler: list[dict], bugun: date) -> list[dict]:
    sonuc, goruldu = [], set()
    for e in etkinlikler:
        bas, saat = _tarih(e.get("startDate"))
        bit, _ = _tarih(e.get("endDate"))
        son = bit or bas
        # geçmiş tek seferlik etkinlikleri ele (yinelenenler kalır)
        if not e.get("recurring") and son and son < bugun:
            continue
        slug = slugify(e.get("name") or "etkinlik")
        if slug in goruldu:
            slug = f"{slug}-{slugify(e.get('venue_name') or e.get('district') or 'ankara')}"
        goruldu.add(slug)
        e["slug"] = slug
        e["_bas"] = bas
        e["_son"] = son
        e["saat"] = saat
        if bas:
            e["tarih_tr"] = f"{bas.day} {AYLAR_TR[bas.month]} {bas.year}"
            if bit and bit != bas:
                e["tarih_tr"] += f" – {bit.day} {AYLAR_TR[bit.month]}"
        else:
            e["tarih_tr"] = None
        e["tip"] = ETKINLIK_TIP.get(e.get("type") or "", {"ad": "Etkinlik", "ikon": "🎫"})
        e["sources"] = e.get("sources") or []
        sonuc.append(e)
    sonuc.sort(key=lambda e: (e["_bas"] is None, e["_bas"] or date.max))
    return sonuc


def liste_sss(konu, mekanlar):
    """Kategori/ilce/yas liste sayfasi icin veri-turevli SSS (FAQPage + GEO)."""
    top = mekanlar[:3]
    sss = []
    if top:
        sss.append({"soru": f"{konu} arasında en yüksek puanlı hangisi?",
                    "cevap": "En yüksek Ankarada Çocuk Puanına sahip olanlar: "
                             + ", ".join(f"{m['name']} ({m['puan']}/10, {m.get('district') or 'Ankara'})" for m in top) + "."})
    ucretsiz = [m for m in mekanlar if m.get("price") == "ücretsiz"]
    if ucretsiz:
        sss.append({"soru": f"{konu} arasında ücretsiz olan var mı?",
                    "cevap": f"Evet, {len(ucretsiz)} ücretsiz seçenek var: "
                             + ", ".join(m["name"] for m in ucretsiz[:4])
                             + (" ve daha fazlası." if len(ucretsiz) > 4 else ".")})
    kapali = [m for m in mekanlar if m.get("indoor")]
    if kapali:
        sss.append({"soru": f"{konu} arasında yağmurlu güne uygun kapalı mekân var mı?",
                    "cevap": f"{len(kapali)} kapalı alan seçeneği yağmurlu ve soğuk günlerde de uygundur: "
                             + ", ".join(m["name"] for m in kapali[:3]) + "."})
    bebek = sorted([m for m in mekanlar if (m.get("score_bebek") or 0) >= 4], key=lambda m: -(m.get("score_bebek") or 0))
    if bebek:
        sss.append({"soru": f"{konu} arasında 0-3 yaş bebeğe en uygunu hangisi?",
                    "cevap": "Bebekle en rahat gezilenler: " + ", ".join(m["name"] for m in bebek[:3]) + "."})
    return sss[:4]


def schema_etkinlik(e: dict, site: dict) -> dict:
    d = {"@context": "https://schema.org", "@type": "Event", "name": e["name"],
         "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
         "eventStatus": "https://schema.org/EventScheduled",
         "description": e.get("description") or "",
         "url": site["url"] + "/etkinlikler/#" + e["slug"],
         "location": {"@type": "Place", "name": e.get("venue_name") or "Ankara",
                      "address": {"@type": "PostalAddress",
                                  "addressLocality": e.get("district") or "Ankara",
                                  "addressRegion": "Ankara", "addressCountry": "TR",
                                  **({"streetAddress": e["address"]} if e.get("address") else {})}}}
    _tz = lambda x: (str(x) + "+03:00") if ("T" in str(x) and "+" not in str(x)) else str(x)
    if e.get("startDate"):
        d["startDate"] = _tz(e["startDate"])
    if e.get("endDate"):
        d["endDate"] = _tz(e["endDate"])
    if e.get("offers_url"):
        d["offers"] = {"@type": "Offer", "url": e["offers_url"], "availability": "https://schema.org/InStock"}
    if e.get("organizer"):
        d["organizer"] = {"@type": "Organization", "name": e["organizer"]}
    d["audience"] = {"@type": "PeopleAudience", "audienceType": "Çocuklar ve aileler"}
    return d


def yaz(yol: str, icerik: str):
    hedef = DIST / yol.strip("/")
    if yol.endswith("/") or "." not in hedef.name:
        hedef = hedef / "index.html"
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text(icerik, encoding="utf-8")


def _km(a_lat, a_lng, b_lat, b_lng):
    """Iki koordinat arasi kus ucusu km (haversine)."""
    dlat, dlng = radians(b_lat - a_lat), radians(b_lng - a_lng)
    h = sin(dlat / 2) ** 2 + cos(radians(a_lat)) * cos(radians(b_lat)) * sin(dlng / 2) ** 2
    return 2 * 6371 * asin(sqrt(h))


def rehber_filtre(r: dict, mekanlar: list[dict]) -> list[dict]:
    k = r.get("kural", {})
    secilen = []
    for m in mekanlar:
        if m["status"] == "kapalı":
            continue
        if k.get("kategori") and m["category"] not in k["kategori"]:
            continue
        if k.get("indoor") is not None and bool(m.get("indoor")) != k["indoor"]:
            continue
        if k.get("fiyat") and m.get("price") not in k["fiyat"]:
            continue
        if k.get("min_puan_alan") and (m.get(k["min_puan_alan"]) or 0) < k.get("min_puan", 4):
            continue
        if k.get("ozellik") and not any(o.lower() in " ".join(m["features"]).lower() for o in k["ozellik"]):
            continue
        if k.get("mevsim") and m.get("best_season") not in k["mevsim"]:
            continue
        if k.get("dogum_gunu") and not m.get("dogum_gunu"):
            continue
        if k.get("ilce") and m.get("district") not in k["ilce"]:
            continue
        if k.get("metin"):
            havuz = " ".join(str(m.get(x) or "") for x in ("name", "address", "district", "subcategory")).lower()
            havuz += " " + " ".join(m.get("features") or []).lower()
            if not any(t.lower() in havuz for t in k["metin"]):
                continue
        if k.get("max_km") and (m.get("distance_km") or 0) > k["max_km"]:
            continue
        secilen.append(m)
    if r.get("ekle"):
        adlar = {m["name"] for m in secilen}
        secilen += [m for m in mekanlar if m["name"] in r["ekle"] and m["name"] not in adlar]
    secilen.sort(key=lambda m: -(m.get(k.get("sirala_alan") or "puan") or 0))
    return secilen[: r.get("limit", 15)]


def main():
    site = yukle("site.json")
    bugun = date.today()
    site["guncelleme"] = date.today().isoformat()
    site["derleme_zamani"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    site["guncelleme_tr"] = date.today().strftime("%d.%m.%Y")
    mekanlar = hazirla(yukle("mekanlar.json"))
    try:
        _foto = yukle("foto.json")
    except FileNotFoundError:
        _foto = {}
    for _m in mekanlar:
        _m["foto"] = _foto.get(_m["name"]) or None
    try:
        _kapak = yukle("kapak.json")
    except FileNotFoundError:
        _kapak = {}
    for _m in mekanlar:
        _m["kapak"] = _kapak.get(_m["name"])
    try:
        _google = yukle("google.json")
    except FileNotFoundError:
        _google = {}
    for _m in mekanlar:
        _m["google"] = _google.get(_m["name"])
    rehberler = yukle("rehberler.json")
    try:
        etkinlikler = etkinlik_hazirla(yukle("etkinlikler.json"), date.today())
    except FileNotFoundError:
        etkinlikler = []

    ilceler = {}
    for m in mekanlar:
        ilceler.setdefault(m["ilce_slug"], {"ad": m.get("district") or "Ankara", "slug": m["ilce_slug"], "mekanlar": []})
        ilceler[m["ilce_slug"]]["mekanlar"].append(m)
    ilce_listesi = sorted(ilceler.values(), key=lambda i: -len(i["mekanlar"]))

    kategoriler = []
    for slug, k in KATEGORILER.items():
        uyeler = [m for m in mekanlar if m["category"] == slug]
        if uyeler:
            kategoriler.append({"slug": slug, **k, "mekanlar": uyeler})

    for r in rehberler:
        r["mekanlar"] = rehber_filtre(r, mekanlar)
        r["url"] = f"/rehber/{r['slug']}/"
    for m in mekanlar:
        m["rehberler"] = [r for r in rehberler if m in r["mekanlar"]][:6]

    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html"]),
                      trim_blocks=True, lstrip_blocks=True)
    env.filters["json"] = lambda v: json.dumps(v, ensure_ascii=False)
    env.filters["slug"] = slugify
    _buyuk = {"festival", "muzikal", "konser", "gosteri"}
    one_etkinlik = [e for e in etkinlikler if e.get("type") in _buyuk][:6] or etkinlikler[:6]
    ortak = dict(site=site, kategoriler=kategoriler, ilceler=ilce_listesi, yas_gruplari=YAS_GRUPLARI,
                 rehberler=rehberler, etkinlikler=etkinlikler, toplam=len(mekanlar), one_etkinlik=one_etkinlik,
                 FIYAT_ETIKET=FIYAT_ETIKET)

    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(STATIC, DIST / "static")
    # kök favicon: tarayıcılar ve Google varsayılan olarak /favicon.ico ister
    shutil.copy(STATIC / "favicon.ico", DIST / "favicon.ico")
    shutil.copy(STATIC / "favicon.svg", DIST / "favicon.svg")

    urls = []

    def sayfa(yol, sablon, **ctx):
        urls.append(yol)
        yaz(yol, env.get_template(sablon).render(**ortak, **ctx))

    # Ana sayfa
    one_cikan = [m for m in mekanlar if m["status"] != "kapalı"][:9]
    sayfa("/", "home.html", one_cikan=one_cikan, schema=[
        {"@context": "https://schema.org", "@type": "WebSite", "name": site["ad"], "url": site["url"] + "/",
         "inLanguage": "tr-TR",
         "potentialAction": {"@type": "SearchAction", "target": site["url"] + "/ara/?q={search_term_string}",
                             "query-input": "required name=search_term_string"}},
        {"@context": "https://schema.org", "@type": "Organization", "name": site["ad"], "url": site["url"] + "/",
         "logo": site["url"] + "/static/logo.svg", "email": site["eposta"],
         "areaServed": {"@type": "City", "name": "Ankara"}},
    ])

    # Mekân sayfaları
    for m in mekanlar:
        acik = [b for b in mekanlar if b is not m and b["status"] != "kapalı"]
        gorulen = set()
        yakin = []
        if m.get("lat") and m.get("lng"):
            aday = [(_km(m["lat"], m["lng"], b["lat"], b["lng"]), b)
                    for b in acik if b.get("lat") and b.get("lng")]
            aday = [t for t in sorted(aday, key=lambda t: t[0]) if t[0] <= 15][:5]
            yakin = [(b, round(km, 1)) for km, b in aday]
            gorulen |= {id(b) for b, _ in yakin}
        benzer = [b for b in sorted([b for b in acik if b["category"] == m["category"]],
                                    key=lambda b: -(b.get("puan") or 0)) if id(b) not in gorulen][:5]
        gorulen |= {id(b) for b in benzer}
        ilce_m = m.get("district")
        ayni_ilce = ([b for b in sorted([b for b in acik if b.get("district") == ilce_m],
                                        key=lambda b: -(b.get("puan") or 0)) if id(b) not in gorulen][:6]
                     if ilce_m else [])
        m_sss = mekan_sss(m)
        sayfa(m["url"], "place.html", m=m, benzer=benzer, yakin=yakin, ayni_ilce=ayni_ilce, sss=m_sss, schema=[
            schema_mekan(m, site),
            kirintilar(site, (m["kategori"]["ad"], f"/kategori/{m['category']}/"), (m["name"], m["url"])),
            sss_schema(m_sss),
        ])

    # Kategori
    for k in kategoriler:
        url = f"/kategori/{k['slug']}/"
        _sss = liste_sss(f"Ankara'da çocukla gidilecek {k['ad'].lower()}", k["mekanlar"])
        sayfa(url, "list.html", baslik=f"Ankara'da Çocuklarla {k['ad']}", alt=k["aciklama"], ikon=k["ikon"],
              mekanlar=k["mekanlar"], canonical=url, sss=_sss, meta_desc=f"Ankara'da çocuklu aileler için {k['ad'].lower()}: "
              f"{len(k['mekanlar'])} mekân, yaşa göre puan, ücret, ulaşım ve aile ipuçları.",
              schema=[liste_schema(site, k["ad"], url, k["mekanlar"]), sss_schema(_sss), kirintilar(site, (k["ad"], url))])

    # İlçe
    for i in ilce_listesi:
        url = f"/ilce/{i['slug']}/"
        _sss = liste_sss(f"{i['ad']} çocuk mekânları", i["mekanlar"])
        sayfa(url, "list.html", baslik=f"{i['ad']}'de Çocuklarla Gidilecek Yerler", alt=f"{i['ad']} ilçesinde çocuklu aileler için seçilmiş mekânlar.",
              ikon="📍", mekanlar=i["mekanlar"], canonical=url, sss=_sss,
              meta_desc=f"Ankara {i['ad']} çocukla gidilecek yerler: parklar, kafeler, müzeler ve oyun alanları — yaşa göre puanlanmış {len(i['mekanlar'])} öneri.",
              schema=[liste_schema(site, i["ad"], url, i["mekanlar"]), sss_schema(_sss), kirintilar(site, (i["ad"], url))])

    # İlçe × kategori (yalnız ≥4 mekân olanlar)
    for i in ilce_listesi:
        for k in kategoriler:
            uyeler = [m for m in i["mekanlar"] if m["category"] == k["slug"]]
            if len(uyeler) < 4:
                continue
            url = f"/ilce/{i['slug']}/{k['slug']}/"
            sayfa(url, "list.html", baslik=f"{i['ad']} {k['ad']}", alt=f"{i['ad']} ilçesinde {k['aciklama'].lower()}",
                  ikon=k["ikon"], mekanlar=uyeler, canonical=url,
                  meta_desc=f"Ankara {i['ad']} çocuklarla {k['ad'].lower()}: {len(uyeler)} mekân, yaşa göre puan, ücret ve aile ipuçları.",
                  schema=[liste_schema(site, f"{i['ad']} {k['ad']}", url, uyeler),
                          kirintilar(site, (i["ad"], f"/ilce/{i['slug']}/"), (k["ad"], url))])

    # Yaş grubu
    for y in YAS_GRUPLARI:
        url = f"/yas/{y['slug']}/"
        uyeler = sorted([m for m in mekanlar if (m.get(y["alan"]) or 0) >= 4 and m["status"] != "kapalı"],
                        key=lambda m: (-(m.get(y["alan"]) or 0), -m["puan"]))
        _sss = liste_sss(f"Ankara'da {y['ad']} çocuklar için mekânlar", uyeler)
        sayfa(url, "list.html", baslik=f"Ankara'da {y['ad']} Çocuklar İçin En İyi Mekânlar", alt=y["aciklama"], ikon=y["ikon"],
              mekanlar=uyeler, canonical=url, yas_alan=y["alan"], sss=_sss,
              meta_desc=f"Ankara'da {y['ad']} çocuklarla gidilecek en iyi {len(uyeler)} mekân: park, kafe, müze ve oyun alanı önerileri, puan ve ipuçlarıyla.",
              schema=[liste_schema(site, y["ad"], url, uyeler), sss_schema(_sss), kirintilar(site, (y["ad"], url))])

    # Rehberler
    for r in rehberler:
        sayfa(r["url"], "guide.html", r=r, canonical=r["url"],
              schema=[liste_schema(site, r["baslik"], r["url"], r["mekanlar"]), sss_schema(r.get("sss", [])),
                      kirintilar(site, (r["baslik"], r["url"]))])

    # Rehberler indeks (sadeleştirme: hepsi tek temiz sayfada)
    sayfa("/rehberler/", "rehberler_index.html", canonical="/rehberler/",
          meta_desc="Ankara'da çocukla gidilecek yerler için tüm rehberler: yaşa, mevsime, ilçeye ve temaya göre "
          "seçilmiş listeler — doğum günü, erişilebilir mekânlar, tiyatro, ücretsiz aktiviteler ve daha fazlası.",
          schema=[kirintilar(site, ("Rehberler", "/rehberler/"))])

    # Bu hafta sonu (dinamik: yaklaşan hafta sonuna denk gelen etkinlikler + öneri mekânlar)
    wd = bugun.weekday()
    cmt = bugun - timedelta(days=wd - 5) if wd >= 5 else bugun + timedelta(days=5 - wd)
    pzr = cmt + timedelta(days=1)
    hs_etkinlik = [e for e in etkinlikler
                   if e.get("recurring") or (e["_bas"] and e["_bas"] <= pzr and (e["_son"] or e["_bas"]) >= cmt)]
    hs_acik = sorted([m for m in mekanlar if not m.get("indoor") and m["status"] != "kapalı"],
                     key=lambda m: -(m.get("puan") or 0))[:6]
    hs_kapali = sorted([m for m in mekanlar if m.get("indoor") and m["status"] != "kapalı"],
                       key=lambda m: -(m.get("puan") or 0))[:6]
    hs_baslik = f"Bu Hafta Sonu Ankara'da Çocukla ({cmt.day} {AYLAR_TR[cmt.month]} – {pzr.day} {AYLAR_TR[pzr.month]})"
    sayfa("/bu-hafta-sonu/", "weekend.html", canonical="/bu-hafta-sonu/", hs_baslik=hs_baslik,
          hs_etkinlik=hs_etkinlik, hs_acik=hs_acik, hs_kapali=hs_kapali, cmt=cmt, pzr=pzr,
          meta_desc="Bu hafta sonu Ankara'da çocukla nereye gidilir? Hafta sonuna denk gelen çocuk etkinlikleri "
          "ve hava durumuna göre açık/kapalı mekân önerileri — güncel liste.",
          schema=[kirintilar(site, ("Bu hafta sonu", "/bu-hafta-sonu/"))])

    # Diğer sayfalar
    sayfa("/harita/", "map.html", mekanlar=[m for m in mekanlar if m.get("lat") and m.get("lng")])
    sayfa("/ara/", "search.html")
    sayfa("/tum-mekanlar/", "list.html", baslik="Ankara'daki Tüm Çocuk Dostu Mekânlar", alt="Puan sırasına göre tüm liste. Filtreleyerek daraltabilirsiniz.",
          ikon="🗂️", mekanlar=mekanlar, canonical="/tum-mekanlar/",
          meta_desc=f"Ankara'da çocuklarla gidilecek {len(mekanlar)} mekânın tam listesi: yaş, ücret, kapalı/açık ve ilçe filtreleriyle.",
          schema=[liste_schema(site, "Tüm mekânlar", "/tum-mekanlar/", mekanlar)])
    # Etkinlikler (yaklaşan çocuk & aile etkinlikleri)
    et_schema = [schema_etkinlik(e, site) for e in etkinlikler]
    et_schema.append(kirintilar(site, ("Etkinlikler", "/etkinlikler/")))
    sayfa("/etkinlikler/", "events.html", canonical="/etkinlikler/",
          meta_desc="Ankara'da çocuklar ve aileler için yaklaşan tiyatro, konser, atölye, festival ve "
          "bilim etkinlikleri — tarih, mekân, yaş ve bilet bilgisiyle güncel takvim.",
          schema=et_schema)

    for p in yukle("sayfalar.json"):
        sayfa(p["url"], "page.html", p=p, canonical=p["url"])
    yaz("/404.html", env.get_template("404.html").render(**ortak))

    # Veri dosyası (arama/harita/sihirbaz için)
    hafif = [{k: m.get(k) for k in ("name", "slug", "url", "category", "district", "ilce_slug", "lat", "lng",
                                    "indoor", "price", "puan", "age_min", "age_max", "features", "best_season",
                                    "status", "score_bebek", "score_okul_oncesi", "score_ilkokul", "score_ergen",
                                    "description", "subcategory", "aile_fiyat", "foto", "kapak", "phone", "maps_url", "google")}
             | {"ikon": m["kategori"]["ikon"], "renk": m["kategori"]["renk"], "kat_ad": m["kategori"]["kisa"]}
             for m in mekanlar]
    (DIST / "static").mkdir(exist_ok=True)
    (DIST / "static" / "mekanlar.json").write_text(json.dumps(hafif, ensure_ascii=False), encoding="utf-8")

    # sitemap, robots, llms.txt, htaccess
    bugun = site["guncelleme"]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
    mekan_gorsel = {m['url']: (m['foto']['lg'] if m.get('foto') else m.get('kapak')) for m in mekanlar if m.get('foto') or m.get('kapak')}
    for u in urls:
        if u == "/":
            oncelik, cf = "1.0", "daily"
        elif u == "/etkinlikler/":
            oncelik, cf = "0.9", "weekly"
        elif u.startswith("/mekan/") or u.startswith("/rehber/"):
            oncelik, cf = "0.8", "monthly"
        else:
            oncelik, cf = "0.6", "monthly"
        img = ""
        if u in mekan_gorsel:
            img = f"<image:image><image:loc>{site['url']}/static/img/mekan/{mekan_gorsel[u]}</image:loc></image:image>"
        sm.append(f"  <url><loc>{site['url']}{u}</loc><lastmod>{bugun}</lastmod><changefreq>{cf}</changefreq><priority>{oncelik}</priority>{img}</url>")
    sm.append("</urlset>")
    (DIST / "sitemap.xml").write_text("\n".join(sm), encoding="utf-8")

    (DIST / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\n"
        "# Yapay zekâ tarayıcıları (GEO): içeriğin alıntılanmasına izin veriyoruz\n"
        "User-agent: GPTBot\nAllow: /\nUser-agent: OAI-SearchBot\nAllow: /\nUser-agent: ClaudeBot\nAllow: /\n"
        "User-agent: Claude-SearchBot\nAllow: /\nUser-agent: PerplexityBot\nAllow: /\nUser-agent: Google-Extended\nAllow: /\n"
        "User-agent: Applebot-Extended\nAllow: /\nUser-agent: CCBot\nAllow: /\n\n"
        f"Sitemap: {site['url']}/sitemap.xml\n", encoding="utf-8")

    llms = [f"# {site['ad']}", "", f"> {site['slogan']} {site['url']} — Ankara'da çocuklu aileler için "
            f"{len(mekanlar)} mekânın yaş gruplarına göre puanlandığı, düzenli güncellenen bağımsız rehber. "
            f"Son güncelleme: {bugun}.", "",
            "## Puanlama", "Her mekân 0-3, 3-6, 6-11 ve 11-16 yaş grupları için 1-5 arasında; erişilebilirlik, güvenlik ve "
            "fiyat/performans için ayrıca puanlanır. Ankarada Çocuk Puanı 10 üzerindendir. Yöntem: "
            f"{site['url']}/puanlama-yontemi/", "", "## Rehberler"]
    llms += [f"- [{r['baslik']}]({site['url']}{r['url']}): {r['ozet']}" for r in rehberler]
    llms += ["", "## Kategoriler"]
    llms += [f"- [{k['ad']}]({site['url']}/kategori/{k['slug']}/): {len(k['mekanlar'])} mekân" for k in kategoriler]
    llms += ["", "## Mekânlar"]
    for m in mekanlar:
        g = f", Google {m['google']['rating']}" if m.get("google") and m["google"].get("rating") else ""
        llms.append(f"- [{m['name']}]({site['url']}{m['url']}): {m['kategori']['kisa']}, {m.get('district') or 'Ankara'}, "
                    f"puan {m['puan']}/10{g}, {m['fiyat_etiket'] or 'ücret bilgisi yok'}, "
                    f"{'kapalı alan' if m.get('indoor') else 'açık hava'}, en uygun yaş {m['en_iyi_yas']}. "
                    f"{m.get('description') or ''}")
    if etkinlikler:
        llms += ["", "## Yaklaşan Etkinlikler"]
        llms += [f"- {e['name']} ({e['tip']['ad']}): {e.get('venue_name') or 'Ankara'}"
                 + (f", {e['tarih_tr']}" if e.get("tarih_tr") else "")
                 + (f", {e['recurring']}" if e.get("recurring") else "")
                 + (f". {e.get('description') or ''}") for e in etkinlikler]
    (DIST / "llms.txt").write_text("\n".join(llms), encoding="utf-8")

    (DIST / "OneSignalSDKWorker.js").write_text(
        'importScripts("https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js");', encoding="utf-8")
    shutil.copy(KOK / "build" / "htaccess.txt", DIST / ".htaccess")
    print(f"✓ {len(urls)} sayfa, {len(mekanlar)} mekân, {len(ilce_listesi)} ilçe, {len(rehberler)} rehber -> {DIST}")


if __name__ == "__main__":
    main()
