# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
import os
from playwright.sync_api import sync_playwright

APP = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "index.html"))

JS = """() => {
  const r = el => { const b = el.getBoundingClientRect();
    return {w:Math.round(b.width), h:Math.round(b.height), x:Math.round(b.left), y:Math.round(b.top)}; };
  const sel = document.getElementById('sortSelect');
  const out = { bar:r(document.querySelector('.bar')),
                actions:r(document.querySelector('.bar-actions')),
                search:r(document.querySelector('.search-wrap')),
                toggle:r(document.getElementById('viewToggle')),
                filters:r(document.getElementById('filterToggle')),
                select:r(sel) };
  const probe = document.createElement('span');
  probe.style.cssText = 'position:absolute;visibility:hidden;white-space:nowrap;font:' + getComputedStyle(sel).font;
  probe.textContent = sel.options[sel.selectedIndex].textContent;
  document.body.appendChild(probe);
  out.selectTextNeed = Math.round(probe.getBoundingClientRect().width);
  out.selectClientW = sel.clientWidth;
  out.selectScrollW = sel.scrollWidth;
  probe.remove();
  return out;
}"""

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context()
    pg = ctx.new_page()
    print("width  selectW  need  barH  verdict")
    for w in (360, 390, 430, 500, 560, 620, 640, 641, 660, 700, 760, 820, 860, 900, 1100, 1440):
        pg.set_viewport_size({"width": w, "height": 1000})
        pg.goto("file://" + APP)
        pg.wait_for_timeout(500)
        o = pg.evaluate(JS)
        bad = o["selectClientW"] < o["selectTextNeed"]
        print("%5d  %7d  %4d  %4d  %s" % (w, o["selectClientW"], o["selectTextNeed"],
                                          o["bar"]["h"], "CLIPPED" if bad else "ok"))
    b.close()