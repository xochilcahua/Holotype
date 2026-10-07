# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Put a 10 on each art form and record what the app calls close and far.

This is the first calibration probe and it uses the app's OWN machinery end to end.
For every one of the 292 forms we set that single form to 10, ask computeNovelty for
its reading of every other form, and take the raw score as "how related is this to
what I already do". The lowest scores are the app's CLOSE and the highest are its
FAR -- the same ordering the user sees in the garden, not a reimplementation of it.

Two automated checks run over all 292 so the sample I read by eye is not the whole
story:

  sameCatNear  - how often the nearest neighbour shares a category. A high rate is
                 healthy (siblings should find each other); too LOW means the model is
                 reaching across the catalogue for company.
  sameCatFar   - how often a FARTHEST form shares a category. A high rate means the
                 model thinks the far end of the catalogue is its own family, which
                 is the classic sign of a hub form sitting close to everything.

The full dump is written to probe_ten.json so later probes can be diffed against it.
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
       'index.html?v=probe10')

SAMPLE = ['Painting', 'Dance', 'Fiction Writing', 'Guitar', 'Cooking',
          'Woodworking', 'Photography', 'Songwriting', 'Pottery', 'Cape',
          'Crochet', 'Stand-up Comedy', 'Data', 'Gardening', 'Jazz',
          'Calligraphy', 'Basketball', 'Electronics', 'Poetry', 'Ceramics']

with sync_playwright() as pw:
    br = pw.chromium.launch()
    pg = br.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(APP)
    pg.wait_for_timeout(1200)

    data = pg.evaluate("""() => {
      const out = [];
      state.discount = 0.5;
      for (const a of ART_FORMS) {
        state.mastery = {}; state.mastery[a.id] = 10;
        const nov = computeNovelty(state.mastery, state.discount);
        // Walk every OTHER form and read its novelty score for this person, rather
        // than trusting nov.order: order holds unrated candidates only, and
        // nearestId is null for the rated form, so it is not a safe way to recover
        // the self entry.
        const scored = [];
        for (const b of ART_FORMS) {
          if (b.id === a.id) continue;
          const o = nov.byId[b.id];
          if (!o) continue;
          scored.push({ id: b.id, name: b.name, cat: b.category,
                        dist: DIST[INDEX[b.id]][INDEX[a.id]], raw: o.raw });
        }
        scored.sort((x, y) => x.raw - y.raw);
        const shape = o => ({ id: o.id, name: o.name, cat: o.cat,
                              dist: +o.dist.toFixed(4), novel: Math.round(o.raw) });
        out.push({ id: a.id, name: a.name, cat: a.category,
                   near: scored.slice(0, 8).map(shape),
                   far: scored.slice(-8).reverse().map(shape) });
      }
      return out;
    }""")
    pg.close()
    br.close()

os.makedirs(os.path.join(_ROOT, 'out', 'audit'), exist_ok=True)
json.dump(data, open(os.path.join(_ROOT, 'out', 'audit', 'probe_ten.json'), 'w'), indent=1)
print('wrote out/audit/probe_ten.json')

# ---- automated checks over all 292 ---------------------------------------
same_near = [d for d in data if d['near'] and d['near'][0]['cat'] == d['cat']]
near_in_cat = sum(1 for d in data for n in d['near'] if n['cat'] == d['cat'])
far_in_cat = sum(1 for d in data for n in d['far'] if n['cat'] == d['cat'])
tot_near = sum(len(d['near']) for d in data)
tot_far = sum(len(d['far']) for d in data)

print('forms probed: %d' % len(data))
print('nearest neighbour shares a category: %d/%d (%.0f%%)'
      % (len(same_near), len(data), 100 * len(same_near) / len(data)))
print('of the 8 nearest, same category:     %d/%d (%.0f%%)'
      % (near_in_cat, tot_near, 100 * near_in_cat / tot_near))
print('of the 8 farthest, same category:    %d/%d (%.0f%%)'
      % (far_in_cat, tot_far, 100 * far_in_cat / tot_far))

if errs:
    print('RUNTIME ERRORS:', errs[:3])

# ---- the sample, read by eye ---------------------------------------------
by_name = {d['name']: d for d in data}
print('\n' + '=' * 100)
for want in SAMPLE:
    d = next((x for x in data if x['name'].startswith(want)), None)
    if not d:
        continue
    print('\n%s  [%s]' % (d['name'], d['cat']))
    print('  CLOSE  ' + ' | '.join('%s (%.2f)' % (n['name'], n['dist'])
                                   for n in d['near'][:6]))
    print('  FAR    ' + ' | '.join('%s (%.2f)' % (n['name'], n['dist'])
                                   for n in d['far'][:6]))