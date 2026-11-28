# -*- coding: utf-8 -*-
"""يبني قسم «حرب الذكاء الاصطناعي» الموحّد داخل index.html.
يستبدل بيانات SHOWDOWN القديمة (53 اسمًا مبعثرًا و29 محورًا متداخلًا) ببيانات
36 شركة مجمّعة و16 محورًا، ويضيف بطاقة الشركة المنبثقة ودليل الشركات.
"""
import json
import re
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ai_war_companies import COMPANIES
from ai_war_axes import AXES

ROOT = os.path.dirname(HERE)
HTML = os.path.join(ROOT, "index.html")

COMPANY_BY_NAME = {c["name"]: c for c in COMPANIES}

# حرس: الصفحة الحية تحمل 115 شركة، وهذا الملف يحمل 36 فقط.
# تشغيله على الصفحة الحية يمحو الخمسة والسبعين الأخرى، فنمنعه.
try:
    _live = re.search(r"const AI_COMPANIES=\{(.*?)\};\n", open(HTML, encoding="utf-8").read(), re.S)
    _live_n = len(re.findall(r'"parent":', _live.group(1))) if _live else 0
    if _live_n and _live_n > len(COMPANIES):
        print("!! الصفحة الحية تحمل %d شركة، وهذا المكوّن %d. لن يُكتب شيء." % (_live_n, len(COMPANIES)))
        sys.exit(2)
except SystemExit:
    raise
except Exception:
    pass
ALL_NAMES = [c["name"] for c in COMPANIES]

# ---------- تحقّق ----------
errs = []
for ax in AXES:
    seen = set()
    for name, score, why in ax["items"]:
        if name not in COMPANY_BY_NAME:
            errs.append("اسم غير معروف في %s: %s" % (ax["id"], name))
        if not (0 <= score <= 100):
            errs.append("درجة خارج النطاق %s %s" % (ax["id"], name))
        if name in seen:
            errs.append("تكرار %s في %s" % (name, ax["id"]))
        seen.add(name)
        if "—" in why:
            errs.append("شرطة طويلة في %s %s" % (ax["id"], name))
for c in COMPANIES:
    if not c.get("subs"):
        errs.append("بلا موديلات: %s" % c["name"])
if errs:
    print("\n".join(errs))
    sys.exit(1)

# ---------- توليد JS ----------
companies_js = {}
for c in COMPANIES:
    companies_js[c["name"]] = {
        "parent": c["parent"],
        "domain": c["domain"],
        "kind": c["kind"],
        "tier": c["tier"],
        "site": c["site"],
        "about": c["about"],
        "subs": [{"n": n, "d": d} for n, d in c["subs"]],
        "strengths": c["strengths"],
        "tools": len(c["subs"]),
    }

axes_js = []
for ax in AXES:
    items = []
    best = max(s for _, s, _ in ax["items"])
    for name, score, why in ax["items"]:
        c = COMPANY_BY_NAME[name]
        names = [n for n, _ in c["subs"]]
        tag = c["kind"] + " · " + " + ".join(names[:2])
        if len(names) > 2:
            tag += " +%d" % (len(names) - 2)
        items.append({
            "name": name,
            "tag": tag,
            "score": score,
            "why": why,
            "gold": score == best,
        })
    items.sort(key=lambda x: -x["score"])
    axes_js.append({"id": ax["id"], "label": ax["label"], "sub": ax["sub"], "caveat": "", "items": items})

block = (
    "const AI_COMPANIES=" + json.dumps(companies_js, ensure_ascii=False, separators=(",", ":")) + ";\n"
    "const AI_AXES=" + json.dumps([{"id": a["id"], "label": a["label"], "sub": a["sub"]} for a in axes_js], ensure_ascii=False, separators=(",", ":")) + ";\n"
    "const SHOWDOWN=" + json.dumps(axes_js, ensure_ascii=False, separators=(",", ":")) + ";\n"
)

cats = {c["name"]: c["kind"] for c in COMPANIES}
domains = {c["name"]: c["domain"] for c in COMPANIES}
tiers = {c["name"]: c["tier"] for c in COMPANIES}

with open(HTML, encoding="utf-8") as f:
    s = f.read()

orig_len = len(s)

# 1) بيانات SHOWDOWN
m = re.search(r"^const SHOWDOWN=\[.*\];$", s, re.M)
assert m, "SHOWDOWN line not found"
s = s[:m.start()] + block.rstrip("\n") + s[m.end():]

# 2) CATS
m = re.search(r"^const CATS=\{.*?\};$", s, re.M)
assert m
s = s[:m.start()] + "const AI_CATS=" + json.dumps(cats, ensure_ascii=False, separators=(",", ":")) + ";" + s[m.end():]
m = re.search(r"^const catOf=n=>\{.*?\};$", s, re.M)
assert m
s = s[:m.start()] + "const catOf=n=>AI_CATS[n]||'أخرى';" + s[m.end():]

# 3) محاور الرادار الخمسة
old_ax5 = re.search(r"const AI_AX5=\[\n(?:.*\n){5}\];", s)
assert old_ax5, "AI_AX5 not found"
new_ax5 = """const AI_AX5=[
  {id:'q', label:'الجودة والاستدلال', tasks:['performance','research']},
  {id:'c', label:'الإبداع والوسائط',  tasks:['image','video','audio']},
  {id:'b', label:'العمل البرمجي',    tasks:['code','office']},
  {id:'a', label:'الوكالة والشخصية', tasks:['agent','automation','memory','voice']},
  {id:'v', label:'القيمة والثقة',    tasks:['value','privacy','catalog','speed','integration']}
];"""
s = s[:old_ax5.start()] + new_ax5 + s[old_ax5.end():]

# 4) AI_DOMAINS
m = re.search(r"const AI_DOMAINS=\{.*?\n\};\nAI_DOMAINS\['ريكبافت'\] = 'recraft\.ai';", s, re.S)
assert m, "AI_DOMAINS block not found"
s = s[:m.start()] + "const AI_DOMAINS=" + json.dumps(domains, ensure_ascii=False, separators=(",", ":")) + ";" + s[m.end():]

# 4b) وزن المحاور ونقاط المطابقة: الجودة والعمل أثقل من الوسائط، والغياب لا يصفّر الشركة
old = """function ax5(name, axis){
  let sum=0, c=0;
  (axis.tasks || []).forEach(id => {
    const t=SHOWDOWN.find(x => x.id === id); if(!t) return;
    const it=t.items.find(x => x.name === name); if(!it) return;
    sum+=it.score; c++;
  });
  if(c) return sum/c;
  return aiAvg(name) * 0.70;
}
function aiMatch(name){
  const vals=AI_AX5.map(a => ax5(name, a));
  return Math.round(vals.reduce((x,y)=>x+y,0) / vals.length);
}"""
assert old in s, 'ax5/aiMatch block not found'
new = """function ax5(name, axis){
  let sum=0, c=0;
  (axis.tasks || []).forEach(id => {
    const t=SHOWDOWN.find(x => x.id === id); if(!t) return;
    const it=t.items.find(x => x.name === name); if(!it) return;
    sum+=it.score; c++;
  });
  if(c) return sum/c;
  return aiAvg(name) * 0.78;
}
/* الوزن تحريري: العمق والاستدلال والعمل البرمجي أثقل من الوسائط (وهي محور واحد
   والمحور الذي لم تُقيَّم فيه الشركة لا يُحسب صفرًا بل بخصم 22% من معدلها */
const AI_DIMW={q:1.5,b:1.3,a:1.1,c:0.7,v:0.8};
function aiMatch(name){
  let sum=0, w=0;
  AI_AX5.forEach(a => { const k=AI_DIMW[a.id]||1; sum += ax5(name, a) * k; w += k; });
  return Math.round(sum / (w||1));
}"""
s = s.replace(old, new, 1)

# 5) aiDesc
old = """function aiDesc(name){
  let best=0, label='';
  SHOWDOWN.forEach(t => { const it=t.items.find(x=>x.name===name); if(it && it.score>best){ best=it.score; label=t.label; } });
  const r=aiRows().find(x=>x.n===name) || {};
  return (r.cat ? r.cat : '') + (label ? ' · الأفضل في ' + label : '');
}"""
assert old in s
new = """function aiDesc(name){
  const c=AI_COMPANIES[name]||{};
  let best=0, axes=[];
  SHOWDOWN.forEach(t => { const it=t.items.find(x=>x.name===name); if(it){ if(it.score>best) best=it.score; if(it.score>=85) axes.push(t.label); } });
  const lead=axes.slice(0,2).join(' و');
  return (c.parent||c.kind||'') + (c.kind? ' · '+c.kind : '') + (lead? ' · متقدم في '+lead : '');
}"""
s = s.replace(old, new, 1)

# 6) بطاقات أفضل 4: قابلة للنقر + عدد الأدوات
old = """    return `<article class="aiCard ${gold?'gold':''}">
      <span class="aiRank">${gold?'♛ ':''}#${rank}</span>
      <div class="aiIconBox">${aiIcon(r.n)}</div>
      <h3>${escHtml(r.n)}</h3>
      <p class="aiTag">${escHtml(aiDesc(r.n))}${d?'<br><span style="color:var(--dim);direction:ltr;display:inline-block">'+escHtml(d)+'</span>':''}</p>
      <div class="aiScore"><span>نقاط المطابقة</span><b>${match}%</b></div>
      <div class="aiBars">${bars}</div>
      <a class="aiVisit" href="${aiSite(r.n)}" target="_blank" rel="noopener noreferrer">زيارة الأداة ↗</a>
      <button class="aiAsk" data-ask="${escHtml(r.n)}" type="button">اسأل ∞ عن هذه الأداة</button>
    </article>`;"""
assert old in s, "top4 card template not found"
new = """    const co=AI_COMPANIES[r.n]||{};
    return `<article class="aiCard ${gold?'gold':''}" data-co="${escHtml(r.n)}" role="button" tabindex="0" aria-label="تفاصيل ${escHtml(r.n)}">
      <span class="aiRank">${gold?'♛ ':''}#${rank}</span>
      <div class="aiIconBox">${aiIcon(r.n)}</div>
      <h3>${escHtml(r.n)}</h3>
      <p class="aiTag">${escHtml(aiDesc(r.n))}${d?'<br><span style="color:var(--dim);direction:ltr;display:inline-block">'+escHtml(d)+'</span>':''}</p>
      <span class="aiToolsChip">${co.tools||0} موديلات وأدوات · اضغط للتفاصيل</span>
      <div class="aiScore"><span>نقاط المطابقة</span><b>${match}%</b></div>
      <div class="aiBars">${bars}</div>
      <div class="aiCardActs">
        <a class="aiVisit" href="${aiSite(r.n)}" target="_blank" rel="noopener noreferrer">زيارة الأداة ↗</a>
        <button class="aiAsk" data-ask="${escHtml(r.n)}" type="button">اسأل ∞</button>
      </div>
    </article>`;"""
s = s.replace(old, new, 1)

# 7) مصفوفة المقارنة: رؤوس قابلة للنقر
old = """  box.innerHTML=`<table class="aiMatrix"><thead><tr><th style="text-align:start">المحور</th>${top4.map(r=>`<th>${escHtml(r.n)}</th>`).join('')}</tr></thead>"""
assert old in s
new = """  box.innerHTML=`<table class="aiMatrix"><thead><tr><th style="text-align:start">المحور</th>${top4.map(r=>`<th data-co="${escHtml(r.n)}" style="cursor:pointer">${escHtml(r.n)}</th>`).join('')}</tr></thead>"""
s = s.replace(old, new, 1)

# 8) الهيدر: عدد الشركات والمواجهات + دليل الشركات
old = """        <div class="aiK"><span class="ic">${IC.apps}</span><div><b>${rows.length}</b><small>الأدوات المتاحة</small></div></div>"""
assert old in s
new = """        <div class="aiK"><span class="ic">${IC.apps}</span><div><b>${rows.length}</b><small>شركة ومنصة</small></div></div>"""
s = s.replace(old, new, 1)

old = """    <div class="aiTop4" id="aiTop4"></div>
"""
assert old in s
new = """    <div class="aiTop4" id="aiTop4"></div>

    <section class="bk" id="aiCosWrap">
      <div class="bkHead"><h2>${IC.apps}دليل الشركات والمنصات</h2><span class="more">كل موديلات وأدوات الشركة داخلها · اضغط أي شركة</span></div>
      <div class="aiGrid" id="aiCos"></div>
    </section>
"""
s = s.replace(old, new, 1)

# 9) استدعاء رسم الدليل + ملاحظة المنهجية
old = """  aiTop4Render(rows);
  aiTop4Wire();"""
assert old in s
new = """  aiTop4Render(rows);
  aiTop4Wire();
  aiCosRender();"""
s = s.replace(old, new, 1)

old = """    <p class="aiNote">ملاحظة: النتائج مبنية على اختيارات عملية ومعايير موضوعية ويتم تحديثها باستمرار · الدرجات تحريرية من 100.</p>"""
assert old in s
new = """    <p class="aiNote">المنهجية: 36 شركة مجمّعة، كل موديلاتها وأدواتها تحت اسمها، و16 محورًا غير متداخل · الدرجات تحريرية من 100 مبنية على قدرة الشركة الفعلية في كل محور (اختبارات 2026، التوثيق الرسمي، وحدود الاستخدام الحقيقي) لا على شعبيتها.</p>"""
s = s.replace(old, new, 1)

# 10) لوحة الصدارة: ترتيب بنقاط المطابقة
old = """  const taskShort=SHOWDOWN.map(t=>t.label);
  const top10=rows.slice(0,10);"""
assert old in s
new = """  const taskShort=SHOWDOWN.map(t=>t.label);
  const top10=aiRanked().slice(0,10);"""
s = s.replace(old, new, 1)
old = """chart('cBar',{grid:{left:10,right:60,top:16,bottom:10,containLabel:true},tooltip:{},"""
assert old in s
new = """const cBarEl=chart('cBar',{grid:{left:10,right:60,top:16,bottom:10,containLabel:true},tooltip:{},"""
s = s.replace(old, new, 1)
# ربط النقر على الأعمدة ببطاقة الشركة
old = """series:[{type:'bar',data:top10.map(r=>({value:+r.avg.toFixed(1),itemStyle:{color:r===top?'#F0E1C4':'#3875B0',borderRadius:7}})).reverse(),barWidth:16,label:{show:true,color:'#F0E1C4',position:'right'}}]},top10.map(r=>[r.n,Math.round(r.avg),r.avg.toFixed(1)]));"""
assert old in s
new = """series:[{type:'bar',data:top10.map(r=>({value:+aiMatch(r.n).toFixed(1),itemStyle:{color:r===top?'#F0E1C4':'#3875B0',borderRadius:7}})).reverse(),barWidth:16,label:{show:true,color:'#F0E1C4',position:'right'}}]},top10.map(r=>[r.n,Math.round(aiMatch(r.n)),aiMatch(r.n).toFixed(1)]));
  if(cBarEl&&cBarEl.on) cBarEl.on('click',p=>{ const r=top10[p.dataIndex]; if(r) aiCompanySheet(r.n); });"""
s = s.replace(old, new, 1)

# 11) مستكشف المهام: صفوف قابلة للنقر
old = """    $('#whys').innerHTML=t.items.map(x=>`<div style="display:flex;gap:10px;align-items:baseline;border-bottom:1px solid var(--line);padding:7px 0"><b style="color:var(--gold);min-width:150px">${x.name}</b><span class="chip">${x.tag}</span><span class="rate">${x.score}</span><small style="color:var(--mut);flex:1">${x.why||''}</small></div>`).join('');"""
assert old in s
new = """    $('#whys').innerHTML=t.items.map(x=>`<div data-co="${escHtml(x.name)}" class="aiWhyRow"><b style="color:var(--gold);min-width:150px">${escHtml(x.name)}</b><span class="chip">${x.tag}</span><span class="rate">${x.score}</span><small style="color:var(--mut);flex:1">${x.why||''}</small></div>`).join('');"""
s = s.replace(old, new, 1)

# 12) المُقارن: المتسابقون الافتراضيون والمحاور
old = """    const pick=['جينسبارك','شات جي بي تي','كلود','جيميناي','جروك','ميتا'].filter(n=>allNames.includes(n));"""
assert old in s
new = """    const pick=['جيميناي','شات جي بي تي','كلود','جينسبارك','جروك','بيكل'].filter(n=>allNames.includes(n));"""
s = s.replace(old, new, 1)
old = """    const DEF=[...st0].filter(i=>['research','code','performance','office','imageAI','videoAI','voice','real','connectors','catalog'].includes(SHOWDOWN[i].id));"""
assert old in s
new = """    const DEF=[...st0].filter(i=>['research','code','performance','office','image','video','voice','integration','catalog','memory'].includes(SHOWDOWN[i].id));"""
s = s.replace(old, new, 1)
old = """        <button class="chip" id="cmpGenspark" style="cursor:pointer">جينسبارك ضد الثلاثة</button>"""
assert old in s
new = """        <button class="chip" id="cmpGenspark" style="cursor:pointer">الأعلى ضد الباقي</button>"""
s = s.replace(old, new, 1)
old = """        <span class="chip">المحاور: <b id="cmpACount">25</b></span>"""
assert old in s
new = """        <span class="chip">المحاور: <b id="cmpACount">${SHOWDOWN.length}</b></span>"""
s = s.replace(old, new, 1)

# 13) أهداف المختار الذكي
old = """const AI_GOALS = [
  {id:'code',   label:'برمجة وكود',        axes:['code','prog','agent','automation','performance']},
  {id:'research',label:'بحث وتقارير',      axes:['research','search','real','files']},
  {id:'image',  label:'صور وتصميم',        axes:['imageAI','editAI','infographic']},
  {id:'video',  label:'فيديو ومونتاج',     axes:['videoAI','editAI','avatar','audioAI']},
  {id:'office', label:'أوفيس وعروض',       axes:['office','slides','files','mail']},
  {id:'voice',  label:'صوت ومكالمات',      axes:['voice','audioAI','meetings']},
  {id:'agents', label:'وكلاء وأتمتة',      axes:['agent','team','computer','remote','connectors']}
];"""
assert old in s
new = """const AI_GOALS = [
  {id:'code',   label:'برمجة وكود',        axes:['code','agent','automation','performance']},
  {id:'research',label:'بحث وتقارير',      axes:['research','office','integration']},
  {id:'image',  label:'صور وتصميم',        axes:['image','video']},
  {id:'video',  label:'فيديو ومونتاج',     axes:['video','image','audio']},
  {id:'office', label:'أوفيس وعروض',       axes:['office','integration','speed']},
  {id:'voice',  label:'صوت ومكالمات',      axes:['voice','audio','memory']},
  {id:'agents', label:'وكلاء وأتمتة',      axes:['agent','automation','integration','memory']}
];"""
s = s.replace(old, new, 1)

# 14) أسعار المختار الذكي
m = re.search(r"const AI_PRICE = \{.*?\n\};", s, re.S)
assert m, "AI_PRICE not found"
s = s[:m.start()] + "const AI_PRICE = " + json.dumps(tiers, ensure_ascii=False, separators=(",", ":")) + ";" + s[m.end():]

# 14b) CSS الجديد
CSS = """
.aiCard{cursor:pointer}
.aiToolsChip{display:block;text-align:center;font-size:.58rem;color:var(--sky);background:rgba(127,178,229,.1);border:1px dashed rgba(127,178,229,.35);border-radius:8px;padding:3px 6px;margin:0 2px}
.aiCardActs{display:flex;flex-direction:column;gap:6px;margin-top:auto}
.aiCardActs .aiVisit{margin-top:0}
.aiGrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(116px,1fr));gap:8px}
.aiCo{display:flex;flex-direction:column;align-items:center;gap:4px;padding:11px 7px 9px;background:linear-gradient(170deg,rgba(8,59,113,.55),rgba(0,34,75,.85));border:1px solid var(--line);border-radius:13px;cursor:pointer;text-align:center;transition:transform .16s ease,border-color .16s ease,background .16s ease;font-family:inherit}
.aiCo:hover,.aiCo:focus-visible{border-color:var(--gold2);transform:translateY(-2px);background:linear-gradient(170deg,rgba(11,60,122,.85),rgba(0,34,75,.95));outline:none}
.aiCo img,.aiCo .aiCoIcon{width:32px;height:32px;border-radius:8px;object-fit:contain;background:#050506;padding:3px}
.aiCo b{font-size:.67rem;color:var(--txt);line-height:1.35;font-weight:700}
.aiCo small{font-size:.55rem;color:var(--mut);line-height:1.3}
.aiCo .aicoSc{font-size:.66rem;color:var(--gold);font-weight:800}
.aiWhyRow{display:flex;gap:10px;align-items:baseline;border-bottom:1px solid var(--line);padding:7px 0;cursor:pointer;border-radius:6px}
.aiWhyRow:hover{background:rgba(127,178,229,.07)}
.aiMatrix th[data-co]{cursor:pointer}
.aiMatrix th[data-co]:hover{color:var(--gold)}
.aiSbBack{position:fixed;inset:0;background:rgba(5,5,6,.78);backdrop-filter:blur(7px);z-index:120;animation:fadeIn .18s ease}
.aiSb{position:fixed;z-index:121;left:50%;bottom:0;transform:translateX(-50%);width:min(760px,100%);max-height:90vh;overflow:auto;background:linear-gradient(170deg,#083B71 0%,#00224B 45%,#050506 100%);border:1px solid var(--gold2);border-radius:22px 22px 0 0;padding:16px 16px 26px;animation:sheetIn .24s ease;box-shadow:0 -20px 60px rgba(5,5,6,.7)}
@media(min-width:860px){.aiSb{top:50%;bottom:auto;transform:translate(-50%,-50%);border-radius:20px;max-height:86vh}}
.aiSbX{position:absolute;top:12px;inset-inline-end:12px;width:34px;height:34px;border-radius:50%;background:rgba(5,5,6,.7);border:1px solid var(--line2);color:var(--txt);font-size:1rem;cursor:pointer;z-index:2}
.aiSbHead{display:flex;align-items:center;gap:12px;padding-inline-end:44px}
.aiSbHead img{width:56px;height:56px;border-radius:14px;background:#050506;padding:4px;object-fit:contain;border:1px solid rgba(127,178,229,.35)}
.aiSbWho b{display:block;color:#fff;font-size:1.08rem;font-family:'IBM Plex Sans Arabic',sans-serif;line-height:1.4}
.aiSbWho small{color:var(--mut);font-size:.7rem;direction:ltr;display:inline-block}
.aiSbChips{display:flex;gap:6px;flex-wrap:wrap;margin:9px 0 0}
.aiSbBadge{margin-inline-start:auto;text-align:center;background:rgba(240,225,196,.1);border:1px solid var(--gold2);border-radius:12px;padding:5px 10px}
.aiSbBadge b{color:var(--gold);font-size:1.05rem}
.aiSbBadge small{font-size:.54rem;color:var(--mut);display:block}
.aiSbAbout{color:var(--stone);font-size:.82rem;line-height:1.85;margin:10px 0 4px}
.aiSbH{color:var(--gold);font-size:.84rem;font-family:'IBM Plex Sans Arabic',sans-serif;margin:14px 0 6px;display:flex;align-items:center;gap:6px}
.aiSbH span{color:var(--mut);font-size:.62rem;font-family:inherit;direction:ltr}
.aiSbStr{display:flex;flex-direction:column;gap:5px;margin:0;padding:0;list-style:none}
.aiSbStr li{color:var(--stone);font-size:.78rem;line-height:1.7;display:flex;gap:7px}
.aiSbStr li::before{content:'◆';color:var(--sky);font-size:.55rem;line-height:2}
.aiSubGrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(196px,1fr));gap:7px}
.aiSub{background:rgba(11,60,122,.35);border:1px solid var(--line);border-radius:11px;padding:8px 10px}
.aiSub b{display:block;color:var(--txt);font-size:.74rem;direction:ltr;text-align:start}
.aiSub small{color:var(--mut);font-size:.65rem;line-height:1.6}
.aiSbAx{display:flex;flex-direction:column;gap:6px}
.aiSbAx .r{display:flex;align-items:center;gap:8px}
.aiSbAx .r span{flex:0 0 126px;font-size:.66rem;color:var(--mut)}
.aiSbAx .r i{flex:1;height:7px;border-radius:9px;background:#00224B;overflow:hidden;display:block}
.aiSbAx .r i em{display:block;height:100%;background:linear-gradient(90deg,#3875B0,#F0E1C4)}
.aiSbAx .r b{font-size:.68rem;color:var(--gold);min-width:24px;text-align:start}
.aiSbActs{display:flex;gap:8px;flex-wrap:wrap;margin-top:15px}
.aiSbActs a,.aiSbActs button{flex:1;min-width:140px;text-align:center;border-radius:11px;padding:10px;font-size:.79rem;font-family:inherit;cursor:pointer;border:1px solid var(--line2);background:rgba(5,5,6,.35);color:var(--txt)}
.aiSbActs a{background:linear-gradient(135deg,var(--royal),var(--mid));border-color:var(--gold2);color:#fff;text-decoration:none}
@media(max-width:560px){.aiSbHead{gap:9px;padding-inline-end:30px}.aiSbHead img{width:46px;height:46px;border-radius:12px}.aiSbBadge{padding:4px 8px}.aiSbWho b{font-size:1rem}.aiSbChips{gap:5px}.aiSbChips .chip{font-size:.6rem;padding:2px 7px}.aiSubGrid{grid-template-columns:1fr}.aiGrid{grid-template-columns:repeat(auto-fill,minmax(102px,1fr))}}
"""
old = ".aiNote{color:var(--dim);font-size:.66rem;text-align:center;margin:2px 0 6px}"
assert old in s, 'aiNote css anchor not found'
s = s.replace(old, old + "\n" + CSS.strip("\n"), 1)

# 14c) دوال دليل الشركات وبطاقة الشركة
JS = """
/* ---------- دليل الشركات + بطاقة الشركة المنبثقة ---------- */
function aiRankOf(name){ const r=aiRanked(); const i=r.findIndex(x=>x.n===name); return i<0?null:i+1; }
function aiCosRender(){
  const box=document.getElementById('aiCos'); if(!box) return;
  box.innerHTML=aiRanked().map(r=>{
    const co=AI_COMPANIES[r.n]||{};
    return `<button class="aiCo" data-co="${escHtml(r.n)}" type="button" title="${escHtml(co.about||'')}">`
      + aiIcon(r.n,'aiCoIcon')
      + `<b>${escHtml(r.n)}</b><small>${escHtml(co.kind||'')} · ${co.tools||0} أدوات</small><span class="aicoSc">${aiMatch(r.n)}%</span></button>`;
  }).join('');
}
function aiSheetClose(){ document.querySelectorAll('.aiSb,.aiSbBack').forEach(x=>x.remove()); document.body.style.overflow=''; }
function aiCompanySheet(name){
  if(!AI_COMPANIES[name]) return;
  aiSheetClose();
  const co=AI_COMPANIES[name], rank=aiRankOf(name), match=aiMatch(name);
  const scores=SHOWDOWN.map(t=>{ const it=t.items.find(x=>x.name===name); return it?{label:t.label,score:it.score}:null; }).filter(Boolean).sort((a,b)=>b.score-a.score);
  const w=document.createElement('div');
  w.innerHTML=`<div class="aiSbBack" data-x="1"></div>
  <div class="aiSb" role="dialog" aria-modal="true" aria-label="${escHtml(name)}">
    <button class="aiSbX" data-x="1" aria-label="إغلاق">✕</button>
    <div class="aiSbHead">${aiIcon(name,'aiSbIcon')}
      <div class="aiSbWho"><b>${escHtml(name)}</b><small>${escHtml(co.parent||'')}</small></div>
      <div class="aiSbBadge"><b>${match}%</b><small>المطابقة${rank?' · #'+rank:''}</small></div>
    </div>
    <div class="aiSbChips"><span class="chip">${escHtml(co.kind||'')}</span><span class="chip">${co.tools||0} موديلات وأدوات</span><span class="chip">${scores.length} محورًا مقيَّمًا</span></div>
    <p class="aiSbAbout">${escHtml(co.about||'')}</p>
    <h4 class="aiSbH">نقاط القوة <span>Strengths</span></h4>
    <ul class="aiSbStr">${(co.strengths||[]).map(x=>`<li>${escHtml(x)}</li>`).join('')}</ul>
    <h4 class="aiSbH">الموديلات والأدوات المشمولة <span>${co.tools||0} داخل ${escHtml(co.parent||name)}</span></h4>
    <div class="aiSubGrid">${(co.subs||[]).map(x=>`<div class="aiSub"><b>${escHtml(x.n)}</b><small>${escHtml(x.d)}</small></div>`).join('')}</div>
    <h4 class="aiSbH">أقوى المحاور <span>من ${SHOWDOWN.length}</span></h4>
    <div class="aiSbAx">${scores.slice(0,6).map(x=>`<div class="r"><span>${escHtml(x.label)}</span><i><em style="width:${x.score}%"></em></i><b>${x.score}</b></div>`).join('')}</div>
    <div class="aiSbActs">
      <a href="${aiSite(name)}" target="_blank" rel="noopener noreferrer">زيارة ${escHtml(co.parent||name)} ↗</a>
      <button type="button" data-ask-co="${escHtml(name)}">اسأل ∞ عن ${escHtml(name)}</button>
    </div>
  </div>`;
  document.body.appendChild(w);
  document.body.style.overflow='hidden';
  w.addEventListener('click',e=>{
    if(e.target.closest('[data-x]')){ aiSheetClose(); return; }
    const b=e.target.closest('[data-ask-co]');
    if(b){ const n=b.dataset.askCo; const it=SHOWDOWN.flatMap(t=>t.items).find(x=>x.name===n); aiSheetClose(); chatAbout({t:n,d:(it?it.why:'')+' · '+(co.kind||''),s:'حرب الذكاء الاصطناعي',l:'#/ai',sec:'ai'}); }
  });
  window.addEventListener('hashchange', aiSheetClose, {once:true});
}
document.addEventListener('click',e=>{
  const t=e.target.closest('[data-co]'); if(!t) return;
  if(e.target.closest('[data-ask],a')) return;
  aiCompanySheet(t.dataset.co);
});
document.addEventListener('keydown',e=>{
  if(e.key==='Escape'){ aiSheetClose(); return; }
  if((e.key==='Enter'||e.key===' ') && e.target.matches('[data-co][role="button"]')){ e.preventDefault(); aiCompanySheet(e.target.dataset.co); }
});
"""
anchor = """function aiMatrixRender(rows){"""
assert anchor in s
s = s.replace(anchor, JS.strip("\n") + "\n" + anchor, 1)

old = "b.textContent='v9 · 27 نوفمبر';"
assert old in s, 'version badge'
s = s.replace(old, "b.textContent='v11 · 27 نوفمبر';", 1)

old = """<a class="smartStep" href="#/ai"><span class="sic">${IC.brain}</span><span><b>دع الذكاء يعمل</b><small>أفضل الأدوات ومقارنة المحاور</small></span><span class="sn">2</span></a>"""
new = """<a class="smartStep" href="#/ai"><span class="sic">${IC.brain}</span><span><b>دع الذكاء يعمل</b><small>${SHOWDOWN.reduce((s,t)=>s+t.items.length,0)} مواجهة بين ${Object.keys(AI_COMPANIES).length} شركة على ${SHOWDOWN.length} محورًا</small></span><span class="sn">2</span></a>"""
assert old in s
s = s.replace(old, new, 1)

# 15) بحث لوحة الأوامر
old = """    const ids=['code','prog','agent','automation','performance'];"""
assert old in s
new = """    const ids=['code','agent','automation','performance','office'];"""
s = s.replace(old, new, 1)

with open(HTML, "w", encoding="utf-8") as f:
    f.write(s)
print("patched. size %d -> %d bytes" % (orig_len, len(s)))
print("companies=%d axes=%d items=%d" % (len(COMPANIES), len(AXES), sum(len(a["items"]) for a in AXES)))
