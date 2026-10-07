#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Final sweep of the states the earlier audit rounds did not get to:
error surfaces, full-profile rendering, search/filter, marker modes, modal,
and HTML-escaping of a hostile exporter name.

    .venv_audit/bin/python tests/ui/verify_states.py
"""
import os
import pathlib
from playwright.sync_api import sync_playwright

APP = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "index.html"))
OUT = pathlib.Path("out/audit")

EVIL = "<img src=x onerror=alert(1)>\"'`&"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(device_scale_factor=2)
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append("pageerror: %s" % e))
        pg.on("dialog", lambda d: (errs.append("DIALOG FIRED: %s" % d.message), d.dismiss()))
        pg.set_viewport_size({"width": 1280, "height": 1000})
        pg.goto("file://" + APP)
        pg.wait_for_timeout(900)

        # 1. escaping of a hostile exporter name (lives in the profile view)
        pg.evaluate("() => setMode('profile')")
        pg.wait_for_timeout(500)
        pg.fill("#exporterNameInput", EVIL)
        pg.wait_for_timeout(400)
        esc = pg.evaluate("""() => {
          const t = document.querySelector('.prof-title');
          return { text: t.textContent, injectedImg: !!t.querySelector('img') };
        }""")
        print("escaping: injected <img> = %s  (title shows %r)" % (esc["injectedImg"], esc["text"][:60]))

        # 2. full profile: rate everything, check every section renders
        pg.evaluate("""() => {
          state.mastery = {};
          for (const a of ART_FORMS) state.mastery[a.id] = 7;
          state.exporterName = 'Full';
          renderGrid(); setMode('profile');
        }""")
        pg.wait_for_timeout(700)
        full = pg.evaluate("""() => ({
          sections: document.querySelectorAll('.prof-section').length,
          catbars: document.querySelectorAll('.prof-catbars .catbar, .prof-catbar-row, .prof-catbars > *').length,
          rows: document.querySelectorAll('.prof-table tbody tr').length,
          overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        })""")
        print("full profile:", full)
        pg.screenshot(path=str(OUT / "after_full_profile.png"), full_page=False)

        # 3. search + filter
        pg.set_mode = None  # not needed; use search field
        pg.fill("#searchInput", "zine")
        pg.wait_for_timeout(500)
        n_search = pg.evaluate("() => document.querySelectorAll('.spec').length")
        pg.fill("#searchInput", "zzzznotathing")
        pg.wait_for_timeout(500)
        empty = pg.evaluate("""() => ({
          specs: document.querySelectorAll('.spec').length,
          emptyMsg: !!document.querySelector('.empty-state, .no-results'),
        })""")
        pg.fill("#searchInput", "")
        pg.wait_for_timeout(400)
        print("search 'zine': %d cards; no-match state: %s" % (n_search, empty))

        # 4. detail modal
        pg.evaluate("openDetail('af038')" if pg.evaluate("() => typeof openDetail") else "()=>0")
        pg.wait_for_timeout(600)
        modal = pg.evaluate("""() => {
          const m = document.querySelector('.modal, #modal, dialog');
          return m ? { present: true, visible: m.offsetParent !== null || getComputedStyle(m).display !== 'none' } : { present: false };
        }""")
        print("modal:", modal)
        pg.screenshot(path=str(OUT / "after_modal.png"))
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(300)

        # 5. print with the hostile name still set
        pg.evaluate("buildPrintExport()")
        pg.wait_for_timeout(300)
        pj = pg.evaluate("""() => {
          const h = document.querySelector('#printExport h1');
          return { injected: !!h.querySelector('img'), text: h.textContent.slice(0, 60) };
        }""")
        print("print title injected <img> = %s" % pj["injected"])

        print("runtime errors/dialogs: %s" % (errs or "none"))
        b.close()


if __name__ == "__main__":
    main()
