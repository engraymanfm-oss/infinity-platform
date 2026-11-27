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

MAX_CUR = 8        # items kept per key in CURATED (page shows 4-6 + ticker)
MAX_SNAP = 20      # items kept per key in SNAPSHOT (offline depth)
KEEP_DAYS = 4      # older items are dropped from the refreshed data
DESC_MAX = 220     # characters of plain description kept per item
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


def merge(old: list[dict], new: list[dict], limit: int) -> list[dict]:
    cutoff = int((datetime.now(timezone.utc) - timedelta(days=KEEP_DAYS)).timestamp() * 1000)
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


def main() -> int:
    if not INDEX.exists():
        print(f"!! {INDEX} not found", file=sys.stderr)
        return 1
    html = INDEX.read_text(encoding="utf-8")

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
        if key in curated:
            curated[key] = shape(merge(curated.get(key, []), items, MAX_CUR), False)
        if key in snapshot:
            snapshot[key] = shape(merge(snapshot.get(key, []), items, MAX_SNAP), True)

    after = (json.dumps(curated, ensure_ascii=False, sort_keys=True),
             json.dumps(snapshot, ensure_ascii=False, sort_keys=True))
    changed = before != after

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
