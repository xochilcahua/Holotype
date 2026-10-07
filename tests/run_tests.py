# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""
Holotype test runner. Loads the app in headless Chromium, feeds each profile from profiles.py through the app's own code
(state.mastery -> computeClassification / computeNovelty / personalStats / the rendered Herbarium page), and records
everything the app produces. It does NOT interpret results.

usage: python3 run_tests.py <path-to-app.html> <output-dir> [only-key-prefix ...]
writes: <output-dir>/data.json  and  <output-dir>/screens/<key>.png
"""
import sys, os, json, hashlib, random, time, datetime, importlib
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# usage: run_tests.py <app.html> <out-dir> [--profiles <module>] [key-prefix ...]
# First two positionals are app and out-dir; the rest are key-prefix filters. Flags are pulled
# out first so they cannot be mistaken for either.
PROFILE_MODULE = "profiles"
_pos, _i = [], 0
_a = sys.argv[1:]
while _i < len(_a):
    if _a[_i] == "--profiles":
        PROFILE_MODULE = _a[_i + 1]; _i += 2
    else:
        _pos.append(_a[_i]); _i += 1
PF = importlib.import_module(PROFILE_MODULE)
if len(_pos) < 2:
    print(__doc__); sys.exit(1)

APP, OUT = os.path.abspath(_pos[0]), os.path.abspath(_pos[1])
ONLY = _pos[2:]
os.makedirs(os.path.join(OUT, "screens"), exist_ok=True)

RUN_JS = r"""
(spec) => {
  const BY = {}; ART_FORMS.forEach(a => BY[a.id] = a);
  const cls = (m) => {
    const saved = state.mastery; state.mastery = m; let o = null;
    try { const bc = computeClassification();
      if (bc) o = { genus: bc.genus.name, genusId: bc.genusId, regime: bc.regime.word, leans: bc.leans.slice(), early: bc.early };
    } finally { state.mastery = saved; }
    return o;
  };
  const mulberry = (a) => () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };

  state.mastery = {}; for (const [id, v] of spec.ratings) state.mastery[id] = v;
  state.discount = spec.discount; state.plantSeed = spec.seed; state.exporterName = spec.name;
  renderGrid(); setMode('profile');
  const out = { ratedCount: Object.values(state.mastery).filter(v => v > 0).length };

  // ---- app-side numbers
  out.stats = personalStats();
  out.vector = personalVector();
  out.hue = personalHue();
  try { out.flowerSVG = holotypeSVG(220); } catch (e) { out.flowerSVG = ""; out.flowerError = String(e); }
  const bc = computeClassification();
  if (bc) {
    out.classification = {
      genusId: bc.genusId, genusName: bc.genus.name, genusText: bc.genus.text,
      regimeId: bc.regimeId, regime: bc.regime, leans: bc.leans,
      leanEpithets: bc.leans.map(t => TRIBE_EPITHET[t]), leanPlain: bc.leans.map(t => TRIBE_PLAIN[t]),
      domainZ: bc.domainZ, early: bc.early, confidence: bc.confidence, earlyClustered: bc.earlyClustered,
      hhi: bc.hhi, zProcess: bc.zProcess, zSoc: bc.zSoc, zForm: bc.zForm, zRegime: bc.zRegime,
      topShare: bc.topShare, topField: bc.topField, totalWeight: bc.totalWeight,
      breadthUnproven: bc.breadthUnproven, breadthRule: bc.breadthRule,
      extra: GENUS_EXTRA[bc.genusId] || null, regimeExtra: REGIME_EXTRA[bc.regimeId],
      leanTexts: bc.leans.map(t => TRIBE_READ[t]), regimeTie: REGIME_TIE[bc.regimeId], genusBio: GENUS_BIO[bc.genus.name] || null,
    };
    try { out.plantSVG = personalPlantSVG(bc, false); } catch (e) { out.plantSVG = ""; out.plantError = String(e); }
  } else { out.classification = null; }

  // ---- what the rendered Herbarium page actually shows
  const pv = document.getElementById('profileView');
  const q = s => pv.querySelector(s), qa = s => [...pv.querySelectorAll(s)];
  const txt = e => e ? e.innerText.replace(/\s+/g, ' ').trim() : null;
  out.dom = {
    title: txt(q('.prof-title')), eyebrow: txt(q('.prof-eyebrow')), h2s: qa('h2').map(txt),
    genus: txt(q('.prof-genus')), tribe: txt(q('.prof-tribe')), mods: txt(q('.prof-mods')),
    bodyParagraphs: qa('.prof-growth-body p').map(txt),
    fieldNotes: qa('.prof-fieldnotes dt').map(dt => [txt(dt), txt(dt.nextElementSibling)]),
    earlyNote: txt(q('.prof-early-note-line')),
    axisBars: qa('.prof-axisbar-row').map(r => ({ lo: txt(r.querySelector('.prof-axisbar-pole.lo')), hi: txt(r.querySelector('.prof-axisbar-pole.hi')),
      markerLeft: r.querySelector('.prof-axisbar-marker') ? r.querySelector('.prof-axisbar-marker').style.left : null, reading: txt(r.querySelector('.prof-axisbar-val')) })),
    ratedRows: qa('.prof-table:not(.prof-table-unexplored) tbody tr').map(tr => [...tr.children].map(txt)),
    unexploredRows: qa('.prof-table-unexplored tbody tr').map(tr => [...tr.children].map(txt)),
    pageTextIfNoClassification: bc ? null : txt(q('.prof-main')),
    sortLabel: (typeof SORT_LABELS !== 'undefined' && SORT_LABELS[ui.sort]) || ui.sort,
  };
  out.dom.unexploredCount = out.dom.unexploredRows.length; out.dom.ratedRowCount = out.dom.ratedRows.length;
  out.dom.unexploredFirst15 = out.dom.unexploredRows.slice(0, 15); out.dom.unexploredLast15 = out.dom.unexploredRows.slice(-15);
  delete out.dom.unexploredRows;

  // ---- novelty for every unrated art form, as the app computes it
  const nv = computeNovelty(state.mastery, state.discount);
  const isRated = id => state.mastery[id] > 0;
  const unrated = ART_FORMS.filter(a => !isRated(a.id)).map(a => { const r = nv.byId[a.id];
    return { id: a.id, name: a.name, category: a.category, score: r.score, tier: r.tier, promoted: r.promoted, nearest: r.nearestId ? BY[r.nearestId].name : null }; });
  unrated.sort((a, b) => a.score - b.score || a.name.localeCompare(b.name));
  const tiers = {}, bins = new Array(10).fill(0);
  unrated.forEach(u => { tiers[u.tier] = (tiers[u.tier] || 0) + 1; bins[Math.min(9, Math.floor((u.score - 1) / 10))]++; });
  const scores = unrated.map(u => u.score);
  out.novelty = { unratedCount: unrated.length, tierCounts: tiers, histogram10: bins,
    min: scores.length ? Math.min(...scores) : null, max: scores.length ? Math.max(...scores) : null,
    mean: scores.length ? scores.reduce((s, x) => s + x, 0) / scores.length : null,
    median: scores.length ? scores[Math.floor(scores.length / 2)] : null,
    closest15: unrated.slice(0, 15), farthest15: unrated.slice(-15).reverse(), all: unrated };

  // ---- stability: drop each rating in turn, and jitter all ratings by -1/0/+1 (seeded)
  const ids = Object.keys(state.mastery).filter(isRated);
  out.leaveOneOut = []; out.jitter = [];
  if (ids.length) {
    for (const id of ids) { const m = Object.assign({}, state.mastery); delete m[id]; out.leaveOneOut.push(Object.assign({ dropped: BY[id].name }, cls(m))); }
    let h = 0; for (const c of spec.key) h = (h * 31 + c.charCodeAt(0)) | 0; const rnd = mulberry(h);
    for (let t = 0; t < 60; t++) { const m = {}; for (const id of ids) { const r = rnd(); const d = r < .25 ? -1 : r < .75 ? 0 : 1; m[id] = Math.max(1, Math.min(10, state.mastery[id] + d)); } out.jitter.push(cls(m)); }
  }

  // ---- screenshot geometry
  const top = pv.getBoundingClientRect().top + window.scrollY;
  const ab = q('.prof-axisbars'); const bottomEl = ab || q('.prof-main') || pv;
  out.clip = { top, bottom: bottomEl.getBoundingClientRect().bottom + window.scrollY };
  return out;
}
"""

APP_INFO_JS = r"""
() => ({
  n: ART_FORMS.length,
  catalog: ART_FORMS.map(a => ({ id: a.id, name: a.name, category: a.category, tag: a.tag, vector: a.vector, meta: a.meta })),
  axes: AXES, axisMean: AXIS_MEAN, axisSD: AXIS_SD, axisGroups: AXIS_GROUPS,
  genusTable: GENUS_TABLE, genusExtra: GENUS_EXTRA, genusBio: GENUS_BIO, regimeLevels: REGIME_LEVELS, regimeExtra: REGIME_EXTRA,
  tribeRead: TRIBE_READ, regimeTie: REGIME_TIE, tribeEpithet: TRIBE_EPITHET, tribePlain: TRIBE_PLAIN, domainTribe: DOMAIN_TRIBE, glossary: GLOSSARY,
  novelty: NOVELTY, tierLabels: TIER_LABELS, defaultDiscount: 0.5, defaultSort: ui.sort,
})
"""

TRACE_JS = r"""
(spec) => {
  const BY = {}; ART_FORMS.forEach(a => BY[a.id] = a);
  const steps = []; let prevKey = null; const m = {};
  state.discount = spec.discount; state.plantSeed = spec.seed;
  for (let i = 0; i < spec.ratings.length; i++) {
    const [id, v] = spec.ratings[i]; m[id] = v; state.mastery = Object.assign({}, m);
    const bc = computeClassification(); const st = personalStats();
    const key = bc ? [bc.genus.name, bc.early ? 'early' : bc.regime.word, bc.leans.join('+')].join('|') : 'none';
    const s = { n: i + 1, added: BY[id].name, rating: v, genus: bc && bc.genus.name, genusId: bc && bc.genusId, regime: bc && (bc.early ? null : bc.regime.word),
      leans: bc ? bc.leans.map(t => TRIBE_EPITHET[t]) : [], early: bc && bc.early, hhi: bc && bc.hhi, hue: personalHue(), avg: st.avgRating,
      categories: st.categoriesTouched, topCategory: st.catBreakdown[0] && st.catBreakdown[0].category,
      tribe: bc && GENUS_EXTRA[bc.genusId] && GENUS_EXTRA[bc.genusId].tribe, keyframe: key !== prevKey };
    if (s.keyframe && bc) { try { s.plantSVG = personalPlantSVG(bc, false); } catch (e) {} }
    prevKey = key; steps.push(s);
  }
  return steps;
}
"""

DET_JS = r"""
(spec) => {
  const mulberry = (a) => () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  const hash = s => { let h = 5381; for (let i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) | 0; return (h >>> 0).toString(16); };
  const snap = () => { const bc = computeClassification(); const nv = computeNovelty(state.mastery, state.discount);
    return JSON.stringify({ bc: bc && { g: bc.genusId, r: bc.regimeId, l: bc.leans, z: [bc.zProcess, bc.zSoc, bc.zForm, bc.zRegime, bc.hhi] }, st: personalStats(), pv: personalVector(), hue: personalHue(),
      nv: ART_FORMS.map(a => nv.byId[a.id].score), flower: holotypeSVG(220), plant: bc ? personalPlantSVG(bc, false) : '' }); };
  state.discount = spec.discount; state.plantSeed = spec.seed;
  const out = { orders: [], repeat: null, seeds: [] };
  const base = spec.ratings.slice(); let first = null;
  for (let k = 0; k < 6; k++) {
    const arr = base.slice(); if (k > 0) { const r = mulberry(1000 + k); for (let i = arr.length - 1; i > 0; i--) { const j = Math.floor(r() * (i + 1)); [arr[i], arr[j]] = [arr[j], arr[i]]; } }
    state.mastery = {}; arr.forEach(([id, v]) => state.mastery[id] = v);
    const h = hash(snap()); if (k === 0) first = h; out.orders.push({ order: k === 0 ? 'as listed' : 'shuffle ' + k, firstThree: arr.slice(0, 3).map(x => x[0]), hash: h, sameAsFirst: h === first });
  }
  state.mastery = {}; base.forEach(([id, v]) => state.mastery[id] = v);
  const a = snap(), b = snap(); out.repeat = { hashA: hash(a), hashB: hash(b), same: a === b };
  for (const s of spec.seeds) { state.plantSeed = s; const bc = computeClassification();
    const svg = personalPlantSVG(bc, false); out.seeds.push({ seed: s, hash: hash(svg), svg, flowerHash: hash(holotypeSVG(220)) }); }
  return out;
}
"""

def resolve(catalog):
    names = [(c["id"], c["name"]) for c in catalog]
    def f(q):
        ql = q.lower()
        ex = [i for i, n in names if n.lower() == ql]
        if len(ex) == 1: return ex[0]
        pre = [i for i, n in names if n.lower().startswith(ql)]
        if len(pre) == 1: return pre[0]
        sub = [i for i, n in names if ql in n.lower()]
        if len(sub) == 1: return sub[0]
        raise SystemExit(f"cannot resolve art form {q!r}: exact={ex} prefix={pre} substring={sub}")
    return f

def spec_for(p, catalog, res):
    if p["ratings"] == "ALL":
        if p["all_random_seed"] is not None:
            r = random.Random(p["all_random_seed"]); ratings = [(c["id"], r.randint(1, 10), None) for c in catalog]
        else:
            ratings = [(c["id"], p["all_value"], None) for c in catalog]
    else:
        ratings = [(res(t[0]), t[1], t[2] if len(t) > 2 else None) for t in p["ratings"]]
    return dict(key=p["key"], ratings=[[i, v] for i, v, _ in ratings], notes={i: n for i, v, n in ratings if n},
                discount=p["discount"], seed="t-" + p["key"], name=p["name"])

def open_page(pw_browser, w=1440, h=2600):
    pg = pw_browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
    errs = []
    pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errs.append("console.error: " + m.text) if m.type == "error" and "403" not in m.text else None)
    pg.goto("file://" + APP); pg.wait_for_timeout(500)
    return pg, errs

def main():
    t0 = time.time()
    data = { "generatedAt": datetime.datetime.now().isoformat(timespec="seconds"),
             "appFile": os.path.basename(APP), "appBytes": os.path.getsize(APP), "appSha256": hashlib.sha256(open(APP, "rb").read()).hexdigest(),
             "ratingScale": {"1": "tried once or twice, or as a kid", "3": "casual / occasional dabbling", "5": "working hobbyist", "7": "quite good, serious hobbyist / semi-pro", "10": "professional-level mastery"},
             "statsNote": PF.STATS_NOTE, "groups": PF.GROUPS, "profileModule": PROFILE_MODULE,
             "profiles": [], "traces": [], "determinism": None }
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg, _ = open_page(br); info = pg.evaluate(APP_INFO_JS); pg.close()
        data["app"] = info
        res = resolve(info["catalog"])
        todo = [p for p in PF.PROFILES if not ONLY or any(p["key"].startswith(o) for o in ONLY)]
        for n, p in enumerate(todo, 1):
            spec = spec_for(p, info["catalog"], res)
            pg, errs = open_page(br)
            r = pg.evaluate(RUN_JS, spec)
            clip = r.pop("clip"); top = max(0, clip["top"] - 8); h = min(2500, max(300, clip["bottom"] - top + 16))
            shot = os.path.join(OUT, "screens", p["key"] + ".png")
            pg.screenshot(path=shot, clip={"x": 0, "y": top, "width": 1440, "height": h})
            pg.close()
            rec = {k: p[k] for k in ("key", "group", "title", "who", "basis", "mapping", "discount", "name")}
            rec["exporterName"] = p["name"]; rec["plantSeed"] = spec["seed"]
            rec["inputs"] = [{"id": i, "name": next(c["name"] for c in info["catalog"] if c["id"] == i), "category": next(c["category"] for c in info["catalog"] if c["id"] == i),
                              "rating": v, "note": spec["notes"].get(i)} for i, v in spec["ratings"]] if p["ratings"] != "ALL" else None
            rec["inputSummary"] = (f"all {len(spec['ratings'])} art forms rated " + (f"with a seeded random 1-10 (seed {p['all_random_seed']})" if p["all_random_seed"] is not None else str(p["all_value"]))) if p["ratings"] == "ALL" else None
            rec["result"] = r; rec["errors"] = errs; rec["screenshot"] = "screens/" + p["key"] + ".png"
            data["profiles"].append(rec)
            print(f"[{n}/{len(todo)}] {p['key']}: {r['ratedCount']} rated -> " + (f"{r['classification']['genusName']}" if r["classification"] else "no classification") + (f"  ERR {errs}" if errs else ""), flush=True)

        by_key = {p["key"]: p for p in PF.PROFILES}
        if not ONLY:
            for k in PF.TRACE_PROFILES:
                p = by_key[k]; spec = spec_for(p, info["catalog"], res)
                pg, _ = open_page(br); steps = pg.evaluate(TRACE_JS, spec); pg.close()
                data["traces"].append({"key": k, "title": p["title"], "steps": steps})
            p = by_key[getattr(PF, "DET_KEY", "A01_singer_multi_instrument")]; spec = spec_for(p, info["catalog"], res)
            spec["seeds"] = ["seed-1", "seed-2", "seed-3", "seed-4", "seed-5", "seed-6", "seed-7", "seed-8"]
            pg, _ = open_page(br); data["determinism"] = pg.evaluate(DET_JS, spec); data["determinism"]["profile"] = p["key"]; pg.close()
        br.close()
    data["elapsedSeconds"] = round(time.time() - t0, 1)
    json.dump(data, open(os.path.join(OUT, "data.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print("done", data["elapsedSeconds"], "s;", len(data["profiles"]), "profiles")

main()
