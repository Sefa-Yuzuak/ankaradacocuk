"""dist/ klasörünü FTP(S) ile cPanel'e yükler.

Bilgiler deploy/.ftp.env dosyasından okunur (git'e girmez):
    FTP_HOST=ftp.ankaradacocuk.com   (ya da sunucu adı)
    FTP_USER=cpanelkullanici
    FTP_PASS=...
    FTP_ROOT=/ankaradacocuk.com      (addon domain kökü; ana domain ise /public_html)

Kullanım: python deploy/yukle.py [--prova]
"""
from __future__ import annotations

import ftplib
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
DIST = KOK / "dist"
ENV = KOK / "deploy" / ".ftp.env"


def ayar() -> dict:
    if not ENV.exists():
        sys.exit(f"Ayar dosyası yok: {ENV}\nÖrnek için deploy/.ftp.env.example dosyasına bakın.")
    a = {}
    for satir in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in satir and not satir.startswith("#"):
            k, v = satir.split("=", 1)
            a[k.strip()] = v.strip()
    eksik = [k for k in ("FTP_HOST", "FTP_USER", "FTP_PASS", "FTP_ROOT") if not a.get(k)]
    if eksik:
        sys.exit(f"Eksik ayar: {', '.join(eksik)}")
    return a


def baglan(a: dict) -> ftplib.FTP:
    try:
        ftp = ftplib.FTP_TLS(a["FTP_HOST"], timeout=30)
        ftp.login(a["FTP_USER"], a["FTP_PASS"])
        ftp.prot_p()
        print("FTPS bağlantısı kuruldu")
    except Exception as e:  # TLS desteklenmiyorsa düz FTP
        print(f"FTPS olmadı ({type(e).__name__}); düz FTP deneniyor")
        ftp = ftplib.FTP(a["FTP_HOST"], timeout=30)
        ftp.login(a["FTP_USER"], a["FTP_PASS"])
    ftp.encoding = "utf-8"
    return ftp


def dizin_olustur(ftp: ftplib.FTP, yol: str):
    parcalar = yol.strip("/").split("/")
    guncel = ""
    for p in parcalar:
        guncel += "/" + p
        try:
            ftp.mkd(guncel)
        except ftplib.error_perm:
            pass


def main():
    prova = "--prova" in sys.argv
    a = ayar()
    if not DIST.exists():
        sys.exit("dist/ yok; önce python build/derle.py çalıştırın")
    dosyalar = [p for p in DIST.rglob("*") if p.is_file()]
    print(f"{len(dosyalar)} dosya yüklenecek -> {a['FTP_HOST']}{a['FTP_ROOT']}")
    if prova:
        for p in dosyalar[:15]:
            print("  ", p.relative_to(DIST).as_posix())
        print("   ... (prova, yükleme yapılmadı)")
        return
    ftp = baglan(a)
    kok = a["FTP_ROOT"].rstrip("/")
    dizin_olustur(ftp, kok)
    olusturulan = set()
    for i, p in enumerate(dosyalar, 1):
        rel = p.relative_to(DIST).as_posix()
        uzak = f"{kok}/{rel}"
        ust = uzak.rsplit("/", 1)[0]
        if ust not in olusturulan:
            dizin_olustur(ftp, ust)
            olusturulan.add(ust)
        with open(p, "rb") as f:
            ftp.storbinary(f"STOR {uzak}", f)
        if i % 25 == 0 or i == len(dosyalar):
            print(f"  {i}/{len(dosyalar)}")
    ftp.quit()
    print("✓ Yükleme tamam")


if __name__ == "__main__":
    main()
