#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Infinity — كتالوج الأفلام: آخر شهرين + القادم (ديسمبر 2026 – 2027).
المصدر: جداول ويكيبيديا «List of American films of 2026» + صفحات الأفلام
(العنوان العربي من langlinks، التصنيفات للأنواع، وصورة البوستر من صندوق المعلومات).

يكتب scripts/catalog.json — والحقن في index.html يتم بسكربت منفصل.

كتالوج الأنمي (أفضل 30 لكل نوع) يُبنى بسكربت مستقل: `build_anime_genres.py`
ويكتب `data/anime-top30.json`. التشغيل هنا: `python3 build_catalog.py --anime`.
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
OUT = ROOT / "scripts" / "catalog.json"
PAGES = ["List of American films of 2026", "List of American films of 2027"]
UA = ("InfinityPlatform/1.0 (movie catalog; "
      "https://engraymanfm-oss.github.io/infinity-platform/) python-urllib")
API = "https://en.wikipedia.org/w/api.php?"
MONTHS = {"January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
          "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12}

GENRE_AR = {
    "action": "أكشن", "adventure": "مغامرة", "animated": "أنيميشن", "animation": "أنيميشن",
    "comedy": "كوميديا", "drama": "دراما", "horror": "رعب", "thriller": "إثارة",
    "science fiction": "خيال علمي", "sci-fi": "خيال علمي", "fantasy": "فانتازيا",
    "romance": "رومانسي", "romantic": "رومانسي", "musical": "موسيقي", "mystery": "غموض",
    "crime": "جريمة", "family": "عائلة", "war": "حرب", "western": "غربي",
    "biographical": "سيرة", "biopic": "سيرة", "sports": "رياضي", "superhero": "أبطال خارقون",
    "documentary": "وثائقي", "historical": "تاريخي", "slasher": "رعب",
}
BAD_FILE = re.compile(r"logo|icon|commons-|question|edit-clear|ambox|symbol|flag|map|"
                      r"signature|userbox|disambig|fileicon|\.svg$|\.ogg$|\.webm$|\.pdf$", re.I)
GOOD_FILE = re.compile(r"poster|teaser|theatrical|one[-_ ]sheet|film|verity", re.I)


def api(params, tries=5):
    url = API + urllib.parse.urlencode(params)
    delay = 1.5
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(delay)
                delay *= 2
                continue
            return {}
        except Exception:
            time.sleep(delay)
            delay *= 2
    return {}


def wikitext(page):
    d = api({"action": "parse", "format": "json", "page": page, "prop": "wikitext",
             "redirects": 1})
    return (d.get("parse") or {}).get("wikitext", {}).get("*", "")


def section(wt, name):
    m = re.search(r"\n==\s*%s\s*==\n(.*?)(?=\n==[^=])" % re.escape(name), wt, re.S)
    return m.group(1) if m else ""


def parse_rows(sec, months):
    """يعيد [(month, day, title, wiki_title, studio, crew)]"""
    rows = re.split(r"\n\|-\n", sec)
    out = []
    month = None
    day = None
    for row in rows:
        mm = re.search(r'data-sort-value="(\d+)"', row)
        if mm:
            month = int(mm.group(1))
        cm = re.search(r"rowspan=\"\d+\"[^|]*\|\s*'''(\d{1,2})'''", row)
        if cm:
            day = int(cm.group(1))
        tm = re.search(r"\|\s*''\[\[([^\]\|]+)(?:\|([^\]]+))?\]\]''", row)
        if not tm:
            tm2 = re.search(r"\|\s*''([^'\[]+)''", row)
            if not tm2:
                continue
            title = tm2.group(1).strip()
            wiki = title
        else:
            wiki = tm.group(1).split("#")[0].strip()
            title = (tm.group(2) or tm.group(1)).strip()
        if not month or not day:
            continue
        studio = ""
        sm = re.search(r"\|\|\s*([^|]+?)\s*\|\|", row)
        if sm:
            studio = re.sub(r"\[\[([^\]\|]+)\|?([^\]]*)\]\]",
                            lambda m: m.group(2) or m.group(1), sm.group(1))
            studio = re.sub(r"'''?", "", studio).strip()[:60]
        out.append({"m": month, "d": day, "t": title, "wiki": wiki, "studio": studio})
    return out


def page_data(wikis):
    """{wiki: {ar, genres, files}}"""
    out = {}
    wikis = sorted(set(wikis))
    for i in range(0, len(wikis), 15):
        chunk = wikis[i:i + 15]
        d = api({"action": "query", "format": "json", "prop": "langlinks|images|categories",
                 "titles": "|".join(chunk), "lllang": "ar", "imlimit": "max",
                 "cllimit": "max", "clshow": "!hidden", "redirects": 1})
        for p in ((d.get("query") or {}).get("pages") or {}).values():
            ar = ""
            for ll in (p.get("langlinks") or []):
                if ll.get("lang") == "ar":
                    ar = ll.get("*", "")
            genres = []
            for c in (p.get("categories") or []):
                t = c.get("title", "")
                mm = re.search(r"Category:.*?(%s).*?(films|film)" % "|".join(GENRE_AR), t, re.I)
                if mm:
                    ar_g = GENRE_AR.get(mm.group(1).lower())
                    if ar_g and ar_g not in genres:
                        genres.append(ar_g)
            out[p.get("title", "")] = {
                "ar": ar,
                "genres": genres[:3],
                "files": [im["title"] for im in (p.get("images") or [])],
            }
        time.sleep(0.5)
    return out


def pick_poster(files, title):
    files = [f for f in files if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
             and not BAD_FILE.search(f)]
    named = [f for f in files if GOOD_FILE.search(f)]
    if named:
        named.sort(key=lambda f: (0 if "poster" in f.lower() else 1, len(f)))
        return named[0]
    words = [w for w in re.findall(r"[A-Za-z]{4,}", title)
             if w.lower() not in ("the", "film", "part", "and", "with")]
    for f in files:
        if any(w.lower() in f.lower() for w in words):
            return f
    return ""


def file_urls(files):
    out = {}
    files = sorted(set(f for f in files if f))
    for i in range(0, len(files), 40):
        d = api({"action": "query", "format": "json", "prop": "imageinfo",
                 "iiprop": "url", "iiurlwidth": 400, "titles": "|".join(files[i:i + 40])})
        for p in ((d.get("query") or {}).get("pages") or {}).values():
            ii = (p.get("imageinfo") or [{}])[0]
            u = ii.get("thumburl") or ii.get("url") or ""
            if u:
                out[p.get("title", "")] = u.split("?")[0]
        time.sleep(0.5)
    return out


def main():
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    rows = []
    for page in PAGES:
        wt = wikitext(page)
        year = int(re.search(r"(\d{4})", page).group(1))
        for sec in ["July–September", "October–December"]:
            for r in parse_rows(section(wt, sec), None):
                if r["m"] < 7:
                    continue
                r["y"] = year
                if year == 2026 and r["m"] < 9:
                    continue          # آخر شهرين فقط (سبتمبر–نوفمبر)
                if year > 2026:
                    r["m"] = r["m"] or 1
                rows.append(r)
        time.sleep(0.6)
    print("صفوف:", len(rows))
    if only:
        rows = rows[:int(only)]
    data = page_data([r["wiki"] for r in rows])
    urls = file_urls([pick_poster((data.get(r["wiki"]) or {}).get("files") or [], r["t"])
                      for r in rows])
    out = []
    for r in rows:
        info = data.get(r["wiki"]) or {}
        f = pick_poster(info.get("files") or [], r["t"])
        out.append({
            "en": r["t"], "ar": info.get("ar", ""), "y": r["y"], "m": r["m"], "d": r["d"],
            "g": info.get("genres") or [], "img": urls.get(f, ""),
            "page": r["wiki"], "studio": r["studio"],
        })
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    missing = sum(1 for x in out if not x["img"])
    print(f"كتب {len(out)} فيلمًا · بلا بوستر {missing}")


if __name__ == "__main__":
    if "--anime" in sys.argv:
        import build_anime_genres
        build_anime_genres.main()
    else:
        main()
