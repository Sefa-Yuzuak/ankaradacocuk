"""Takvim regresyonları: python -m unittest discover -s build -p test_etkinlik.py"""
import unittest
from datetime import date
from derle import etkinlik_hazirla, hafta_sonuna_denk


class TakvimTest(unittest.TestCase):
    def hazirla(self, **kw):
        return etkinlik_hazirla([dict(name='Deneme', **kw)], date(2026, 10, 6))

    def test_gecmis_tekrar_yasamaz(self):
        self.assertEqual(self.hazirla(startDate='2026-09-01', recurring='Her hafta'), [])

    def test_ayrik_seans_arasinda_hayali_etkinlik_yok(self):
        e = self.hazirla(startDate='2026-09-01', endDate='2026-11-30', recurring='Belirli günler')[0]
        self.assertFalse(hafta_sonuna_denk(e, date(2026,10,10), date(2026,10,11)))

    def test_dogrulanmis_seans_var(self):
        e = self.hazirla(occurrence_dates=['2026-09-01','2026-10-11','2026-11-01'])[0]
        self.assertTrue(hafta_sonuna_denk(e, date(2026,10,10), date(2026,10,11)))
        self.assertFalse(hafta_sonuna_denk(e, date(2026,10,17), date(2026,10,18)))

    def test_devam_eden_sergi(self):
        e = self.hazirla(startDate='2026-10-01',endDate='2026-10-31')[0]
        self.assertTrue(hafta_sonuna_denk(e, date(2026,10,10), date(2026,10,11)))

    def test_kaynak_degismez(self):
        kaynak = dict(name='Deneme', occurrence_dates=['2026-10-11'])
        etkinlik_hazirla([kaynak], date(2026,10,6))
        self.assertNotIn('startDate', kaynak)

    def test_tarihsiz_hafta_sonu_onerilmez(self):
        e = self.hazirla()[0]
        self.assertFalse(hafta_sonuna_denk(e,date(2026,10,10),date(2026,10,11)))

if __name__ == '__main__':
    unittest.main()
