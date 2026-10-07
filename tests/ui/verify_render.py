#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Render a wide slice of parameter space and report sparse or broken plants.

Geometry checks (archetype_grid.py) prove nothing escapes its viewBox. They cannot tell you
a plant has collapsed to three shapes, or that one genus throws where another does not. This
walks genus x regime x domains x confidence, counts drawn primitives, and reports the thinnest
results plus any exception.
"""
import os, sys
from playwright.sync_api import sync_playwright

APP = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "index.html"))

JS = r"""() => {
  const out = [];
  for (const g of HolotypePlant.genera) {
    for (const reg of ['ordinata', 'flexilis', 'aleatoria']) {
      for (const dom of [[], ['Petal'], ['Root'], ['Nectar', 'Trellis'], ['Tendril'], ['Reed', 'Vine']]) {
        for (const conf of ['early', 'settled']) {
          const p = { genus: g, seed: 'audit-seed-' + g, regime: reg, domains: dom, confidence: conf };
          let s = '', err = null;
          try { s = HolotypePlant.svg(p, {}); } catch (e) { err = String(e && e.message || e); }
          out.push({ g, reg, dom: dom.join('+') || '-', conf,
                     n: (s.match(/<(path|circle|ellipse|rect|polygon|line)/g) || []).length,
                     err });
        }
      }
    }
  }
  return out;
}"""

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_context().new_page()
    perrs = []
    pg.on("pageerror", lambda e: perrs.append(str(e)))
    pg.goto("file://" + APP)
    pg.wait_for_timeout(800)
    r = pg.evaluate(JS)
    b.close()

errs = [x for x in r if x["err"]]
ok = [x for x in r if not x["err"]]
print("combinations rendered: %d" % len(r))
print("threw: %d" % len(errs))
for e in errs[:10]:
    print("   %s %s %s %s -> %s" % (e["g"], e["reg"], e["dom"], e["conf"], e["err"]))
print("page errors: %d %s" % (len(perrs), perrs[:3]))
ok.sort(key=lambda x: x["n"])
print("\nthinnest 15 plants by drawn primitive count:")
for x in ok[:15]:
    print("   %-13s %-11s %-14s %-8s %d" % (x["g"], x["reg"], x["dom"], x["conf"], x["n"]))
thin = [x for x in ok if x["n"] < 4]
print("\nsuspiciously sparse (<4 primitives): %d" % len(thin))
by_g = {}
for x in thin:
    by_g.setdefault(x["g"], 0)
    by_g[x["g"]] += 1
print("   by genus: %s" % (by_g or "none"))
print("\nRESULT: %s" % ("PASS" if not errs and not perrs else "FAIL"))
