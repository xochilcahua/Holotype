#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Measurement probe for the Holotype design audit.

Read-only: loads the app, then asks the live layout engine questions that are
easier to measure than to eyeball. Reports horizontal overflow, clipped text,
undersized tap targets, and whether the print tree is actually populated.

    python3 probe.py APP.html
"""
import os, json, sys
from playwright.sync_api import sync_playwright

APP = os.path.abspath(sys.argv[1] if len(sys.argv) > 1
                     else os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "index.html"))

SEED = """state.mastery = {};
for (const [i, id] of ["af038","af003","af064","af010","af037"].entries())
  state.mastery[id] = [7,7,6,4,3][i];
state.exporterName = "Sample";
renderGrid();"""

# Elements that genuinely must never be cut off: text the reader needs.
CLIP_JS = """
() => {
  const out = [];
  const seen = new Set();
  for (const el of document.querySelectorAll('body *')) {
    // scrollWidth/scrollHeight are undefined-ish inside SVG; those hits are noise.
    if (el.namespaceURI && el.namespaceURI !== 'http://www.w3.org/1999/xhtml') continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    if (cs.overflow === 'visible' && cs.overflowY === 'visible' && cs.overflowX === 'visible') {
      // not a clipper: scroll metrics can still exceed client box for wrapping text
    }
    // Only leaf-ish text nodes matter; a wrapper clipping text is a symptom
    // but the element the reader actually loses the glyphs on is the leaf.
    const hasText = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (!hasText) continue;
    const ov = el.scrollWidth - el.clientWidth;
    const oh = el.scrollHeight - el.clientHeight;
    if (ov > 1 || oh > 1) {
      const r = el.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) continue;
      const key = el.tagName + '.' + el.className + '|' + el.textContent.trim().slice(0, 40);
      if (seen.has(key)) continue;
      seen.add(key);
      const clipping = cs.overflow !== 'visible' || cs.overflowY !== 'visible';
      out.push({ sel: el.tagName.toLowerCase() + (el.id ? '#'+el.id : '') +
                    (el.className && typeof el.className === 'string' ? '.'+el.className.trim().split(/\\s+/).join('.') : ''),
                 dx: ov, dy: oh, w: Math.round(r.width), h: Math.round(r.height),
                 clip: cs.overflow + '/' + cs.overflowX + '/' + cs.overflowY,
                 lineHeight: cs.lineHeight, fontSize: cs.fontSize, clipping,
                 txt: el.textContent.trim().slice(0, 50) });
    }
  }
  return out;
}"""

# Anything whose clickable box is under 44px in the smaller axis is hard to hit.
TAP_JS = """
() => {
  const out = [];
  for (const el of document.querySelectorAll('button, a, input, select, [role=tab]')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    if (r.height < 40 || r.width < 24) {
      out.push({ sel: el.tagName.toLowerCase() + (el.id ? '#'+el.id : '') +
                       (typeof el.className === 'string' && el.className ? '.'+el.className.trim().split(/\\s+/)[0] : ''),
                    w: Math.round(r.width), h: Math.round(r.height),
                    label: (el.getAttribute('aria-label') || el.textContent || '').trim().slice(0, 30) });
    }
  }
  return out;
}"""

OVERFLOW_JS = """
() => {
  const de = document.documentElement;
  const wide = [];
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0) continue;
    if (r.right > de.clientWidth + 1) {
      wide.push({ sel: el.tagName.toLowerCase() + (el.id ? '#'+el.id : '') +
                       (typeof el.className === 'string' && el.className ? '.'+el.className.trim().split(/\\s+/)[0] : ''),
                   right: Math.round(r.right), vw: de.clientWidth });
    }
  }
  return { docScrollW: de.scrollWidth, clientW: de.clientWidth, offenders: wide.slice(0, 12) };
}"""


def run(width, theme, height=1000):
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(device_scale_factor=1)
        page = ctx.new_page()
        page.set_viewport_size({"width": width, "height": height})
        page.goto("file://" + APP)
        page.wait_for_timeout(900)
        page.evaluate(SEED)
        page.evaluate("document.documentElement.setAttribute('data-theme','%s')" % theme)
        page.wait_for_timeout(500)

        rep = {"viewport": width, "theme": theme}
        for name, js in (("garden_clip", CLIP_JS), ("garden_tap", TAP_JS),
                         ("garden_overflow", OVERFLOW_JS)):
            rep[name] = page.evaluate(js)

        page.evaluate("setMode('profile')")
        page.wait_for_timeout(600)
        rep["prof_clip"] = page.evaluate(CLIP_JS)
        rep["prof_overflow"] = page.evaluate(OVERFLOW_JS)

        # Print: is there anything to print before the export button is used?
        page.emulate_media(media="print")
        page.wait_for_timeout(300)
        rep["print_before_click"] = page.evaluate("""() => {
          const pe = document.getElementById('printExport');
          return { innerHTMLLen: pe.innerHTML.length,
                   visibleText: (pe.innerText || '').trim().length,
                   display: getComputedStyle(pe).display,
                   anyVisible: [...document.body.children]
                     .filter(e => getComputedStyle(e).display !== 'none')
                     .map(e => e.id || e.tagName.toLowerCase()) };
        }""")
        page.evaluate("buildPrintExport()")
        page.wait_for_timeout(400)
        rep["print_after_click"] = page.evaluate("""() => {
          const pe = document.getElementById('printExport');
          return { innerHTMLLen: pe.innerHTML.length,
                   visibleText: (pe.innerText || '').trim().length,
                   anyVisible: [...document.body.children]
                     .filter(e => getComputedStyle(e).display !== 'none')
                     .map(e => e.id || e.tagName.toLowerCase()) };
        }""")
        page.emulate_media(media="screen")
        b.close()
    return rep


if __name__ == "__main__":
    # .spec-tag is line-clamped on purpose (2-line teaser); report it separately
    # from text that is actually being cut off by a width the reader never asked for.
    for w in (390, 900, 1440):
        rep = run(w, "light")
        print("=" * 72)
        print("VIEWPORT %d  theme=light" % w)
        po, pp = rep["garden_overflow"], rep["prof_overflow"]
        print("  h-overflow: docScrollW=%s clientW=%s" % (po["docScrollW"], po["clientW"]))
        for o in po["offenders"]:
            print("     RIGHT-EDGE  %s  right=%d > vw=%d" % (o["sel"], o["right"], o["vw"]))
        for label in ("garden_clip", "prof_clip"):
            for c in rep[label]:
                if c["sel"].endswith("spec-tag"):
                    continue          # intentional 2-line clamp
                print("  CLIPPED %-10s dx=%-4d dy=%-4d %s" % (label, c["dx"], c["dy"], c["txt"][:44]))
                print("           %-52s %dx%d clip=%s lh=%s fs=%s" %
                      (c["sel"][:52], c["w"], c["h"], c["clip"], c["lineHeight"], c["fontSize"]))
        for t in rep["garden_tap"]:
            print("  SMALL TAP  %dx%d  %s" % (t["w"], t["h"], t["label"] or t["sel"]))
        b4, af = rep["print_before_click"], rep["print_after_click"]
        print("  PRINT before click: len=%s text=%s visible=%s" % (b4["innerHTMLLen"], b4["visibleText"], b4["anyVisible"]))
        print("  PRINT after  click: len=%s text=%s visible=%s" % (af["innerHTMLLen"], af["visibleText"], af["anyVisible"]))