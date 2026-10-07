#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Group the undersized tap targets by DOM ancestry.

probe.py lists every small target one line at a time, which is useless when the
same component repeats 300 times. This collapses them into component paths so the
report can name a component instead of a count of symptoms.

    python3 tap_probe.py APP.html
"""
import os, sys
from playwright.sync_api import sync_playwright

APP = os.path.abspath(sys.argv[1] if len(sys.argv) > 1
                     else os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "index.html"))

JS = """() => {
  const out = {};
  for (const el of document.querySelectorAll('button, a, input, select, [role=tab]')) {
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    if (r.height >= 40 && r.width >= 24) continue;
    const name = el.tagName.toLowerCase() +
      (el.id ? '#' + el.id : '') +
      (typeof el.className === 'string' && el.className
         ? '.' + el.className.trim().split(/\\s+/).join('.') : '');
    let p = el.parentElement, chain = [];
    while (p && p !== document.body && chain.length < 4) {
      chain.unshift(p.tagName.toLowerCase() +
        (p.id ? '#' + p.id : '') +
        (typeof p.className === 'string' && p.className
           ? '.' + p.className.trim().split(/\\s+/)[0] : ''));
      p = p.parentElement;
    }
    const key = chain.join(' > ') + '  >>  ' + name;
    const e = out[key] || (out[key] = { n: 0, w: 0, h: 0, label: '' });
    e.n++; e.w = Math.round(r.width); e.h = Math.round(r.height);
    e.label = (el.getAttribute('aria-label') || el.textContent || '').trim().slice(0, 40);
  }
  return out;
}"""

SEED = """state.mastery = {};
for (const [i, id] of ["af038","af003","af064","af010","af037"].entries())
  state.mastery[id] = [7,7,6,4,3][i];
state.exporterName = "Sample";
renderGrid();"""


def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context().new_page()
        pg.set_viewport_size({"width": 390, "height": 1000})
        pg.goto("file://" + APP)
        pg.wait_for_timeout(900)
        pg.evaluate(SEED)
        pg.wait_for_timeout(500)
        for label, setup in (("GARDEN", None), ("PROFILE", "setMode('profile')")):
            if setup:
                pg.evaluate(setup)
                pg.wait_for_timeout(600)
            print("=" * 72)
            print("%s @390px" % label)
            rows = pg.evaluate(JS)
            for k, v in sorted(rows.items(), key=lambda x: -x[1]["n"])[:15]:
                print("  %4d x  %3dx%-3d  %s" % (v["n"], v["w"], v["h"], k))
                if v["label"]:
                    print("        e.g. %r" % v["label"])
        b.close()


if __name__ == "__main__":
    main()
