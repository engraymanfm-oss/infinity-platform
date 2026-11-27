#!/usr/bin/env python3
"""Infinity — auto news updater.

Runs server-side (GitHub Actions): fetches the same RSS feeds the page declares in
`const FEEDS`, then rewrites ONLY two data blocks inside index.html:

    const CURATED_AT="..."      (the time the data was refreshed, Riyadh time)
    const CURATED={...}         (curated, description-rich items used first)
    const SNAPSHOT={...}        (deeper per-feed snapshot used as offline fallback)

Everything else in index.html is left byte-identical: sections, layout, the +18
anime category, hand-curated keys with no feed (barca, selfdev), and all logic.
No CORS proxies are used; the page then needs no network to show news.

Exit codes: 0 ok, 1 hard failure (index.html unreadable or every feed failed).
"""

from __future__ import annotations

import gzip
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
RIYADH = timezone(timedelta(hours=3))

MAX_CUR = 14       # items kept per key in CURATED (page shows 4-6 + ticker)
MAX_SNAP = 30      # items kept per key in SNAPSHOT (offline depth)
KEEP_DAYS = 14     # older general-news items are dropped from the refreshed data
DESC_MAX = 220     # characters of plain description kept per item

# التحديث التراكمي: هذه المصادر تغذّي الأنمي والأفلام (وشباك التذاكر)، فلا يُحذف
# منها قديم أبدًا — تُضاف الجديدة أولًا وتُكرَّر بحسب الرابط/العنوان فقط.
CUMULATIVE_KEYS = {"ANN", "MALN", "VERGE", "VARIETY", "IGN", "SKY", "CNN"}
CUM_KEEP_DAYS = 3650      # عمليًا: بلا حد زمني
CUM_MAX_SNAP = 70         # ذاكرة أعمق للأرشيف التراكمي
MAX_OG = 60               # أقصى عدد صفحات تُفتح لاستخراج og:image في التشغيل الواحد
OG_LIMIT = 6              # صفحات لكل مصدر

# علامات v8: إن غابت لا نكتب على index.html حتى لا نكسر الواجهة
V8_MARKERS = ("function v8Home", "function openSheet", "class=\"v8acts\"")
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36 InfinityBot/1.0 (+https://github.com/engraymanfm-oss/infinity-platform)")

FEED_LINE = re.compile(
    r"^\s*([A-Za-z0-9_]+)\s*:\s*\{u:'([^']+)',\s*v:\[([^\]]*)\],\s*n:'([^']*)'\}",
    re.M,
)
TAG_RE = re.compile(r"<[^>]*>")
IMG_RE = re.compile(r"<img[^>]+src=[\"'](https?://[^\"']+)[\"']", re.I)
WS_RE = re.compile(r"\s+")


def plain(raw: str) -> str:
    """HTML fragment -> single-line plain text (same intent as the page's plainText)."""
    if not raw:
        return ""
    s = TAG_RE.sub(" ", raw)
    s = unescape(s)
    s = TAG_RE.sub(" ", s)
    return WS_RE.sub(" ", s).strip()


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        "Accept-Language": "ar,en;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
        enc = (resp.headers.get("Content-Encoding") or "").lower()
    if enc == "gzip" or raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return raw


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def child_text(el: ET.Element, names: tuple[str, ...]) -> str:
    for ch in el:
        if local(ch.tag) in names:
            if local(ch.tag) == "link" and ch.get("href"):
                return ch.get("href") or ""
            return "".join(ch.itertext())
    return ""


def item_link(el: ET.Element) -> str:
    """The article URL: <link> first (many feeds put <guid> before it), then guid/id."""
    for wanted in ("link", ("guid", "id")):
        for ch in el:
            if local(ch.tag) in (wanted if isinstance(wanted, tuple) else (wanted,)):
                u = (ch.get("href") or "".join(ch.itertext())).strip()
                if u.startswith("http"):
                    return u
    return ""


def item_date(el: ET.Element) -> int:
    raw = child_text(el, ("pubdate", "published", "updated", "date", "dc:date"))
    raw = raw.strip()
    if not raw:
        return 0
    try:
        dt = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return 0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def item_image(el: ET.Element, desc: str) -> str:
    for ch in el:
        if local(ch.tag) in ("enclosure", "content", "thumbnail", "group"):
            u = ch.get("url") or ch.get("href") or ""
            if u.startswith("http"):
                return u
            for sub in ch:
                u = sub.get("url") or ""
                if u.startswith("http"):
                    return u
    m = IMG_RE.search(desc or "")
    return m.group(1) if m else ""


def parse_feed(raw: bytes, source_name: str) -> list[dict]:
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        txt = raw.decode("utf-8", "replace")
        txt = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", txt)
        root = ET.fromstring(txt)

    out: list[dict] = []
    for el in root.iter():
        if local(el.tag) not in ("item", "entry"):
            continue
        title = plain(child_text(el, ("title",)))[:300]
        link = item_link(el)
        desc_raw = child_text(el, ("description", "summary", "content", "encoded"))
        if not title or not link.startswith("http"):
            continue
        desc = plain(desc_raw)
        if len(desc) > DESC_MAX:
            desc = desc[: DESC_MAX - 1].rstrip() + "…"
        out.append({
            "t": title,
            "l": link,
            "s": source_name,
            "d": desc,
            "p": item_date(el),
            "img": item_image(el, desc_raw),
        })
    out.sort(key=lambda x: x["p"], reverse=True)
    return out


def merge(old: list[dict], new: list[dict], limit: int, keep_days: int = KEEP_DAYS) -> list[dict]:
    """دمج تراكمي: الجديد أولًا، ثم القديم بلا تكرار (بالرابط)، ولا حذف داخل المدة."""
    cutoff = int((datetime.now(timezone.utc) - timedelta(days=keep_days)).timestamp() * 1000)
    seen: set[str] = set()
    merged: list[dict] = []
    for it in new:
        key = it["l"].split("?")[0]
        if key in seen:
            continue
        seen.add(key)
        merged.append(it)
    for it in old:
        key = (it.get("l") or "").split("?")[0]
        if not key or key in seen:
            continue
        if (it.get("p") or 0) < cutoff:
            continue
        seen.add(key)
        merged.append(it)
    merged.sort(key=lambda x: x.get("p") or 0, reverse=True)
    return merged[:limit]


def js_json(obj) -> str:
    s = json.dumps(obj, ensure_ascii=False, separators=(", ", ": "))
    return s.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def shape(items: list[dict], with_img: bool) -> list[dict]:
    out = []
    for it in items:
        row = {"t": it.get("t", ""), "l": it.get("l", ""), "s": it.get("s", ""),
               "d": it.get("d", ""), "p": int(it.get("p") or 0)}
        if with_img:
            row["img"] = it.get("img") or ""
        out.append(row)
    return out


def og_image(url: str) -> str:
    """صورة المشاركة من صفحة الخبر نفسها (og:image) — بديل نظيف حين لا تضع الخلاصة صورة."""
    raw = fetch(url)
    txt = raw.decode("utf-8", "replace")[:400000]
    for pat in (r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image'):
        m = re.search(pat, txt, re.I)
        if m and m.group(1).startswith("http"):
            return unescape(m.group(1))
    return ""


WIKI_UA = ("InfinityPlatformBot/1.0 (https://github.com/engraymanfm-oss/infinity-platform; "
           "contact: engraymanfm@gmail.com) python-urllib/3.12")
WIKI_CACHE = ROOT / 'scripts' / 'image-cache.json'
POSTERS_RE = re.compile(r"^const POSTERS=\{.*\};[ \t]*$", re.M)
CLUBS_RE = re.compile(r"^const CLUBS=\{.*\};[ \t]*$", re.M)

# خريطة الأندية: الاسم العربي كما في بيانات برشلونة → عنوان الصفحة في ويكيبيديا
CLUB_PAGES = {
    'برشلونة': 'FC Barcelona',
    'ريال مدريد': 'Real Madrid CF',
    'أتلتيكو مدريد': 'Atlético Madrid',
    'ديبورتيفو لاكورونيا': 'Deportivo de La Coruña',
    'إشبيلية': 'Sevilla FC',
    'فالنسيا': 'Valencia CF',
    'فياريال': 'Villarreal CF',
    'ريال سوسيداد': 'Real Sociedad',
    'أتلتيك بلباو': 'Athletic Bilbao',
    'ريال بيتيس': 'Real Betis',
    'خيتافي': 'Getafe CF',
    'سيلتا فيغو': 'RC Celta de Vigo',
    'أوساسونا': 'CA Osasuna',
    'مايوركا': 'RCD Mallorca',
    'جيرونا': 'Girona FC',
    'إسبانيول': 'RCD Espanyol',
    'لاس بالماس': 'UD Las Palmas',
    'رايو فاييكانو': 'Rayo Vallecano',
    'ألافيس': 'Deportivo Alavés',
    'إلتشي': 'Elche CF',
    'ليفانتي': 'Levante UD',
    'ألميريا': 'UD Almería',
    'إيبار': 'SD Eibar',
    'غرناطة': 'Granada CF',
    'قادش': 'Cádiz CF',
    'بلد الوليد': 'Real Valladolid',
}


def wiki_thumb(title: str, size: int = 500) -> str:
    """صورة الصفحة (بوستر فيلم أو شعار نادٍ) من ويكيبيديا الإنجليزية."""
    q = urllib.parse.urlencode({
        'action': 'query', 'titles': title, 'prop': 'pageimages',
        'pithumbsize': size, 'format': 'json', 'redirects': '1', 'pilicense': 'any',
    })
    url = 'https://en.wikipedia.org/w/api.php?' + q
    req = urllib.request.Request(url, headers={'User-Agent': WIKI_UA, 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=25) as resp:
        data = json.loads(resp.read())
    for page in (data.get('query', {}).get('pages', {}) or {}).values():
        thumb = page.get('thumbnail', {}).get('source', '')
        if thumb:
            return thumb.split('?utm_')[0]
    return ''


def load_cache() -> dict:
    try:
        return json.loads(WIKI_CACHE.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def save_cache(cache: dict) -> None:
    try:
        WIKI_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding='utf-8')
    except OSError:
        pass


def movie_titles(html: str) -> list[str]:
    out: list[str] = []
    bo = re.search(r"^const BOX_OFFICE=(\{.*?\n\});", html, re.M | re.S)
    if bo:
        out += re.findall(r"t:'([^']+)'", bo.group(1))
    genres = re.search(r"^const MOVIE_GENRES = \[.*?^\];", html, re.M | re.S)
    if genres:
        out += re.findall(r"\['[^']*',\s*'([^']+)',\s*\d{4}", genres.group(0))
    seen, uniq = set(), []
    for t in out:
        t = t.strip()
        if t and t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq


def club_names(html: str) -> list[str]:
    m = re.search(r"^const BARCA_DATA=(\{.*\});[ \t]*$", html, re.M)
    names: list[str] = ['برشلونة']
    if m:
        for fixture in re.findall(r'"m":\s*"([^"]+)"', m.group(1)):
            for part in re.split(r'\s*[×xX]\s*', fixture):
                part = part.strip()
                if part and part not in names:
                    names.append(part)
    return names


def refresh_clubs(html: str) -> tuple[str, int]:
    """شعارات الأندية بمفاتيح عربية (أسماء الفرق كما تظهر في بيانات المنصة)."""
    found = CLUBS_RE.search(html)
    existing: dict[str, str] = {}
    if found:
        try:
            existing = json.loads(found.group(0)[len('const CLUBS='):-1])
        except ValueError:
            existing = {}
    cache = load_cache()
    out: dict[str, str] = {}
    added = 0
    for arabic in club_names(html):
        page = CLUB_PAGES.get(arabic)
        if not page:
            continue
        img = existing.get(arabic) or existing.get(page) or cache.get('CLUBS:' + page, '')
        if not img:
            try:
                img = wiki_thumb(page)
            except Exception as exc:  # noqa: BLE001
                print(f"   · CLUBS {arabic!r} skipped — {type(exc).__name__}")
                img = ''
            cache['CLUBS:' + page] = img
            time.sleep(0.5)
        if img:
            out[arabic] = img
            added += 1
    save_cache(cache)
    block = 'const CLUBS=' + js_json(out) + ';'
    if found:
        html = CLUBS_RE.sub(lambda _m: block, html, count=1)
    else:
        html = re.sub(r"^(const CURATED_AT=)", block + r"\n\1", html, count=1, flags=re.M)
    return html, added


def refresh_wiki_map(html: str, kind: str, titles: list[str], budget: int = 70) -> tuple[str, int]:
    """يكتب/يحدّث const POSTERS أو const CLUBS بصورة حقيقية لكل عنوان (بلا تكرار)."""
    reg = POSTERS_RE if kind == 'POSTERS' else CLUBS_RE
    found = reg.search(html)
    existing: dict[str, str] = {}
    if found:
        try:
            existing = json.loads(found.group(0)[len('const ' + kind + '='):-1])
        except ValueError:
            existing = {}
    cache = load_cache()
    added = 0
    for title in titles:
        if not title or existing.get(title):
            continue
        if budget <= 0:
            break
        key = kind + ':' + title
        img = cache.get(key, '')
        if not img:
            try:
                img = wiki_thumb(title)
            except Exception as exc:  # noqa: BLE001 - عنوان واحد لا يوقف التشغيل
                print(f"   · {kind} {title!r} skipped — {type(exc).__name__}")
                img = ''
            cache[key] = img
            budget -= 1
            time.sleep(0.6 if img else 0.2)
        if img:
            existing[title] = img
            added += 1
    save_cache(cache)
    block = 'const ' + kind + '=' + js_json(existing) + ';'
    if found:
        html = reg.sub(lambda _m: block, html, count=1)
    else:
        html = re.sub(r"^(const CURATED_AT=)", block + r"\n\1", html, count=1, flags=re.M)
    return html, added


def fill_og(curated: dict, snapshot: dict) -> int:
    """يكمل الصور الناقصة في CURATED/SNAPSHOT من og:image — بعدد محدود لكل تشغيل."""
    cands = []
    for k, items in curated.items():
        for it in items:
            if not it.get("img") and it.get("l"):
                cands.append(((it.get("p") or 0), k, it))
    cands.sort(key=lambda r: r[0], reverse=True)
    picked, per, budget = [], {}, MAX_OG
    for row in cands:
        if budget <= 0:
            break
        if per.get(row[1], 0) >= OG_LIMIT:
            continue
        per[row[1]] = per.get(row[1], 0) + 1
        budget -= 1
        picked.append(row)
    if not picked:
        return 0

    def work(row):
        _, k, it = row
        try:
            return k, it.get("l"), og_image(it.get("l", ""))
        except Exception:  # noqa: BLE001 - صورة واحدة لا توقف التشغيل
            return k, it.get("l"), ""

    found = 0
    with ThreadPoolExecutor(max_workers=6) as pool:
        for k, link, img in pool.map(work, picked):
            if not img:
                continue
            for it in curated.get(k, []):
                if it.get("l") == link:
                    it["img"] = img
            for it in snapshot.get(k, []):
                if it.get("l") == link and not it.get("img"):
                    it["img"] = img
            found += 1
    return found


def main() -> int:
    if not INDEX.exists():
        print(f"!! {INDEX} not found", file=sys.stderr)
        return 1
    html = INDEX.read_text(encoding="utf-8")
    missing = [m for m in V8_MARKERS if m not in html]
    if missing:
        print("!! index.html is not the v8 page (missing markers: " + ", ".join(missing) + ")", file=sys.stderr)
        return 1

    feeds = {m.group(1): (m.group(2), m.group(4)) for m in FEED_LINE.finditer(html)}
    if not feeds:
        print("!! no FEEDS parsed from index.html", file=sys.stderr)
        return 1

    def grab(name: str):
        m = re.search(r"^const " + name + r"=(\{.*\});[ \t]*$", html, re.M)
        if not m:
            raise SystemExit(f"!! const {name} block not found")
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"!! const {name} is not valid JSON: {exc}")

    curated = grab("CURATED")
    snapshot = grab("SNAPSHOT")
    before = (json.dumps(curated, ensure_ascii=False, sort_keys=True),
              json.dumps(snapshot, ensure_ascii=False, sort_keys=True))

    results: dict[str, list[dict]] = {}

    def work(key: str):
        url, name = feeds[key]
        try:
            items = parse_feed(fetch(url), name)
            if not items:
                raise ValueError("feed returned no usable items")
            return key, items, None
        except Exception as exc:  # noqa: BLE001 - one feed must not stop the rest
            return key, [], f"{type(exc).__name__}: {exc}"

    keys = sorted(feeds)
    with ThreadPoolExecutor(max_workers=8) as pool:
        for key, items, err in pool.map(work, keys):
            if items:
                results[key] = items
            else:
                print(f"   · {key:8s} skipped — {err}")

    if not results:
        print("!! every feed failed; index.html left untouched", file=sys.stderr)
        return 1

    for key, items in results.items():
        # never invent a section: refresh keys that already exist in the page data
        cum = key in CUMULATIVE_KEYS
        if key in curated:
            curated[key] = shape(merge(curated.get(key, []), items, MAX_CUR,
                                       CUM_KEEP_DAYS if cum else KEEP_DAYS), True)
        if key in snapshot:
            snapshot[key] = shape(merge(snapshot.get(key, []), items,
                                        CUM_MAX_SNAP if cum else MAX_SNAP,
                                        CUM_KEEP_DAYS if cum else KEEP_DAYS), True)

    with_img = fill_og(curated, snapshot)
    print(f"   · صور og:image مكملة {with_img}")

    after = (json.dumps(curated, ensure_ascii=False, sort_keys=True),
             json.dumps(snapshot, ensure_ascii=False, sort_keys=True))
    changed = before != after

    # صور حقيقية: بوسترات الأفلام + شعارات الأندية (تُكمَّل مرة واحدة وتُحفظ في index.html)
    html, posters = refresh_wiki_map(html, 'POSTERS', movie_titles(html))
    html, crests = refresh_clubs(html)
    print(f'   · صور: {posters} بوستر فيلم · {crests} شعار نادٍ')

    now = datetime.now(RIYADH).replace(microsecond=0)
    stamp_line = f'const CURATED_AT="{now.isoformat()}";'

    if changed or "const CURATED_AT=" not in html:
        if "const CURATED_AT=" in html:
            html = re.sub(r"^const CURATED_AT=.*$", stamp_line, html, count=1, flags=re.M)
        else:
            html = re.sub(r"^(const CURATED=)", stamp_line + r"\n\1", html, count=1, flags=re.M)
        if changed:
            html = re.sub(r"^const CURATED=\{.*\};[ \t]*$", "const CURATED=" + js_json(curated) + ";",
                          html, count=1, flags=re.M)
            html = re.sub(r"^const SNAPSHOT=\{.*\};[ \t]*$", "const SNAPSHOT=" + js_json(snapshot) + ";",
                          html, count=1, flags=re.M)
        INDEX.write_text(html, encoding="utf-8")

    total = sum(len(v) for v in results.values())
    print(f"{'updated' if changed else 'no content change'} · {len(results)}/{len(keys)} feeds · "
          f"{total} items fetched · CURATED_AT={now.isoformat()}")
    for key in sorted(results):
        print(f"   · {key:8s} {len(curated.get(key, [])):>2} curated / {len(snapshot.get(key, [])):>2} snapshot")
    return 0


if __name__ == "__main__":
    sys.exit(main())
