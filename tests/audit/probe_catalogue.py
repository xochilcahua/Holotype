# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Is the catalogue a fair map? Facts about its shape, from the app's own DIST matrix.

usage (repository root):  python3 tests/audit/probe_catalogue.py
writes out/audit/catalogue.json and prints the summary. Changes nothing, judges nothing.

Reports: forms per category; mean distance from each category to the rest of the catalogue;
forms whose nearest neighbour is in another category (with the neighbour); the 15 most isolated
forms (largest distance to their nearest neighbour); the 10 closest pairs (possible duplicates).
"""
import json, pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
JS = """() => {
  const N = ART_FORMS.length, cats = {};
  ART_FORMS.forEach((a, i) => (cats[a.category] = cats[a.category] || []).push(i));
  const nn = ART_FORMS.map((a, i) => { let b = -1, d = 9; for (let j = 0; j < N; j++) if (j !== i && DIST[i][j] < d) { d = DIST[i][j]; b = j; } return { i, b, d }; });
  const catMean = {};
  for (const [c, idx] of Object.entries(cats)) {
    let s = 0, n = 0; for (const i of idx) for (let j = 0; j < N; j++) if (ART_FORMS[j].category !== c) { s += DIST[i][j]; n++; }
    catMean[c] = { forms: idx.length, mean_dist_to_rest: +(s / n).toFixed(3) };
  }
  const cross = nn.filter(x => ART_FORMS[x.i].category !== ART_FORMS[x.b].category)
                  .map(x => [ART_FORMS[x.i].name, ART_FORMS[x.b].name, ART_FORMS[x.i].category, ART_FORMS[x.b].category, +x.d.toFixed(3)]);
  const isolated = nn.slice().sort((p, q) => q.d - p.d).slice(0, 15).map(x => [ART_FORMS[x.i].name, ART_FORMS[x.b].name, +x.d.toFixed(3)]);
  const pairs = []; for (let i = 0; i < N; i++) for (let j = i + 1; j < N; j++) pairs.push([DIST[i][j], i, j]);
  pairs.sort((p, q) => p[0] - q[0]);
  const closest = pairs.slice(0, 10).map(([d, i, j]) => [ART_FORMS[i].name, ART_FORMS[j].name, +d.toFixed(4)]);
  return { forms: N, catMean, cross_category_nearest: cross, most_isolated: isolated, closest_pairs: closest };
}"""
with sync_playwright() as pw:
    br = pw.chromium.launch(); pg = br.new_page()
    pg.goto((ROOT / "index.html").as_uri()); pg.wait_for_timeout(1000)
    r = pg.evaluate(JS); br.close()
p = ROOT / "out" / "audit"; p.mkdir(parents=True, exist_ok=True)
(p / "catalogue.json").write_text(json.dumps(r, indent=1), encoding="utf-8")
print("forms:", r["forms"])
print("\nCATEGORIES (forms, mean distance to the rest; higher = more apart from everything else)")
for c, v in sorted(r["catMean"].items(), key=lambda kv: -kv[1]["mean_dist_to_rest"]):
    print("  %-26s %3d forms   %.3f" % (c, v["forms"], v["mean_dist_to_rest"]))
print("\nFORMS WHOSE NEAREST NEIGHBOUR IS IN ANOTHER CATEGORY: %d" % len(r["cross_category_nearest"]))
for x in r["cross_category_nearest"]: print("  %-38s -> %-34s (%s -> %s) %.3f" % (x[0], x[1], x[2], x[3], x[4]))
print("\n15 MOST ISOLATED (largest distance to nearest neighbour)")
for x in r["most_isolated"]: print("  %-38s nearest %-34s %.3f" % tuple(x))
print("\n10 CLOSEST PAIRS (possible duplicates)")
for x in r["closest_pairs"]: print("  %-34s %-34s %.4f" % tuple(x))
print("\nwrote out/audit/catalogue.json")
