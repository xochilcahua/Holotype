# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Assert the distance model against pairs whose answer is not arguable.

A CORRECTION worth recording: an earlier version of this check asked "which of these
two forms is nearer the other", which is meaningless -- DIST is symmetric, so
DIST[i][j] and DIST[j][i] are the same number and the comparison can only ever come
out one way. It reported five failures that did not exist. Comparing a pair against
something asymmetric, its own distance to the rest of the catalogue, is the question
that means something.

So each declared pair is checked against the two forms' own mean distances:

  CLOSE  dist(a,b) must be BELOW both forms' mean distance to everything else --
         these two genuinely belong together more than either belongs to a stranger.
  FAR    dist(a,b) must be ABOVE both -- these two are further apart than typical.

The pass rate is the calibration score. The second half of the script does the same
job for the metric choice on the domain group, which still scores itself half on
jaccard and may have the same sparse-magnitude flaw that was just fixed on sensory.
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
       'index.html?v=cal2')

CLOSE = [
    ('Painting', 'Drawing'), ('Painting', 'Illustration'), ('Painting', 'Printmaking'),
    ('Ceramics & Pottery', 'Sculpture'), ('Ceramics & Pottery', 'Mosaic'),
    ('Woodworking', 'Wood Turning'), ('Woodworking', 'Blacksmithing'),
    ('Cooking', 'Baking & Pastry'), ('Cooking', 'Chocolate Making & Confectionery'),
    ('Fiction Writing', 'Poetry'), ('Fiction Writing', 'Nonfiction & Journalism'),
    ('Dance', 'Choreography'), ('Dance', 'Flamenco'), ('Calligraphy', 'Icon Painting'),
    ('Songwriting', 'Spoken Word & Rap'), ('Weaving', 'Sewing & Tailoring'),
    ('Gardening & Plant Cultivation', 'Bonsai'), ('Distilling', 'Brewing, Wine & Spirits'),
    ('Fermentation & Pickling', 'Cheese Making'),
]
FAR = [
    ('Painting', 'Puzzle & Crossword Construction'),
    ('Painting', 'Charcuterie & Butchery'),
    ('Woodworking', 'Invented Languages'),
    ('Fiction Writing', 'Distilling'),
    ('Dance', 'Type Design'),
    ('Cooking', 'Type Design'),
    ('Ceramics & Pottery', 'Puzzle & Crossword Construction'),
    ('Photography', 'Cheese Making'),
    ('Calligraphy', 'Puzzle & Crossword Construction'),
    ('Songwriting', 'Cheese Making'),
    ('Gardening & Plant Cultivation', 'Data Visualization & Infographic Design'),
    ('Woodworking', 'Micro-Sculpture'),
]

# ---- ADDED IN PASS 03, by the reviewer, not the author -------------------------
# The list above predates this review. Coverage gaps measured by reading it rather
# than by taste: the author's CLOSE list touches Visual, Craft, Food, Writing and
# two dance pairs, but has NO music-music pair, no technology pair, no sport pair
# (Sport & Martial Arts did not exist when the list was written), and nothing that
# tests whether the model separates two things in the same world from two things in
# different ones within one category.
#
# Each pair below is one whose answer I would defend without seeing the model, and
# they are deliberately spread across all twelve categories so a pass rate is not
# quietly carried by Visual and Craft.
#
# Two of them are tests I expect to FAIL, and I am leaving them in if they fail
# rather than quietly dropping them:
#   Woodworking <-> Sculpture   I expect this to be close (joinery and modelling are
#                               both subtractive hand-craft) and the author's list has
#                               Ceramics<->Sculpture but not this one.
#   Stained & Fused Glass <-> Mosaic  I expect close, and probe_ten reports Papercraft
#                               as stained glass's nearest neighbour, which I doubt.
CLOSE += [
    ('Knitting & Crochet', 'Macrame'),
    ('Candle Making', 'Soap Making'),
    ('Songwriting', 'Music Composition'),
    ('Jewelry Making', 'Silversmithing'),
    ('Weaving', 'Rug Hooking & Tufting'),
    ('Quilting', 'Rug Hooking & Tufting'),
    ('Glassblowing', 'Stained & Fused Glass'),
    ('Stained & Fused Glass', 'Mosaic'),
    ('Bonsai', 'Topiary'),
    ('Improv Theater', 'Stand-Up Comedy'),
    ('Poetry', 'Spoken Word & Rap'),
    ('Origami', 'Paper Cutting (Kirigami & Scherenschnitte)'),
    ('Metal Casting', 'Blacksmithing'),
    ('Bookbinding', 'Book Carving'),
    ('Woodworking', 'Sculpture'),
]
FAR += [
    ('Puzzle & Crossword Construction', 'Baking & Pastry'),
    ('Scat Singing', 'Wood Turning'),
    ('Sushi Making', 'Metal Casting'),
    ('Beadwork', 'Nonfiction & Journalism'),
    ('Puppetry', 'Fermentation & Pickling'),
    ('Creative Taxidermy', 'Songwriting'),
]

with sync_playwright() as pw:
    br = pw.chromium.launch()
    pg = br.new_page()
    pg.goto(APP)
    pg.wait_for_timeout(1200)
    D = pg.evaluate("""() => ({
      eff: EFF, groups: AXIS_GROUPS, weights: GROUP_WEIGHTS,
      forms: ART_FORMS.map(a => ({ name: a.name, cat: a.category })),
    })""")
    pg.close()
    br.close()

EFF, G, W = D['eff'], D['groups'], D['weights']
F = D['forms']
N = len(F)
NAME = {f['name']: i for i, f in enumerate(F)}


def jaccard(a, b, ax):
    mn = mx = 0.0
    for k in ax:
        x, y = a[k], b[k]
        mn, mx = (mn + x, mx + y) if x < y else (mn + y, mx + x)
    return 0.0 if mx == 0 else 1 - mn / mx


def rms(a, b, ax):
    return (sum((a[k] - b[k]) ** 2 for k in ax) / len(ax)) ** 0.5


def l1(a, b, ax):
    return sum(abs(a[k] - b[k]) for k in ax) / len(ax)


def build(dfun):
    m = [[0.0] * N for _ in range(N)]
    for i in range(N):
        for j in range(i + 1, N):
            m[i][j] = m[j][i] = dfun(i, j)
    mean = [sum(m[i]) / (N - 1) for i in range(N)]
    return m, mean


def make(domain_fun):
    def dfun(i, j):
        a, b = EFF[i], EFF[j]
        return (W['domain'] * domain_fun(a, b)
                + W['sensory'] * l1(a, b, G['sensory'])
                + W['technique'] * l1(a, b, G['technique'])
                + W['material'] * rms(a, b, G['material'])
                + W['context'] * l1(a, b, G['context'])
                + W['category'] * (0 if F[i]['cat'] == F[j]['cat'] else 1))
    return dfun


DOMAIN_VARIANTS = {
    '0.5jac+0.5rms (NOW)': lambda a, b: 0.5 * jaccard(a, b, G['domain'])
                                       + 0.5 * rms(a, b, G['domain']),
    'rms               ': lambda a, b: rms(a, b, G['domain']),
    'l1                ': lambda a, b: l1(a, b, G['domain']),
    'jaccard           ': lambda a, b: jaccard(a, b, G['domain']),
    '0.5jac+0.5l1      ': lambda a, b: 0.5 * jaccard(a, b, G['domain'])
                                      + 0.5 * l1(a, b, G['domain']),
}


def score(dfun):
    m, mean = build(dfun)
    bad = []
    for a, b in CLOSE:
        i, j = NAME[a], NAME[b]
        if not (m[i][j] < mean[i] and m[i][j] < mean[j]):
            bad.append('CLOSE %-30s %.3f vs means %.3f/%.3f' % (a + ' <-> ' + b, m[i][j], mean[i], mean[j]))
    for a, b in FAR:
        i, j = NAME[a], NAME[b]
        if not (m[i][j] > mean[i] and m[i][j] > mean[j]):
            bad.append('FAR   %-30s %.3f vs means %.3f/%.3f' % (a + ' <-> ' + b, m[i][j], mean[i], mean[j]))
    nn = sum(1 for i in range(N)
             if F[min((k for k in range(N) if k != i), key=lambda k: m[i][k])]['cat'] == F[i]['cat'])
    return bad, nn / N, len(CLOSE) + len(FAR)


print('%-20s %7s %8s %9s' % ('domain metric', 'PASS', 'of', 'NN-in-cat'))
print('-' * 50)
best = None
for label, dfun in DOMAIN_VARIANTS.items():
    bad, nn, tot = score(make(dfun))
    print('%-20s %7d %8d %8.0f%%' % (label, tot - len(bad), tot, 100 * nn))
    if best is None or len(bad) < best[1]:
        best = (label, len(bad))
print('\nbest: %s (%d failures)' % best)

bad, nn, tot = score(make(DOMAIN_VARIANTS['0.5jac+0.5rms (NOW)']))
print('\n=== failures with the domain metric as it stands ===')
print('\n'.join(bad) if bad else '  none')