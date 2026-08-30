# ankaradacocuk.com

Ankara'da çocuklu aileler için yaşa göre puanlanmış, kaynaklı mekân rehberi. Tamamen statik site
(HTML/CSS/JS), Python + Jinja2 ile üretilir, cPanel'e FTP ile yüklenir.

## Yapı

```
data/raw/*.json      araştırma çıktıları (park, muze, oyun, yemek, gezi) — kaynak veri
data/koordinat.json  OSM Nominatim geokod önbelleği (build/geokod.py üretir)
data/mekanlar.json   birleştirilmiş veri (build/birlestir.py üretir; elle düzenleme!)
data/rehberler.json  küratörlü listeler (kural tabanlı: yağmurlu gün, ücretsiz, bebekle...)
data/sayfalar.json   sabit sayfalar (hakkında, puanlama yöntemi, öneri formu, gizlilik)
data/site.json       site adı, URL, e-posta
templates/           Jinja2 şablonları
static/              CSS, JS, logo, ikonlar, OG görseli
build/derle.py       siteyi dist/ klasörüne yazar (sitemap, robots, llms.txt, .htaccess dahil)
deploy/yukle.py      dist/ -> FTP(S)
```

## Komutlar

```bash
pip install jinja2 pillow
python build/birlestir.py   # raw -> mekanlar.json (kopya birleştirme, kategori düzeltme)
python build/geokod.py      # koordinatı olmayanları OSM'den bul (1 istek/sn, önbellekli)
python build/birlestir.py   # koordinatları uygula
python build/ikon.py        # PNG ikon + og.png (yalnız logo değişince)
python build/derle.py       # dist/ üret
python deploy/yukle.py --prova   # ne yükleneceğini göster
python deploy/yukle.py           # FTP ile yükle (deploy/.ftp.env gerekir)
```

## Mekân ekleme / düzeltme

`data/raw/<kategori>.json` içine aynı şemayla kayıt ekleyin (bkz. mevcut kayıtlar). Zorunlu:
`name, category, district, description, score_*` (7 puan, 0-5). Bilinmeyen alan `null` — uydurma
değer girilmez; `status` "açık|kapalı|belirsiz". Sonra `birlestir` + `derle`.

Puan formülü ve kategori listesi `build/derle.py` başındadır; site üzerinde `/puanlama-yontemi/`.

## Dağıtım

`deploy/.ftp.env.example` → `deploy/.ftp.env` (git dışı). Addon domain kökü cPanel > Domains
ekranındaki "Document Root" değeridir. `.htaccess` HTTPS + www→kök yönlendirmesi, önbellek ve
sıkıştırma başlıklarını içerir; LiteSpeed/Apache ile uyumludur.

## Yayın sonrası yapılacaklar

1. Google Search Console'a `https://ankaradacocuk.com` ekle, `sitemap.xml` gönder.
2. Bing Webmaster Tools'a ekle (Search Console'dan içe aktarma ile).
3. `merhaba@ankaradacocuk.com` posta kutusunu cPanel'de oluştur (öneri formu buraya gider).
4. Google Business Profile yerine: site "Organization" schema'sında `sameAs` için Instagram hesabı açılırsa `templates/base.html`'e ekle.
5. Fiyat/saat alanları 90 günde bir yeniden doğrulanmalı; `site.guncelleme` otomatik bugünün tarihi.
