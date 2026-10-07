#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Verify the native-print fix: dispatch beforeprint WITHOUT ever calling
printGardenExport(), which is the path Cmd/Ctrl+P and the browser Print... menu take.

Before the fix this produced a blank sheet (len=0); after it, the sheet must contain
the full dossier. Also checks that afterprint restores the document title and that no
page errors were raised.

    .venv_audit/bin/python tests/ui/verify_print.py
"""
import os
import pathlib
from playwright.sync_api import sync_playwright

APP = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "index.html"))
OUT = pathlib.Path("out/audit")

SEED = """state.mastery = {};
for (const [i, id] of ["af038","af003","af064","af010","af037"].entries())
  state.mastery[id] = [7,7,6,4,3][i];
state.exporterName = "Sample"; renderGrid(); setMode('profile');"""

REPORT = """() => {
  const pe = document.getElementById('printExport');
  return { len: pe.innerHTML.length, text: (pe.innerText || '').trim().length,
           height: pe.scrollHeight, h2: pe.querySelectorAll('h2').length,
           rows: pe.querySelectorAll('.pe-table tr').length,
           svgs: pe.querySelectorAll('svg').length, title: document.title };
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(device_scale_factor=2)
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.set_viewport_size({"width": 900, "height": 1200})
        pg.goto("file://" + APP)
        pg.wait_for_timeout(900)
        pg.evaluate(SEED)
        pg.wait_for_timeout(400)

        # Native print path only. No click, no direct buildPrintExport() call.
        pg.evaluate("window.dispatchEvent(new Event('beforeprint'))")
        pg.wait_for_timeout(600)
        pg.emulate_media(media="print")
        pg.wait_for_timeout(600)
        r = pg.evaluate(REPORT)
        print("NATIVE PRINT  len={len}  text={text}  height={height}  h2={h2}  "
              "rows={rows}  svg={svgs}".format(**r))
        print("  title during print: %r" % r["title"])
        pg.screenshot(path=str(OUT / "after_noclick_nativeprint.png"), full_page=True)
        pg.pdf(path=str(OUT / "after_native.pdf"), format="A4", print_background=True)
        pg.emulate_media(media="screen")

        pg.evaluate("window.dispatchEvent(new Event('afterprint'))")
        pg.wait_for_timeout(300)
        print("  title after afterprint: %r" % pg.title())
        print("  page errors: %s" % (errs or "none"))
        print("  " + str(OUT / "after_noclick_nativeprint.png"))
        b.close()


if __name__ == "__main__":
    main()
