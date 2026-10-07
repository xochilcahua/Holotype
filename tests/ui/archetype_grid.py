#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Render every genus archetype and audit the plant geometry.

Checks the things a screenshot alone will not tell you: whether the plant is
actually inside its own viewBox, whether petals collapse to nothing at slider
extremes, and whether the per-person detail glyph escapes the frame.

    python3 archetype_grid.py APP.html OUTDIR
"""
import os, sys, json, pathlib
from playwright.sync_api import sync_playwright

APP = os.path.abspath(sys.argv[1])
OUT = pathlib.Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)

# One profile per genus, identical in every other respect, so any silhouette
# difference between these cards is the genus taxonomy and nothing else.
GRID = """() => {
  const genera = HolotypePlant.genera;
  // A STATIC host, deliberately not position:fixed. A fixed box is viewport-height, so with
  // full_page=True the lower rows of the grid fell outside it and never appeared in the
  // screenshot, while the app's own catalogue below showed through instead. The capture now
  // clips to this element, and it grows to fit every card.
  const host = document.createElement('div');
  host.id = 'archetypeHost';
  host.style.cssText = 'position:absolute;left:0;top:0;width:1180px;z-index:9999;' +
    'background:#fff;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px;padding:8px';
  document.body.appendChild(host);
  window.__cells = [];
  for (const g of genera) {
    const cell = document.createElement('div');
    // minmax(0,1fr) above matters: plain 1fr is minmax(auto,1fr), and the unbroken params
    // JSON below has a min-content width far wider than a quarter of the host, so the tracks
    // grow and the last column falls outside the capture. overflow-wrap keeps it honest.
    cell.style.cssText = 'border:1px solid #ccc;text-align:center;font:11px sans-serif;' +
      'padding:2px;overflow-wrap:anywhere;min-width:0';
    const prof = { genus: g, seed: 'audit-seed-' + g, regime: 'ordinata',
                   domains: [], confidence: 'settled' };
    cell.innerHTML = HolotypePlant.svg(prof, {}) + '<div>' + g + '</div>' +
      '<div>' + JSON.stringify(HolotypePlant.params(prof)) + '</div>';
    host.appendChild(cell);
    window.__cells.push(cell);
  }
  window.__genera = genera;
  return { genera: genera.length, cells: window.__cells.length };
}"""

# Prove the capture is honest: once layout has settled, every card must sit inside the host's
# own painted box. Checked in a separate evaluate on purpose -- measuring in the same tick as the
# insert reads the grid's pre-layout height and reports rows as escaping that have not escaped.
ESCAPED_JS = """() => {
  const host = document.getElementById('archetypeHost');
  const hb = host.getBoundingClientRect();
  const out = window.__cells.filter(c => {
    const r = c.getBoundingClientRect();
    return r.bottom > hb.bottom + 1 || r.right > hb.right + 1;
  }).map(c => c.textContent.trim().split('\\n')[0]);
  return { hostH: Math.round(hb.height), cells: window.__cells.length, escaped: out };
}"""

# Is any drawn geometry outside the SVG's own viewBox?
FIT_JS = """() => {
  const out = [];
  for (const cell of window.__cells) {
    const svg = cell.querySelector('svg');
    const vb = svg.getAttribute('viewBox').split(/\\s+/).map(Number);
    const g = svg.querySelector('g') || svg;
    let bb; try { bb = g.getBBox(); } catch (e) { bb = null; }
    const name = cell.textContent.trim().split('\\n')[0];
    if (!bb || bb.width === 0) { out.push({ name, degenerate: true, vb }); continue; }
    const gx = Math.min(bb.x - vb[0], vb[0] + vb[2] - (bb.x + bb.width));
    const gy = Math.min(bb.y - vb[1], vb[1] + vb[3] - (bb.y + bb.height));
    out.push({ name,
               vb: vb.map(n => +n.toFixed(1)),
               bbox: [bb.x, bb.y, bb.width, bb.height].map(n => +n.toFixed(1)),
               aspect: +(bb.width / bb.height).toFixed(3),
               // slack in user units on the tightest side; negative means clipped
               slackX: +gx.toFixed(1), slackY: +gy.toFixed(1),
               paths: svg.querySelectorAll('path,polygon,circle,ellipse,line').length });
  }
  return out;
}"""

# The grid above uses one seed per genus. resolveParams() folds regime, up to two
# tribes, and the early/settled flag into the six sliders, so one seed proves very
# little. This walks the real combinations instead and asks three questions:
#   1. does any drawn geometry leave its own viewBox?  (the frame is auto-fitted with
#      1.1x padding, so a negative slack means the fitter itself failed)
#   2. does any combination collapse to an empty or near-empty plant?
#   3. does the plate aspect stay close to the requested 0.79, or do tall stems and
#      round heads produce wildly different card heights?
SEEDS = ["a8f3kq2z", "0000zzzz", "9x", "seed-1", "w"]
SWEEP_JS = """() => {
  const genera = HolotypePlant.genera, tribes = HolotypePlant.tribes;
  const SEEDS = %s;
  const regimes = ['ordinata', 'flexilis', 'aleatoria'];""" % json.dumps(SEEDS) + """
  const host = document.createElement('div');
  host.style.cssText = 'position:fixed;left:-9999px;top:0;width:900px';
  document.body.appendChild(host);
  const out = { cases: 0, clipped: [], degenerate: [], aspects: [], extremes: [] };
  for (const g of genera) {
    for (const regime of regimes) {
      for (let t = 0; t <= 3; t++) {
        // 0, 1, 2 and 3 tribes: TRIBE_MOD is applied as a list, so ordering and
        // count both change the sum that reaches the clamps.
        const combos = [[], [tribes[t % tribes.length]],
                        [tribes[t % tribes.length], tribes[(t + 3) % tribes.length]],
                        tribes.slice(0, 4)];
        for (const domains of combos) {
          for (const conf of ['early', 'established']) {
            for (const seed of SEEDS) {
              const prof = { genus: g, regime, domains, confidence: conf, seed };
              const p = HolotypePlant.params(prof);
              host.innerHTML = HolotypePlant.svg(prof, {});
              const svg = host.querySelector('svg');
              const vb = svg.getAttribute('viewBox').split(/\\s+/).map(Number);
              const gr = svg.querySelector('g');
              const bb = gr.getBBox();
              const key = g + '/' + regime + '/' + domains.join('+') + '/' + conf + '/' + seed;
              out.cases++;
              if (!bb || bb.width < 0.5 || bb.height < 0.5) {
                out.degenerate.push({ key, params: p,
                  bbox: bb ? [bb.width, bb.height] : null });
                continue;
              }
              const gx = Math.min(bb.x - vb[0], vb[0] + vb[2] - (bb.x + bb.width));
              const gy = Math.min(bb.y - vb[1], vb[1] + vb[3] - (bb.y + bb.height));
              if (gx < -0.5 || gy < -0.5)
                out.clipped.push({ key, slackX: +gx.toFixed(1), slackY: +gy.toFixed(1) });
              const pa = (vb[2] / vb[3]);
              out.aspects.push(pa);
              // The plate is auto-fitted, so a plate far from 0.79 is a real layout
              // signal: the card is a fixed aspect box, so an outlier stretches or
              // letterboxes its plant relative to every other card in the row.
              if (Math.abs(pa - 0.79) > 0.22)
                out.extremes.push({ key, plate: +pa.toFixed(3), params: p });
            }
          }
        }
      }
    }
  }
  host.remove();
  return out;
}"""


def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context(device_scale_factor=1).new_page()
        pg.set_viewport_size({"width": 1200, "height": 1000})
        pg.goto("file://" + APP)
        pg.wait_for_timeout(900)
        n = pg.evaluate(GRID)
        pg.wait_for_timeout(400)
        esc = pg.evaluate(ESCAPED_JS)
        # element clip, not full_page: this is what makes all 16 rows actually appear
        pg.locator("#archetypeHost").screenshot(path=str(OUT / "archetypes_grid.png"))
        rows = pg.evaluate(FIT_JS)
        sweep = pg.evaluate(SWEEP_JS)
        b.close()

    print("%d archetypes, %d cards captured, host %dpx tall, %d escaped the capture"
          % (n["genera"], esc["cells"], esc["hostH"], len(esc["escaped"])))
    for e in esc["escaped"]:
        print("   NOT CAPTURED: %s" % e)
    print("%-14s %-6s %-7s %-8s %-7s %s" % ("genus", "aspect", "slackX", "slackY", "paths", "viewBox"))
    bad = []
    for r in rows:
        if r.get("degenerate"):
            print("%-14s DEGENERATE (empty bbox)" % r["name"]); bad.append(r["name"]); continue
        flag = ""
        if r["slackX"] < 0 or r["slackY"] < 0:
            flag = "  <-- CLIPPED"; bad.append(r["name"])
        print("%-14s %-6.3f %-7.1f %-8.1f %-7d %s%s" %
              (r["name"], r["aspect"], r["slackX"], r["slackY"], r["paths"], r["vb"], flag))
    aspects = [r["aspect"] for r in rows if not r.get("degenerate")]
    print("\naspect range %.3f .. %.3f" % (min(aspects), max(aspects)))
    print("PROBLEMS: %s" % (bad or "none"))

    # ---- full parameter-space sweep -------------------------------------------
    pa = sweep["aspects"]
    print("\n" + "=" * 72)
    print("SWEEP: %d genus x regime x tribe x confidence x seed combinations"
          % sweep["cases"])
    print("  clipped (geometry outside its own viewBox): %d" % len(sweep["clipped"]))
    for c in sweep["clipped"][:10]:
        print("     %s slackX=%s slackY=%s" % (c["key"], c["slackX"], c["slackY"]))
    print("  degenerate (collapsed to nothing): %d" % len(sweep["degenerate"]))
    for d in sweep["degenerate"][:10]:
        print("     %s  %s  bbox=%s" % (d["key"], json.dumps(d["params"]), d["bbox"]))
    if pa:
        print("  plate aspect: min %.3f  max %.3f  (requested 0.79)"
              % (min(pa), max(pa)))
    print("  plate aspect outliers >0.22 from target: %d" % len(sweep["extremes"]))
    seen = set()
    for e in sweep["extremes"]:
        k = (e["key"].split("/")[0], round(e["plate"], 2))
        if k in seen:
            continue
        seen.add(k)
        print("     %-16s plate=%.3f  %s"
              % (e["key"].split("/")[0], e["plate"], json.dumps(e["params"])))
    print("SWEEP PROBLEMS: %s" % (
        (sweep["clipped"] or sweep["degenerate"]) and "see above" or "none"))


if __name__ == "__main__":
    main()