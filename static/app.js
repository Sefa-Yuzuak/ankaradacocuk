/* ankaradacocuk.com — filtre, sihirbaz/arama, harita, paylaş */
(function () {
  'use strict';
  const YAS = { b: 'score_bebek', o: 'score_okul_oncesi', i: 'score_ilkokul', e: 'score_ergen' };
  const YAS_DATA = { b: 'b', o: 'o', i: 'i', e: 'e' };

  // Mobil menü
  const ham = document.querySelector('.hamburger');
  const mob = document.getElementById('mobilmenu');
  if (ham && mob) ham.addEventListener('click', () => {
    mob.hidden = !mob.hidden; ham.setAttribute('aria-expanded', String(!mob.hidden));
  });

  // Paylaş
  document.querySelectorAll('[data-paylas]').forEach(b => b.addEventListener('click', async () => {
    const veri = { title: b.dataset.baslik, url: location.href };
    if (navigator.share) { try { await navigator.share(veri); } catch (e) { /* iptal */ } }
    else { await navigator.clipboard.writeText(location.href); b.textContent = '✅ Bağlantı kopyalandı'; }
  }));

  // Öne çıkan etkinlik slider'ı
  const slider = document.querySelector('[data-slider]');
  if (slider) {
    const yol = slider.querySelector('[data-track]');
    const slaytlar = Array.from(yol.children);
    const noktalar = slider.querySelector('[data-dots]');
    const azalt = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let i = 0, sayac;
    const git = (x) => {
      i = (x + slaytlar.length) % slaytlar.length;
      yol.style.transform = 'translateX(-' + (i * 100) + '%)';
      if (noktalar) Array.from(noktalar.children).forEach((d, x2) => d.setAttribute('aria-current', x2 === i ? 'true' : 'false'));
      sifirla();
    };
    const sifirla = () => { if (azalt || slaytlar.length < 2) return; clearInterval(sayac); sayac = setInterval(() => git(i + 1), 5500); };
    if (slaytlar.length > 1) {
      slaytlar.forEach((_, x) => {
        const b = document.createElement('button'); b.type = 'button';
        b.setAttribute('aria-label', (x + 1) + '. etkinlik');
        b.addEventListener('click', () => git(x));
        noktalar.appendChild(b);
      });
      slider.querySelector('[data-next]').addEventListener('click', () => git(i + 1));
      slider.querySelector('[data-prev]').addEventListener('click', () => git(i - 1));
      slider.addEventListener('mouseenter', () => clearInterval(sayac));
      slider.addEventListener('mouseleave', sifirla);
      let sx = 0;
      yol.addEventListener('touchstart', e => sx = e.touches[0].clientX, { passive: true });
      yol.addEventListener('touchend', e => { const dx = e.changedTouches[0].clientX - sx; if (Math.abs(dx) > 40) git(i + (dx < 0 ? 1 : -1)); });
      git(0);
    } else {
      slider.querySelectorAll('[data-prev],[data-next]').forEach(b => b.hidden = true);
    }
  }

  // Liste sayfası: DOM kartlarını filtrele
  const filtre = document.getElementById('filtre');
  const liste = document.getElementById('liste');
  if (filtre && liste) {
    const kartlar = Array.from(liste.querySelectorAll('.kart'));
    const bos = document.getElementById('bos');
    const uygula = () => {
      const f = Object.fromEntries(new FormData(filtre));
      let n = 0;
      kartlar.forEach(k => {
        let ok = true;
        if (f.yas && Number(k.dataset[YAS_DATA[f.yas]]) < 4) ok = false;
        if (f.ortam !== '' && f.ortam !== undefined && k.dataset.indoor !== f.ortam) ok = false;
        if (f.fiyat && k.dataset.fiyat !== f.fiyat) ok = false;
        if (f.ilce && k.dataset.ilce !== f.ilce) ok = false;
        if (f.kat && k.dataset.kat !== f.kat) ok = false;
        k.hidden = !ok; if (ok) n++;
      });
      const sira = f.sira || 'puan';
      const gorunen = kartlar.filter(k => !k.hidden);
      gorunen.sort((a, b) => sira === 'ad' ? a.dataset.ad.localeCompare(b.dataset.ad, 'tr')
        : (f.yas ? Number(b.dataset[YAS_DATA[f.yas]]) - Number(a.dataset[YAS_DATA[f.yas]]) : 0) || Number(b.dataset.puan) - Number(a.dataset.puan));
      gorunen.forEach(k => liste.appendChild(k));
      filtre.elements.sayi.value = n + ' mekân';
      bos.hidden = n > 0;
    };
    filtre.addEventListener('change', uygula);
    filtre.addEventListener('reset', () => setTimeout(uygula, 0));
    // URL'den ön ayar (?yas=b&ortam=1)
    const p = new URLSearchParams(location.search);
    for (const [k, v] of p) if (filtre.elements[k]) filtre.elements[k].value = v;
    uygula();
  }

  // Arama / sihirbaz sayfası: JSON'dan kart üret
  const araForm = document.getElementById('ara-form');
  if (araForm) {
    const hedef = document.getElementById('sonuclar');
    const bos = document.getElementById('bos');
    const p = new URLSearchParams(location.search);
    for (const [k, v] of p) if (araForm.elements[k]) araForm.elements[k].value = v;
    let veri = [];
    const norm = s => (s || '').toLocaleLowerCase('tr').replace(/i̇/g, 'i');
    const kart = m => `
      <article class="kart${m.status === 'kapalı' ? ' kapali' : ''}">
        <a class="kart-kapak${m.foto || m.kapak ? ' foto' : ''}" href="${m.url}" style="--kr:${m.renk}" aria-hidden="true" tabindex="-1">${m.foto ? `<img class="kapak-img" src="/static/img/mekan/${m.foto.sm}" alt="${m.name}" loading="lazy">` : (m.kapak ? `<img class="kapak-img" src="/static/img/mekan/${m.kapak}" alt="${m.name}" loading="lazy">` : `<span class="kapak-ikon">${m.ikon}</span>`)}<span class="puan-rozet">${m.puan}</span>${m.status === 'kapalı' ? '<span class="etiket-kapali">Kapalı</span>' : ''}</a>
        <div class="kart-govde"><div class="kart-meta"><span class="kat" style="--kr:${m.renk}">${m.kat_ad}</span> · ${m.district || 'Ankara'}</div>
        <h3><a href="${m.url}">${m.name}</a></h3><p class="kart-aciklama">${(m.description || '').slice(0, 120)}…</p>
        <div class="kart-alt"><span class="rozet">${m.indoor ? '🏠 Kapalı alan' : '☀️ Açık hava'}</span>${m.price ? `<span class="rozet">${{ 'ücretsiz': 'Ücretsiz', 'uygun': '₺ Uygun', 'orta': '₺₺ Orta', 'yüksek': '₺₺₺ Yüksek' }[m.price] || ''}</span>` : ''}</div><div class="kart-eylem"><a class="kart-btn birincil" href="${m.maps_url}" target="_blank" rel="noopener">📍 Yol tarifi</a>${m.phone ? `<a class="kart-btn" href="tel:${m.phone.replace(/\s/g,'')}">📞 Ara</a>` : ''}</div></div>
      </article>`;
    const calistir = () => {
      const f = Object.fromEntries(new FormData(araForm));
      const q = norm(f.q).trim();
      let s = veri.filter(m => {
        if (f.yas && (m[YAS[f.yas]] || 0) < 4) return false;
        if (f.ortam !== '' && f.ortam !== undefined && String(m.indoor ? 1 : 0) !== f.ortam) return false;
        if (f.fiyat && m.price !== f.fiyat) return false;
        if (f.ilce && m.ilce_slug !== f.ilce) return false;
        if (f.kat && m.category !== f.kat) return false;
        if (q) {
          const metin = norm([m.name, m.district, m.subcategory, m.kat_ad, (m.features || []).join(' '), m.description].join(' '));
          if (!q.split(/\s+/).every(t => metin.includes(t))) return false;
        }
        return true;
      });
      if (f.yas) s.sort((a, b) => (b[YAS[f.yas]] - a[YAS[f.yas]]) || (b.puan - a.puan));
      hedef.innerHTML = s.map(kart).join('');
      araForm.elements.sayi.value = s.length + ' mekân';
      bos.hidden = s.length > 0;
    };
    fetch('/static/mekanlar.json').then(r => r.json()).then(d => { veri = d; calistir(); });
    araForm.addEventListener('input', calistir);
    araForm.addEventListener('change', calistir);
    araForm.addEventListener('submit', e => e.preventDefault());
  }

  // Harita (Leaflet CDN'den geliyor; defer sırasıyla önce yüklenir)
  const ikon = (m) => L.divIcon({ className: '', html: `<div class="pin" style="--kr:${m.renk || '#ff7a59'}"><span>${m.ikon || '📍'}</span></div>`, iconSize: [34, 34], iconAnchor: [17, 34], popupAnchor: [0, -30] });
  const osm = (map) => L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' }).addTo(map);

  const tekil = document.getElementById('harita');
  if (tekil && window.L) {
    const lat = +tekil.dataset.lat, lng = +tekil.dataset.lng;
    const map = L.map(tekil, { scrollWheelZoom: false }).setView([lat, lng], 14);
    osm(map);
    L.marker([lat, lng]).addTo(map).bindPopup(`<b>${tekil.dataset.ad}</b>`).openPopup();
  }

  const buyuk = document.getElementById('buyuk-harita');
  if (buyuk && window.L) {
    const map = L.map(buyuk).setView([39.92, 32.85], 11);
    osm(map);
    const grup = L.layerGroup().addTo(map);
    const form = document.getElementById('harita-filtre');
    let veri = [];
    const ciz = () => {
      grup.clearLayers();
      const f = Object.fromEntries(new FormData(form));
      veri.filter(m => m.lat && m.lng && m.status !== 'kapalı')
        .filter(m => (!f.kat || m.category === f.kat) && (!f.yas || (m[YAS[f.yas]] || 0) >= 4) && (f.ortam === '' || f.ortam === undefined || String(m.indoor ? 1 : 0) === f.ortam))
        .forEach(m => L.marker([m.lat, m.lng], { icon: ikon(m) }).addTo(grup)
          .bindPopup(`<b>${m.name}</b>${m.kat_ad} · ${m.district || ''} · <b style="display:inline">${m.puan}/10</b><br><a href="${m.url}">Detay →</a> · <a target="_blank" rel="noopener" href="https://www.google.com/maps/dir/?api=1&destination=${m.lat},${m.lng}">Yol tarifi</a>`));
    };
    fetch('/static/mekanlar.json').then(r => r.json()).then(d => { veri = d; ciz(); });
    form.addEventListener('change', ciz);
    document.getElementById('konum').addEventListener('click', () => {
      navigator.geolocation?.getCurrentPosition(p => {
        map.setView([p.coords.latitude, p.coords.longitude], 13);
        L.circleMarker([p.coords.latitude, p.coords.longitude], { radius: 8, color: '#2f7de1' }).addTo(map).bindPopup('Buradasınız').openPopup();
      }, () => alert('Konum alınamadı. Tarayıcı izni gerekiyor.'));
    });
  }

  // E-bülten aboneliği
  const bultenForm = document.getElementById('bulten-form');
  if (bultenForm) {
    const sonuc = document.getElementById('bulten-sonuc');
    const goster = (msg, ok) => { sonuc.textContent = msg; sonuc.hidden = false; sonuc.className = 'bulten-sonuc' + (ok ? ' ok' : ' hata'); };
    bultenForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = (bultenForm.email.value || '').trim();
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) { goster('Lütfen geçerli bir e-posta gir.', false); return; }
      const endpoint = bultenForm.dataset.endpoint;
      if (endpoint) {
        try {
          const r = await fetch(endpoint, { method: 'POST', headers: { Accept: 'application/json', 'Content-Type': 'application/json' }, body: JSON.stringify({ email: email, kaynak: 'ankaradacocuk e-bulten' }) });
          if (r.ok) { goster('Teşekkürler! Aboneliğin alındı. 🎉', true); bultenForm.reset(); }
          else { goster('Bir sorun oldu, birazdan tekrar dene.', false); }
        } catch (x) { goster('Bağlantı hatası, tekrar dene.', false); }
      } else {
        const adres = bultenForm.dataset.eposta || 'merhaba@ankaradacocuk.com';
        location.href = 'mailto:' + adres + '?subject=' + encodeURIComponent('E-bulten aboneligi') + '&body=' + encodeURIComponent('Beni e-bultene ekleyin: ' + email);
        goster('E-posta uygulaman açılıyor; göndererek aboneliğini tamamla.', true);
      }
    });
  }

  // Çerez onay bildirimi (Google Consent Mode)
  const cbanner = document.getElementById('cerez-banner');
  if (cbanner) {
    let mevcut = null; try { mevcut = localStorage.getItem('cerez_ok'); } catch (e) {}
    if (mevcut === null) cbanner.hidden = false;
    const kapat = (deger) => {
      try { localStorage.setItem('cerez_ok', deger); } catch (e) {}
      cbanner.hidden = true;
      if (deger === '1' && typeof gtag === 'function') gtag('consent', 'update', { analytics_storage: 'granted' });
    };
    const k = document.getElementById('cerez-kabul'); if (k) k.addEventListener('click', () => kapat('1'));
    const r = document.getElementById('cerez-red'); if (r) r.addEventListener('click', () => kapat('0'));
  }

})();

/* Etkinlik filtreleri: gun / yas / tur tek secim, ucretsiz acik-kapali; secim URL'de.
   Tarihsiz ("Surekli") etkinlik gun filtrelerinde her zaman gorunur. */
(function () {
  var form = document.getElementById('etk-filtre');
  if (!form) return;
  var kartlar = Array.prototype.slice.call(document.querySelectorAll('.etkinlik-kart'));
  var sayac = document.getElementById('etk-sayac');
  var secim = {};
  function gun0(d) { return new Date(d.getFullYear(), d.getMonth(), d.getDate()); }
  function aralik(anahtar) {
    var b = gun0(new Date()), s;
    if (anahtar === 'bugun') return [b, b];
    if (anahtar === 'hafta') { s = new Date(b); s.setDate(b.getDate() + 6); return [b, s]; }
    var cmt = new Date(b); cmt.setDate(b.getDate() + ((6 - b.getDay() + 7) % 7));
    var paz = new Date(cmt); paz.setDate(cmt.getDate() + 1);
    return [b.getDay() === 0 ? b : cmt, paz];
  }
  function tarih(s) { var d = s ? new Date(s) : null; return d && !isNaN(d) ? gun0(d) : null; }
  function uyar(k) {
    if (secim.gun) {
      var bas = tarih(k.dataset.bas), bit = tarih(k.dataset.bit) || bas, ar = aralik(secim.gun);
      if (bas && (bit < ar[0] || bas > ar[1])) return false;
    }
    if (secim.yas) {
      var p = secim.yas.split('-'), ymin = +k.dataset.ymin, ymax = +k.dataset.ymax;
      if (ymax < +p[0] || ymin > +p[1]) return false;
    }
    if (secim.tip && k.dataset.tip !== secim.tip) return false;
    if (secim.ucretsiz && k.dataset.ucretsiz !== '1') return false;
    return true;
  }
  function uygula() {
    var n = 0;
    kartlar.forEach(function (k) { var g = uyar(k); k.classList.toggle('gizle', !g); if (g) n++; });
    var acik = Object.keys(secim).filter(function (x) { return secim[x]; });
    if (sayac) sayac.textContent = acik.length ? n + ' etkinlik gösteriliyor' : '';
    form.querySelectorAll('.cip').forEach(function (b) {
      var f = b.dataset.f.split(':');
      b.setAttribute('aria-pressed', (f.length > 1 ? secim[f[0]] === f[1] : !!secim[f[0]]) ? 'true' : 'false');
    });
    var q = acik.map(function (x) { return x + '=' + encodeURIComponent(secim[x] === true ? '1' : secim[x]); }).join('&');
    history.replaceState(null, '', location.pathname + (q ? '?' + q : ''));
  }
  form.addEventListener('click', function (ev) {
    var b = ev.target.closest('.cip'); if (!b) return;
    var f = b.dataset.f.split(':');
    if (f.length > 1) secim[f[0]] = secim[f[0]] === f[1] ? '' : f[1];
    else secim[f[0]] = !secim[f[0]];
    uygula();
  });
  var p = new URLSearchParams(location.search);
  ['gun', 'yas', 'tip'].forEach(function (x) { if (p.get(x)) secim[x] = p.get(x); });
  if (p.get('ucretsiz') === '1') secim.ucretsiz = true;
  if (Object.keys(secim).length) uygula();
})();
