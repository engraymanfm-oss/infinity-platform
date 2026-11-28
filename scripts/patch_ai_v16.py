# -*- coding: utf-8 -*-
"""يطبّق v16 على بيانات حرب الذكاء داخل index.html: شركات ناقصة + معايرة جيميناي."""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HTML = os.path.join(ROOT, "index.html")
sys.path.insert(0, HERE)
import ai_war_v16 as V  # noqa

s = open(HTML, encoding="utf-8").read()

m = re.search(r"^const AI_COMPANIES=(\{.*?\});$", s, re.M)
assert m, "AI_COMPANIES not found"
companies = json.loads(m.group(1))

m2 = re.search(r"^const SHOWDOWN=(\[.*?\]);$", s, re.M)
assert m2, "SHOWDOWN not found"
axes = json.loads(m2.group(1))

before = len(companies)

# ---------- شركات جديدة ----------
for name, parent, domain, kind, tier, site, about, subs, strengths in V.NEW_COMPANIES:
    companies[name] = {
        "parent": parent, "domain": domain, "kind": kind, "tier": tier, "site": site,
        "about": about,
        "subs": [{"n": n, "d": d} for n, d in subs],
        "strengths": strengths,
        "tools": len(subs),
    }

# ---------- معايرة جيميناي ----------
fixed = 0
for ax in axes:
    for it in ax["items"]:
        if it["name"] == "جيميناي" and ax["id"] in V.GEMINI_FIX:
            score, why = V.GEMINI_FIX[ax["id"]]
            it["score"] = score
            it["why"] = why
            fixed += 1
        if it["name"] == "جينسبارك" and ax["id"] == "research":
            it["score"] = 89
            it["why"] = "Super Agent يبحث بعدة جولات ويسلّم تقريرًا موثّقًا أو ملفًا جاهزًا، وهو أسبق من جيميناي في هذا المحور."

# ---------- درجات الشركات الجديدة ----------
added = 0
for ax in axes:
    for name, score, why in V.AXIS_ADD.get(ax["id"], []):
        co = companies[name]
        names = [x["n"] for x in co["subs"]]
        tag = co["kind"] + " · " + " + ".join(names[:2])
        if len(names) > 2:
            tag += " +%d" % (len(names) - 2)
        ax["items"] = [i for i in ax["items"] if i["name"] != name]
        ax["items"].append({"name": name, "tag": tag, "score": score, "why": why, "gold": False})
        added += 1

# ---------- إعادة الترتيب ووسم المتصدر ----------
for ax in axes:
    best = max(i["score"] for i in ax["items"])
    for i in ax["items"]:
        i["gold"] = (i["score"] == best)
    ax["items"].sort(key=lambda i: -i["score"])

cats = {k: v["kind"] for k, v in companies.items()}
domains = {k: v["domain"] for k, v in companies.items()}
tiers = {k: v["tier"] for k, v in companies.items()}

s = s[:m.start()] + "const AI_COMPANIES=" + json.dumps(companies, ensure_ascii=False, separators=(",", ":")) + ";" + s[m.end():]

m2 = re.search(r"^const SHOWDOWN=(\[.*?\]);$", s, re.M)
axes_js = [{"id": a["id"], "label": a["label"], "sub": a["sub"], "caveat": "", "items": a["items"]} for a in axes]
s = s[:m2.start()] + "const SHOWDOWN=" + json.dumps(axes_js, ensure_ascii=False, separators=(",", ":")) + ";" + s[m2.end():]

m3 = re.search(r"^const AI_CATS=(\{.*?\});$", s, re.M)
assert m3
s = s[:m3.start()] + "const AI_CATS=" + json.dumps(cats, ensure_ascii=False, separators=(",", ":")) + ";" + s[m3.end():]

m4 = re.search(r"^const AI_DOMAINS=(\{.*?\});$", s, re.M)
assert m4
s = s[:m4.start()] + "const AI_DOMAINS=" + json.dumps(domains, ensure_ascii=False, separators=(",", ":")) + ";" + s[m4.end():]

m5 = re.search(r"^const AI_PRICE ?= ?(\{.*?\});$", s, re.M)
assert m5
s = s[:m5.start()] + "const AI_PRICE = " + json.dumps(tiers, ensure_ascii=False, separators=(",", ":")) + ";" + s[m5.end():]

# ---------- العدّادات في النصوص ----------
s = s.replace("المنهجية: 36 شركة مجمّعة", "المنهجية: %d شركة ومنصة مجمّعة" % len(companies))

open(HTML, "w", encoding="utf-8").write(s)
print("companies", before, "->", len(companies), "| axes entries added", added, "| gemini fixed", fixed)
