# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
import sys
from playwright.sync_api import sync_playwright

import os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
APP_PATH = os.path.join(ROOT, "index.html")
HTML = 'file://' + APP_PATH
fails = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + ("   " + str(detail) if detail else ""))
    if not cond:
        fails.append(name)


with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1440, "height": 1000})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append("console:" + m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
    # domcontentloaded, not "load": the page pulls fonts from
    # fonts.googleapis.com, so waiting on "load" stalls offline and reports a
    # timeout that looks like an app failure. The app renders before the fonts
    # arrive, and nothing checked here depends on them.
    pg.goto(HTML, wait_until="domcontentloaded")
    pg.wait_for_timeout(1000)
    pg.evaluate("""() => {
      const seed = {af008:9, af009:6, af010:5, af039:10, af053:3};
      for (const [id, v] of Object.entries(seed)) state.mastery[id] = v;
      state.colorRules = [{dimension:'cost', values:['low'], color:'#c0392b'}];
      saveStore();
    }""")

    # --- session file round-trip -------------------------------------------
    # ui.sort lives in the exported session file, not localStorage: saveStore() only writes state.
    # sessionNormalize returns {norm, report}; the sort is norm.sort.
    for s in ["common_desc", "common_asc", "tag"]:
        pg.select_option("#sortSelect", s)
        pg.wait_for_timeout(300)
        res = pg.evaluate("""() => {
          const file = sessionBuild(sessionSnapshot());
          const {norm, report} = sessionNormalize(JSON.parse(JSON.stringify(file)));
          const next = sessionMerge(sessionSnapshot(), norm, 'replace');
          return { fileSort: file.sort, normSort: norm.sort, nextSort: next.ui.sort };
        }""")
        check(f"session file keeps {s}", res["fileSort"] == s, res)
        check(f"  normalizer accepts {s}", res["normSort"] == s, res)
        check(f"  merge restores {s}", res["nextSort"] == s, res)
    # An unknown sort must still be refused, not silently accepted.
    bad = pg.evaluate("""() => {
      const doc = Object.assign(sessionBuild(sessionSnapshot()), {sort: 'popularity_asc'});
      const {norm, report} = sessionNormalize(JSON.parse(JSON.stringify(doc)));
      return { sort: norm.sort, ignored: report.ignored };
    }""")
    check("unknown sort still refused", bad["sort"] is None and bad["ignored"], bad)

    # --- print sheet keeps every row and shows the caveat -------------------
    pg.select_option("#sortSelect", "common_desc")
    pg.wait_for_timeout(400)
    pg.click("#tabProfile")
    pg.wait_for_timeout(700)
    # The print sheet is only built on demand, and hidden on screen: build it, then measure it
    # under print media, which is the only state where it has a layout.
    pg.evaluate("() => buildPrintExport()")
    pg.emulate_media(media="print")
    pg.wait_for_timeout(400)
    pe_rows = pg.eval_on_selector_all(
        "#printExport .pe-table tbody tr",
        "rs => rs.map(r => Array.from(r.cells).map(c => c.textContent.trim()))")
    # The sheet holds BOTH lists. Rated rows are 3 cells (icon/name/rating); unrated rows are
    # 5 (icon/name/dots/novelty/pct), because print keeps the novelty figure the screen shows.
    by_len = {}
    for r in pe_rows:
        by_len[len(r)] = by_len.get(len(r), 0) + 1
    # The sheet holds one row per form in the catalogue, and how many are 3-cell
    # rather than 5-cell depends on how many this run rated. Both read from the page.
    n_forms = pg.evaluate("ART_FORMS.length")
    n_rated = pg.evaluate("Object.keys(state.mastery).length")
    check("print: rows present", len(pe_rows) == n_forms,
          (len(pe_rows), n_forms, by_len))
    print("     cells-per-row histogram:", by_len)
    print("     sample unrated row:", [r for r in pe_rows if len(r) == 5][:1])
    check("print: unrated rows are 5 cells",
          by_len.get(5, 0) == n_forms - n_rated, by_len)
    check("print: rated rows are 3 cells", by_len.get(3, 0) == n_rated, by_len)
    check("print: every unrated row carries a % in the last cell",
          all("%" in r[4] for r in pe_rows if len(r) == 5),
          [r for r in pe_rows if len(r) == 5 and "%" not in r[4]][:2])
    body = pg.inner_text("#printExport")
    check("print: source note present", "at some point in their lives" in body,
          [l for l in body.split("\n") if "lives" in l][:2])
    check("print: legend expanded (no <details>)",
          pg.eval_on_selector_all("#printExport details", "e => e.length") == 0)
    # A non-commonness sort must NOT add the column, or the sheet claims a figure it isn't showing.
    pg.emulate_media(media="screen")
    pg.select_option("#sortSelect", "name_asc")
    pg.wait_for_timeout(300)
    pg.evaluate("() => buildPrintExport()")
    pg.emulate_media(media="print")
    pg.wait_for_timeout(300)
    plain = pg.eval_on_selector_all(
        "#printExport .pe-table tbody tr",
        "rs => rs.map(r => Array.from(r.cells).map(c => c.textContent.trim()))")
    check("print: no pct column for A-Z", all(len(r) != 5 for r in plain),
          [r for r in plain if len(r) == 5][:2])
    pg.emulate_media(media="screen")
    pg.select_option("#sortSelect", "common_desc")
    pg.wait_for_timeout(400)
    pg.click("#tabProfile")
    pg.wait_for_timeout(700)

    # --- screen legend explains the dot ------------------------------------
    # The legend lives in a closed <details>, so open it before reading the text.
    pg.evaluate("""() => { const d = document.querySelector('.prof-legend');
      if (d) d.open = true; }""")
    pg.wait_for_timeout(300)
    leg = pg.inner_text(".prof-legend-body")
    check("legend explains filled vs hollow", "Hollow rings are estimates" in leg and "order of magnitude" in leg, leg[-300:])

    # --- help panel mentions the new sorts ---------------------------------
    help_txt = pg.evaluate("() => document.body.innerText")
    check("help/legend reachable", len(help_txt) > 500)

    # --- narrow viewport: the new column must not push overflow ------------
    for w in [390, 780, 1180]:
        pg.set_viewport_size({"width": w, "height": 900})
        pg.wait_for_timeout(500)
        ov = pg.evaluate("""() => {
          const d = document.documentElement;
          return d.scrollWidth - d.clientWidth;
        }""")
        check(f"no horizontal overflow at {w}px", ov <= 1, ov)

    check("no page errors", not errors, errors[:3])
    b.close()

print("\n" + ("ALL PASS" if not fails else "FAILURES: " + ", ".join(fails)))
sys.exit(1 if fails else 0)
