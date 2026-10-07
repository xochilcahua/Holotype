# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Read the saved sessions in a folder and show what the app says about each.

The folder is $HOLOTYPE_SESSIONS, default tests/sample_sessions (synthetic). Point it at real session files to check real people.

These are the author's own people, not synthetic ones, so they are the strongest
evidence available: a reading that is wrong here is wrong about an actual person.
The whole classification is dumped -- the four genus bits, the regime, the leans and
the z-scores behind them -- because a wrong reading and a right-but-for-the-wrong-
reason reading look identical in the genus name alone.

Two questions this is here to answer:
  do two sessions that describe different people land on the same reading,
      and if so which bit collapsed them?
  what does a session's sociability bit say, and what is the z-score underneath it?
"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
APP_PATH = os.path.join(ROOT, "index.html")
import json
import glob
import os
from playwright.sync_api import sync_playwright

import pathlib as _pl
_ROOT = _pl.Path(__file__).resolve().parents[2]
APP = (_ROOT.as_uri() + '/'
       'index.html?v=sess1')
SESSIONS = sorted(glob.glob(str(_pl.Path(os.environ.get('HOLOTYPE_SESSIONS', _ROOT / 'tests' / 'sample_sessions')) / '*.json')))

data = []
for p in SESSIONS:
    d = json.load(open(p))
    data.append((os.path.basename(p), d['name'], d['ratings']))

with sync_playwright() as pw:
    br = pw.chromium.launch()
    pg = br.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(APP)
    pg.wait_for_timeout(1200)

    out = pg.evaluate("""(sess) => sess.map(([file, label, ratings]) => {
      state.mastery = {};
      for (const r of ratings) if (r.id in BY_ID) state.mastery[r.id] = r.rating;
      const bc = computeClassification();
      const pv = personalVector();
      const stats = personalStats();
      const bits = bc.genusId.split('');
      const NAMES = { breadth: ['focused', 'WIDE'], process: ['literal', 'planned'],
                      sociability: ['solo', 'COLLABORATIVE'], form: ['ephemeral', 'enduring'] };
      return {
        file, label, n: Object.keys(state.mastery).length,
        genusId: bc.genusId, genus: bc.genus ? bc.genus.name : null,
        tribe: bc.tribe, regime: bc.regimeId, regimeId: bc.regimeId,
        leans: bc.leans, topShare: +bc.topShare.toFixed(3),
        cats: bc.categoriesTouched, topKept: bc.topKept, ratedCount: bc.ratedCount,
        early: bc.early, confidence: bc.confidence,
        keptEnough: bc.keptEnough, socPoolSize: bc.socUsedCount,
        socUmbrellaOnly: bc.socUmbrellaOnly, socUsed: bc.socUsedCount,
        zProcess: +bc.zProcess.toFixed(3), zSocRaw: +bc.zSoc.toFixed(3),
        zForm: +bc.zForm.toFixed(3),
        genusMargin: bc.genusMargin, genusFragile: bc.genusFragile,
        genusFlips: bc.genusFlips,
        closeAxes: bc.closeAxes,
        bitsNamed: { breadth: NAMES.breadth[bits[0]], process: NAMES.process[bits[1]],
                     sociability: NAMES.sociability[bits[2]], form: NAMES.form[bits[3]] },
        avgRating: +stats.avgRating.toFixed(2),
        topCats: stats.catBreakdown.slice(0, 4).map(c => `${c.category} ${Math.round(c.pct*100)}%`),
        leanText: bc.leans ? bc.leans.map(l => l.tribe || l.name || String(l)).join(',') : '',
      };
    })""", [[f, l, r] for f, l, r in data])
    pg.close()
    br.close()

for r in out:
    print('=' * 78)
    print('%s  (%s)   %d ratings, avg %.2f' % (r['label'], r['file'], r['n'], r['avgRating']))
    print('  GENUS  %s  -> %s   [%s]' % (r['genusId'], r['genus'], r['tribe']))
    print('  bits   breadth=%s  process=%s  sociability=%s  form=%s'
          % (r['bitsNamed']['breadth'], r['bitsNamed']['process'],
             r['bitsNamed']['sociability'], r['bitsNamed']['form']))
    print('  regime %s (%s)   confidence=%s  early=%s' %
          (r['regimeId'], r['regime'], r['confidence'], r['early']))
    print('  leans  %s' % (r['leans'] or 'NONE'))
    print('  z      process=%+.2f  soc=%+.2f  form=%+.2f   (band margin=%s)'
          % (r['zProcess'], r['zSocRaw'], r['zForm'], r['genusMargin']))
    print('  soc    umbrellaOnly=%s  formsUsedForAxis=%s' % (r['socUmbrellaOnly'], r['socUsed']))
    print('  spread topShare=%.3f  cats=%d  topKept=%d  keptEnough=%s'
          % (r['topShare'], r['cats'], r['topKept'], r['keptEnough']))
    print('  cats   %s' % ' | '.join(r['topCats']))

if errs:
    print('\nRUNTIME ERRORS:', errs[:3])