# -*- coding: utf-8 -*-
"""v16: قسم الأنمي — إزالة كل محتوى الهنتاي/+18، و77 نوعًا، وأفضل 30 لكل نوع."""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "index.html")
GEN = os.path.join(ROOT, "scripts", "build_anime_genres.py")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import build_anime_genres as B  # noqa

genres_js = json.dumps([[g[0], g[1], g[2]] for g in B.GENRES], ensure_ascii=False, separators=(",", ":"))

NEW_BLOCK = r"""/* ===== الأنمي v16 — 77 نوعًا بلا أي محتوى +18، وأفضل 30 لكل نوع ===== */
const ANIME_GENRES = __GENRES__;
let AN_CACHE = null;
let AN_BUILT = false;
const AN_MAP_SRC = 'AniList GraphQL · MyAnimeList (Jikan)';

/* نسخة محفوظة محلية تعمل بلا إنترنت — تُبنى بـ scripts/build_anime_genres.py */
async function anCacheLoad(){
  if(AN_CACHE) return AN_CACHE;
  try{
    const r = await fetch('data/anime-top30.json', {cache:'no-cache'});
    AN_CACHE = await r.json();
  }catch(e){ AN_CACHE = {genres:{}}; }
  return AN_CACHE;
}
function anFilter(g){
  if(g[1] === 's') return 'averageScore_greater:84';
  return (g[1] === 'g' ? 'genre:"' : 'tag:"') + g[2] + '"';
}
function anItemFromAniList(m, ix){
  const tt = m.title || {};
  return {
    t: tt.romaji || tt.english || '', e: tt.english || '',
    sc: +m.averageScore || 0, ep: m.episodes || 0,
    y: ((m.startDate || {}).year) || 0,
    u: m.siteUrl || '', i: ((m.coverImage || {}).large) || '', rank: ix + 1
  };
}
async function anFetchTop(g){
  const Q = '{Page(page:1,perPage:30){media(type:ANIME,isAdult:false,sort:SCORE_DESC,'
    + anFilter(g) + '){title{romaji english} averageScore episodes siteUrl coverImage{large} startDate{year}}}}';
  const r = await fetch('https://graphql.anilist.co', {
    method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({query:Q})
  }).then(x => x.json());
  const ms = (r && r.data && r.data.Page) ? r.data.Page.media : [];
  return ms.map(anItemFromAniList);
}
function anCard(x, ix){
  const nm = arTitle({title:{romaji:x.t, english:x.e}}) || x.t;
  const cov = x.i || fbImg(x.t, 'ア');
  const k = vReg({t:nm, d:'أنمي · ' + (x.f||'') + (x.y? ' · '+x.y : ''), s:'AniList', l:x.u||'', img:cov, p:Date.now(), sec:'anime'}, {anime:x});
  const rank = ix + 1;
  return '<article class="n-item v8card anCard" data-k="' + k + '" style="cursor:pointer">'
    + '<div class="thumbWrap">' + firstImg({img:cov}, 'ア')
    + (rank === 1 ? '<span class="crown">#1 المتصدر</span>' : '<span class="mood tech anRank">#' + rank + '</span>')
    + '<button class="bookBtn" data-save="' + escHtml(String(nm).slice(0,90)) + '" data-sub="أنمي · ' + escHtml(String(x.sc)) + '/100" data-url="' + escHtml(x.u||'') + '">☆</button></div>'
    + '<div class="t">' + escHtml(nm) + '</div>'
    + '<div class="rateRow"><b>' + (x.sc || '—') + '</b><span class="pbar" style="flex:1"><i style="--w:' + Math.max(2, Math.min(100, x.sc||0)) + '%"></i></span><span>' + (x.ep ? 'حلقات ' + x.ep : (x.y||'')) + '</span></div>'
    + '<div class="meta"><b>AniList</b><span>' + (x.y ? x.y : '—') + '</span></div>'
    + '</article>';
}
async function viewAnime(sec, force){
  setStatus('load', 'يجلب أفضل 30 من AniList…');
  $('#body').innerHTML = '<div id="anCatalog"></div>'
    + '<div class="anGenreBar">'
      + '<div class="anGenreHead"><b>الأنواع</b><span id="anGenreCount">' + ANIME_GENRES.length + ' نوعًا</span></div>'
      + '<input class="anGenreSearch" id="anGenreSearch" type="search" placeholder="دوّر نوعًا… أكشن · إيسيكاي · رومانسي" autocomplete="off">'
      + '<div class="anGenreChips" id="ag">'
      + ANIME_GENRES.map((g,i)=>'<button data-g="' + i + '" class="' + (i===0?'on':'') + '">' + escHtml(g[0]) + '</button>').join('')
      + '</div></div>'
    + '<div id="alist"><div class="panel">يجهز…</div></div>'
    + '<div class="panel"><small>أفضل 30 لكل نوع بترتيب التقييم من AniList GraphQL، ومع كل عمل غلافه وعدد حلقاته ورابط صفحته · نسخة محفوظة من MyAnimeList (Jikan) تُدمج عند توفرها · لا يُعرض أي محتوى +18 في المنصة.</small></div>';
  anCatalog();

  const show = async i => {
    const g = ANIME_GENRES[i];
    document.querySelectorAll('#ag button').forEach(b => b.classList.toggle('on', +b.dataset.g === i));
    $('#alist').innerHTML = '<div class="panel">يجلب أفضل 30 — ' + escHtml(g[0]) + '…</div>';
    let items = [], src = 'AniList';
    try{ items = await anFetchTop(g); }catch(e){ items = []; }
    if(!items.length){
      const c = await anCacheLoad();
      const rec = (c.genres || {})[g[0]];
      if(rec && rec.items && rec.items.length){ items = rec.items; src = 'نسخة محفوظة'; }
    }
    if(!items.length){
      $('#alist').innerHTML = '<div class="panel">ما وصلت قائمة «' + escHtml(g[0]) + '» الآن — جرّب التحديث بعد قليل.</div>';
      setStatus('bad', 'تعذر الوصول'); return;
    }
    vReset();
    items = items.slice(0, 30).map((x, ix) => Object.assign({}, x, {rank: ix + 1}));
    const arch = ARCH.merge('anime:' + g[0], items.map(x => ({t: x.t, s: 'AniList', l: x.u || '', img: x.i || '', p: Date.now()})));
    $('#alist').innerHTML = '<h2 class="anHead">أفضل 30 — ' + escHtml(g[0]) + ' <span>' + src + '</span></h2>'
      + '<div class="cumNote" style="margin-bottom:8px">تراكمي · <b>' + arch.length + '</b> عملًا محفوظًا في هذا النوع · الترتيب بتقييم AniList</div>'
      + '<div class="news anGrid">' + items.map(anCard).join('') + '</div>';
    paintBooks();
    setStatus('ok', 'حية — ' + g[0] + ' · أفضل 30 · ' + src);
  };

  $('#ag').addEventListener('click', e => {
    const b = e.target.closest('button'); if(!b) return;
    show(+b.dataset.g);
  });
  const srch = document.getElementById('anGenreSearch');
  if(srch){
    srch.addEventListener('input', () => {
      const q = AR_NORM(srch.value).trim();
      let n = 0;
      document.querySelectorAll('#ag button').forEach(b => {
        const ok = !q || AR_NORM(b.textContent).includes(q) || String(b.textContent).includes(srch.value.trim());
        b.style.display = ok ? '' : 'none';
        if(ok) n++;
      });
      const c = document.getElementById('anGenreCount');
      if(c) c.textContent = q ? (n + ' من ' + ANIME_GENRES.length) : (ANIME_GENRES.length + ' نوعًا');
    });
  }
  show(0);
}
"""

s = open(HTML, encoding="utf-8").read()
start = s.find("/* ===== الأنمي — بوسترات AniList + تريلرات + تقييمات ===== */")
end = s.find("function viewSelfdev(sec, force){")
assert start > 0 and end > start, (start, end)
block = NEW_BLOCK.replace("__GENRES__", genres_js)
s = s[:start] + block + s[end:]

# كتالوج الأنمي: بلا قسم +18
old_cat = """  const Q='{'
    + 'recent: Page(perPage:24){media(type:ANIME,startDate_greater:20260825,startDate_lesser:20261128,sort:POPULARITY_DESC,isAdult:false){'+F+'}}'
    + 'upcoming: Page(perPage:24){media(type:ANIME,startDate_greater:20261127,sort:POPULARITY_DESC,isAdult:false){'+F+'}}'
    + 'adult: Page(perPage:12){media(type:ANIME,startDate_greater:20260825,sort:POPULARITY_DESC,isAdult:true){'+F+'}}'
    + '}';"""
new_cat = """  const Q='{'
    + 'recent: Page(perPage:24){media(type:ANIME,startDate_greater:20260825,startDate_lesser:20261128,sort:POPULARITY_DESC,isAdult:false){'+F+'}}'
    + 'upcoming: Page(perPage:24){media(type:ANIME,startDate_greater:20261127,sort:POPULARITY_DESC,isAdult:false){'+F+'}}'
    + '}';"""
assert old_cat in s, "catalog query not found"
s = s.replace(old_cat, new_cat, 1)

old_blocks = """    const blocks=[
      ['anRecent','صدر في آخر شهرين · سبتمبر – نوفمبر 2026',((page.recent||{}).media||[])],
      ['anUpcoming','قادم · من ديسمبر 2026',((page.upcoming||{}).media||[])],
      ['anAdult','للبالغين · +18',((page.adult||{}).media||[])]
    ];"""
new_blocks = """    const blocks=[
      ['anRecent','صدر في آخر شهرين · سبتمبر – نوفمبر 2026',((page.recent||{}).media||[])],
      ['anUpcoming','قادم · من ديسمبر 2026',((page.upcoming||{}).media||[])]
    ];"""
assert old_blocks in s, "catalog blocks not found"
s = s.replace(old_blocks, new_blocks, 1)

s = s.replace("/* ===== كتالوج الأنمي: آخر شهرين + القادم + +18 — أغلفة وأسماء من AniList ===== */",
              "/* ===== كتالوج الأنمي: آخر شهرين + القادم — أغلفة وأسماء من AniList ===== */", 1)

open(HTML, "w", encoding="utf-8").write(s)
print("anime ok", len(s))
