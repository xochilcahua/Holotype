# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""A saved session must survive the catalogue shrinking under it.

When the dance prune removed 14 rows, anyone who had already rated Ballet, Tap or
Chalk & Pavement Art had that work sitting in localStorage pointing at ids the build
no longer has. The app claims those are parked with a reason rather than dropped, so
this checks the claim three ways: the app still loads, the ratings it CAN still place
are intact, and the ones it cannot are parked rather than silently used.

A ghost row or a NaN in the plant shape would be the failure modes worth catching, so
both the rendered output and the derived numbers are inspected, not just the state.
"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
APP_PATH = os.path.join(ROOT, "index.html")
import json
from playwright.sync_api import sync_playwright

import pathlib as _pl
_ROOT = _pl.Path(__file__).resolve().parents[2]
APP = (_ROOT.as_uri() + '/'
       'index.html?v=orphan1')

# A session written against the 306-form catalogue: two live ratings plus one rating
# for every id the prune removed.
SESSION = {
    "mastery": {
        "af001": 7,          # Fiction Writing, still exists
        "af008": 4,          # Painting, still exists
        "af244": 9,          # Ballet          - removed
        "af247": 6,          # Tap Dance       - removed
        "af253": 8,          # Folk & Traditional - removed
        "af144": 5,          # Chalk & Pavement  - removed
        "af999": 10,         # never existed at all
    },
    "ratingExtras": {},
    "parked": {"ratings": [], "tags": []},
    "plantSeed": "", "discount": 0.5, "themeChoice": None,
    "colorRules": [], "exporterName": "", "exportSections": {},
}

with sync_playwright() as pw:
    br = pw.chromium.launch()
    pg = br.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: errs.append('console.error: ' + m.text)
          if m.type == 'error' and 'Failed to load resource' not in m.text else None)
    pg.goto(APP)
    pg.wait_for_timeout(800)
    pg.evaluate('k => localStorage.setItem(k, %s)' % json.dumps(json.dumps(SESSION)),
                'holotype_state_v1')
    pg.reload()
    pg.wait_for_timeout(1500)

    live = pg.evaluate('Object.entries(state.mastery)')
    parked = pg.evaluate('state.parked')
    rows = pg.evaluate('document.querySelectorAll(".flower").length')
    ghost = pg.evaluate(
        "Array.from(document.querySelectorAll('.flower'))"
        ".map(e => e.textContent || '')"
        ".filter(t => /Ballet|Tap Dance|Folk & Traditional|Chalk/.test(t))")
    pv = pg.evaluate('JSON.stringify(personalVector())')
    bc = pg.evaluate('JSON.stringify(computeClassification())')
    pg.close()
    br.close()

bad = []
print('mastery after reload:', live)
print('parked ratings     :', json.dumps(parked.get('ratings', []), indent=None)[:400])
print('parked tags        :', parked.get('tags'))
print('rendered card rows :', rows)

for want, fid in (('af001', 'af001'), ('af008', 'af008')):
    if not any(k == fid and v for k, v in live):
        bad.append('lost a rating that still exists: %s' % want)

if not parked.get('ratings'):
    bad.append('nothing was parked -- the removed ratings were dropped, not parked')

kept = dict(live)
for gone in ('af244', 'af247', 'af253', 'af144', 'af999'):
    if gone in kept:
        bad.append('%s is still in active mastery' % gone)

if ghost:
    bad.append('ghost rows rendered for removed forms: %r' % ghost[:3])

if 'null' in pv or 'NaN' in pv:
    bad.append('personalVector is degenerate: %s' % pv[:120])
if 'NaN' in bc:
    bad.append('classification contains NaN')

if errs:
    bad.append('runtime errors: %s' % errs[:3])

print()
print('FAIL:\n  ' + '\n  '.join(bad) if bad else
      'PASS: the session survived the catalogue shrinking; removed ratings are '
      'parked with a reason, live ratings intact, no ghost rows, no NaN')
raise SystemExit(1 if bad else 0)