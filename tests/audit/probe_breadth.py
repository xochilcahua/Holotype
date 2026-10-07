# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Does the breadth bit actually work, or is the 4% figure a real defect?

The population check reports that only 4% of people with 12+ ratings are called wide.
That looks alarming until you look at why: the population model gives every TYPE a
reach list drawn from its own category, so a hobby dancer rates Dance, Flamenco,
Noh, Butoh and Choreography and touches one field. Its largest-field share is
therefore 1.00, and "focused" is the correct reading of that person. A threshold
loosened until the population model agreed would start calling genuinely single-field
people wide, which is worse than a low number.

So the model is not the test. This checks the bit directly against hand-built people
whose answer is not arguable -- one spanning eight categories, one sitting entirely in
a single field at the same number of ratings -- and confirms the bit separates them.
The comparison matters more than either number: the same rating COUNT must produce
opposite readings when the spread differs, or the bit is measuring count rather than
spread.
"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
APP_PATH = os.path.join(ROOT, "index.html")
from playwright.sync_api import sync_playwright

import pathlib as _pl
_ROOT = _pl.Path(__file__).resolve().parents[2]
APP = (_ROOT.as_uri() + '/'
       'index.html?v=breadth1')

# Eight different categories, one form each. The app's own F33 fixture uses this set.
EIGHT_CATEGORIES = ['Drawing', 'Singing', 'Cooking', 'Woodworking',
                    'Acting', 'Photography', 'Ceramics & Pottery', 'Poetry']
# Eight forms in ONE category, same count, same ratings.
EIGHT_ONE_FIELD = ['Weaving', 'Embroidery', 'Quilting', 'Crochet',
                   'Rug Hooking & Tufting', 'Knitting', 'Sewing & Tailoring',
                   'Papercraft']

CASES = [
    ('8 forms, 8 categories', [(n, 5) for n in EIGHT_CATEGORIES]),
    ('8 forms, 1 category ', [(n, 5) for n in EIGHT_ONE_FIELD]),
    ('24 forms, many fields', [(n, 5) for n in EIGHT_CATEGORIES * 3]),
    ('1 form only', [('Drawing', 5)]),
    ('2 forms, 2 categories', [('Drawing', 6), ('Cooking', 6)]),
]

with sync_playwright() as pw:
    br = pw.chromium.launch()
    pg = br.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(APP)
    pg.wait_for_timeout(1200)

    out = pg.evaluate("""(cases) => cases.map(([label, ratings]) => {
      const find = n => ART_FORMS.find(a => a.name === n);
      state.mastery = {};
      for (const [n, r] of ratings) { const f = find(n); if (f) state.mastery[f.id] = r; }
      const bc = computeClassification();
      return { label,
               // NOTE: computeClassification does not export a `breadth` field.
               // The bit is the FIRST CHARACTER of genusId, which is built as
               // `${breadth}${process}${sociability}${form}`. Reading bc.breadth here
               // returns undefined and silently reports everybody as focused.
               breadth: Number(bc.genusId[0]),
               topShare: +bc.topShare.toFixed(3),
               cats: bc.categoriesTouched,
               topKept: bc.topKept,
               genus: bc.genusId };
    })""", [[l, r] for l, r in CASES])
    pg.close()
    br.close()

print('%-24s %8s %9s %6s %7s  %s' %
      ('person', 'breadth', 'topShare', 'cats', 'topKept', 'genus bits'))
print('-' * 72)
for r in out:
    print('%-24s %8s %9.3f %6s %7d  %s'
          % (r['label'], 'WIDE' if r['breadth'] else 'focused',
             r['topShare'], r['cats'], r['topKept'], r['genus']))

wide = [r for r in out if r['breadth']]
focus = [r for r in out if not r['breadth']]
print('\n%d/%d wide' % (len(wide), len(out)))
bad = []
if not wide:
    bad.append('nobody is ever called wide')
if not focus:
    bad.append('everybody is called wide')
eight_multi = next((r for r in out if r['label'].startswith('8 forms, 8')), None)
eight_one = next((r for r in out if r['label'].startswith('8 forms, 1')), None)
if eight_multi and eight_one and eight_multi['breadth'] == eight_one['breadth']:
    bad.append('8 forms across 8 fields and 8 forms in 1 field give the SAME reading '
               '- the bit is counting ratings, not measuring spread')
if errs:
    bad.append('runtime errors: %s' % errs[:2])
print('\n' + ('FAIL: ' + '; '.join(bad) if bad else
              'PASS: the bit separates genuine spread from genuine focus at the same '
              'rating count'))