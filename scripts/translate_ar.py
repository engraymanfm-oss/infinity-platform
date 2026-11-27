#!/usr/bin/env python3
"""ترجمة العناوين والملخصات غير العربية إلى العربية.

يُستخدم من `update_news.py` بعد جلب الخلاصات، ومن سكربت التصحيح مرة واحدة على
البيانات الموجودة داخل index.html. المبدأ:

* كل نص إنجليزي (عنوان أو ملخص) يُترجم إلى العربية قبل أن يصل الصفحة.
* كاش محلي `scripts/translate-cache.json` يمنع تكرار الترجمة ويخفض الطلبات.
* أكثر من مزوّد: `clients5.google.com` ثم `translate.googleapis.com`، مع إعادة
  محاولة وتراجع تدريجي. لو فشل الكل يبقى النص كما هو ويُطبع تحذير — لا اختراع.

لا يحتاج أي مفتاح API.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE_PATH = HERE / "translate-cache.json"

AR_RE = re.compile(r"[\u0600-\u06FF]")
LAT_RE = re.compile(r"[A-Za-z]")
UA = ("Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Mobile Safari/537.36 InfinityTranslator/1.0")

BATCH = 20          # نصوص في الطلب الواحد
PAUSE = 0.35        # ثوانٍ بين الطلبات — أدب مع الخدمة المجانية
MAX_TRIES = 3


def is_arabic(text: str) -> bool:
    """هل النص عربي فعليًا؟ (حروف عربية أكثر من اللاتينية)"""
    t = text or ""
    ar = len(AR_RE.findall(t))
    la = len(LAT_RE.findall(t))
    return ar >= 3 and ar >= la


def _endpoint_qs(batch: list[str]) -> str:
    return urllib.parse.urlencode([("q", t) for t in batch])


def _request(url: str, timeout: int = 25) -> list[str] | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8", "replace")
    data = json.loads(raw)
    if isinstance(data, list):
        if data and isinstance(data[0], list):          # translate_a/single
            return ["".join(seg[0] for seg in data[0] if seg and seg[0])]
        return [str(x) for x in data]
    if isinstance(data, dict) and data.get("sentences"):
        return ["".join(s.get("trans", "") for s in data["sentences"])]
    return None


def translate_batch(batch: list[str]) -> list[str]:
    """يترجم مجموعة نصوص؛ يرجع نفس العدد (النص الأصلي عند الفشل)."""
    qs = _endpoint_qs(batch)
    urls = [
        "https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=en&tl=ar&" + qs,
        "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ar&dt=t&" + qs,
    ]
    for url in urls:
        for attempt in range(MAX_TRIES):
            try:
                out = _request(url)
                if out is None:
                    break
                if len(out) == len(batch):
                    return out
                if len(batch) == 1 and out:
                    return [out[0]]
            except Exception:                      # noqa: BLE001 - جرّب المزوّد التالي
                time.sleep(1.2 * (attempt + 1))
    return batch


def load_cache() -> dict[str, str]:
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:                              # noqa: BLE001
        return {}


def save_cache(cache: dict[str, str]) -> None:
    try:
        CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=0, sort_keys=True),
                              encoding="utf-8")
    except Exception:                              # noqa: BLE001
        pass


def translate_texts(texts: list[str], cache: dict[str, str], save_every: int = 120) -> dict[str, str]:
    """يترجم النصوص المطلوبة فقط، ويستخدم الكاش لكل ما سبق."""
    need = []
    for t in texts:
        t = (t or "").strip()
        if not t or is_arabic(t):
            continue
        if t not in cache and t not in need:
            need.append(t)
    done = 0
    for i in range(0, len(need), BATCH):
        chunk = need[i:i + BATCH]
        out = translate_batch(chunk)
        for src, tr in zip(chunk, out):
            tr = (tr or "").strip()
            if tr and tr != src:
                cache[src] = tr
        done += len(chunk)
        if done % save_every == 0:
            save_cache(cache)
        time.sleep(PAUSE)
    if need:
        save_cache(cache)
    return cache


def arabize_items(rows: list[dict], cache: dict[str, str]) -> int:
    """يترجم حقول t وd داخل قائمة أخبار (in place) ويرجع عدد النصوص المترجمة."""
    texts: list[str] = []
    for it in rows:
        for f in ("t", "d"):
            v = (it.get(f) or "").strip()
            if v and not is_arabic(v):
                texts.append(v)
    if not texts:
        return 0
    translate_texts(texts, cache)
    n = 0
    for it in rows:
        for f in ("t", "d"):
            v = (it.get(f) or "").strip()
            if not v or is_arabic(v):
                continue
            tr = cache.get(v)
            if tr:
                it[f] = tr
                n += 1
    return n


def arabize_blocks(curated: dict, snapshot: dict, cache: dict[str, str] | None = None) -> int:
    """يمرّ على كل مفاتيح CURATED/SNAPSHOT ويترجم ما هو غير عربي."""
    cache = cache if cache is not None else load_cache()
    rows: list[dict] = []
    for block in (curated, snapshot):
        for items in block.values():
            rows.extend(items or [])
    n = arabize_items(rows, cache)
    save_cache(cache)
    return n


if __name__ == "__main__":                       # اختبار سريع
    c = load_cache()
    sample = ["Apple unveils the new iPhone with a bigger battery",
              "Barcelona beat Real Madrid 3-0 at the Camp Nou"]
    print(translate_texts(sample, c))
    for s in sample:
        print(c.get(s, "!! فشلت الترجمة"))
    if len(sys.argv) > 1:
        print("cache entries:", len(c), "→", CACHE_PATH)
