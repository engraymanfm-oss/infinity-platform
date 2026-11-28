# -*- coding: utf-8 -*-
"""v16: قسم «العطور» — Infinity DNA + الهرم التفاعلي + Top 3 + المجموعة + Fragrantica Top 10."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "index.html")
RAW = json.load(open("/workspace/scratch/perfume-raw2.json", encoding="utf-8"))

NOTES_AR = {
    "Agarwood (Oud)": "العود", "Akigalawood": "أكيغالاوود", "Amber": "عنبر", "Ambergris": "عنبر الأشهب",
    "Ambermax™": "أمبرماكس", "Amberwood": "خشب العنبر", "Ambroxan": "أمبروكسان", "Apple": "تفاح",
    "Atlas Cedar": "أرز أطلسي", "Basil": "ريحان", "Benzoin": "بنزوين", "Bergamot": "برغموت",
    "Birch": "خشب البتولا", "Black Amber": "عنبر أسود", "Black Cardamom": "هيل أسود",
    "Black Currant": "كشمش أسود", "Black Pepper": "فلفل أسود", "Bourbon Vanilla": "فانيلا بوربون",
    "Brazilian Rosewood": "خشب الورد البرازيلي", "Calabrian bergamot": "برغموت كالابريا",
    "Cambodian Oud": "عود كمبودي", "Candied Fruits": "فواكه مسكّرة", "Caramel": "كراميل",
    "Cardamom": "هيل", "Cardamon": "هيل", "Cedar": "أرز", "Cedarwood": "خشب الأرز",
    "Ceylon Cinnamon": "قرفة سيلانية", "Chinese Black Tea": "شاي أسود صيني", "Cinnamon": "قرفة",
    "Citron": "أترج", "Coffee": "قهوة", "Coriander": "كزبرة", "Coumarin": "كومارين", "Dates": "تمر",
    "Driftwood": "خشب البحر", "Geranium": "جيرانيوم", "Ginger": "زنجبيل", "Grapefruit": "جريب فروت",
    "Green Apple": "تفاح أخضر", "Guaiac Wood": "خشب الغاياك", "Haitian Vetiver": "فيتيفر هايتي",
    "Himalayan Cedar": "أرز هيمالايي", "Indian Oud": "عود هندي", "Iris": "سوسن", "Italian Lemon": "ليمون إيطالي",
    "Jasmine": "ياسمين", "Jasmine Sambac": "ياسمين سامباك", "Juniper": "عرعر", "Juniper Berries": "حب العرعر",
    "Lavender": "لافندر", "Leather": "جلد", "Lemon": "ليمون", "Licorice": "عرقسوس",
    "Madagascar Vanilla": "فانيلا مدغشقر", "Mahonial": "ماهونيال", "Mandarin Orange": "يوسفي",
    "Mint": "نعنع", "Moroccan Jasmine": "ياسمين مغربي", "Moss": "طحلب", "Musk": "مسك", "Myrrh": "مُرّ",
    "Nigerian Ginger": "زنجبيل نيجيري", "Nutmeg": "جوزة الطيب", "Oakmoss": "طحلب البلوط",
    "Olibanum": "لبان", "Orange Blossom": "زهر البرتقال", "Oriental notes": "نفحات شرقية",
    "Orris Root": "أوريس (جذور السوسن)", "Patchouli": "باتشولي", "Pepper": "فلفل", "Pineapple": "أناناس",
    "Pink Pepper": "فلفل وردي", "Plum": "برقوق", "Praline": "برالين", "Rose": "ورد", "Sage": "مريمية",
    "Sandalwood": "صندل", "Sicilian Bergamot": "برغموت صقلّي", "Sicilian Orange": "برتقال صقلّي",
    "Star Anise": "يانسون نجمي", "Suede": "شامواه", "Tobacco": "تبغ", "Toffee": "توفي",
    "Tolu Balsam": "بلسم تولو", "Tonka Bean": "حبة التونكا", "Tuberose": "مسك الروم",
    "Tunisian Neroli": "نيرولي تونسي", "Vanilla": "فانيلا", "Vetiver": "فيتيفر", "Violet": "بنفسج",
    "Virginian Cedar": "أرز فرجيني", "White Flowers": "زهور بيضاء", "Woodsy Notes": "نفحات خشبية",
    "elemi": "إيلمي", "oak moss": "طحلب البلوط", "Balsam Fir": "تنوب بلسمي", "Sea Notes": "نفحات بحرية",
    "Sea Salt": "ملح البحر", "Seaweed": "طحالب البحر", "Styrax": "ستيراكس", "Pepperwood": "خشب الفلفل",
    "Cumin": "كمون", "Bourbon Whiskey": "ويسكي بوربون", "Saffron": "زعفران", "Candied Fruits": "فواكه مسكّرة",
}

BRANDS = {
    "Dolce&Gabbana": ("دولتشي أند غابانا", "dolcegabbana.com"),
    "Tom Ford": ("توم فورد", "tomford.com"),
    "Viktor&Rolf": ("فيكتور أند رولف", "viktor-rolf.com"),
    "Versace": ("فيرزاتشي", "versace.com"),
    "Rabanne": ("باكو رابان", "rabanne.com"),
    "Dior": ("ديور", "dior.com"),
    "Creed": ("كريد", "creedboutique.com"),
    "Jean Paul Gaultier": ("جان بول غوتييه", "jeanpaulgaultier.com"),
    "Parfums de Marly": ("بارفان دو مارلي", "parfumsdemarly.com"),
    "Burberry": ("بربري", "burberry.com"),
    "Arabian Oud": ("العربية للعود", "arabianoud.com"),
    "French Avenue": ("فرنش أفينيو", "frenchavenue.com"),
    "Giorgio Armani": ("جورجيو أرماني", "armani.com"),
    "Lattafa Perfumes": ("لطافة", "lattafa.com"),
    "Afnan": ("أفنان", "afnan.com"),
    "Louis Vuitton": ("لويس فيتون", "louisvuitton.com"),
    "Yves Saint Laurent": ("إيف سان لوران", "ysl.com"),
    "Armaf": ("أرماف", "armaf.com"),
    "Rasasi": ("رصاصي", "rasasi.com"),
}

AR_NAMES = {
    "the-one-edp": "The One EDP",
    "ombre-leather": "Ombré Leather",
    "spicebomb-extreme": "Spicebomb Extreme",
    "eros": "Eros EDT",
    "black-xs": "Black XS",
    "sauvage-elixir": "Sauvage Elixir",
    "aventus": "Aventus",
    "le-male-le-parfum": "Le Male Le Parfum",
    "oud-minerale": "Oud Minérale",
    "sauvage-parfum": "Sauvage Parfum",
    "layton": "Layton",
    "burberry-hero": "Burberry Hero",
    "blue-oud": "Blue Oud",
    "woody": "Woody",
    "arabian-leather": "The Leather (دهن)",
    "liquid-brun": "Liquid Brun",
    "swy-intensely": "Stronger With You Intensely",
    "khamrah": "Khamrah",
    "supremacy-collector": "Supremacy Collector's Edition",
    "imagination": "Imagination",
    "khamrah-qahwa": "Khamrah Qahwa",
    "y-edp": "Y Eau de Parfum",
    "club-de-nuit": "Club de Nuit Intense Man",
    "hawas-ice": "Hawas Ice",
}

EXTRA_NOTES = {
    "spicebomb-extreme": "Vanilla, Tobacco, Cinnamon, Cumin, Bourbon Whiskey, Saffron",
    "oud-minerale": "Sea Notes, Sea Salt, Seaweed, Agarwood (Oud), Ambergris, Pink Pepper, Styrax, Balsam Fir, Pepperwood",
}


def split_notes(txt):
    out = []
    for n in (txt or "").replace(" and ", ", ").split(","):
        n = n.strip()
        if not n:
            continue
        out.append(NOTES_AR.get(n, n))
    return out


def season_tags(w):
    if not w:
        return []
    t = []
    pairs = [("winter", "شتاء"), ("fall", "خريف"), ("spring", "ربيع"), ("summer", "صيف")]
    rank = sorted(pairs, key=lambda p: -(w.get(p[0]) or 0))
    for k, ar in rank[:2]:
        if (w.get(k) or 0) > 0:
            t.append(ar)
    if (w.get("night") or 0) >= (w.get("day") or 0):
        t.append("ليل")
    else:
        t.append("نهار")
    return t


def build():
    items = []
    order = ["the-one-edp", "ombre-leather", "spicebomb-extreme", "eros", "black-xs", "sauvage-elixir",
             "aventus", "le-male-le-parfum", "oud-minerale", "sauvage-parfum", "layton", "burberry-hero",
             "blue-oud", "woody", "arabian-leather",
             "liquid-brun", "swy-intensely", "khamrah", "supremacy-collector", "imagination",
             "khamrah-qahwa", "y-edp", "club-de-nuit", "hawas-ice"]
    for k in order:
        d = RAW[k]
        brand = d.get("brand") or ""
        bar, dom = BRANDS.get(brand, (brand, ""))
        top = split_notes(d.get("top"))
        heart = split_notes(d.get("heart"))
        base = split_notes(d.get("base"))
        notes = split_notes(EXTRA_NOTES.get(k, "")) if not (top or heart or base) else []
        items.append({
            "id": k,
            "en": AR_NAMES.get(k, d.get("name") or k),
            "full": d.get("name") or "",
            "brand": brand,
            "brandAr": bar,
            "dom": dom,
            "perf": d.get("perfumer") or "",
            "year": d.get("year") or 0,
            "rating": d.get("rating") or 0,
            "family": d.get("family") or "",
            "gender": d.get("gender") or "",
            "img": d.get("img") or "",
            "top": top, "heart": heart, "base": base, "notes": notes,
            "tags": season_tags(d.get("wear")),
            "url": d.get("url") or "",
        })
    return items


DATA_JS = json.dumps(build(), ensure_ascii=False, separators=(",", ":"))

BLOCK = r"""
/* ==================================================================
   العطور v16 — بصمة Infinity DNA + الهرم العطري التفاعلي + مجموعة أبو غيث
   البيانات: Fragrantica (28 نوفمبر 2026) — الأسماء والنوتات والعطّارون والتقييمات.
   ================================================================== */
const PERF = __DATA__;
const PERF_BY_ID = {};
PERF.forEach(p => PERF_BY_ID[p.id] = p);
const PERF_TOP3 = ['the-one-edp', 'ombre-leather', 'spicebomb-extreme'];
const PERF_COLLECTION = ['eros', 'black-xs', 'sauvage-elixir', 'aventus', 'le-male-le-parfum', 'oud-minerale',
  'sauvage-parfum', 'layton', 'burberry-hero', 'blue-oud', 'woody', 'arabian-leather'];
const PERF_FTOP10 = ['liquid-brun', 'swy-intensely', 'khamrah', 'supremacy-collector', 'imagination',
  'le-male-le-parfum', 'khamrah-qahwa', 'y-edp', 'club-de-nuit', 'hawas-ice'];
const DNA = {
  img: 'assets/infinity-dna.jpg',
  formula: [['Tom Ford Ombré Leather', 47], ['D&G The One', 25], ['Spicebomb Extreme', 15], ['The Leather — العربية للعود', 13]],
  desc: 'عطر للتميز والاناقة عطر حميمي للعلاقات رومنسي جذاب حضور قوي طاغي فخم بامتياز عطر من يسعى للكمال',
  pyramid: [
    {id:'top', name:'المقدمة', time:'أول 15–30 دقيقة', notes:'برغموت · هيل · فلفل وردي · تفاح مسكّر', src:'The One · The Leather · Spicebomb',
     why:'البرغموت والفلفل الوردي يفتحون العطر بلمعة نظيفة، والتفاح المسكّر يعطي انطباعًا حميميًا من أول رشّة.'},
    {id:'heart', name:'القلب', time:'الساعة 1–3 — ذروة الخلطة', notes:'قرفة · توابل · ياسمين · أوريس (الجذور)', src:'Spicebomb · Ombré · The Leather',
     why:'هنا تلتقي حلاوة القرفة مع زهر الياسمين، والقلب هو اللحظة التي يظهر فيها «حضور» Infinity DNA كاملًا.'},
    {id:'base', name:'القاعدة', time:'من الساعة 3 إلى آخر الثبات', notes:'جلد · تبغ · فانيلا · كراميل · عنبر · مسك · باتشولي', src:'Ombré · The One · The Leather',
     why:'الجلد والتبغ يمسكان الذيل الجلدي، والفانيلا والكراميل يدوّنان الختام بدفء يمتد لساعات.'}
  ]
};
function perfImg(p){
  if(!p.img) return fbImg(p.en, 'ع');
  return '<img class="perfBottle" loading="lazy" decoding="async" alt="" src="assets/perfumes/' + escHtml(p.id) + '.jpg"'
    + ' onerror="this.onerror=null;this.src=\'' + escHtml(p.img) + '\'">';
}
function perfLogo(p){
  const letter = escHtml((p.brandAr || p.brand || 'ع').charAt(0));
  const fb = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="72" height="72"><rect width="72" height="72" rx="16" fill="#0B3C7A"/><text x="36" y="47" font-family="serif" font-size="30" fill="#F0E1C4" text-anchor="middle">' + letter + '</text></svg>').replace(/'/g, '%27');
  if(!p.dom) return '<img class="perfLogo" alt="" src="' + fb + '">';
  return '<img class="perfLogo" loading="lazy" alt="" src="https://www.google.com/s2/favicons?domain=' + encodeURIComponent(p.dom) + '&sz=128" onerror="this.onerror=null;this.src=\'' + fb + '\'">';
}
function perfTags(p){
  return (p.tags || []).map(t => '<span class="perfTag">' + escHtml(t) + '</span>').join('')
    + (p.family ? '<span class="perfTag fam">' + escHtml(p.family) + '</span>' : '');
}
function perfCard(id, ix, opts){
  const p = PERF_BY_ID[id]; if(!p) return '';
  opts = opts || {};
  return '<article class="perfCard" data-perf="' + p.id + '" role="button" tabindex="0">'
    + (opts.rank ? '<span class="perfRank">#' + opts.rank + '</span>' : '')
    + '<div class="perfPic">' + perfImg(p) + '</div>'
    + '<div class="perfBody"><b>' + escHtml(p.en) + '</b>'
    + '<small>' + escHtml(p.brandAr) + (p.year ? ' · ' + p.year : '') + '</small>'
    + '<div class="perfTags">' + perfTags(p) + '</div>'
    + (p.rating ? '<span class="perfRate">★ ' + p.rating.toFixed(2) + ' <i>Fragrantica</i></span>' : '')
    + '</div></article>';
}
function perfPyramidDNA(){
  const p = DNA.pyramid;
  return '<div class="perfPyrWrap">'
    + '<div class="perfPyr" id="dnaPyr">'
    + p.map((l, i) => '<button type="button" class="pyrL lvl' + i + '" data-l="' + i + '"><b>' + l.name + '</b><small>' + l.time + '</small></button>').join('')
    + '</div>'
    + '<div class="perfPyrDetail" id="dnaPyrDetail"></div>'
    + '</div>';
}
function perfPyrShow(i){
  const l = DNA.pyramid[i]; if(!l) return;
  document.querySelectorAll('#dnaPyr .pyrL').forEach((b, k) => b.classList.toggle('on', k === i));
  const box = document.getElementById('dnaPyrDetail');
  if(!box) return;
  box.innerHTML = '<div class="pyrHead"><b>' + l.name + '</b><span>' + l.time + '</span></div>'
    + '<div class="pyrNotes">' + l.notes.split(' · ').map(n => '<span class="pyrNote">' + escHtml(n) + '</span>').join('') + '</div>'
    + '<p class="pyrWhy">' + l.why + '</p>'
    + '<div class="pyrSrc">من: <b>' + escHtml(l.src) + '</b></div>';
}
function perfDetailSheet(id){
  const p = PERF_BY_ID[id]; if(!p) return;
  document.querySelectorAll('.perfSb,.perfSbBack').forEach(x => x.remove());
  document.body.style.overflow = 'hidden';
  const w = document.createElement('div');
  const layers = [
    ['المقدمة', p.top], ['القلب', p.heart], ['القاعدة', p.base]
  ];
  if(p.notes.length) layers.length = 0;
  const bars = layers.map(([nm, arr], i) => arr.length ? '<div class="perfAx"><span>' + nm + '</span><div class="perfAxN">'
    + arr.map(n => '<span class="pyrNote">' + escHtml(n) + '</span>').join('') + '</div></div>' : '').join('');
  w.innerHTML = '<div class="perfSbBack" data-x="1"></div>'
    + '<div class="perfSb" role="dialog" aria-modal="true" aria-label="' + escHtml(p.en) + '">'
    + '<button class="perfX" data-x="1" aria-label="إغلاق">✕</button>'
    + '<div class="perfSbTop">' + perfImg(p) + '<div class="perfSbWho"><b>' + escHtml(p.en) + '</b>'
    + '<span class="perfSbBrand">' + perfLogo(p) + '<span>' + escHtml(p.brandAr) + '<small>' + escHtml(p.brand) + '</small></span></span>'
    + '<div class="perfTags">' + perfTags(p) + '</div>'
    + (p.rating ? '<span class="perfRate">★ ' + p.rating.toFixed(2) + ' <i>Fragrantica</i></span>' : '')
    + '</div></div>'
    + '<div class="perfSbMeta">'
    + (p.perf ? '<div><b>العطّار</b><span>' + escHtml(p.perf) + '</span></div>' : '<div><b>العطّار</b><span>غير معلن في Fragrantica</span></div>')
    + (p.year ? '<div><b>سنة الإصدار</b><span>' + p.year + '</span></div>' : '')
    + (p.family ? '<div><b>العائلة</b><span>' + escHtml(p.family) + '</span></div>' : '')
    + (p.gender ? '<div><b>لمن</b><span>' + escHtml(p.gender) + '</span></div>' : '')
    + '</div>'
    + '<h4 class="perfSbH">الهرم العطري</h4>'
    + '<div class="perfAxWrap">' + (p.notes.length ? '<div class="perfAx"><span>المكونات</span><div class="perfAxN">'
        + p.notes.map(n => '<span class="pyrNote">' + escHtml(n) + '</span>').join('') + '</div></div>' : bars) + '</div>'
    + '<div class="perfSbActs">'
    + (p.url ? '<a href="' + escHtml(p.url) + '" target="_blank" rel="noopener noreferrer">صفحة العطر في Fragrantica ↗</a>' : '')
    + '<button type="button" data-save="' + escHtml(p.en) + '" data-sub="عطر · ' + escHtml(p.brandAr) + '" data-url="' + escHtml(p.url) + '">☆ احفظه</button>'
    + '</div></div>';
  document.body.appendChild(w);
  w.querySelectorAll('[data-x]').forEach(b => b.addEventListener('click', () => {
    document.querySelectorAll('.perfSb,.perfSbBack').forEach(x => x.remove());
    document.body.style.overflow = '';
  }));
  paintBooks();
}
function viewPerfumes(){
  killCharts();
  document.title = 'العطور — Infinity';
  setStatus('ok', 'Infinity DNA · ' + PERF.length + ' عطرًا · Fragrantica');
  $('#body').innerHTML = '<div class="perfDna">'
    + '<div class="perfDnaPic"><img src="' + escHtml(DNA.img) + '" alt="Infinity DNA" loading="eager"></div>'
    + '<div class="perfDnaBody"><span class="perfKicker">بصمة أبو غيث</span>'
    + '<h2>Infinity DNA</h2>'
    + '<p class="perfDnaDesc">' + escHtml(DNA.desc) + '</p>'
    + '<ul class="perfFormula">' + DNA.formula.map(f => '<li><b>' + escHtml(f[0]) + '</b><i><em style="width:' + f[1] + '%"></em></i><span>' + f[1] + '%</span></li>').join('') + '</ul>'
    + '<div class="perfDnaTags"><span class="perfTag">حميمي</span><span class="perfTag">جلدي</span><span class="perfTag">شرقي</span><span class="perfTag">حضور طاغي</span></div>'
    + '</div></div>'
    + '<section class="bk perfPyrSec"><div class="bkHead"><h2>الهرم العطري التفاعلي</h2><span class="more">اضغط أي طبقة تشوف نوتاتها وتوقيتها ومن أي عطر جاءت</span></div>'
    + perfPyramidDNA() + '</section>'
    + '<h2 class="perfH">أفضل ٣ عطور له</h2><div class="perfGrid top3">' + PERF_TOP3.map((id, i) => perfCard(id, i, {rank: i + 1})).join('') + '</div>'
    + '<h2 class="perfH">مجموعته</h2><div class="perfGrid">' + PERF_COLLECTION.map(id => perfCard(id)).join('') + '</div>'
    + '<section class="bk"><div class="bkHead"><h2>Fragrantica Top 10</h2><span class="more">الأكثر رواجًا على Fragrantica — 28 نوفمبر 2026</span></div>'
    + '<div class="perfGrid">' + PERF_FTOP10.map((id, i) => perfCard(id, i, {rank: i + 1})).join('') + '</div></section>'
    + '<div class="panel"><small>النوتات والعطّارون والتقييمات من صفحات العطر في Fragrantica · الترتيب في Top 10 من قائمة «Most Popular Perfumes» الحية على الموقع · اضغط أي بطاقة يفتح الهرم العطري كامل مع صورة القارورة وبيت العطر.</small></div>';
  document.querySelectorAll('#body .perfCard').forEach(c => {
    c.addEventListener('click', () => perfDetailSheet(c.dataset.perf));
    c.addEventListener('keydown', e => { if(e.key === 'Enter' || e.key === ' ') { e.preventDefault(); perfDetailSheet(c.dataset.perf); } });
  });
  document.querySelectorAll('#dnaPyr .pyrL').forEach(b => b.addEventListener('click', () => perfPyrShow(+b.dataset.l)));
  perfPyrShow(0);
  paintBooks();
}
"""

CSS = """
/* ===== العطور v16 ===== */
.perfDna{display:grid;grid-template-columns:minmax(0,300px) 1fr;gap:16px;align-items:center;background:linear-gradient(165deg,rgba(11,60,122,.6),rgba(0,34,75,.92));border:1px solid var(--gold2);border-radius:20px;padding:14px;margin:6px 0 14px;box-shadow:0 18px 50px rgba(5,5,6,.5)}
.perfDnaPic{border-radius:16px;overflow:hidden;background:#050506;border:1px solid rgba(127,178,229,.3)}
.perfDnaPic img{display:block;width:100%;height:auto}
.perfKicker{display:inline-block;font-size:.62rem;color:#050506;background:linear-gradient(135deg,var(--gold),#DED6C2);border-radius:99px;padding:2px 10px;font-weight:800;margin-bottom:6px}
.perfDnaBody h2{font-family:'Amiri',serif;font-size:1.7rem;color:var(--gold);line-height:1.2}
.perfDnaDesc{color:var(--mut);font-size:.84rem;line-height:1.9;margin:6px 0 10px}
.perfFormula{list-style:none;display:flex;flex-direction:column;gap:7px;margin:0;padding:0}
.perfFormula li{display:grid;grid-template-columns:1fr 92px 34px;align-items:center;gap:8px}
.perfFormula b{font-size:.72rem;color:var(--txt);font-weight:600;line-height:1.5}
.perfFormula i{height:7px;border-radius:9px;background:#00224B;overflow:hidden;display:block;order:2}
.perfFormula i em{display:block;height:100%;background:linear-gradient(90deg,#3875B0,#F0E1C4)}
.perfFormula span{order:3;font-size:.68rem;color:var(--gold);font-weight:800;text-align:start}
.perfDnaTags{display:flex;flex-wrap:wrap;gap:5px;margin-top:10px}
.perfTag{font-size:.6rem;color:var(--mut);background:rgba(5,5,6,.4);border:1px solid var(--line);border-radius:99px;padding:2px 8px}
.perfTag.fam{color:var(--gold);border-color:rgba(240,225,196,.4)}
.perfPyrSec{margin:10px 0}
.perfPyrWrap{display:grid;grid-template-columns:1fr 1fr;gap:14px;align-items:start}
.perfPyr{display:flex;flex-direction:column;align-items:center;gap:7px;padding:8px 0}
.perfPyr .pyrL{border:1px solid var(--line2);background:linear-gradient(160deg,rgba(11,60,122,.7),rgba(0,34,75,.95));color:var(--txt);cursor:pointer;font-family:inherit;padding:11px 8px;display:flex;flex-direction:column;align-items:center;gap:2px;transition:transform .16s ease,border-color .16s ease,background .16s ease}
.perfPyr .pyrL b{font-size:.8rem;color:var(--gold)}
.perfPyr .pyrL small{font-size:.58rem;color:var(--dim)}
.perfPyr .pyrL:hover{transform:translateY(-2px);border-color:var(--gold2)}
.perfPyr .pyrL.on{background:linear-gradient(160deg,#0B3C7A,#3875B0);border-color:var(--gold);box-shadow:0 8px 26px rgba(240,225,196,.18)}
.perfPyr .lvl0{width:56%;clip-path:polygon(18% 0,82% 0,100% 100%,0 100%)}
.perfPyr .lvl1{width:78%;clip-path:polygon(11% 0,89% 0,100% 100%,0 100%)}
.perfPyr .lvl2{width:100%;clip-path:polygon(6% 0,94% 0,100% 100%,0 100%)}
.perfPyrDetail{background:rgba(5,5,6,.35);border:1px solid var(--line);border-radius:14px;padding:12px;min-height:130px}
.pyrHead{display:flex;align-items:baseline;gap:8px;margin-bottom:8px}
.pyrHead b{color:var(--gold);font-family:'IBM Plex Sans Arabic',sans-serif;font-size:.95rem}
.pyrHead span{color:var(--dim);font-size:.64rem}
.pyrNotes{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:9px}
.pyrNote{font-size:.66rem;color:var(--txt);background:rgba(56,117,176,.22);border:1px solid rgba(127,178,229,.35);border-radius:8px;padding:3px 9px;white-space:nowrap}
.pyrWhy{color:var(--mut);font-size:.76rem;line-height:1.9}
.pyrSrc{margin-top:8px;font-size:.63rem;color:var(--dim)}
.pyrSrc b{color:var(--sky,#7FB2E5);font-weight:600}
.perfH{color:var(--gold);font-family:'Amiri',serif;font-size:1.2rem;margin:16px 0 8px}
.perfGrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin-bottom:6px}
.perfGrid.top3{grid-template-columns:repeat(auto-fill,minmax(184px,1fr))}
.perfCard{position:relative;background:linear-gradient(170deg,rgba(8,59,113,.5),rgba(0,34,75,.9));border:1px solid var(--line);border-radius:15px;padding:10px;cursor:pointer;text-align:center;transition:transform .16s ease,border-color .16s ease}
.perfCard:hover,.perfCard:focus-visible{transform:translateY(-3px);border-color:var(--gold2);outline:none}
.perfRank{position:absolute;top:7px;inset-inline-start:7px;z-index:2;font-size:.6rem;font-weight:800;color:#050506;background:linear-gradient(135deg,var(--gold),#DED6C2);border-radius:99px;padding:1px 7px}
.perfPic{height:170px;display:flex;align-items:center;justify-content:center;background:radial-gradient(circle at 50% 35%,rgba(127,178,229,.16),transparent 70%);border-radius:11px;margin-bottom:8px}
.perfGrid.top3 .perfPic{height:210px}
img.perfBottle{max-height:100%;max-width:100%;object-fit:contain;filter:drop-shadow(0 10px 18px rgba(0,0,0,.5))}
.perfBody b{display:block;font-size:.78rem;color:var(--txt);line-height:1.5;direction:ltr}
.perfBody small{display:block;font-size:.62rem;color:var(--dim);margin-top:2px}
.perfTags{display:flex;flex-wrap:wrap;gap:4px;justify-content:center;margin-top:6px}
.perfRate{display:inline-block;margin-top:6px;font-size:.66rem;color:var(--gold);font-weight:700}
.perfRate i{font-style:normal;color:var(--dim);font-weight:400;font-size:.56rem}
.perfSbBack{position:fixed;inset:0;background:rgba(5,5,6,.8);backdrop-filter:blur(7px);z-index:130;animation:fadeIn .18s ease}
.perfSb{position:fixed;z-index:131;left:50%;bottom:0;transform:translateX(-50%);width:min(680px,100%);max-height:90vh;overflow:auto;background:linear-gradient(170deg,#083B71 0%,#00224B 45%,#050506 100%);border:1px solid var(--gold2);border-radius:22px 22px 0 0;padding:16px 16px 26px;animation:sheetIn .24s ease;box-shadow:0 -20px 60px rgba(5,5,6,.7)}
@media(min-width:860px){.perfSb{top:50%;bottom:auto;transform:translate(-50%,-50%);border-radius:20px;max-height:88vh}}
.perfX{position:absolute;top:12px;inset-inline-end:12px;width:34px;height:34px;border-radius:50%;background:rgba(5,5,6,.7);border:1px solid var(--line2);color:var(--txt);font-size:1rem;cursor:pointer;z-index:2}
.perfSbTop{display:flex;gap:14px;align-items:center;padding-inline-end:40px}
.perfSbTop .perfPic{width:124px;height:150px;flex:0 0 124px;margin:0}
.perfSbWho b{display:block;color:#fff;font-size:1.02rem;line-height:1.4;direction:ltr;text-align:start}
.perfSbBrand{display:flex;align-items:center;gap:7px;margin-top:6px}
.perfSbBrand span{display:flex;flex-direction:column;font-size:.72rem;color:var(--mut)}
.perfSbBrand small{font-size:.6rem;color:var(--dim);direction:ltr}
img.perfLogo{width:26px;height:26px;border-radius:7px;background:#050506;padding:2px;object-fit:contain;border:1px solid rgba(127,178,229,.3)}
.perfSbMeta{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:8px;margin:14px 0 4px}
.perfSbMeta div{background:rgba(5,5,6,.35);border:1px solid var(--line);border-radius:11px;padding:7px 9px}
.perfSbMeta b{display:block;font-size:.58rem;color:var(--dim);font-weight:500}
.perfSbMeta span{font-size:.72rem;color:var(--txt);line-height:1.6}
.perfSbH{color:var(--gold);font-size:.84rem;font-family:'IBM Plex Sans Arabic',sans-serif;margin:14px 0 8px}
.perfAxWrap{display:flex;flex-direction:column;gap:8px}
.perfAx{display:grid;grid-template-columns:74px 1fr;gap:8px;align-items:start}
.perfAx>span{font-size:.64rem;color:var(--gold);padding-top:4px}
.perfAxN{display:flex;flex-wrap:wrap;gap:5px}
.perfSbActs{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}
.perfSbActs a,.perfSbActs button{flex:1;min-width:130px;text-align:center;border-radius:11px;padding:10px;font-size:.76rem;font-family:inherit;cursor:pointer;border:1px solid var(--line2);background:rgba(5,5,6,.35);color:var(--txt);text-decoration:none}
.perfSbActs a{background:linear-gradient(135deg,var(--blue2),var(--blue));border-color:var(--gold2);color:#fff}
@media(max-width:680px){.perfDna{grid-template-columns:1fr}.perfDnaPic{max-width:230px;margin:0 auto}.perfPyrWrap{grid-template-columns:1fr}.perfGrid{grid-template-columns:repeat(2,minmax(0,1fr))}.perfGrid.top3{grid-template-columns:repeat(2,minmax(0,1fr))}.perfSbTop .perfPic{width:96px;height:120px;flex:0 0 96px}}
"""

s = open(HTML, encoding="utf-8").read()

def rep(a, b, n=1):
    global s
    assert a in s, "missing anchor: " + a[:90]
    s = s.replace(a, b, n)

# 1) الأيقونة
rep("const IC = {\n  globe:", "const IC = {\n  bottle:'<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.9\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M10 2h4v3h-4zM9 5h6l1 3v11a2 2 0 0 1-2 2H10a2 2 0 0 1-2-2V8z\"/><path d=\"M8 11h8M8 15h8\"/></svg>',\n  globe:")

# 2) التنقل
rep("  ['ai',IC.swords,'حرب الذكاء الاصطناعي'],",
    "  ['ai',IC.swords,'حرب الذكاء الاصطناعي'],\n  ['perfumes',IC.bottle,'العطور'],")
# شريط الجوال السفلي يبقى خمسة أزرار — العطور في القائمة والدرج والبحث

# 3) المسار
rep("  if(p[0]==='ai') return aiDash();",
    "  if(p[0]==='ai') return aiDash();\n  if(p[0]==='perfumes') return viewPerfumes();")

# 4) البحث
rep("  push('مقارنة الأجهزة','33 هاتف قمة','تنقّل',()=>location.hash='#/devices');",
    "  push('مقارنة الأجهزة','33 هاتف قمة','تنقّل',()=>location.hash='#/devices');\n  push('العطور','Infinity DNA · top 3 · مجموعته · Fragrantica Top 10','تنقّل',()=>location.hash='#/perfumes');\n  if(typeof PERF!=='undefined') PERF.forEach(p=>push(p.en+' · '+p.brandAr,'عطر · '+p.brandAr+' · '+p.family,'العطور',()=>location.hash='#/perfumes',{why:(p.top.concat(p.heart,p.base).join(' · ')),src:'Fragrantica',url:p.url}));")

# 5) الدرج الجانبي (أزرار سريعة)
rep("      + '<button type=\"button\" data-go=\"#/devices\">'+IC.phone+'<span>مقارنة الأجهزة والجوالات</span></button>'",
    "      + '<button type=\"button\" data-go=\"#/devices\">'+IC.phone+'<span>مقارنة الأجهزة والجوالات</span></button>'\n      + '<button type=\"button\" data-go=\"#/perfumes\">'+IC.bottle+'<span>العطور وInfinity DNA</span></button>'")

# 6) CSS + الكود
rep("</style>", CSS + "\n</style>")
BLOCK_FILLED = BLOCK.replace("__DATA__", DATA_JS)
rep("/* ---------- محفوظاتي ---------- */", BLOCK_FILLED + "\n/* ---------- محفوظاتي ---------- */")

open(HTML, "w", encoding="utf-8").write(s)
print("perfumes ok", len(s))
