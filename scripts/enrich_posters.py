#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Infinity — تعويض بوسترات الأفلام من ويكيبيديا.

لكل عنوان في index.html (POSTERS + BOX_OFFICE):
  • أفلام الشباك/القادمة (BOX_OFFICE): البحث بسنة الإصدار أولًا (2026 ثم 2027).
  • أفلام قديمة/مرجعية (POSTERS فقط): صفحة العنوان نفسه أولًا.
ثم يأخذ ملف البوستر من صندوق المعلومات (اسم الملف يحتوي poster/teaser/theatrical)
ويحوّله إلى رابط صورة بعرض 500px في scripts/poster-cache.json.

الاستخدام: python3 scripts/enrich_posters.py [--limit N] [--reset]
"""
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
CACHE = ROOT / "scripts" / "poster-cache.json"
UA = ("InfinityPlatform/1.0 (poster enrichment; "
      "https://engraymanfm-oss.github.io/infinity-platform/) python-urllib")
API = "https://en.wikipedia.org/w/api.php?"

ALIASES = {
    "ليلة عنيفة 2": "Violent Night 2",
    "سبايدر-مان: يوم جديد": "Spider-Man: Brand New Day",
    "كثيب: الجزء الثالث": "Dune: Part Three",
    "العيون الساهرة: الساس": "The Sleepless Eyes",
    "ممسوس": "Hexed",
    "حدوتة": "Hadoota",
    "Hadoota · حدوتة": "Hadoota",
    "Dune: Part One وPart Two · إعادة عرض": "Dune: Part Two",
    "OM: Chapter 1 · Udhiram: The Blood Wood": "O.M: Operation Mole",
}


def api(params, tries=4):
    url = API + urllib.parse.urlencode(params)
    delay = 1.0
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except Exception:
            time.sleep(delay)
            delay *= 2
    return {}


def clean(t):
    t = re.sub(r"·.*$", "", t or "").strip()
    return re.sub(r"\s{2,}", " ", t)


BAD_FILE = re.compile(
    r"logo|icon|commons-|question|edit-clear|ambox|symbol|flag|map|signature|"
    r"userbox|disambig|fileicon|\.svg$|\.ogg$|\.webm$|\.pdf$", re.I)
GOOD_FILE = re.compile(r"poster|teaser|theatrical|one[-_ ]sheet|film|cover", re.I)


def collect():
    html = INDEX.read_text(encoding="utf-8")
    keys = {}
    m = re.search(r"const POSTERS=(\{.*?\});\n", html, re.S)
    if m:
        for k in json.loads(m.group(1)):
            keys[k] = {"posters": True, "bo": False}
    m = re.search(r"const BOX_OFFICE=(\{.*?\});\n(?:const |\Z)", html, re.S)
    if m:
        for mt in re.finditer(r"t:'((?:[^'\\]|\\.)*)'", m.group(1)):
            k = mt.group(1).replace("\\'", "'")
            keys.setdefault(k, {"posters": False, "bo": False})
            keys[k]["bo"] = True
    return keys


def exact_pages(titles):
    """{title: page_title} للعناوين الموجودة كما هي"""
    found = {}
    titles = list(titles)
    for i in range(0, len(titles), 20):
        chunk = titles[i:i + 20]
        d = api({"action": "query", "format": "json", "titles": "|".join(chunk),
                 "redirects": 1})
        q = (d.get("query") or {})
        norm = {}
        for n in q.get("normalized") or []:
            norm[n["from"]] = n["to"]
        for r in q.get("redirects") or []:
            norm[r["from"]] = r["to"]
        for p in (q.get("pages") or {}).values():
            if "missing" in p:
                continue
            found[p["title"]] = p["title"]
        for k in chunk:
            t = k
            for _ in range(3):
                t = norm.get(t, t)
            if t in found:
                found[k] = t
        time.sleep(0.35)
    return found


def search(q, year=""):
    tries = []
    if year:
        tries.append('intitle:"%s" %s film' % (q, year))
    tries.append('intitle:"%s" film' % q)
    if year:
        tries.append('"%s" %s film' % (q, year))
    tries.append('"%s" film' % q)
    for s in tries:
        d = api({"action": "query", "format": "json", "list": "search",
                 "srsearch": s, "srlimit": 1})
        hits = (d.get("query") or {}).get("search") or []
        if hits and "(disambiguation)" not in hits[0]["title"].lower():
            return hits[0]["title"]
        time.sleep(0.3)
    return ""


def images_of(pages):
    out = {}
    pages = sorted(set(p for p in pages if p))
    for i in range(0, len(pages), 20):
        chunk = pages[i:i + 20]
        d = api({"action": "query", "format": "json", "prop": "images|langlinks",
                 "titles": "|".join(chunk), "imlimit": "max", "lllang": "ar",
                 "redirects": 1})
        for p in ((d.get("query") or {}).get("pages") or {}).values():
            out[p.get("title", "")] = {
                "files": [im["title"] for im in (p.get("images") or [])],
                "ar": ((p.get("langlinks") or [{}])[0].get("*", "")),
            }
        time.sleep(0.35)
    return out


def pick_poster(files, hint=""):
    files = [f for f in files if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
    clean_files = [f for f in files if not BAD_FILE.search(f)]
    named = [f for f in clean_files if GOOD_FILE.search(f)]
    if named:
        named.sort(key=lambda f: (0 if "poster" in f.lower() else 1, len(f)))
        return named[0]
    words = [w for w in re.findall(r"[A-Za-z]{4,}", hint) if w.lower() not in ("film", "the", "part")]
    for f in clean_files:
        if any(w.lower() in f.lower() for w in words):
            return f
    return clean_files[0] if clean_files else ""


def urls_of(files):
    out = {}
    files = sorted(set(f for f in files if f))
    for i in range(0, len(files), 40):
        chunk = files[i:i + 40]
        d = api({"action": "query", "format": "json", "prop": "imageinfo",
                 "iiprop": "url|mime", "iiurlwidth": 500,
                 "titles": "|".join(chunk)})
        for p in ((d.get("query") or {}).get("pages") or {}).values():
            ii = (p.get("imageinfo") or [{}])[0]
            u = ii.get("thumburl") or ii.get("url") or ""
            if u:
                out[p.get("title", "")] = u.split("?")[0]
        time.sleep(0.35)
    return out


def main():
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    if "--reset" in sys.argv and CACHE.exists():
        CACHE.unlink()
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    keys = collect()
    todo = [k for k in keys if k not in cache]
    if limit:
        todo = todo[:limit]
    print(f"{len(keys)} عنوانًا · {len(todo)} بحاجة بحث")

    exact = exact_pages([clean(ALIASES.get(k, k)) for k in todo])
    cand = {}
    for k in todo:
        base = clean(ALIASES.get(k, k))
        cs = []
        if keys[k]["bo"] and re.search(r"[A-Za-z]", base):
            p = search(base, "2026")
            if p:
                cs.append(p)
        p = exact.get(base)
        if p and p not in cs:
            cs.append(p)
        if not cs:
            p = search(base, "" if not keys[k]["bo"] else "2027")
            if p:
                cs.append(p)
        cand[k] = cs
        time.sleep(0.35)

    imgs = images_of([p for cs in cand.values() for p in cs])
    chosen = {}
    for k, cs in cand.items():
        for p in cs:
            f = pick_poster((imgs.get(p) or {}).get("files") or [], clean(ALIASES.get(k, k)))
            if f:
                chosen[k] = {"page": p, "file": f, "ar": (imgs.get(p) or {}).get("ar", "")}
                break

    # محاولة ثانية: بحث صريح "<العنوان> film" لما لم يُوجد له بوستر
    retry = {k: search(clean(ALIASES.get(k, k)), "" if not keys[k]["bo"] else "2026")
             for k in cand if k not in chosen}
    retry = {k: p for k, p in retry.items() if p and p not in cand[k]}
    if retry:
        imgs.update(images_of(list(retry.values())))
        for k, p in retry.items():
            f = pick_poster((imgs.get(p) or {}).get("files") or [], clean(ALIASES.get(k, k)))
            if f:
                chosen[k] = {"page": p, "file": f, "ar": (imgs.get(p) or {}).get("ar", "")}
    for k in cand:
        if k not in chosen:
            print("  ! بلا بوستر:", k, "→", " / ".join(cand[k]) or "لا صفحة")

    urls = urls_of([v["file"] for v in chosen.values()])
    added = 0
    for k, v in chosen.items():
        u = urls.get(v["file"], "")
        if u:
            cache[k] = {"url": u, "page": v["page"], "ar": v["ar"]}
            added += 1
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"محفوظ {len(cache)} · جديد {added}")


if __name__ == "__main__":
    main()
