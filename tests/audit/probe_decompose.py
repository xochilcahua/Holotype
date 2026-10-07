# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Break a distance into its six group contributions.

probe_extremes found the whole Writing & Language category sitting at the far end of
the catalogue (mean distance 0.53 against a catalogue mean of 0.41) while Craft &
Sculpture sat at the near end (0.33). That is a big enough asymmetry to be worth
asking whether it is real or an artefact, and "real or artefact" has a different answer
depending on WHICH term is doing it:

  if ONE group carries almost all of it, the group weights are miscalibrated and the
      fix is a number in GROUP_WEIGHTS;
  if the distance is spread evenly across all six, the writers' vectors genuinely sit
      apart from everyone else's and the honest fix is to leave it alone.

So each pair is decomposed rather than judged from the total. A pair the reader
believes is CLOSE is included as a control: if the same group is small there, it is
genuinely doing the work rather than dominating by accident.
"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
APP_PATH = os.path.join(ROOT, "index.html")
from playwright.sync_api import sync_playwright

import pathlib as _pl
_ROOT = _pl.Path(__file__).resolve().parents[2]
APP = (_ROOT.as_uri() + '/'
       'index.html?v=decomp1')

PAIRS = [
    ('Fiction Writing', 'Artistic Gymnastics', 'far'),
    ('Fiction Writing', 'Poetry', 'close'),
    ('Nonfiction & Journalism', 'Gardening & Plant Cultivation', 'far'),
    ('Papercraft', 'Artistic Gymnastics', 'far'),
    ('Papercraft', 'Illustration', 'close'),
    ('Literary Translation', 'Puzzle & Crossword Construction', 'close'),
    ('Speechwriting', 'Songwriting', 'far-ish'),
    ('Woodworking', 'Sculpture', 'close'),
    ('Dance', 'Danza de los Voladores (Flyers\' Ritual)', 'should be close'),
]

with sync_playwright() as pw:
    br = pw.chromium.launch()
    pg = br.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(APP)
    pg.wait_for_timeout(1200)

    res = pg.evaluate("""(pairs) => {
      const find = n => ART_FORMS.find(a => a.name === n);
      const G = AXIS_GROUPS, W = GROUP_WEIGHTS;
      const parts = (i, j) => {
        const a = EFF[i], b = EFF[j];
        return {
          domain:    W.domain * (0.5 * jaccardDist(a, b, G.domain) + 0.5 * rmsDist(a, b, G.domain)),
          sensory:   W.sensory * l1Dist(a, b, G.sensory),
          technique: W.technique * l1Dist(a, b, G.technique),
          material:  W.material * rmsDist(a, b, G.material),
          context:   W.context * l1Dist(a, b, G.context),
          category:  W.category * (ART_FORMS[i].category === ART_FORMS[j].category ? 0 : 1),
        };
      };
      return pairs.map(([an, bn, expect]) => {
        const fa = find(an), fb = find(bn);
        if (!fa || !fb) return { an, bn, missing: true };
        const p = parts(INDEX[fa.id], INDEX[fb.id]);
        return { an, bn, expect, total: computePairDistance(INDEX[fa.id], INDEX[fb.id]),
                 parts: p };
      });
    }""", PAIRS)
    pg.close()
    br.close()

# SELF-CHECK. This tool re-states the app's distance formula to split it into groups. If
# the app's formula changes and this copy does not, the split would attribute distance to
# the wrong group and still look plausible. So the parts must add up to the app's own total.
_drift = [r for r in res if not r.get('missing')
          and abs(sum(r['parts'].values()) - r['total']) > 1e-6]
if _drift:
    raise SystemExit('STALE: the parts here no longer sum to computePairDistance (e.g. %s <-> %s). '
                     'Update the `parts` function to match src/model/distances.js.'
                     % (_drift[0]['an'], _drift[0]['bn']))

names = ['domain', 'technique', 'sensory', 'material', 'context', 'category']
print('%-52s %6s  %s' % ('pair', 'total', '  '.join('%9s' % n for n in names)))
print('-' * 120)
for r in res:
    if r.get('missing'):
        print('%-52s MISSING' % (r['an'] + ' <-> ' + r['bn']))
        continue
    cells = '  '.join('%9.4f' % r['parts'][n] for n in names)
    share = {n: r['parts'][n] / r['total'] for n in names} if r['total'] else {}
    top = max(share, key=share.get)
    print('%-52s %6.3f  %s   <- %s %.0f%%  (%s)'
          % (r['an'][:25] + ' <-> ' + r['bn'][:25], r['total'], cells,
             top, 100 * share[top], r['expect']))
if errs:
    print('RUNTIME ERRORS:', errs[:3])