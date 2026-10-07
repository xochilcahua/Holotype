# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Check that every collapsed subject is still reachable by typing its old name.

A collapse must not lose a subject. If someone who has always known Holotype as having a
Ballet row types "ballet", they must still land somewhere real -- otherwise the prune
has quietly deleted a topic rather than folding it away.

This mirrors the app's real matcher rather than doing a plain substring test.
Holotype's search is:

    name.includes(q) || startsAWord(aka, q) || (q.length >= 3 && startsAWord(tag, q))

where q is accent-folded and lowercased. A query only matches an alias if it begins
exactly at a word boundary. Testing with substring matching passes on "belly" while
the real app cannot find "belly dance" -- which is the bug this suite exists to
catch.
"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
APP_PATH = os.path.join(ROOT, "index.html")
import json
import unicodedata

import sys
sys.path.insert(0, HERE)
import loadapp

forms = loadapp.forms()


def fold(t):
    t = unicodedata.normalize('NFD', str(t))
    t = ''.join(c for c in t if not unicodedata.combining(c))
    return t.replace("'", '').lower()


def starts_a_word(hay, q):
    if not q:
        return False
    for k in range(len(hay)):
        if k == 0 or not hay[k - 1].isalnum():
            if hay.startswith(q, k):
                return True
    return False


def matches(f, query):
    q = fold(query)
    return (q in fold(f.get('name', ''))
            or starts_a_word(fold(f.get('aka', '')), q)
            or (len(q) >= 3 and starts_a_word(fold(f.get('tag', '')), q)))


# Each entry is a phrase that used to be someone's own row. Searching it must now
# land on the row that absorbed it. "folklórico" exercises accent folding, and the
# multi-word entries exercise the word-boundary requirement.
COLLAPSED = {
    'ballet': 'af053', 'pointe': 'af053', 'ballroom': 'af053',
    'ballroom & latin dance': 'af053', 'tap dance': 'af053',
    'hip-hop & street dance': 'af053', 'breaking': 'af053',
    'belly dance': 'af053', 'raqs sharqi': 'af053',
    'social partner dance': 'af053', 'classical indian dance': 'af053',
    'folk & traditional dance': 'af053', 'irish & highland dance': 'af053',
    'west african & diaspora dance': 'af053', 'polynesian & māori dance': 'af053',
    'mexican folkloric dance': 'af053', 'folklórico': 'af053',
    'contemporary & modern dance': 'af053',
    'chalk & pavement art': 'af018', 'sidewalk chalk': 'af018',
    '3d street painting': 'af018', 'graffiti': 'af018',
}

bad = []
for term, want in COLLAPSED.items():
    hits = [f['id'] for f in forms if matches(f, term)]
    if want not in hits:
        bad.append('  %-34r -> expected %s, matched %s'
                   % (term, want, hits or 'NOTHING'))

print('forms: %d' % len(forms))
if bad:
    print('\nUNREACHABLE (%d of %d):' % (len(bad), len(COLLAPSED)))
    print('\n'.join(bad))
else:
    print('all %d collapsed subjects resolve under the real matcher'
          % len(COLLAPSED))
    for fid in sorted(set(COLLAPSED.values())):
        f = next(x for x in forms if x['id'] == fid)
        print('  %s  %-26s %d words of alias'
              % (fid, f['name'], len(f['aka'].split())))