# -*- coding: utf-8 -*-
"""أفضل 30 أنمي لكل نوع.

المصدر الأول: MyAnimeList عبر Jikan (`/v4/anime?genres=<id>&order_by=score&sort=desc`).
المصدر الثاني: AniList GraphQL (ترتيب SCORE_DESC) للأغلفة والحلقات والروابط.
كل نوع يُحفظ في `data/anime-top30.json` كنسخة محفوظة تعمل بلا إنترنت،
ويظهر التطبيق/الموقع النسخة الحية أولًا ثم يرجع للمحفوظة عند التعذر.

التشغيل:
    python3 scripts/build_anime_genres.py            # كل الأنواع
    python3 scripts/build_anime_genres.py 0 25       # شريحة (من، إلى)
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "data", "anime-top30.json")

# (الاسم العربي، النوع، قيمة الفلتر، معرّف النوع في MAL إن وُجد)
# kind: g = genre في AniList · t = tag · s = فلتر خاص
GENRES = [
    ("فانتازيا", "g", "Fantasy", 10),
    ("مغامرة", "g", "Adventure", 2),
    ("القوى الخارقة", "t", "Super Power", 31),
    ("شونن", "t", "Shounen", 27),
    ("تشويق", "g", "Thriller", 41),
    ("نفسي", "g", "Psychological", 40),
    ("لعبة المخاطر العالية", "t", "Gambling", 11),
    ("دراما", "g", "Drama", 8),
    ("أكشن", "g", "Action", 1),
    ("خارق للطبيعة", "g", "Supernatural", 37),
    ("مدرسي", "t", "School", 23),
    ("كوميديا هزلية", "t", "Slapstick", 4),
    ("إيسيكاي", "t", "Isekai", 62),
    ("سينين", "t", "Seinen", 42),
    ("الخيال العلمي", "g", "Sci-Fi", 24),
    ("رومانسية", "g", "Romance", 22),
    ("كوميديا", "g", "Comedy", 4),
    ("تاريخي", "t", "Historical", 13),
    ("لعبة استراتيجية", "t", "Board Game", 11),
    ("شريحة من الحياة", "g", "Slice of Life", 36),
    ("البقاء على قيد الحياة", "t", "Survival", 0),
    ("غموض", "g", "Mystery", 7),
    ("رعب", "g", "Horror", 14),
    ("عنف دموي", "t", "Gore", 0),
    ("ميكا", "g", "Mecha", 18),
    ("حائز على جائزة", "s", "award", 0),
    ("أنثروبومورفيك", "t", "Anthropomorphism", 0),
    ("بارودي", "t", "Parody", 20),
    ("تعليمي", "t", "Educational", 0),
    ("تناسخ", "t", "Reincarnation", 0),
    ("السفر عبر الزمن", "t", "Time Manipulation", 0),
    ("ساموراي", "t", "Samurai", 21),
    ("أنمي الفتيات يفعلن أشياء لطيفة", "t", "Cute Girls Doing Cute Things", 0),
    ("مكان العمل", "t", "Work", 48),
    ("رياضات الفريق", "t", "Athletics", 0),
    ("رياضة", "g", "Sports", 30),
    ("فنون قتالية", "t", "Martial Arts", 17),
    ("عسكري", "t", "Military", 38),
    ("سباق", "t", "Cars", 3),
    ("شوجو", "t", "Shoujo", 25),
    ("الأساطير", "t", "Mythology", 0),
    ("طاقم بالغين", "t", "Primarily Adult Cast", 0),
    ("ذواقة", "t", "Food", 47),
    ("حريم", "t", "Female Harem", 35),
    ("إيتشي", "g", "Ecchi", 9),
    ("الفضاء", "t", "Space", 26),
    ("أنيمي الشافي", "t", "Iyashikei", 0),
    ("ألعاب الفيديو", "t", "Video Games", 79),
    ("مثل الأعلى ذكور", "t", "Primarily Male Cast", 0),
    ("عالم الترفيه", "t", "Acting", 0),
    ("تلميح رومانسي", "t", "Unrequited Love", 0),
    ("موسيقى", "g", "Music", 19),
    ("طبي", "t", "Medicine", 0),
    ("المحقق", "t", "Detective", 39),
    ("مصاص الدماء", "t", "Vampire", 32),
    ("ارتداء ملابس الجنس الآخر", "t", "Crossdressing", 0),
    ("مضلع الحب", "t", "Love Triangle", 0),
    ("الجريمة المنظمة", "t", "Criminal Organization", 0),
    ("الفنون الأدائية", "t", "Musical Theater", 0),
    ("آيدولات (إناث)", "t", "Idol", 60),
    ("فتاة ساحرة", "g", "Mahou Shoujo", 66),
    ("رعاية الأطفال", "t", "Parenthood", 0),
    ("الحريم العكسي", "t", "Male Harem", 0),
    ("ثقافة الأوتاكو", "t", "Otaku Culture", 0),
    ("جوسي", "t", "Josei", 43),
    ("إيروتيكا", "g", "Ecchi", 0),
    ("المشاغبون", "t", "Delinquents", 0),
    ("أطفال", "t", "Kids", 15),
    ("الشريرة", "t", "Villainess", 0),
    ("رياضات القتال", "t", "Boxing", 0),
    ("طليعي", "t", "Meta", 0),
    ("حيوانات أليفة", "t", "Animals", 0),
    ("الفنون البصرية", "t", "Drawing", 0),
    ("التحول الجنسي السحري", "t", "Gender Bending", 0),
    ("حب الفتيات", "t", "Yuri", 34),
    ("فانتازيا حضرية", "t", "Urban Fantasy", 0),
    ("الحب الراهن", "t", "Marriage", 0),
]

FIELDS = ("title{romaji english native} averageScore meanScore popularity episodes "
          "siteUrl coverImage{large extraLarge} startDate{year} format isAdult")

CURL = ["curl", "-s", "--max-time", "40", "-X", "POST", "https://graphql.anilist.co",
        "-H", "Content-Type: application/json"]


def anilist(query, tries=4):
    for i in range(tries):
        p = subprocess.run(CURL + ["-d", json.dumps({"query": query})],
                           capture_output=True, text=True)
        try:
            d = json.loads(p.stdout)
        except Exception:
            d = {}
        if d.get("data"):
            return d["data"]
        msg = (d.get("errors") or [{}])[0].get("message", "")
        wait = 20 * (i + 1) if "Too Many" in msg else 4 * (i + 1)
        time.sleep(wait)
    return None


def anilist_top(kind, value):
    if kind == "s":  # حائز على جائزة: الأعلى تقييمًا (85+)
        f = "averageScore_greater:84"
    elif kind == "g":
        f = 'genre:"%s"' % value
    else:
        f = 'tag:"%s"' % value
    q = ("{Page(page:1,perPage:30){media(type:ANIME,isAdult:false,sort:SCORE_DESC,%s){%s}}}"
         % (f, FIELDS))
    d = anilist(q)
    if not d:
        return []
    return d["Page"]["media"]


JIKAN_UP = None


def jikan_alive():
    global JIKAN_UP
    if JIKAN_UP is None:
        p = subprocess.run(["curl", "-s", "--max-time", "10",
                            "https://api.jikan.moe/v4/top/anime?limit=1"],
                           capture_output=True, text=True)
        JIKAN_UP = "\"data\"" in p.stdout
        print("Jikan:", "متاح" if JIKAN_UP else "غير متاح — يُكتفى بـ AniList", flush=True)
    return JIKAN_UP


def jikan_top(mal_id, key):
    """MyAnimeList عبر Jikan — يُستخدم إن كان متاحًا وقت التحديث."""
    if not mal_id or not jikan_alive():
        return []
    url = ("https://api.jikan.moe/v4/anime?genres=%d&order_by=score&sort=desc&limit=25&sfw"
           % mal_id)
    p = subprocess.run(["curl", "-s", "--max-time", "25", url], capture_output=True, text=True)
    try:
        d = json.loads(p.stdout)
    except Exception:
        return []
    out = []
    for a in (d.get("data") or [])[:25]:
        out.append({"t": a.get("title") or "", "mal": a.get("score"),
                    "id": a.get("mal_id"), "ep": a.get("episodes"),
                    "img": ((a.get("images") or {}).get("jpg") or {}).get("image_url", "")})
    return out


def build_one(g):
    ar, kind, value, mal_id = g
    key = ar
    medias = anilist_top(kind, value)
    items = []
    for m in medias:
        t = m.get("title") or {}
        items.append({
            "t": t.get("romaji") or t.get("english") or "",
            "e": t.get("english") or "",
            "n": t.get("native") or "",
            "sc": m.get("averageScore") or 0,
            "ep": m.get("episodes") or 0,
            "y": ((m.get("startDate") or {}).get("year") or 0),
            "f": m.get("format") or "",
            "u": m.get("siteUrl") or "",
            "i": ((m.get("coverImage") or {}).get("extraLarge")
                  or (m.get("coverImage") or {}).get("large") or ""),
        })
    if not items:
        return key, {"ar": ar, "src": "anilist", "kind": kind, "value": value, "items": [], "ok": False}
    mal = jikan_top(mal_id, key)
    return key, {"ar": ar, "src": "anilist", "kind": kind, "value": value,
                 "mal": mal, "items": items, "ok": True}


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end = int(sys.argv[2]) if len(sys.argv) > 2 else len(GENRES)
    data = {}
    if os.path.exists(OUT):
        try:
            data = json.load(open(OUT, encoding="utf-8"))
        except Exception:
            data = {}
    data.setdefault("genres", {})
    data["updated"] = time.strftime("%Y-%m-%d")
    for g in GENRES[start:end]:
        key, rec = build_one(g)
        data["genres"][key] = rec
        print(key, len(rec["items"]), "مال:", len(rec.get("mal") or []), flush=True)
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        time.sleep(2)
    print("saved", OUT, os.path.getsize(OUT))


if __name__ == "__main__":
    main()
