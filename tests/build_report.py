# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""
Turns out/data.json into the compiled documents. Pure formatting: no interpretation.
usage: python3 build_report.py <out-dir-with-data.json> <destination-dir>
writes: Holotype_profile_test_report.html, Holotype_profile_definitions.md, holotype_profile_test_index.csv, holotype_profile_test_data.json
"""
import sys, os, json, csv, io, base64, html, shutil
from collections import Counter
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import profiles as PF

SRC = os.path.abspath(sys.argv[1]); DST = os.path.abspath(sys.argv[2]); os.makedirs(DST, exist_ok=True)
D = json.load(open(os.path.join(SRC, "data.json"), encoding="utf-8"))
E = html.escape
TL = D["app"].get("tierLabels", {})
SOURCES = [
  ("NEA, Arts Participation Patterns in 2022: Highlights from the Survey of Public Participation in the Arts", "https://www.arts.gov/sites/default/files/2022-SPPA-final.pdf"),
  ("NEA / NASERC, Indicator B.3: Who Is Personally Creating or Performing Art? (2022 data)", "https://arts.gov/sites/default/files/b3-report-202403.pdf"),
  ("NEA Quick Study, 19 October 2023 (2022 survey, art forms and trends)", "https://www.arts.gov/stories/research-quick-study/quick-study-october-19-2023"),
  ("NEA 2017 SPPA summary as reported by the Arizona Commission on the Arts (home / place-of-worship figures)", "https://azarts.gov/news/nea-reports-on-national-survey-of-public-participation-in-the-arts/"),
  ("YouGov, Young Americans increasingly exposed to music (3,000 US adults, instrument experience)", "https://yougov.com/en-us/articles/43512-young-americans-increasingly-exposed-music"),
  ("Baylor University alumni piano-study questionnaire (564 respondents; small, non-representative)", "https://www.proquest.com/docview/304275764/abstract/6C27B7E9B2ED4063PQ/1"),
]

def leanset(c): return " et ".join(c["leanEpithets"]) if c and c["leanEpithets"] else "none"
def var_of(c): return "indeterminata" if (c and c["early"]) else (c["regime"]["word"] if c else "-")
def summarize(lst):
    n = len(lst); g = Counter(); r = Counter(); l = Counter(); early = 0; none = 0
    for x in lst:
        if x is None or "genus" not in x: none += 1; continue
        g[x["genus"]] += 1; r[x["regime"] if not x["early"] else "indeterminata"] += 1; l[" et ".join(x["leans"]) or "none"] += 1; early += bool(x["early"])
    return dict(n=n, genus=g.most_common(), regime=r.most_common(), leans=l.most_common(), early=early, noClassification=none)
def fmt_counts(cs): return ", ".join(f"{k} {v}" for k, v in cs) if cs else "-"
def f2(x, d=2): return "-" if x is None else f"{x:.{d}f}"

# ------------------------------------------------------------------------------------------------ csv
def build_csv():
    tiers = sorted({t for p in D["profiles"] for t in p["result"]["novelty"]["tierCounts"]})
    cols = ["key", "group", "title", "rated", "avg_rating", "categories_touched", "top_category", "top_category_share", "hhi", "genus", "genus_id", "tribe", "var", "cf", "early",
            "early_clustered", "z_process", "z_soc", "z_form", "z_regime", "unrated", "novelty_mean", "novelty_median", "novelty_min", "novelty_max"] + [f"tier_{t}" for t in tiers] + \
           ["dropone_runs", "dropone_same_genus", "dropone_distinct_genera", "jitter_runs", "jitter_same_genus", "jitter_distinct_genera", "jitter_modal_genus", "reach", "plant_seed", "exporter_name"]
    out = io.StringIO(); w = csv.writer(out); w.writerow(cols)
    for p in D["profiles"]:
        r = p["result"]; c = r["classification"]; st = r["stats"]; nv = r["novelty"]; top = st["catBreakdown"][0] if st["catBreakdown"] else None
        lo = summarize(r["leaveOneOut"]); ji = summarize(r["jitter"]); gname = c["genusName"] if c else None
        same = lambda s: dict(s["genus"]).get(gname, 0) if gname else ""
        w.writerow([p["key"], p["group"], p["title"], r["ratedCount"], f2(st["avgRating"]), st["categoriesTouched"], top["category"] if top else "", f2(top["pct"] if top else None, 3),
                    f2(c["hhi"], 3) if c else "", gname or "", c["genusId"] if c else "", (c["extra"] or {}).get("tribe", "") if c else "", var_of(c) if c else "", leanset(c) if c else "",
                    c["early"] if c else "", c["earlyClustered"] if c else "", f2(c["zProcess"]) if c else "", f2(c["zSoc"]) if c else "", f2(c["zForm"]) if c else "", f2(c["zRegime"]) if c else "",
                    nv["unratedCount"], f2(nv["mean"], 1), nv["median"] if nv["median"] is not None else "", nv["min"] if nv["min"] is not None else "", nv["max"] if nv["max"] is not None else ""] +
                   [nv["tierCounts"].get(t, 0) for t in tiers] +
                   [lo["n"], same(lo), len(lo["genus"]), ji["n"], same(ji), len(ji["genus"]), ji["genus"][0][0] if ji["genus"] else "", p["discount"], p["plantSeed"], p["exporterName"]])
    open(os.path.join(DST, "holotype_profile_test_index.csv"), "w", encoding="utf-8", newline="").write(out.getvalue())

# ------------------------------------------------------------------------------------------------ markdown definitions
def build_md():
    L = ["# Holotype profile test set: definitions (inputs only)", "",
         f"Generated {D['generatedAt']} against `{D['appFile']}` (sha256 `{D['appSha256'][:16]}…`, {D['appBytes']:,} bytes). {len(D['profiles'])} profiles.", "",
         "This document lists what was fed into the app. Outputs are in `Holotype_profile_test_report.html` and `holotype_profile_test_data.json`. Nothing here is analysis.", "",
         "## Rating scale used (the app's own definition)", ""]
    L += [f"- **{k}** = {v}" for k, v in D["ratingScale"].items()]
    L += ["", "## How the profiles were built", "",
          "- Ratings are on the app's 1-10 scale. Values were assigned by the profile author using the app's own scale definition above; the statistics below inform *which* activities are common and how they tend to co-occur, not the specific numbers.",
          "- The app's catalog has one generic item for many real-world activities (for example a single 'Playing an Instrument', 'Dance', 'Photography'). Where a real-life persona does several of these, the mapping is stated in the profile.",
          "- Every profile starts from a blank state: no color tags, default sort, default reach 0.5 unless stated, a fixed plant seed `t-<key>`, and a blank exporter name unless stated.", "",
          "## Statistical basis", "", D["statsNote"], "", "Sources:", ""]
    L += [f"- {t}: {u}" for t, u in SOURCES]
    for gk, gname in D["groups"]:
        L += ["", f"## {gk}. {gname}", ""]
        for p in [x for x in D["profiles"] if x["group"] == gk]:
            L += [f"### {p['key']}: {p['title']}", "", f"- **Who:** {p['who']}", f"- **Basis / purpose:** {p['basis']}"]
            if p["mapping"]: L.append(f"- **Mapping notes:** {p['mapping']}")
            L.append(f"- **Settings:** reach {p['discount']}, plant seed `{p['plantSeed']}`, exporter name {p['exporterName']!r}")
            if p["inputs"] is None: L.append(f"- **Ratings:** {p['inputSummary']}")
            else:
                L.append(f"- **Ratings ({len(p['inputs'])}):**")
                for i in p["inputs"]: L.append(f"    - {i['name']} ({i['category']}): **{i['rating']}**" + (f" - {i['note']}" if i['note'] else ""))
            L.append("")
    for t in D["traces"]:
        L += [f"## Evolution trace input: {t['key']}", "", "Ratings added one at a time in this order: " + "; ".join(f"{s['added']} {s['rating']}" for s in t["steps"]), ""]
    open(os.path.join(DST, "Holotype_profile_definitions.md"), "w", encoding="utf-8").write("\n".join(L))

# ------------------------------------------------------------------------------------------------ html
CSS = """
:root{--ink:#22303A;--ink2:#56606a;--ink3:#8a929a;--paper:#F6F3EC;--card:#FDFBF6;--line:#DAD3C2;--acc:#A5583F;--ink-2:#44515A;--ink-3:#666C6C;--line-2:#BDB599;--surface:#FDFBF6;--edge:#23303A;--f-slate:#2A4359;--f-terra:#C8472F;--f-ochre:#DDA62F;--f-forest:#4A6340;--font-display:'Josefin Sans',system-ui,sans-serif;--font-ui:Georgia,serif}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.55 Georgia,'Times New Roman',serif}
.wrap{max-width:1180px;margin:0 auto;padding:32px 28px 80px}
h1{font:700 30px/1.2 system-ui,sans-serif;margin:0 0 6px}h2{font:700 21px system-ui,sans-serif;margin:46px 0 12px;padding-top:18px;border-top:2px solid var(--ink)}
h3{font:700 16px system-ui,sans-serif;margin:0}h4{font:700 11px system-ui,sans-serif;letter-spacing:.12em;text-transform:uppercase;color:var(--ink3);margin:18px 0 6px}
small,.muted{color:var(--ink3)}code{font:12.5px ui-monospace,Menlo,monospace;background:#ece7da;padding:1px 5px;border-radius:3px}
.lede{max-width:78ch;color:var(--ink2)}a{color:var(--acc)}
.idx{columns:2 460px;column-gap:36px;padding-left:0;list-style:none;font:13px/1.5 system-ui,sans-serif}.idx li{break-inside:avoid;margin:0 0 5px}.idx b{font-weight:600}
.card{background:var(--card);border:1px solid var(--line);border-radius:6px;margin:22px 0;padding:22px 24px;box-shadow:0 1px 0 rgba(0,0,0,.02)}
.card>header{display:flex;flex-wrap:wrap;gap:4px 14px;align-items:baseline;border-bottom:1px solid var(--line);padding-bottom:10px;margin-bottom:12px}
.card>header .key{font:12px ui-monospace,Menlo,monospace;color:var(--ink3)}
.cols{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.15fr);gap:6px 34px}@media(max-width:900px){.cols{grid-template-columns:1fr}}
.chips{display:flex;flex-wrap:wrap;gap:5px}.chip{font:12.5px system-ui,sans-serif;background:#efeade;border:1px solid var(--line);border-radius:12px;padding:2px 9px;white-space:nowrap}
.chip b{font-weight:700;margin-left:4px}.catl{font:600 11px system-ui,sans-serif;color:var(--ink3);margin:8px 0 3px}
dl.kv{display:grid;grid-template-columns:max-content 1fr;gap:3px 14px;margin:0;font:13.5px/1.45 system-ui,sans-serif}dl.kv dt{color:var(--ink3)}dl.kv dd{margin:0}
.vis{display:flex;flex-wrap:wrap;gap:18px;align-items:flex-start;margin:6px 0 4px}.vis .flower svg{width:210px;height:210px}
.plate{width:170px;padding:8px 8px 6px;background:#FDFBF6;border:1px solid #23303A;box-shadow:inset 0 0 0 3px #FDFBF6,inset 0 0 0 4px #BDB599;text-align:center}
.plate svg{width:100%;height:auto;display:block}.plate div{font:600 8px system-ui;letter-spacing:.28em;text-transform:uppercase;color:#6B6F70;margin-top:4px}
.bar{display:flex;align-items:center;gap:8px;font:12.5px system-ui,sans-serif;margin:2px 0}.bar .n{width:170px;flex:none}.bar .t{flex:1;height:8px;background:#ece7da;border-radius:4px;overflow:hidden}.bar .t i{display:block;height:100%}.bar .v{width:44px;text-align:right;color:var(--ink2)}
.ax{display:grid;grid-template-columns:82px 1fr 92px 138px;gap:8px;align-items:center;font:11px system-ui,sans-serif;letter-spacing:.06em;text-transform:uppercase;color:var(--ink3);margin:4px 0}
.ax .tr{position:relative;height:6px;background:#e6e0d1;border-radius:3px}.ax .tr i{position:absolute;top:-3px;width:12px;height:12px;border-radius:50%;background:var(--acc);margin-left:-6px}.ax .rd{text-transform:none;letter-spacing:0;color:var(--ink);font-size:12.5px;text-align:right}
.txt p{margin:6px 0;max-width:76ch;font-size:14.5px}.txt .genus{font:italic 700 30px Georgia,serif;color:var(--acc);margin:4px 0 0}.txt .tribe{font-style:italic;color:var(--ink2);font-size:17px;margin-bottom:2px}.txt .mods{font-size:14px;color:var(--ink2);margin-bottom:6px}
.fn{font:13px/1.45 system-ui,sans-serif;margin:8px 0}.fn b{color:var(--ink3);font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;margin-right:6px}
.hist{display:flex;gap:2px;align-items:flex-end;height:44px;margin:4px 0 2px}.hist i{flex:1;background:#b9a988;min-height:1px}.histl{display:flex;gap:2px;font:9.5px system-ui;color:var(--ink3)}.histl span{flex:1;text-align:center}
ol.nv{margin:4px 0;padding-left:22px;font:12.5px/1.5 system-ui,sans-serif;columns:1}ol.nv li span{color:var(--ink3)}
details{margin:10px 0}summary{cursor:pointer;font:600 12.5px system-ui,sans-serif;color:var(--ink2)}details img{max-width:100%;border:1px solid var(--line);margin-top:8px}
.sm{font:12.5px/1.5 system-ui,sans-serif}.err{color:#9b2c2c}
.trace{font:12.5px/1.45 system-ui,sans-serif}.trace .st{display:grid;grid-template-columns:26px 210px 1fr;gap:4px 12px;padding:3px 0;border-bottom:1px dotted var(--line)}.trace .st.kf{background:#f4efe1}
.pl{transform-origin:0 0;stroke:var(--surface);stroke-width:.7px;stroke-opacity:1;fill-opacity:1;vector-effect:non-scaling-stroke}.pl-t{fill:var(--c1)}.pl-d{fill:var(--c2)}.pl-s{fill:var(--c3)}.heart{fill:var(--c1);stroke:none}.heart2{fill:var(--surface);stroke:none}.heart3{fill:var(--c3);stroke:none}
.thumbs{display:flex;flex-wrap:wrap;gap:12px}.thumbs figure{margin:0;font:11px system-ui;color:var(--ink3);text-align:center}.thumbs .plate{width:120px}
"""

def plate(svg, label="Plate I"):
    return f'<div class="plate">{svg}<div>{E(label)}</div></div>' if svg else ""

def img_b64(path, width=860, q=48):
    im = Image.open(path).convert("RGB")
    if im.width > width: im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "JPEG", quality=q, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()

def card(p):
    r = p["result"]; c = r["classification"]; st = r["stats"]; nv = r["novelty"]; dom = r["dom"]
    h = [f'<section class="card" id="{p["key"]}"><header><h3>{E(p["title"])}</h3><span class="key">{p["key"]}</span></header><div class="cols"><div>']
    h.append(f'<h4>Who</h4><p class="sm">{E(p["who"])}</p><h4>Basis / purpose</h4><p class="sm">{E(p["basis"])}</p>')
    if p["mapping"]: h.append(f'<h4>Mapping notes</h4><p class="sm">{E(p["mapping"])}</p>')
    h.append(f'<h4>Input ratings</h4>')
    if p["inputs"] is None: h.append(f'<p class="sm">{E(p["inputSummary"])}</p>')
    elif not p["inputs"]: h.append('<p class="sm muted">none</p>')
    else:
        bycat = {}
        for i in p["inputs"]: bycat.setdefault(i["category"], []).append(i)
        for cat, items in bycat.items():
            h.append(f'<div class="catl">{E(cat)}</div><div class="chips">' + "".join(f'<span class="chip" title="{E(i["note"] or "")}">{E(i["name"])}<b>{i["rating"]}</b></span>' for i in items) + '</div>')
        notes = [i for i in p["inputs"] if i["note"]]
        if notes: h.append('<p class="sm muted" style="margin-top:8px">' + "; ".join(f'{E(i["name"])}: {E(i["note"])}' for i in notes) + '</p>')
    h.append(f'<h4>Settings</h4><dl class="kv"><dt>Reach</dt><dd>{p["discount"]}</dd><dt>Plant seed</dt><dd><code>{E(p["plantSeed"])}</code></dd><dt>Exporter name</dt><dd>{E(p["exporterName"]) or "<span class=muted>blank</span>"}</dd></dl>')
    h.append('</div><div>')
    h.append(f'<div class="vis"><div class="flower">{r["flowerSVG"]}</div>{plate(r.get("plantSVG",""))}</div>')
    # facts
    kv = [("Rated", r["ratedCount"]), ("Average rating", f2(st["avgRating"])), ("Categories touched", st["categoriesTouched"]), ("Hue (top category)", r["hue"])]
    if c:
        kv += [("Genus", f'<i>{E(c["genusName"])}</i> &nbsp;<code>{c["genusId"]}</code>'), ("Tribe", E((c["extra"] or {}).get("tribe", "-"))), ("var.", f'<i>{E(var_of(c))}</i>' + ("" if c["early"] else f' &nbsp;({E(c["regime"]["label"])})')),
               ("cf.", (f'<i>{E(leanset(c))}</i> &nbsp;({E(" and ".join(c["leanPlain"]))})' if c["leans"] else "none")), ("Early read", ("yes" if c["early"] else "no") + (f' (all in one category: {"yes" if c["earlyClustered"] else "no"})' if c["early"] else "")),
               ("Breadth concentration (hhi)", f2(c["hhi"], 3)), ("z process / social / form / chance", f'{f2(c["zProcess"])} / {f2(c["zSoc"])} / {f2(c["zForm"])} / {f2(c["zRegime"])}'),
               ("Top domain z", ", ".join(f'{d["ax"]} {f2(d["z"])}' for d in c["domainZ"][:3]))]
    else: kv.append(("Classification", "none (no ratings)"))
    h.append('<dl class="kv">' + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in kv) + '</dl>')
    if st["catBreakdown"]:
        h.append('<h4>Category share of rating weight</h4>' + "".join(f'<div class="bar"><span class="n">{E(cb["category"])}</span><span class="t"><i style="width:{cb["pct"]*100:.1f}%;background:oklch(0.64 0.13 {cb["hue"]})"></i></span><span class="v">{cb["pct"]*100:.0f}%</span></div>' for cb in st["catBreakdown"]))
    if dom["axisBars"]:
        h.append('<h4>Axis bars as displayed</h4>' + "".join(f'<div class="ax"><span>{E(a["lo"])}</span><span class="tr"><i style="left:{a["markerLeft"]}"></i></span><span>{E(a["hi"])}</span><span class="rd">{E(a["reading"])} <small>({E(a["markerLeft"])})</small></span></div>' for a in dom["axisBars"]))
    h.append('</div></div>')
    # text
    h.append('<h4>Text as displayed in the Herbarium</h4><div class="txt">')
    if c:
        h.append(f'<div class="genus">{E(dom["genus"] or "")}</div><div class="tribe">{E(dom["tribe"] or "")}</div><div class="mods">{E(dom["mods"] or "")}</div>')
        if dom["earlyNote"]: h.append(f'<p class="muted"><i>{E(dom["earlyNote"])}</i></p>')
        h.extend(f"<p>{E(t)}</p>" for t in dom["bodyParagraphs"])
        if dom["fieldNotes"]: h.append('<div class="fn">' + " &nbsp;&middot;&nbsp; ".join(f"<b>{E(k)}</b>{E(v)}" for k, v in dom["fieldNotes"]) + '</div>')
    else: h.append(f'<p class="muted">{E(dom["pageTextIfNoClassification"] or "")}</p>')
    h.append('</div>')
    # novelty
    h.append(f'<h4>Novelty (all {nv["unratedCount"]} unrated art forms)</h4>')
    tiers = ", ".join(f'{E(TL.get(t, t))} {n}' for t, n in sorted(nv["tierCounts"].items(), key=lambda x: -x[1]))
    h.append(f'<p class="sm">Tier counts: {tiers or "-"}. Score min {nv["min"]}, median {nv["median"]}, mean {f2(nv["mean"],1)}, max {nv["max"]}.</p>')
    if nv["histogram10"] and max(nv["histogram10"]) > 0:
        m = max(nv["histogram10"]); h.append('<div class="hist">' + "".join(f'<i style="height:{v/m*100:.0f}%" title="{v}"></i>' for v in nv["histogram10"]) + '</div><div class="histl">' + "".join(f"<span>{i*10+1}-{i*10+10}</span>" for i in range(10)) + '</div>')
    if r["ratedCount"]:
        h.append('<div class="cols"><div><h4>Closest 12 (lowest score)</h4><ol class="nv">' + "".join(f'<li>{E(u["name"])} <span>· {u["score"]} · near {E(u["nearest"] or "-")}</span></li>' for u in nv["closest15"][:12]) + '</ol></div>'
                 '<div><h4>Farthest 12 (highest score)</h4><ol class="nv">' + "".join(f'<li>{E(u["name"])} <span>· {u["score"]}{" · promoted" if u["promoted"] else ""}</span></li>' for u in nv["farthest15"][:12]) + '</ol></div></div>')
        lo, ji = summarize(r["leaveOneOut"]), summarize(r["jitter"])
        h.append('<h4>Stability runs</h4><dl class="kv">'
                 f'<dt>Drop one rating ({lo["n"]} runs)</dt><dd>genus: {E(fmt_counts(lo["genus"]))}<br>var.: {E(fmt_counts(lo["regime"]))}<br>cf.: {E(fmt_counts(lo["leans"]))}<br>early reads: {lo["early"]}, no classification: {lo["noClassification"]}</dd>'
                 f'<dt>Jitter each rating -1/0/+1 ({ji["n"]} runs)</dt><dd>genus: {E(fmt_counts(ji["genus"]))}<br>var.: {E(fmt_counts(ji["regime"]))}<br>cf.: {E(fmt_counts(ji["leans"]))}</dd></dl>')
        changed = [x for x in r["leaveOneOut"] if x and "genus" in x and c and (x["genus"] != c["genusName"])]
        if changed: h.append('<p class="sm">Drop-one runs whose genus differs from the full profile: ' + "; ".join(f'without {E(x["dropped"])} → {E(x["genus"])}' for x in changed[:25]) + (f' … (+{len(changed)-25} more)' if len(changed) > 25 else '') + '</p>')
    shot = os.path.join(SRC, p["screenshot"])
    if os.path.exists(shot): h.append(f'<details><summary>Rendered page (screenshot, fallback fonts)</summary><img loading="lazy" alt="rendered Herbarium page for {E(p["key"])}" src="{img_b64(shot)}"></details>')
    if p["errors"]: h.append(f'<p class="err sm">Page errors: {E("; ".join(p["errors"]))}</p>')
    h.append('</section>')
    return "".join(h)

def build_html():
    P = D["profiles"]; app = D["app"]
    h = [f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Holotype profile test report</title><style>{CSS}</style></head><body><div class="wrap">']
    h.append(f'<h1>Holotype profile test report</h1><p class="lede">Raw results only. Generated {E(D["generatedAt"])} against <code>{E(D["appFile"])}</code> (sha256 <code>{D["appSha256"][:16]}…</code>, {D["appBytes"]:,} bytes; {app["n"]} art forms). '
             f'{len(P)} profiles, {len(D["traces"])} evolution traces, 1 determinism check. Nothing in this document is an evaluation.</p>')
    h.append('<h2>How to read a profile card</h2><div class="sm" style="max-width:86ch">'
             '<p><b>Inputs</b> are the ratings fed to the app (1-10, the app\'s own scale). <b>Outputs</b> are read from the app\'s own functions and from the rendered Herbarium page.</p>'
             '<p><b>Genus id</b> is four bits: breadth (1 = wide, concentration below 0.4), process (1 = planned), sociability (1 = collaborative), form (1 = open to interpretation). '
             '<b>hhi</b> is the concentration of rating weight across categories (1 = a single category). <b>z</b> values are how far the profile\'s weighted axis average sits from the catalog average, in catalog standard deviations. '
             '<b>var.</b> is the approach-to-chance word (<i>ordinata</i>, <i>flexilis</i>, <i>aleatoria</i>; <i>indeterminata</i> below four ratings). <b>cf.</b> lists up to two domain leans as Latin adjectives. '
             '<b>Novelty</b> is the score 1-100 the app shows for each unrated art form; tier names are the app\'s labels. <b>Stability runs</b> re-classify the profile with each rating removed in turn, and with every rating randomly moved by -1, 0 or +1 (60 seeded trials); they change nothing in the app.</p>'
             f'<p><b>Rating scale:</b> ' + "; ".join(f"{k} = {E(v)}" for k, v in D["ratingScale"].items()) + '.</p>'
             f'<p><b>Statistical basis for the common-person profiles:</b> {E(D["statsNote"])}</p><ul>' + "".join(f'<li><a href="{u}">{E(t)}</a></li>' for t, u in SOURCES) + '</ul></div>')
    h.append('<h2>Index</h2>')
    for gk, gname in D["groups"]:
        h.append(f'<h4>{gk}. {E(gname)}</h4><ul class="idx">')
        for p in [x for x in P if x["group"] == gk]:
            c = p["result"]["classification"]
            h.append(f'<li><a href="#{p["key"]}"><b>{E(p["title"])}</b></a> <span class="muted">· {p["result"]["ratedCount"]} rated · ' + (f'<i>{E(c["genusName"])}</i> var. {E(var_of(c))}' + (f' cf. {E(leanset(c))}' if c["leans"] else "") if c else "no classification") + '</span></li>')
        h.append('</ul>')
    h.append('<h4>Other sections</h4><ul class="idx"><li><a href="#traces">Evolution traces</a></li><li><a href="#determinism">Determinism checks</a></li><li><a href="#catalog">Catalog reference</a></li></ul>')
    for gk, gname in D["groups"]:
        h.append(f'<h2 id="g{gk}">{gk}. {E(gname)}</h2>')
        h.extend(card(p) for p in P if p["group"] == gk)
    # traces
    h.append('<h2 id="traces">Evolution traces</h2><p class="lede">The same ratings entered one at a time, in the listed order, with the app\'s result recorded after each addition. Shaded rows are steps where the genus, var. or cf. changed from the previous step; their plants are shown.</p>')
    for t in D["traces"]:
        h.append(f'<div class="card"><header><h3>{E(t["title"])}</h3><span class="key">{t["key"]}</span></header><div class="trace">')
        for s in t["steps"]:
            v = "indeterminata" if s["early"] else (s["regime"] or "-")
            h.append(f'<div class="st{" kf" if s["keyframe"] else ""}"><span>{s["n"]}</span><span>{E(s["added"])} <b>{s["rating"]}</b></span><span><i>{E(s["genus"] or "-")}</i> <code>{s["genusId"] or ""}</code> · var. {E(v)} · cf. {E(" et ".join(s["leans"]) or "none")} · {E(s["tribe"] or "")} · hhi {f2(s["hhi"],3)} · avg {f2(s["avg"])} · {s["categories"]} {"category" if s["categories"] == 1 else "categories"} · top {E(s["topCategory"] or "-")}</span></div>')
        h.append('</div><div class="thumbs" style="margin-top:12px">' + "".join(f'<figure>{plate(s.get("plantSVG",""), f"after {s["n"]}")}<figcaption>{E(s["genus"] or "")}</figcaption></figure>' for s in t["steps"] if s.get("plantSVG")) + '</div></div>')
    # determinism
    d = D["determinism"]
    h.append('<h2 id="determinism">Determinism checks</h2>')
    if d:
        h.append(f'<div class="card"><p class="sm">Profile <code>{d["profile"]}</code>. Each run records a hash of the classification, personal vector, statistics, hue, all novelty scores, the flower SVG and the plant SVG.</p><dl class="kv">')
        h.append('<dt>Rating order</dt><dd>' + "<br>".join(f'{E(o["order"])}: <code>{o["hash"]}</code> {"identical to first" if o["sameAsFirst"] else "DIFFERENT from first"}' for o in d["orders"]) + '</dd>')
        h.append(f'<dt>Repeat, same state</dt><dd><code>{d["repeat"]["hashA"]}</code> / <code>{d["repeat"]["hashB"]}</code>: {"identical" if d["repeat"]["same"] else "DIFFERENT"}</dd></dl>')
        h.append('<h4>Same ratings, different plant seeds</h4><div class="thumbs">' + "".join(f'<figure>{plate(s["svg"], s["seed"])}<figcaption><code>{s["hash"]}</code><br>flower <code>{s["flowerHash"]}</code></figcaption></figure>' for s in d["seeds"]) + '</div></div>')
    # catalog reference
    cats = {}
    for a in app["catalog"]: cats.setdefault(a["category"], []).append(a["name"])
    h.append('<h2 id="catalog">Catalog reference</h2><p class="lede">The art forms the app contained when the tests ran.</p>')
    for cat, names in cats.items(): h.append(f'<h4>{E(cat)} ({len(names)})</h4><p class="sm">{E(" · ".join(names))}</p>')
    h.append('</div></body></html>')
    open(os.path.join(DST, "Holotype_profile_test_report.html"), "w", encoding="utf-8").write("".join(h))

build_csv(); build_md(); build_html()
shutil.copy(os.path.join(SRC, "data.json"), os.path.join(DST, "holotype_profile_test_data.json"))
print("built", os.listdir(DST))
