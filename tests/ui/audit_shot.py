#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Screenshot driver for the Holotype design audit.

Loads the real page in headless Chromium, seeds a profile, and captures the
views named on the command line. Nothing in here changes the app.

    python3 audit_shot.py APP.html OUTDIR --tag before --views garden,modal,prof
"""
import argparse, os, sys, pathlib
from playwright.sync_api import sync_playwright

SEED_5 = """state.mastery = {};
for (const [i, id] of ["af038","af003","af064","af010","af037"].entries())
  state.mastery[id] = [7,7,6,4,3][i];
state.exporterName = "Sample";
renderGrid(); setMode('profile');
"""

SEED_FULL = """// rate the whole catalog: a full profile
state.mastery = {};
let k = 0;
for (const f of ART_FORMS) {
  const base = 2 + ((k * 7) % 9);            // deterministic 2..10 spread
  state.mastery[f.id] = ((base + Math.floor(k / 3)) % 10) + 1;
  k++;
}
state.exporterName = "Rosalind Fairweather-Vance";
renderGrid(); setMode('profile');
"""

SEED_EMPTY = "state.mastery = {}; state.exporterName=''; renderGrid(); setMode('garden');"

SEED_ONE = """state.mastery = { af038: 7 }; state.exporterName = "A";
renderGrid(); setMode('garden');"""

SEED_LONGNAME = """state.mastery = {};
for (const [i, id] of ["af038","af003","af064","af010","af037"].entries())
  state.mastery[id] = [7,7,6,4,3][i];
state.exporterName = "Wilhelmina Aurelia Featherstonehaugh-Vandermeer <b>esq.</b> & co";
renderGrid(); setMode('profile');"""

SEEDS = {
    "five": SEED_5,
    "full": SEED_FULL,
    "empty": SEED_EMPTY,
    "one": SEED_ONE,
    "longname": SEED_LONGNAME,
}

WIDTHS = {"desktop": 1440, "tablet": 900, "phone": 390}


def open_app(page, path, seed, theme, width, height=1000):
    page.set_viewport_size({"width": width, "height": height})
    page.goto("file://" + os.path.abspath(path))
    page.wait_for_timeout(900)
    if seed != "none":
        page.evaluate(SEEDS[seed])
        page.wait_for_timeout(500)
    if theme == "dark":
        page.evaluate("document.documentElement.setAttribute('data-theme','dark')")
    else:
        page.evaluate("document.documentElement.setAttribute('data-theme','light')")
    page.wait_for_timeout(350)


def shot(page, outdir, name, full=False):
    p = os.path.join(outdir, name + ".png")
    page.screenshot(path=p, full_page=full)
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("app")
    ap.add_argument("outdir")
    ap.add_argument("--tag", default="before")
    ap.add_argument("--seed", default="five")
    ap.add_argument("--views", default="garden,modal,prof,help,settings,filter,print")
    ap.add_argument("--widths", default="desktop")
    ap.add_argument("--themes", default="light")
    ap.add_argument("--height", type=int, default=1000)
    ap.add_argument("--full", action="store_true")
    a = ap.parse_args()

    outdir = pathlib.Path(a.outdir); outdir.mkdir(parents=True, exist_ok=True)
    views = a.views.split(",")
    made = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(device_scale_factor=2)
        page = ctx.new_page()
        for wname in a.widths.split(","):
            w = WIDTHS[wname]
            for theme in a.themes.split(","):
                open_app(page, a.app, a.seed, theme, w, a.height)
                for v in views:
                    n = f"{a.tag}_{v}_{a.seed}_{theme}_{wname}"
                    if v == "garden":
                        page.evaluate("setMode('garden')")
                        page.wait_for_timeout(300)
                        made.append(shot(page, str(outdir), n, a.full))
                    elif v == "modal":
                        page.evaluate("openDetail('af038')")
                        page.wait_for_timeout(450)
                        made.append(shot(page, str(outdir), n, a.full))
                        page.evaluate("document.getElementById('modalRoot').innerHTML=''")
                        page.wait_for_timeout(200)
                    elif v == "prof":
                        page.evaluate("setMode('profile')")
                        page.wait_for_timeout(500)
                        made.append(shot(page, str(outdir), n, a.full))
                        page.evaluate("setMode('garden')")
                        page.wait_for_timeout(250)
                    elif v == "help":
                        page.evaluate("toggleHelp()")
                        page.wait_for_timeout(400)
                        made.append(shot(page, str(outdir), n, False))
                        page.evaluate("closeHelp && closeHelp()")
                        page.wait_for_timeout(200)
                    elif v == "settings":
                        page.evaluate("openSettings && openSettings()")
                        page.wait_for_timeout(400)
                        made.append(shot(page, str(outdir), n, False))
                        page.evaluate("closeSettings && closeSettings()")
                        page.wait_for_timeout(200)
                    elif v == "filter":
                        page.evaluate("openFilterPanel()")
                        page.wait_for_timeout(400)
                        made.append(shot(page, str(outdir), n, False))
                        page.evaluate("closeFilterPanel()")
                        page.wait_for_timeout(200)
                    elif v == "print":
                        page.evaluate("setMode('profile')")
                        page.wait_for_timeout(500)
                        page.emulate_media(media="print")
                        page.wait_for_timeout(400)
                        made.append(shot(page, str(outdir), n, a.full))
                        page.emulate_media(media="screen")
                        page.wait_for_timeout(200)
        browser.close()
    for m in made:
        print(m)


if __name__ == "__main__":
    main()
