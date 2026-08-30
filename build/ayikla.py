"""Agent transkriptindeki (JSONL) son ```json bloğunu data/raw/<ad>.json olarak kaydeder.
Kullanım: python build/ayikla.py <transkript.jsonl> <ad>
"""
import html
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')
import re
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
kaynak, ad = sys.argv[1], sys.argv[2]

metinler = []
with open(kaynak, encoding="utf-8") as f:
    for satir in f:
        try:
            kayit = json.loads(satir)
        except json.JSONDecodeError:
            continue
        mesaj = kayit.get("message") or {}
        if mesaj.get("role") != "assistant":
            continue
        for parca in mesaj.get("content") or []:
            if isinstance(parca, dict) and parca.get("type") == "text":
                metinler.append(parca["text"])

bloklar = []
for t in metinler:
    bloklar += re.findall(r"```json\s*(\[.*?\])\s*```", t, flags=re.S)
if not bloklar:
    sys.exit("JSON bloğu bulunamadı")

veri = json.loads(html.unescape(bloklar[-1]))
hedef = KOK / "data" / "raw" / f"{ad}.json"
hedef.parent.mkdir(parents=True, exist_ok=True)
hedef.write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{ad}: {len(veri)} kayıt -> {hedef}")
