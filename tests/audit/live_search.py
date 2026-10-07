# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Run the collapsed terms through the app's OWN search() in a real browser.

The Python suites reimplement the matcher. This one does not: it loads the actual
page and calls the page's search() function, so if the aliases work the way the
source reads, the real UI agrees. Cache-busted with a query string so a stale copy
of the file cannot pass this.
"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
APP_PATH = os.path.join(ROOT, "index.html")
import sys
from playwright.sync_api import sync_playwright

import pathlib as _pl
_ROOT = _pl.Path(__file__).resolve().parents[2]
APP = (_ROOT.as_uri() + '/'
       'index.html?v=danceprune2')

CASES = {
    'ballet': 'af053', 'ballroom & latin dance': 'af053', 'tap dance': 'af053',
    'belly dance': 'af053', 'raqs sharqi': 'af053', 'breaking': 'af053',
    'folklorico': 'af053', 'māori dance': 'af053',
    'social partner dance': 'af053', 'hip-hop': 'af053',
    'sidewalk chalk': 'af018', '3d street painting': 'af018',
}

with sync_playwright() as pw:
    br = pw.chromium.launch()
    pg = br.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(APP)
    pg.wait_for_timeout(1200)

    total = pg.evaluate('ART_FORMS.length')
    results = pg.evaluate(
        'cs => cs.map(([q, want]) => [q, want, search(q).slice(0, 5)])',
        [[q, w] for q, w in CASES.items()])

    # The rows we kept must still be their own rows, reachable by their own name.
    kept = pg.evaluate(
        "['Capoeira','Flamenco','Chinese Opera'].map(n => [n, !!ART_FORMS.find(f => f.name.startsWith(n))])")

    # And the collapsed ids must really be gone from the data.
    gone = pg.evaluate(
        "['af244','af248','af253','af144'].filter(i => ART_FORMS.some(f => f.id === i))")

    pg.close()
    br.close()

print('ART_FORMS.length = %d' % total)
bad = []
for q, want, hits in results:
    ok = want in hits
    names = ''
    print('  %-26s -> %-6s %s' % (q, 'OK' if ok else 'MISS', hits if not ok
                                 else 'rank %d' % (hits.index(want) + 1)))
    if not ok:
        bad.append(q)

for name, present in kept:
    print('  kept row %-16s %s' % (name, 'present' if present else 'GONE'))
    if not present:
        bad.append(name)

print('  collapsed ids still present:', gone or 'none')
if gone:
    bad.append('collapsed ids present: %s' % gone)

print('\n' + ('FAIL: %s' % bad if bad or errs else
              'PASS: every collapsed term finds its survivor in the live app'))
if errs:
    print('runtime errors:', errs[:5])
sys.exit(1 if (bad or errs or total != 292) else 0)