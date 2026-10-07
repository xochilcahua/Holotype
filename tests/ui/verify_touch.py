#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Check tap targets under a real touch profile.

The fix grew .icon-btn/.pill-btn/.text-select to 44px and the mastery slider's hit
box to 24px under (pointer: coarse). Playwright's has_touch + is_mobile profile is
what actually triggers those rules, so this is the only way to verify them.

    .venv_audit/bin/python tests/ui/verify_touch.py
"""
import os
import pathlib
from playwright.sync_api import sync_playwright

APP = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "index.html"))
OUT = pathlib.Path("out/audit")

REPORT = """() => {
  const grab = sel => {
    const e = document.querySelector(sel);
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return { w: Math.round(r.width), h: Math.round(r.height) };
  };
  return {
    iconBtn: grab('#themeToggle'),
    pillBtn: grab('#filterToggle'),
    sort: grab('#sortSelect'),
    search: grab('.search-input'),
    slider: grab('.spec-rate'),
    sliderCount: document.querySelectorAll('.spec-rate').length,
    smallSliders: [...document.querySelectorAll('.spec-rate')]
      .filter(e => e.getBoundingClientRect().height < 24).length,
  };
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(device_scale_factor=2, has_touch=True, is_mobile=True,
                            viewport={"width": 390, "height": 844})
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto("file://" + APP)
        pg.wait_for_timeout(900)
        r = pg.evaluate(REPORT)
        for k in ("iconBtn", "pillBtn", "sort", "search", "slider"):
            v = r[k]
            print("  %-9s %sx%s" % (k, v["w"], v["h"]) if v else "  %-9s (absent)" % k)
        print("  sliders under 24px tall: %d of %d" % (r["smallSliders"], r["sliderCount"]))
        print("  page errors: %s" % (errs or "none"))
        pg.screenshot(path=str(OUT / "after_touch_390.png"))
        b.close()


if __name__ == "__main__":
    main()
