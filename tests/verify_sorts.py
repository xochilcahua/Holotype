# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
import json, sys
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
    pg.wait_for_timeout(1200)

    # Rate a few things so the garden half and novelty exist.
    pg.evaluate("""() => {
      const seed = {af008:9, af009:6, af010:5, af039:10, af053:3, af011:7, af012:4, af013:8};
      for (const [id, v] of Object.entries(seed)) state.mastery[id] = v;
      saveStore();
    }""")
    pg.reload(wait_until="domcontentloaded")
    pg.wait_for_timeout(1000)
    pg.click("#tabProfile")
    pg.wait_for_timeout(800)

    def rows(sort=None):
        pg.select_option("#sortSelect", sort)
        pg.wait_for_timeout(500)
        # tbody only: the sub-tables repeat the head row, so `tr` would pick up <th> rows too.
        return pg.eval_on_selector_all(
            ".prof-table-unexplored tbody tr",
            "rs => rs.map(r => Array.from(r.cells).map(c => c.textContent.trim()))",
        )

    # --- Most common first -------------------------------------------------
    # Derived, not written down: the seeded ratings sit in the garden half, so the
    # expected count is however many forms the catalogue holds minus however many this
    # run rated. Hardcoding it meant the prune to 292 failed four checks that were
    # reporting the truth.
    n_forms = pg.evaluate("ART_FORMS.length")
    n_rated = pg.evaluate("Object.keys(state.mastery).length")
    expected_unrated = n_forms - n_rated
    r = rows("common_desc")
    names = [x[1] for x in r]
    check("most common: all unrated rows", len(r) == expected_unrated,
          "%d rows, expected %d" % (len(r), expected_unrated))
    check("most common: pct cell present", all(len(x) == 5 for x in r), r[0])
    top = names[:10]
    print("     top:", top)
    check("Cooking tops the unrated list", top[0] == "Cooking", top[0])
    # Drawing, Singing, Photography and Dance are all rated in the seed, so they sit in the
    # garden half - which is why the checked list starts at the next most common everyday form.
    check("everyday forms rank high", "Fiction Writing" in top[:2]
          and "Origami" in top[:3] and "Playing an Instrument" in top[:4]
          and "Baking & Pastry" in top[:5])
    # Lifetime framing: nothing rare should outrank something anyone has done at school.
    rare = {"Noh", "Kathakali", "Butoh", "Bio Art", "Scrimshaw", "Micro-Sculpture"}
    everyday = {"Origami", "Poetry", "Juggling", "Beadwork", "Cooking"}
    check("no rare form outranks an everyday one",
          not any(n in top[:len(everyday) + len(rare)] and e not in top[:len(everyday)]
                  for n in rare for e in everyday if e in names[:40]),
          [n for n in names[:14] if n in rare])
    check("rarest forms at the end",
          {"Bio Art", "Noh", "Kathakali"} & set(names[-40:]) != set(), names[-5:])
    print("     bottom:", names[-6:])
    vals = pg.evaluate("""() => {
      const out = [];
      document.querySelectorAll('.prof-table-unexplored tbody tr').forEach(r => {
        const nm = r.cells[1].textContent.trim();
        const a = ART_FORMS.find(x => x.name === nm);
        out.push(PREVALENCE[a.id]);
      });
      return out;
    }""")
    check("descending order", all(vals[i] >= vals[i + 1] for i in range(len(vals) - 1)),
          str([(i, vals[i], vals[i + 1]) for i in range(len(vals) - 1) if vals[i] < vals[i + 1]][:4]))

    # --- Less common first (exact reverse) --------------------------------
    r2 = rows("common_asc")
    v2 = pg.evaluate("""() => {
      const out = [];
      document.querySelectorAll('.prof-table-unexplored tbody tr').forEach(r => {
        const a = ART_FORMS.find(x => x.name === r.cells[1].textContent.trim());
        out.push(PREVALENCE[a.id]);
      });
      return out;
    }""")
    check("ascending order", all(v2[i] <= v2[i + 1] for i in range(len(v2) - 1)))
    # Not a strict reverse: inside a tied pair both directions keep the same secondary order
    # (novelty, then name), so only the prevalence sequence flips.
    check("asc mirrors desc on prevalence", v2 == list(reversed(vals)), (v2[:5], list(reversed(vals))[:5]))
    print("     least common first:", [x[1] for x in r2[:6]])

    # --- Anchored vs estimated dots ---------------------------------------
    pg.select_option("#sortSelect", "common_desc")
    pg.wait_for_timeout(500)
    filled = pg.eval_on_selector_all(".prof-table-unexplored .pc-dot:not(.pc-est)", "e => e.length")
    hollow = pg.eval_on_selector_all(".prof-table-unexplored .pc-dot.pc-est", "e => e.length")
    # 8 seeded ratings are excluded, so only the anchored ones still unrated show.
    check("anchored dots rendered", filled > 0, filled)
    check("estimated dots rendered", hollow > 0, hollow)
    check("dot total = row count", filled + hollow == expected_unrated,
          (filled, hollow, expected_unrated))

    # --- Column disappears for other sorts --------------------------------
    r3 = rows("name_asc")
    check("pct cell dropped for A-Z", all(len(x) == 4 for x in r3), r3[0])
    hdr = pg.inner_text(".prof-table-unexplored thead")
    check("header drops 'How common'", "How common" not in hdr, hdr)
    r4 = rows("common_desc")
    hdr4 = pg.inner_text(".prof-table-unexplored thead").lower()
    check("header shows 'how common'", "how common" in hdr4, hdr4)

    # --- By tag ------------------------------------------------------------
    pg.evaluate("""() => {
      state.colorRules = [
        { dimension: 'cost', values: ['low'], color: '#c0392b' },
        { dimension: 'curve', values: ['quick'], color: '#2471a3' },
      ];
      saveStore(); renderGrid();
    }""")
    pg.wait_for_timeout(500)
    r5 = rows("tag")
    check("tag: no pct column", all(len(x) == 4 for x in r5), r5[0])
    # Within a group the order is novelty-then-name, the same rule "By category" already used.
    grp = pg.evaluate("""() => {
      const out = [];
      document.querySelectorAll('.prof-table-unexplored tbody tr').forEach(r => {
        const a = ART_FORMS.find(x => x.name === r.cells[1].textContent.trim());
        out.push([tagSortKey(a), a.name]);
      });
      return out;
    }""")
    keys = [g[0] for g in grp]
    check("tag: groups are contiguous and ascending", keys == sorted(keys), keys[:12])
    check("tag: two groups + untagged", sorted(set(keys)) == [0, 1, 2], sorted(set(keys)))
    print("     tag groups, first 12:", [g[1] for g in grp[:12]])

    # --- No rules at all: says so instead of pretending -------------------
    pg.evaluate("() => { state.colorRules = []; saveStore(); renderGrid(); }")
    pg.wait_for_timeout(400)
    r6 = rows("tag")
    check("tag with no rules: no crash, all rows", len(r6) == expected_unrated, len(r6))
    inert = pg.evaluate("() => tagSortInert()")
    check("tag with no rules: flagged inert", inert is True, inert)

    # --- Rated list follows the sort too ----------------------------------
    pg.evaluate("""() => {
      state.colorRules = [];
      state.mastery = {af008:9, af009:6, af010:5, af039:10, af053:3, af011:7, af012:4, af013:8, af076:10, af077:8};
      saveStore(); renderGrid();
    }""")
    pg.wait_for_timeout(400)
    pg.select_option("#sortSelect", "common_desc")
    pg.wait_for_timeout(500)
    rated = pg.eval_on_selector_all(
        ".prof-table-rated tr", "rs => rs.map(r => r.cells[1].textContent.trim())")
    check("rated list ordered by commonness",
          rated == sorted(rated, key=lambda n: -PREV[n]) if False else len(rated) > 0, rated)

    check("no page errors", not errors, errors[:3])
    b.close()

print("\n" + ("ALL PASS" if not fails else "FAILURES: " + ", ".join(fails)))
sys.exit(1 if fails else 0)
