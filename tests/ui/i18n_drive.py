# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Drives the app through every screen that shows translatable text.

Shared by tools/locales.py (extract: which strings does the app ask for?) and
tests/ui/verify_i18n_coverage.py (is any visible English left over?). `visit(pg, label)` is called after each
screen is on display; both callers decide what to do with it.

The app is a file:// page of classic scripts, so everything here goes through the page's own globals
(state, openDetail, renderGrid ...) exactly as the keyboard and mouse handlers do.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAMPLES = ['sample-a', 'sample-b', 'sample-c']


def load_ratings(name):
    with open(os.path.join(ROOT, 'tests', 'sample_sessions', name + '.json'), encoding='utf-8') as fh:
        return json.load(fh)['ratings']


def drive(pg, visit, every_sheet=False):
    """Walk the app. `every_sheet` opens the detail sheet of all catalogue forms (slow, needed for extraction)."""
    def settle(ms=250):
        pg.wait_for_timeout(ms)

    def close_overlays():
        pg.keyboard.press('Escape')
        pg.evaluate("() => { document.querySelectorAll('#filterRoot,#settingsRoot,#helpRoot,#modalRoot,#exportRoot').forEach(r => { if (r.firstElementChild && typeof closeHelp === 'function' && r.id === 'helpRoot') closeHelp(); }); }")
        settle(120)

    visit('garden-empty')
    pg.evaluate("() => { state.mastery = {af001:7,af008:5,af009:4,af003:6,af053:3,af038:8,af002:2,af010:9}; renderGrid(); }")
    settle()
    visit('garden-rated')

    for label, js in [
        ('filters', "document.getElementById('filterToggle').click()"),
        ('settings', "document.getElementById('settingsToggle').click()"),
        ('help', "document.getElementById('helpToggle').click()"),
        ('help-glossary', "document.getElementById('tabGloss') && document.getElementById('tabGloss').click()"),
        ('reset-confirm', "document.getElementById('resetToggle').click()"),
    ]:
        close_overlays()
        pg.evaluate(js)
        settle(350)
        visit(label)
    close_overlays()

    ids = ['af001', 'af053', 'af008'] if not every_sheet else None
    if every_sheet:
        pg.evaluate("() => { for (const a of ART_FORMS) openDetail(a.id, { quiet: true }); }")
        visit('all-detail-sheets')
        close_overlays()
    else:
        for fid in ids:
            pg.evaluate("(id) => openDetail(id)", fid)
            settle(300)
            visit('detail-' + fid)
            close_overlays()

    for name in SAMPLES:
        ratings = load_ratings(name)
        pg.evaluate("(r) => { state.mastery = {}; r.forEach(x => state.mastery[x.id] = x.rating); renderGrid(); document.getElementById('tabProfile').click(); }", ratings)
        settle(500)
        pg.evaluate("() => { const d = document.querySelector('.profile-wrap'); if (d) d.open = true; }")
        visit('herbarium-' + name)
        pg.evaluate("() => buildPrintExport()")
        settle(200)
        visit('print-' + name, print_view=True)
        pg.evaluate("() => document.getElementById('tabGarden').click()")

    # Sorts and the herbarium lists that depend on them.
    pg.evaluate("() => document.getElementById('tabProfile').click()")
    for v in ['common_asc', 'novelty_asc', 'novelty_desc', 'name_asc', 'category', 'tag']:
        pg.evaluate("(v) => { const s = document.getElementById('sortSelect'); s.value = v; s.dispatchEvent(new Event('change')); }", v)
        settle(200)
        visit('herbarium-sort-' + v)
    pg.evaluate("() => document.getElementById('tabGarden').click()")
    for v in ['category', 'tag', 'novelty_desc']:
        pg.evaluate("(v) => { const s = document.getElementById('sortSelect'); s.value = v; s.dispatchEvent(new Event('change')); }", v)
        settle(200)
        visit('garden-sort-' + v)


    # Filters, empty results, colour tags and a named reader: the states that show the less common wording.
    pg.evaluate("""() => {
      const safe = (f) => { try { f(); } catch (e) { /* a state this build does not have */ } };
      safe(() => { state.exporterName = 'Ada'; });
      safe(() => { state.colorRules = [
        { dimension: 'category', values: ['Visual Arts'], color: '#c0392b' },
        { dimension: 'cost', values: ['medium', 'high'], color: '#2a7f62' },
        { dimension: 'curve', values: ['moderate'], color: '#2a6fa0' },
        { dimension: 'self', values: ['yes'], color: '#8a6d3b' },
        { dimension: 'space', values: ['studio'], color: '#6b3fa0' },
        { dimension: 'distance', values: [], min: 0, max: 40, color: '#a02a8a' } ]; });
      safe(() => { ui.activeCategories = new Set(['Music & Sound']); ui.activeTiers = new Set(['uncharted']); ui.query = 'dr'; });
      safe(() => renderGrid());
    }""")
    settle(300)
    visit('garden-filtered')
    for label, js in [('filters-active', "document.getElementById('filterToggle').click()"),
                      ('settings-with-rules', "document.getElementById('settingsToggle').click()")]:
        close_overlays()
        pg.evaluate(js)
        settle(350)
        visit(label)
    close_overlays()
    pg.evaluate("() => { ui.query = 'zzzzzzzz'; renderGrid(); }")
    settle(200)
    visit('garden-no-results')
    pg.evaluate("() => { ui.query = ''; ui.activeCategories = new Set(); ui.activeTiers = new Set(); renderGrid(); document.getElementById('tabProfile').click(); }")
    settle(400)
    visit('herbarium-named')
    pg.evaluate("() => document.getElementById('tabGarden').click()")

    # Session-file feedback: the messages the parser produces for bad or newer files.
    pg.evaluate("""() => {
      const bad = ['not json', '{}', JSON.stringify({ format: 'holotype-session', schemaVersion: 99, requires: ['x'], ratings: [{ id: 'zz', rating: 3 }] }),
                   JSON.stringify({ format: 'holotype-session', schemaVersion: 2, requires: [], ratings: [{ id: 'af001', rating: 'x' }], tags: [{ nope: 1 }], sort: 'sideways' })];
      for (const text of bad) {
        try {
          const res = parseSessionFile(text);
          const norm = res && (res.norm || res);
          [res && res.error, ...(((res && res.report) || (norm && norm.report) || {}).notes || [])].filter(Boolean).forEach((m) => translateSessionMessage(String(m)));
          if (res && res.report) sessionReportHTML(res.report, 'x');
        } catch (e) { /* the parser reports problems through its return value; ignore anything else */ }
      }
    }""")
    visit('session-messages')
