# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""How does 'how new would this be to me' behave as ratings are added?

Calls the app's own computeNovelty(mastery, discount) in a headless browser; re-implements
nothing. Four parts, all numbers, no verdicts:
  A  invariants      properties that must always hold (any violation is a finding)
  (the 'resolution' figures in B and C show how many forms sit at the displayed ceiling of 100,
   and how much the underlying raw value, which the sort actually uses, differs among them)
  B  scenarios       rate a few forms; where do the expected-near and expected-far forms land
  C  growth curve    three personas, ratings added one at a time; does the spread stay useful
  D  tier vs score   can a form be labelled 'uncharted' and still show a low score

usage (repository root):  python3 tests/audit/probe_novelty.py
writes out/audit/novelty.json   (exit 0 always; read the output)

RANK: position in the app's own 'furthest first' order among forms the person has NOT rated (1 = furthest).
A near form should have a HIGH rank number (close to the bottom); a far form a LOW one. Percentile is also
kept in the JSON but ties at the score ceiling make it blunt; prefer rank.
Names are exact catalogue names (docs/catalogue_names.txt). A name that is not found is printed
as UNRESOLVED, never silently substituted.
"""
import json, os, pathlib, random
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
APP = (ROOT / "index.html").as_uri()

SCENARIOS = [
    ("S1 painter", {"Painting": 8},
     ["Drawing", "Digital Painting", "Illustration"], ["Blacksmithing", "Beekeeping", "Singing"]),
    ("S2 instrumentalist", {"Playing an Instrument": 7},
     ["Singing", "Music Composition", "Songwriting"], ["Painting", "Woodworking", "Poetry"]),
    ("S3 metalworker", {"Blacksmithing": 7, "Metal Casting": 6},
     ["Jewelry Making", "Sculpture"], ["Dance", "Poetry", "Singing"]),
    ("S4 writer", {"Fiction Writing": 8, "Poetry": 6},
     ["Playwriting & Screenwriting", "Nonfiction & Journalism"], ["Blacksmithing", "DJing", "Ceramics & Pottery"]),
    ("S5 dancer", {"Dance": 8},
     ["Choreography"], ["Blacksmithing", "Poetry", "Generative Art"]),
]
GENERALIST = {"Drawing": 4, "Singing": 3, "Cooking": 5, "Woodworking": 3, "Acting": 4, "Photography": 6,
              "Ceramics & Pottery": 3, "Poetry": 4, "Gardening & Plant Cultivation": 5, "Dance": 3,
              "Playing an Instrument": 4, "Graphic Design": 3}
PERSONAS = {
 "painter": ["Painting", "Drawing", "Digital Painting", "Illustration", "Collage", "Calligraphy", "Graphic Design",
             "Photography", "Concept Art", "Caricature", "Comics", "Storyboarding", "Scratchboard", "Airbrush Art",
             "Graffiti & Street Art", "Mosaic", "Sculpture", "Body Art", "Packaging Design", "Type Design",
             "Hand-Drawn Animation", "Origami", "Papercraft", "Zine Making", "Book Carving", "Printmaking"],
 "musician": ["Playing an Instrument", "Singing", "Music Composition", "Songwriting", "Musical Improvisation",
              "Music Production", "Mixing & Mastering", "Sound Design", "Beatboxing", "DJing", "Foley Sound Effects",
              "Field Recording & Sound Maps", "Live Coding Music", "Chiptune & Demoscene Music",
              "Podcasting & Audio Storytelling", "Audio Drama & Radio Play Production", "Freestyle & Battle Rap",
              "Spoken Word & Rap", "Voice Acting", "Scat Singing", "Conducting", "Music Arranging & Orchestration"],
 "maker": ["Woodworking", "Blacksmithing", "Metal Casting", "Jewelry Making", "Ceramics & Pottery", "Leatherworking",
           "Sewing & Tailoring", "Weaving", "Furniture Design", "Stone Carving", "Instrument Making (Lutherie)",
           "Bookbinding", "Papier-Mâché", "Pyrography", "Wire Wrapping", "Scrimshaw", "Product Design",
           "Miniatures & Dioramas", "Knitting & Crochet", "Candle Making", "Glassblowing", "Quilting", "Embroidery",
           "Resin Art", "Felting", "Macrame"],
}
LADDER_RATINGS = [8, 7, 7, 6, 6, 5, 5, 5, 4, 4, 4, 3, 3, 3, 3, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1]
STEPS = [1, 3, 5, 10, 15, 25]

JS = r"""
(a) => {
  const byName = new Map(ART_FORMS.map(f => [f.name, f.id]));
  const ids = ART_FORMS.map(f => f.id);
  const idOf = n => byName.get(n);
  const asMastery = obj => { const m = {}; for (const [n, v] of Object.entries(obj)) { const i = idOf(n); if (i) m[i] = v; } return m; };
  const run = (m, d = 0.5) => computeNovelty(m, d);
  const out = { unresolved: [], A: {}, B: [], C: {}, D: {} };
  const note = n => { if (!idOf(n) && !out.unresolved.includes(n)) out.unresolved.push(n); };
  const pct = (res, m, id) => {            // percentile among unrated, 0 familiar .. 100 new
    const un = ids.filter(i => !(i in m)); const s = res.byId[id].score;
    return Math.round(100 * un.filter(i => res.byId[i].score < s).length / (un.length - 1));
  };
  const stats = (res, m) => {
    const un = ids.filter(i => !(i in m)); const sc = un.map(i => res.byId[i].score).sort((x, y) => x - y);
    const q = p => sc[Math.min(sc.length - 1, Math.floor(p * (sc.length - 1)))];
    const tiers = {}; un.forEach(i => { const t = res.byId[i].tier; tiers[t] = (tiers[t] || 0) + 1; });
    const top = un.filter(i => res.byId[i].score === 100), rw = top.map(i => res.byId[i].raw);
    const resolution = { at_100: top.length, raw_min: top.length ? +Math.min(...rw).toFixed(5) : null,
      raw_max: top.length ? +Math.max(...rw).toFixed(5) : null, distinct_raw_at_1e3: new Set(rw.map(x => x.toFixed(3))).size,
      distinct_raw_at_1e6: new Set(rw.map(x => x.toFixed(6))).size };
    return { resolution, unrated: un.length, median: q(.5), q1: q(.25), q3: q(.75), iqr: q(.75) - q(.25), min: sc[0], max: sc[sc.length - 1],
             tiers, promoted: un.filter(i => res.byId[i].promoted).length };
  };

  // ---------- A. invariants over random states ----------
  let seed = a.seed; const rnd = () => (seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff;
  const viol = { I1: [], I2: [], I3: [], I4: [], I5_up: 0, I5_down: 0, I6: [] };
  const N = a.nstates;
  for (let t = 0; t < N; t++) {
    const k = 1 + Math.floor(rnd() * 30); const m = {};
    while (Object.keys(m).length < k) m[ids[Math.floor(rnd() * ids.length)]] = 1 + Math.floor(rnd() * 10);
    const r0 = run(m);
    for (const i of Object.keys(m)) {                                     // I1 rated form score
      const want = Math.max(1, Math.round((10 - m[i]) * 10));
      if (r0.byId[i].score !== want) viol.I1.push({ id: i, got: r0.byId[i].score, want });
    }
    for (const i of ids) { const s = r0.byId[i].score; if (!Number.isInteger(s) || s < 1 || s > 100) viol.I2.push({ id: i, s }); }
    const some = Object.keys(m)[0];                                        // I3 raise one rating
    if (m[some] < 10) {
      const m2 = { ...m, [some]: m[some] + 1 }; const r2 = run(m2);
      for (const i of ids) if (!(i in m) && r2.byId[i].raw > r0.byId[i].raw + 1e-9) viol.I3.push({ id: i, before: r0.byId[i].raw, after: r2.byId[i].raw });
    }
    const extra = ids.filter(i => !(i in m))[Math.floor(rnd() * (ids.length - k))];   // I4 add a rated form
    const m3 = { ...m, [extra]: 1 + Math.floor(rnd() * 10) }; const r3 = run(m3);
    for (const i of ids) if (!(i in m3) && r3.byId[i].raw > r0.byId[i].raw + 1e-9) viol.I4.push({ id: i, before: r0.byId[i].raw, after: r3.byId[i].raw });
    const rA = run(m, 0), rB = run(m, 1);                                  // I5 reach slider direction
    let up = 0, down = 0;
    for (const i of ids) if (!(i in m)) { if (rB.byId[i].raw > rA.byId[i].raw + 1e-9) up++; if (rB.byId[i].raw < rA.byId[i].raw - 1e-9) down++; }
    if (up) viol.I5_up++; if (down) viol.I5_down++;
    const r6 = run(m); for (const i of ids) if (r6.byId[i].score !== r0.byId[i].score) { viol.I6.push(i); break; }
  }
  out.A = { states: N, I1_violations: viol.I1.length, I2_violations: viol.I2.length, I3_violations: viol.I3.length,
            I4_violations: viol.I4.length, I5_states_where_some_form_rose_when_reach_0_to_1: viol.I5_up,
            I5_states_where_some_form_fell_when_reach_0_to_1: viol.I5_down, I6_nondeterministic_states: viol.I6.length,
            examples: { I1: viol.I1.slice(0, 3), I3: viol.I3.slice(0, 3), I4: viol.I4.slice(0, 3) } };

  // ---------- B. scenarios ----------
  for (const [label, rated, near, far] of a.scenarios) {
    Object.keys(rated).concat(near, far).forEach(note);
    const m = asMastery(rated), res = run(m);
    const row = { label, rated, near: {}, far: {}, stats: stats(res, m) };
    const info = n => { const i = idOf(n); return i ? { pct: pct(res, m, i), score: res.byId[i].score, tier: res.byId[i].tier,
                          rank: res.order.indexOf(i) + 1, of: res.order.length } : 'UNRESOLVED'; };
    near.forEach(n => { row.near[n] = info(n); });
    far.forEach(n => { row.far[n] = info(n); });
    out.B.push(row);
  }
  { const m = asMastery(a.generalist); Object.keys(a.generalist).forEach(note); out.B.push({ label: 'S6 generalist', stats: stats(run(m), m) }); }

  // ---------- C. growth curve ----------
  for (const [pname, names] of Object.entries(a.personas)) {
    const found = names.filter(n => idOf(n)); names.filter(n => !idOf(n)).forEach(note);
    const seq = found.slice(0, 25), rows = {}; const m = {};
    seq.forEach((n, idx) => {
      m[idOf(n)] = a.ladder[idx];
      if (a.steps.includes(idx + 1)) {
        const s = stats(run(m), m); const top = Math.max(...Object.values(s.tiers)) / s.unrated;
        rows[idx + 1] = { ...s, top_tier_share: +top.toFixed(2), flag_one_tier_over_60pct: top > 0.6, flag_iqr_under_10: s.iqr < 10 };
      }
    });
    out.C[pname] = { forms_used: seq.length, rows };
  }

  // ---------- D. tier vs score ----------
  {
    let uncharted_low = 0, total = 0, promotedScores = [], examples = [];
    for (const pname of Object.keys(a.personas)) {
      const found = a.personas[pname].filter(n => idOf(n)).slice(0, 25); const m = {};
      found.forEach((n, idx) => {
        m[idOf(n)] = a.ladder[idx];
        if ([5, 10, 25].includes(idx + 1)) {
          const res = run(m);
          for (const i of ids) if (!(i in m)) {
            total++; const r = res.byId[i];
            if (r.tier === 'uncharted' && r.score <= 70) { uncharted_low++; if (r.promoted) promotedScores.push(r.score); if (examples.length < 3) examples.push({ persona: pname, n: idx + 1, id: i, score: r.score, promoted: r.promoted }); }
          }
        }
      });
    }
    out.D = { unrated_checked: total, uncharted_with_score_70_or_less: uncharted_low,
              promoted_among_them: promotedScores.length, promoted_score_min: Math.min(...promotedScores, 999), promoted_score_max: Math.max(...promotedScores, -1), examples };
  }
  return out;
}
"""

def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(); pg = br.new_page()
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(APP); pg.wait_for_timeout(1000)
        res = pg.evaluate(JS, {"seed": 11, "nstates": 40, "scenarios": SCENARIOS, "generalist": GENERALIST,
                               "personas": PERSONAS, "ladder": LADDER_RATINGS, "steps": STEPS})
        br.close()
    res["page_errors"] = errs[:3]
    (ROOT / "out" / "audit").mkdir(parents=True, exist_ok=True)
    (ROOT / "out" / "audit" / "novelty.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print("page errors:", errs[:3] or "none")
    print("UNRESOLVED names:", res["unresolved"] or "none")
    print("\nA. INVARIANTS (%d random states)" % res["A"]["states"])
    for k, v in res["A"].items():
        if k not in ("states", "examples"): print("  %-62s %s" % (k, v))
    if any(res["A"]["examples"].values()): print("  examples:", json.dumps(res["A"]["examples"])[:400])
    print("\nB. SCENARIOS (rank in the app furthest-first order; near forms should have a high rank number, far forms a low one)")
    for r in res["B"]:
        s = r["stats"]
        print("  %-20s median %s IQR %s min %s max %s tiers %s resolution %s" % (r["label"], s["median"], s["iqr"], s["min"], s["max"], s["tiers"], s["resolution"]))
        for kind in ("near", "far"):
            if kind in r: print("      %-4s %s" % (kind, {n: (v if isinstance(v, str) else "rank %d of %d (1 = furthest by the sort), score %d, %s" % (v["rank"], v["of"], v["score"], v["tier"])) for n, v in r[kind].items()}))
    print("\nC. GROWTH CURVE")
    for p, d in res["C"].items():
        print("  %s (%d forms)" % (p, d["forms_used"]))
        for n, s in d["rows"].items():
            print("    n=%-3s median %-3s IQR %-3s tiers %s promoted %s top_tier_share %s resolution %s%s%s"
                  % (n, s["median"], s["iqr"], s["tiers"], s["promoted"], s["top_tier_share"], s["resolution"],
                     "  FLAG one tier >60%" if s["flag_one_tier_over_60pct"] else "", "  FLAG IQR<10" if s["flag_iqr_under_10"] else ""))
    print("\nD. TIER vs SCORE:", json.dumps(res["D"]))
    print("\nwrote out/audit/novelty.json")

if __name__ == "__main__":
    main()
