#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Screenshot the print tree, with and without going through the export handler.

The point of the "noclick" run is the defect this audit found: #printExport is
empty on a normal page load, and the print stylesheet hides every sibling of it.
So a user who prints from the browser menu gets a blank page. The "noclick" run
reproduces that exactly, because it never calls buildPrintExport().

    TAG=before BUILD=0 python3 print_shot.py OUTDIR
    TAG=after  BUILD=1 python3 print_shot.py OUTDIR
"""
import os, sys, pathlib
from playwright.sync_api import sync_playwright

APP = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "index.html"))
OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "out/audit")
TAG = os.environ.get("TAG", "print")
BUILD = os.environ.get("BUILD", "1") == "1"

SEED = """state.mastery = {};
for (const [i, id] of ["af038","af003","af064","af010","af037"].entries())
  state.mastery[id] = [7,7,6,4,3][i];
state.exporterName = "Sample";
renderGrid(); setMode('profile');"""

REPORT = """() => {
  const pe = document.getElementById('printExport');
  const cs = getComputedStyle(pe);
  const visible = [...document.body.children]
    .filter(e => getComputedStyle(e).display !== 'none')
    .map(e => e.id || e.tagName.toLowerCase());
  return { len: pe.innerHTML.length, text: (pe.innerText || '').trim().length,
           display: cs.display, height: pe.scrollHeight, visible,
           sectionCount: pe.querySelectorAll('h2').length,
           tableRows: pe.querySelectorAll('.pe-table tr').length,
           svgs: pe.querySelectorAll('svg').length };
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context(device_scale_factor=2).new_page()
        pg.set_viewport_size({"width": 900, "height": 1200})
        pg.goto("file://" + APP)
        pg.wait_for_timeout(900)
        pg.evaluate(SEED)
        pg.wait_for_timeout(500)
        if BUILD:
            pg.evaluate("buildPrintExport()")
        pg.emulate_media(media="print")
        pg.wait_for_timeout(600)
        rep = pg.evaluate(REPORT)
        path = str(OUT / (TAG + ".png"))
        pg.screenshot(path=path, full_page=True)
        pg.emulate_media(media="screen")
        b.close()
    print("%-14s build=%-5s len=%-7d text=%-6d height=%-6d h2=%-3d rows=%-4d svg=%-3d visible=%s"
          % (TAG, BUILD, rep["len"], rep["text"], rep["height"],
             rep["sectionCount"], rep["tableRows"], rep["svgs"], rep["visible"]))
    print("  " + path)


if __name__ == "__main__":
    main()
