#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Check whether a very long exporter name breaks the Herbarium heading.

The phone screenshot shows the name running off the right edge, but a screenshot
cannot tell a clipped word from a word that is merely near the edge. This measures
the heading's own scrollWidth/clientWidth and whether the document itself scrolls,
and does the same for a name containing markup.

    python3 longname_probe.py APP.html
"""
import os, sys
from playwright.sync_api import sync_playwright

APP = os.path.abspath(sys.argv[1] if len(sys.argv) > 1
                     else os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "index.html"))

SEED = """state.mastery = {};
for (const [i, id] of ["af038","af003","af064","af010","af037"].entries())
  state.mastery[id] = [7,7,6,4,3][i];
renderGrid(); setMode('profile');"""

CASES = {
    "short":   "Alex",
    "long":    "Wilhelmina Aurelia Featherstonehaugh-Vandermeer",
    "markup":  "A <b>Bold</b> & <script>alert(1)</script> Name",
    "oneword": "Featherstonehaughvandermeerfeatherstonehaughvandermeer",
}

JS = """(name) => {
  const inp = document.getElementById('exporterNameInput');
  inp.value = name;
  inp.dispatchEvent(new Event('input', { bubbles: true }));
  const h1 = document.querySelector('#profileView h1') ||
             document.getElementById('profileView').querySelector('h1');
  const r = h1.getBoundingClientRect();
  const cs = getComputedStyle(h1);
  return {
    text: h1.textContent.trim().slice(0, 60),
    // text the reader loses because a box is narrower than its content
    overflowX: h1.scrollWidth - h1.clientWidth,
    boxW: Math.round(r.width), boxRight: Math.round(r.right),
    fontSize: cs.fontSize, lineHeight: cs.lineHeight,
    wordBreak: cs.wordBreak, overflowWrap: cs.overflowWrap,
    whiteSpace: cs.whiteSpace, overflow: cs.overflow,
    lines: Math.round(r.height / parseFloat(cs.lineHeight)),
    docScrollW: document.documentElement.scrollWidth,
    docClientW: document.documentElement.clientWidth,
    bodyOverflowX: getComputedStyle(document.body).overflowX,
    htmlOverflowX: getComputedStyle(document.documentElement).overflowX,
    // the name also appears in the print sheet, so check that copy too
    peName: (document.getElementById('profileView').innerHTML.match(
             /Featherstone|Wilhelmina|Alex/g) || []).length,
  };
}"""


def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context().new_page()
        for w in (390, 900, 1440):
            pg.set_viewport_size({"width": w, "height": 1000})
            pg.goto("file://" + APP)
            pg.wait_for_timeout(900)
            pg.evaluate(SEED)
            pg.wait_for_timeout(400)
            print("=" * 72)
            print("VIEWPORT %d" % w)
            for label, name in CASES.items():
                pg.evaluate(JS, name)
                pg.wait_for_timeout(250)
                o = pg.evaluate(JS, name)
                flag = "CLIPPED" if o["overflowX"] > 1 else "ok"
                if o["boxRight"] > w:
                    flag += " OFFSCREEN"
                print("  %-8s %-8s lines=%-2d boxW=%-4d right=%-5d dx=%-4d %s"
                      % (label, flag, o["lines"], o["boxW"], o["boxRight"],
                         o["overflowX"], o["text"][:34]))
                print("           fs=%s lh=%s wordBreak=%s overflowWrap=%s "
                      "overflow=%s bodyOX=%s"
                      % (o["fontSize"], o["lineHeight"], o["wordBreak"],
                         o["overflowWrap"], o["overflow"], o["bodyOverflowX"]))
            # escaping check: markup must not become live DOM
            pg.evaluate(JS, CASES["markup"])
            pg.wait_for_timeout(200)
            esc = pg.evaluate("""() => {
              const h1 = document.querySelector('#profileView h1');
              return { live: h1.querySelectorAll('b,script,em,i').length,
                       text: h1.textContent.trim().slice(0, 50) };
            }""")
            print("  ESCAPING: live tags in h1 = %d  text = %r"
                  % (esc["live"], esc["text"]))
            d = pg.evaluate("""() => ({ ds: document.documentElement.scrollWidth,
                                         dc: document.documentElement.clientWidth })""")
            print("  doc scrollW=%s clientW=%s" % (d["ds"], d["dc"]))
        b.close()


if __name__ == "__main__":
    main()
