#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Re-check the three layout defects fixed after the audit.

  1. sort select truncating to "CLOS" on a 390px phone
  2. a long unbroken exporter name overflowing .prof-title
  3. whether the toolbar still fits / stays on one line after the target-size growth

    .venv_audit/bin/python tests/ui/verify_responsive.py
"""
import os
import pathlib
from playwright.sync_api import sync_playwright

APP = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "index.html"))
OUT = pathlib.Path("out/audit")

LONG = "Wilhelmina Aurelia Featherstonehaugh-Vandermeerfeather"

REPORT = """() => {
  const sel = document.getElementById('sortSelect');
  const title = document.querySelector('.prof-title');
  const doc = document.documentElement;
  const bar = document.querySelector('.bar');
  const actions = document.querySelector('.bar-actions');
  const cs = getComputedStyle(sel);
  // ScrollWidth on a <select> is the intrinsic text width; clientWidth is what it got.
  return {
    sortW: sel.clientWidth,
    sortScrollW: sel.scrollWidth,
    sortText: sel.selectedOptions[0].textContent,
    sortClipped: sel.scrollWidth > sel.clientWidth + 1,
    sortHeight: cs.height,
    titleW: title.clientWidth,
    titleScrollW: title.scrollWidth,
    titleOverflow: title.scrollWidth - title.clientWidth,
    docOverflow: doc.scrollWidth - doc.clientWidth,
    barH: bar.getBoundingClientRect().height,
    actionsH: actions.getBoundingClientRect().height,
  };
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context(device_scale_factor=2).new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto("file://" + APP)
        pg.wait_for_timeout(800)

        for w in (390, 414, 768, 1440):
            pg.set_viewport_size({"width": w, "height": 900})
            pg.evaluate("""() => {
              state.exporterName = %s;
              state.mastery = {};
              for (const [i,id] of ["af038","af003","af064"].entries())
                state.mastery[id] = [7,5,3][i];
              renderGrid(); setMode('profile');
            }""" % ("'" + LONG + "'"))
            pg.wait_for_timeout(500)
            r = pg.evaluate(REPORT)
            print("w=%-5d sort %3dpx (text needs %3d) clipped=%-5s  "
                  "title overflow=%-5d  doc overflow=%-4d  barH=%-4.0f actionsH=%-4.0f"
                  % (w, r["sortW"], r["sortScrollW"], r["sortClipped"],
                     r["titleOverflow"], r["docOverflow"], r["barH"], r["actionsH"]))
            pg.screenshot(path=str(OUT / ("after_prof_%d.png" % w)))

        # Print title must wrap the same long name too.
        pg.evaluate("buildPrintExport()")
        pg.wait_for_timeout(300)
        t = pg.evaluate("""() => { const h = document.querySelector('#printExport h1');
          return { scrollW: h.scrollWidth, clientW: h.clientWidth }; }""")
        print("print h1 overflow: %d" % (t["scrollW"] - t["clientW"]))
        print("page errors: %s" % (errs or "none"))
        b.close()


if __name__ == "__main__":
    main()
