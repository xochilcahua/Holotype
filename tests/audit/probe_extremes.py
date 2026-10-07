# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Find the extremes of the distance model: hubs, isolates, and specific pair checks.

probe_ten showed the bulk of the catalogue reads well. This looks for the forms that
break the pattern, because a calibration is only as good as its worst case.

Three questions:

  HUBS      A form that is close to everything ends up recommending itself back to
            everyone, which is the classic failure of a similarity model. The mean
            distance to all 291 others is the score; low is suspicious.
  ISOLATES  A form far from everything is defensible only if it really is unlike
            everything -- so each isolate's own nearest neighbours are printed, to
            see whether it has company it is failing to find.
  PAIRS     Named pairs whose relative order should not be arguable, checked
            directly against the model rather than inferred from a sample.
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
       'index.html?v=extremes1')

# (a, b, closer_to) -- closer_to is the one that should have the SMALLER distance.
PAIRS = [
    ('Dance', 'Choreography', 'Dance'),
    ('Dance', 'Danza de los Voladores (Flyers\' Ritual)', 'Dance'),
    ('Dance', 'Flamenco', 'Dance'),
    ('Dance', 'Ballet', 'Dance'),
    ('Painting', 'Drawing', 'Painting'),
    ('Fiction Writing', 'Poetry', 'Fiction Writing'),
    ('Guitar', 'Singing', None),          # None = only report, do not assert
    ('Woodworking', 'Metalworking', None),
    ('Speechwriting', 'Fiction Writing', None),
    ('Danza de los Voladores (Flyers\' Ritual)', 'Capoeira', None),
    ('Danza de los Voladores (Flyers\' Ritual)', 'Sushi Making', None),
]

with sync_playwright() as pw:
    br = pw.chromium.launch()
    pg = br.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(APP)
    pg.wait_for_timeout(1200)

    res = pg.evaluate("""() => {
      const find = n => ART_FORMS.find(a => a.name === n);
      const meanOf = i => { let t = 0; for (let j = 0; j < N; j++)
        if (j !== i) t += DIST[i][j]; return t / (N - 1); };
      const mean = [], iso = [];
      for (let i = 0; i < N; i++) {
        let s = 0; for (let j = 0; j < N; j++) if (j !== i) s += DIST[i][j];
        const m = s / (N - 1);
        mean.push({ id: ART_FORMS[i].id, name: ART_FORMS[i].name,
                    cat: ART_FORMS[i].category, mean: +m.toFixed(4) });
        const near = [];
        for (let j = 0; j < N; j++) if (j !== i) near.push(j);
        near.sort((x, y) => DIST[i][x] - DIST[i][y]);
        iso.push({ name: ART_FORMS[i].name, mean: +m.toFixed(4),
                   near: near.slice(0, 5).map(j => ({
                     name: ART_FORMS[j].name,
                     cat: ART_FORMS[j].category,
                     d: +DIST[i][j].toFixed(3) })) });
      }
      const pairs = %s.map(([a, b, want]) => {
        const fa = find(a), fb = find(b);
        if (!fa || !fb) return { a, b, missing: true };
        const d = +DIST[INDEX[fa.id]][INDEX[fb.id]].toFixed(4);
        // "Which of these two is nearer the other" is not a question about a
        // SYMMETRIC matrix -- both directions are the same number, so that
        // comparison could only ever answer one way, and it reported five failures
        // that did not exist. Ask instead whether the pair sits closer than
        // either form's own average distance to everything else.
        const meanA = meanOf(INDEX[fa.id]), meanB = meanOf(INDEX[fb.id]);
        return { a, b, catA: fa.category, catB: fb.category, dist: d, want,
                 meanA: +meanA.toFixed(3), meanB: +meanB.toFixed(3),
                 closerThanBoth: d < meanA && d < meanB,
                 furtherThanBoth: d > meanA && d > meanB };
      });
      return { mean, iso, pairs };
    }""" % json.dumps([[a, b, w] for a, b, w in PAIRS]))
    pg.close()
    br.close()

mean = sorted(res['mean'], key=lambda r: r['mean'])
iso = {r['name']: r for r in res['iso']}

print('=== HUBS: closest to everything (low mean distance) ===')
for r in mean[:10]:
    print('  %.3f  %-38s [%s]' % (r['mean'], r['name'], r['cat']))
print('\n  catalogue mean distance: %.3f' % (
    sum(r['mean'] for r in res['mean']) / len(res['mean'])))

print('\n=== ISOLATES: furthest from everything, with their nearest company ===')
for r in sorted(res['iso'], key=lambda r: -r['mean'])[:10]:
    print('\n  %.3f  %s' % (r['mean'], r['name']))
    for n in r['near']:
        print('        %.3f  %-34s [%s]' % (n['d'], n['name'], n['cat']))

print('\n=== NAMED PAIRS ===')
fails = []
for p in res['pairs']:
    if p.get('missing'):
        print('  %-30s <-> %-30s MISSING from catalogue' % (p['a'], p['b']))
        continue
    if p['want']:
        ok = p['want'] and (p['closerThanBoth'] if p['want'] == 'close'
                               else p['furtherThanBoth'])
        if not ok:
            fails.append('%s <-> %s: %.4f vs means %.3f/%.3f, wanted %s'
                         % (p['a'], p['b'], p['dist'], p['meanA'], p['meanB'],
                            p['want']))
        print('  %-30s <-> %-30s %.4f  means %.3f/%.3f  %s'
              % (p['a'], p['b'], p['dist'], p['meanA'], p['meanB'],
                 'ok' if ok else 'WRONG'))
    else:
        print('  %-30s <-> %-30s %.4f  means %.3f/%.3f'
              % (p['a'], p['b'], p['dist'], p['meanA'], p['meanB']))

print('\n' + ('PAIR FAILURES:\n  ' + '\n  '.join(fails) if fails
             else 'all asserted pair orderings hold'))
if errs:
    print('RUNTIME ERRORS:', errs[:3])
os.makedirs(os.path.join(_ROOT, 'out', 'audit'), exist_ok=True)
json.dump(res['mean'], open(os.path.join(_ROOT, 'out', 'audit', 'means.json'), 'w'), indent=1)
print('wrote out/audit/means.json')