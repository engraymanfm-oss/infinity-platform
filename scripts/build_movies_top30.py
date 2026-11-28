# -*- coding: utf-8 -*-
"""أفضل 30 فيلمًا لكل تصنيف — أفلام حقيقية بتقييم IMDb ونسبة Rotten Tomatoes وبوسترات.

المصادر (كلها حقيقية ومجانية بلا مفاتيح):
  1. IMDb Datasets  · title.ratings.tsv.gz + title.basics.tsv.gz
     التقييم وعدد الأصوات والأنواع والسنة لكل فيلم (تحديث يومي من IMDb).
  2. Wikidata       · P345 (IMDb id) ← الاسم العربي، صورة P18، معرّف Rotten Tomatoes P1258،
     ورابط مقالة ويكيبيديا الإنجليزية والعربية.
  3. Wikipedia      · صورة صندوق المعلومات (البوستر) بعرض 400px لكل مقالة فيلم.
  4. Rotten Tomatoes · صفحة الفيلم نفسها: نسبة الطماطم (Tomatometer).

الترتيب: ترتيب IMDb المرجّح بعدد الأصوات
    WR = (v/(v+m))·R + (m/(v+m))·C     حيث C = 6.9 ومتوسط m لكل نوع
حتى لا يتصدّر فيلم غامض بـ 7000 صوت على كلاسيكية يشاهدها الملايين.

الكتابة تراكمية: فشل نوع واحد لا يمسّ بقية الأنواع، والنوع الذي يفشل يبقى بنسخته
السابقة، ومعه عدّاد `arch` لكل ما ظهر في النوع عبر التحديثات.

التشغيل:
    python3 scripts/build_movies_top30.py              # كل الأنواع
    python3 scripts/build_movies_top30.py 2 5          # شريحة (من، إلى)
    python3 scripts/build_movies_top30.py --no-download  # استخدم كاش IMDb الموجود
"""
import csv
import gzip
import html
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
import urllib.parse
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "data", "movies-top30.json")
CACHE_DIR = os.path.join(ROOT, "data", ".cache", "imdb")
RT_CACHE = os.path.join(HERE, "movies-rt-cache.json")
META_CACHE = os.path.join(HERE, "movies-meta-cache.json")

UA = ("InfinityPlatform/1.0 (movies top30 builder; "
      "https://engraymanfm-oss.github.io/infinity-platform/)")
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
IMDB_BASE = "https://datasets.imdbws.com/"

# الاسم العربي، الاسم الإنجليزي، أنواع IMDb، أدنى عدد أصوات، متوسط m للترجيح
GENRES = [
    ("سوبر هيرو", "Superhero", None, 10000, 30000, "hero"),
    ("أكشن", "Action", ["Action"], 30000, 50000, "g"),
    ("دراما", "Drama", ["Drama"], 30000, 50000, "g"),
    ("جريمة وإثارة", "Crime & Thriller", ["Crime", "Thriller"], 30000, 50000, "g"),
    ("خيال علمي", "Sci-Fi", ["Sci-Fi"], 20000, 35000, "g"),
    ("فانتازيا ومغامرة", "Fantasy & Adventure", ["Fantasy", "Adventure"], 25000, 45000, "g"),
    ("غموض وتشويق", "Mystery", ["Mystery"], 20000, 35000, "g"),
    ("رعب", "Horror", ["Horror"], 20000, 35000, "g"),
    ("رومانسي", "Romance", ["Romance"], 25000, 40000, "g"),
    ("كوميدي", "Comedy", ["Comedy"], 25000, 50000, "g"),
    ("رسوم متحركة وعائلي", "Animation & Family", ["Animation", "Family"], 15000, 40000, "g"),
    ("حربي وتاريخي", "War & History", ["War", "History"], 20000, 30000, "g"),
    ("سيرة ذاتية", "Biography", ["Biography"], 15000, 25000, "g"),
    ("وثائقي", "Documentary", ["Documentary"], 8000, 12000, "g"),
    ("موسيقي", "Musical & Music", ["Music", "Musical"], 8000, 12000, "g"),
]

HERO_QID = "Q1535153"      # superhero film
BAYES_C = 6.9              # متوسط تقييم IMDb التقريبي لكل الأفلام
TOP_N = 30
CANDIDATES = 46            # نأخذ أكثر من 30 مرشحًا لتعويض من لا بوستر له
IMDB_CACHE_HOURS = 20
RT_CACHE_DAYS = 7
META_CACHE_DAYS = 14

# عنوان عربي راسخ لفيلم ترجمته الآلية على ويكيبديا ركيكة أو مضللة
AR_TITLE = {
    "The Exorcist": "طارد الأرواح",
    "Saw": "ساو 1",
    "V for Vendetta": "V للثأر",
    "Full Metal Jacket": "قبعة معدنية كاملة",
    "The Prestige": "البريستيج",
    "Baraka": "باراكا",
    "Heat": "المواجهة",
    "The Intouchables": "الأصدقاء المقربون",
    "Dancer in the Dark": "راقصة في الظلام",
    "The Thing": "الشيء",
}


def log(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------- شبكة
def curl(args, timeout=60):
    try:
        p = subprocess.run(["curl", "-sS", "--max-time", str(timeout)] + args,
                           capture_output=True, text=True)
        return p.stdout
    except Exception:
        return ""


def curl_json(url, headers=None, timeout=90):
    args = ["-H", "Accept: application/json", "-A", UA]
    for h in headers or []:
        args += ["-H", h]
    txt = curl(args + [url], timeout)
    try:
        return json.loads(txt)
    except Exception:
        return {}


def sparql(query, tries=3):
    for i in range(tries):
        txt = curl(["-H", "Accept: application/sparql-results+json", "-A", UA,
                    "--get", "--data-urlencode", "query=" + query,
                    "--data", "format=json",
                    "https://query.wikidata.org/sparql"], 120)
        try:
            return json.loads(txt).get("results", {}).get("bindings", [])
        except Exception:
            time.sleep(8 * (i + 1))
    return []


# ---------------------------------------------------------------- IMDb datasets
def ensure_dataset(name):
    """ينزّل ملف IMDb إن لم يوجد أو تجاوز عمره 20 ساعة."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, name)
    fresh = os.path.exists(path) and (time.time() - os.path.getmtime(path)) < IMDB_CACHE_HOURS * 3600
    if fresh:
        return path
    tmp = path + ".part"
    log("  · تنزيل", name, "…")
    curl(["-L", "-o", tmp, IMDB_BASE + name], 280)
    if os.path.exists(tmp) and os.path.getsize(tmp) > 1_000_000:
        os.replace(tmp, path)
    elif os.path.exists(tmp):
        os.remove(tmp)
    return path


def load_imdb():
    ratings = ensure_dataset("title.ratings.tsv.gz")
    basics = ensure_dataset("title.basics.tsv.gz")
    rat = {}
    with gzip.open(ratings, "rt", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            try:
                rat[row["tconst"]] = (float(row["averageRating"]), int(row["numVotes"]))
            except ValueError:
                continue
    movies = {}
    with gzip.open(basics, "rt", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            if row["titleType"] != "movie" or row["isAdult"] == "1":
                continue
            tt = row["tconst"]
            info = rat.get(tt)
            if not info or info[1] < 5000 or row["startYear"] in ("\\N", ""):
                continue
            try:
                year = int(row["startYear"])
            except ValueError:
                continue
            movies[tt] = {"t": row["primaryTitle"], "y": year,
                          "g": [g for g in row["genres"].split(",") if g and g != "\\N"],
                          "r": info[0], "v": info[1]}
    log("  · IMDb:", len(movies), "فيلمًا بأكثر من 5000 صوت")
    return movies


# ---------------------------------------------------------------- Wikidata
def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


def hero_ids():
    q = ("SELECT ?imdb WHERE { ?item wdt:P136 wd:%s ; wdt:P345 ?imdb . } LIMIT 3000" % HERO_QID)
    return {b["imdb"]["value"] for b in sparql(q)}


def wikidata_meta(ids, cache):
    """اسم عربي + صورة P18 + معرّف RT + مقالة ويكيبيديا (إنجليزية/عربية)."""
    need = [t for t in sorted(ids) if cache.get(t, {}).get("ts", 0) < time.time() - META_CACHE_DAYS * 86400]
    for i in range(0, len(need), 120):
        chunk = need[i:i + 120]
        vals = " ".join('"%s"' % t for t in chunk)
        q = ("SELECT ?imdb ?arL ?arArt ?enArt ?img ?rt WHERE { VALUES ?imdb { %s } "
             "?item wdt:P345 ?imdb . "
             "OPTIONAL { ?item rdfs:label ?arL FILTER(lang(?arL)=\"ar\") } "
             "OPTIONAL { ?arArt schema:about ?item ; schema:isPartOf <https://ar.wikipedia.org/> . } "
             "OPTIONAL { ?enArt schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> . } "
             "OPTIONAL { ?item wdt:P18 ?img } "
             "OPTIONAL { ?item wdt:P1258 ?rt } }" % vals)
        rows = sparql(q)
        got = {}
        for b in rows:
            tt = b["imdb"]["value"]
            rec = got.setdefault(tt, {"a": "", "arw": "", "enw": "", "img": [], "rt": ""})
            if b.get("arL") and not rec["a"]:
                rec["a"] = b["arL"]["value"]
            if b.get("arArt") and not rec["arw"]:
                rec["arw"] = urllib.parse.unquote(b["arArt"]["value"].rsplit("/", 1)[-1])
            if b.get("enArt") and not rec["enw"]:
                rec["enw"] = urllib.parse.unquote(b["enArt"]["value"].rsplit("/", 1)[-1])
            if b.get("img"):
                rec["img"].append(urllib.parse.unquote(b["img"]["value"].rsplit("/", 1)[-1]))
            if b.get("rt") and not rec["rt"]:
                rec["rt"] = b["rt"]["value"]
        for tt in chunk:
            rec = got.get(tt) or {"a": "", "arw": "", "enw": "", "img": [], "rt": ""}
            old = cache.get(tt) or {}
            # لا نمحو ما عُرف سابقًا إن رجع الاستعلام فارغًا
            for k in ("a", "arw", "enw", "rt"):
                if not rec.get(k) and old.get(k):
                    rec[k] = old[k]
            imgs = rec.get("img") or old.get("img") or []
            # البوستر أولًا: اسم الملف يحمل poster/teaser/theatrical
            imgs.sort(key=lambda n: (0 if re.search(r"poster|teaser|theatrical", n, re.I) else 1, len(n)))
            rec["img"] = imgs[:4]
            rec["ts"] = time.time()
            cache[tt] = rec
        save_json(META_CACHE, cache)
        log("  · Wikidata", min(i + 120, len(need)), "/", len(need))
        time.sleep(1)
    return cache


# ---------------------------------------------------------------- Wikipedia posters
def wiki_posters(articles, cache):
    """بوستر من صورة صندوق المعلومات في مقالة الفيلم، بعرض 400px."""
    need = [a for a in articles if a and cache.get("w:" + a, {}).get("ts", 0) < time.time() - META_CACHE_DAYS * 86400]
    for i in range(0, len(need), 40):
        chunk = need[i:i + 40]
        q = urllib.parse.urlencode({
            "action": "query", "format": "json", "prop": "pageimages",
            "piprop": "thumbnail", "pithumbsize": "400",
            "pilicense": "any", "redirects": "1",
            "titles": "|".join(chunk)})
        d = curl_json("https://en.wikipedia.org/w/api.php?" + q, timeout=60)
        pages = ((d.get("query") or {}).get("pages") or {})
        found = {}
        for p in pages.values():
            th = (p.get("thumbnail") or {}).get("source", "")
            if th:
                th = th.split("?")[0].replace("thumb.wikimedia.org", "upload.wikimedia.org")
                found[p.get("title", "")] = th
        # redirects: من العنوان المطلوب إلى العنوان الفعلي
        redirects = {r["from"]: r["to"] for r in ((d.get("query") or {}).get("redirects") or [])}
        normalized = {n["from"]: n["to"] for n in ((d.get("query") or {}).get("normalized") or [])}
        for a in chunk:
            key = redirects.get(a) or normalized.get(a) or a
            url = found.get(key) or found.get(a) or ""
            cache["w:" + a] = {"u": url, "ts": time.time()}
        save_json(META_CACHE, cache)
        log("  · ويكيبيديا", min(i + 40, len(need)), "/", len(need))
        time.sleep(1)
    return cache


# ---------------------------------------------------------------- Rotten Tomatoes
def rt_page_score(slug, english, year):
    url = "https://www.rottentomatoes.com/" + slug.lstrip("/")
    txt = curl(["-A", BROWSER_UA, "-w", "\n%{http_code}", url], 40)
    code = txt.rsplit("\n", 1)[-1].strip()
    if code != "200":
        return None
    title = re.search(r"<title>([^<]*)</title>", txt)
    page_title = html.unescape(title.group(1)).split("|")[0].strip() if title else ""
    if english and page_title and norm(english) != norm(page_title):
        # تحقّق مرن: كل كلمات العنوان الإنجليزي موجودة
        words = [w for w in norm(english).split() if len(w) > 3]
        if words and not all(w in norm(page_title) for w in words):
            return None
    scores = re.findall(r'"scorePercent":"(\d+)%"', txt)
    if not scores:
        return None
    pct = int(scores[0])
    aud = int(scores[1]) if len(scores) > 1 else None
    return {"rt": pct, "aud": aud, "u": url}


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9 ]+", " ", s.lower())
    s = re.sub(r"^(marvel s|dc s|marvel|dc) ", "", s.strip())
    return re.sub(r"\s+", " ", s).strip()


def overlap(a, b):
    A = set(norm(a).split())
    if not A:
        return 0.0
    return len(A & set(norm(b).split())) / len(A)


def rt_search(title, year):
    q = urllib.parse.urlencode({"search": title})
    txt = curl(["-A", BROWSER_UA, "https://www.rottentomatoes.com/search?" + q], 40)
    rows = re.findall(r"<search-page-media-row([^>]*)>(.*?)</search-page-media-row>", txt, re.S)
    best = None
    for attrs, body in rows:
        d = dict(re.findall(r"(\S+)=\"([^\"]*)\"", attrs))
        if not d.get("tomatometer-score"):
            continue
        u = re.search(r'href="(https://www\.rottentomatoes\.com/m/[^"?]+)"', body)
        alt = re.search(r'alt="([^"]*)"', body)
        if not u:
            continue
        ryear = d.get("release-year", "")
        rt = html.unescape(alt.group(1)) if alt else ""
        ov = overlap(title, rt)
        same_year = bool(ryear and year and int(ryear) == year)
        near_year = bool(ryear and year and abs(int(ryear) - year) <= 1)
        if ov >= 0.75 and near_year or ov >= 0.5 and same_year:
            cand = {"rt": int(d["tomatometer-score"]), "aud": None, "u": u.group(1)}
            if same_year and ov >= 0.75:
                return cand
            best = best or cand
    return best


def rt_scores(films, cache):
    """نسبة الطماطم لكل tconst، بكاش 7 أيام (والأفلام الحديثة تُحدَّث دائمًا)."""
    now = time.time()
    todo = []
    for tt, f in films.items():
        rec = cache.get(tt) or {}
        fresh_enough = rec.get("ts", 0) > now - RT_CACHE_DAYS * 86400
        recent = f["y"] >= datetime.now(timezone.utc).year - 1
        if rec and fresh_enough and not (recent and rec.get("ts", 0) < now - 2 * 86400):
            continue
        todo.append(tt)
    log("  · Rotten Tomatoes: يحتاج تحديثًا", len(todo), "من", len(films))
    for n, tt in enumerate(todo, 1):
        f = films[tt]
        rec = cache.get(tt) or {}
        got = None
        slug = (rec.get("slug") or "").strip()
        if slug:
            got = rt_page_score(slug, f["t"], f["y"])
        if not got:
            got = rt_search(f["t"], f["y"])
        if got:
            got["slug"] = got["u"].replace("https://www.rottentomatoes.com/", "")
            got["ts"] = now
            cache[tt] = got
        else:
            rec["ts"] = now
            rec.setdefault("rt", None)
            cache[tt] = rec | {"rt": rec.get("rt")}
        if n % 25 == 0:
            save_json(RT_CACHE, cache)
            log("     RT", n, "/", len(todo))
        time.sleep(0.35)
    save_json(RT_CACHE, cache)
    return cache


# ---------------------------------------------------------------- بناء الأنواع
def main():
    start = 0
    end = len(GENRES)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    no_dl = "--no-download" in sys.argv
    if len(args) >= 2:
        start, end = int(args[0]), int(args[1])

    data = load_json(OUT, {}) or {}
    data.setdefault("genres", {})
    old_genres = data.get("genres") or {}
    arch = data.get("arch") or {}

    movies = load_imdb()
    log("  · أفلام:", len(movies))
    heroes = hero_ids()
    log("  · سوبر هيرو على Wikidata:", len(heroes))

    # المرشحون لكل نوع (أكثر من 30 لتعويض من لا بوستر له)
    chosen = {}
    for ar, en, gs, minv, m, kind in GENRES:
        pool = []
        for tt, x in movies.items():
            if x["v"] < minv:
                continue
            if kind == "hero":
                if tt not in heroes:
                    continue
            elif not (set(gs) & set(x["g"])):
                continue
            wr = (x["v"] / (x["v"] + m)) * x["r"] + (m / (x["v"] + m)) * BAYES_C
            pool.append((wr, x["v"], tt))
        pool.sort(reverse=True)
        chosen[ar] = [tt for _, _, tt in pool[:CANDIDATES]]
        log("  ·", ar, len(pool), "مرشحًا")

    ids = {tt for v in chosen.values() for tt in v}
    meta = wikidata_meta(ids, load_json(META_CACHE, {}))
    arts = []
    for tt in ids:
        rec = meta.get(tt) or {}
        for key in ("enw", "arw"):
            if rec.get(key) and rec[key] not in arts:
                arts.append(rec[key])
    meta = wiki_posters(arts, meta)

    films = {tt: movies[tt] for tt in ids}
    rtc = rt_scores(films, load_json(RT_CACHE, {}))

    updated = datetime.now().strftime("%Y-%m-%d")
    ok_count = 0
    for ar, en, gs, minv, m, kind in GENRES:
        items = []
        for tt in chosen[ar]:
            x = movies[tt]
            rec = meta.get(tt) or {}
            poster = ""
            for key in ("enw", "arw"):
                art = rec.get(key)
                if art:
                    poster = (meta.get("w:" + art) or {}).get("u", "")
                    if poster:
                        break
            if not poster and rec.get("img"):
                name = rec["img"][0]
                poster = ("https://commons.wikimedia.org/wiki/Special:FilePath/"
                          + urllib.parse.quote(name.replace(" ", "_")) + "?width=400")
            rt = (rtc.get(tt) or {})
            items.append({
                "t": x["t"], "a": AR_TITLE.get(x["t"]) or rec.get("a") or "", "y": x["y"],
                "r": round(x["r"], 1), "v": x["v"],
                "rt": rt.get("rt"), "rtu": rt.get("u", ""),
                "u": "https://www.imdb.com/title/%s/" % tt,
                "id": tt, "i": poster,
            })
        # البطاقات ذات البوستر الحقيقي أولًا، ثم الأفضل ترتيبًا
        withp = [x for x in items if x["i"]]
        nop = [x for x in items if not x["i"]]
        ordered = withp[:TOP_N] + nop[:max(0, TOP_N - len(withp))]
        ordered = ordered[:TOP_N]
        if not ordered:
            log("  !!", ar, "بلا نتائج — تبقى النسخة السابقة")
            continue
        # تراكمي: عدّ كل عنوان ظهر في النوع سابقًا أو الآن
        prev = old_genres.get(ar) or {}
        seen = set(arch.get(ar, [])) | {x["t"] for x in prev.get("items", [])} | {x["t"] for x in ordered}
        arch[ar] = sorted(seen)
        data["genres"][ar] = {
            "ar": ar, "en": en, "kind": kind,
            "items": ordered,
            "arch": len(seen),
            "withPoster": len(withp),
            "withRT": sum(1 for x in ordered if x.get("rt") is not None),
            "src": "IMDb · Rotten Tomatoes · Wikidata",
            "ok": True,
        }
        ok_count += 1
        log("  ✓", ar, len(ordered), "فيلمًا · بوستر", len(withp), "· RT", data["genres"][ar]["withRT"])
        save_json(OUT, data)

    data["updated"] = updated
    data["arch"] = arch
    data["src"] = "IMDb ratings dataset · Rotten Tomatoes Tomatometer · Wikidata/Wikipedia posters"
    save_json(OUT, data)
    log("saved", OUT, os.path.getsize(OUT), "بايت ·", ok_count, "نوعًا")


if __name__ == "__main__":
    main()
