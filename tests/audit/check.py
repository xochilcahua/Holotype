# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Check nothing dangles after the catalogue was pruned and the file was split.

A dropped art form id still sitting in HIERARCHY, PARENT_WHY or the prevalence table
would not throw -- it would render an empty breadcrumb or a silently wrong figure -- so
every id reference is checked against the forms that actually exist, and the app is
loaded once to catch anything that throws at load.

The data now lives in src/** behind <script src> tags rather than inline in one
HTML file, so this reads the modules through loadapp. It asserts it found a catalogue:
a checker that silently parses nothing would report success, which is worse than
failing outright.
"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
APP_PATH = os.path.join(ROOT, "index.html")
import re
import sys

sys.path.insert(0, HERE)
import loadapp

forms = loadapp.forms()
ids = {f['id'] for f in forms}
if len(ids) < 100:
    raise SystemExit('loader returned %d forms -- refusing to report on nothing'
                     % len(ids))
print('forms loaded: %d' % len(ids))

problems = []

hb = loadapp.hierarchy()
hier = {}
for m in re.finditer(r'^\s*(af\d+):\s*\[([^\]]*)\]', hb, re.M):
    hier[m.group(1)] = re.findall(r'"(af\d+)"', m.group(2))
for p, kids in hier.items():
    if p not in ids:
        problems.append('HIERARCHY parent %s does not exist' % p)
    for k in kids:
        if k not in ids:
            problems.append('HIERARCHY child %s of %s does not exist' % (k, p))
        if k == p:
            problems.append('HIERARCHY %s is its own child' % p)

why = set(re.findall(r'^\s*(af\d+):', loadapp.parent_why(), re.M))
for w in why:
    if w not in ids:
        problems.append('PARENT_WHY %s does not exist' % w)
for p in hier:
    if p not in why:
        problems.append('parent %s has children but no PARENT_WHY argument' % p)

prev_ids = set(loadapp.const_int_map('src/data/prevalence.js', 'PREVALENCE'))
for pid in sorted(prev_ids - ids):
    problems.append('prevalence table lists %s, which no longer exists' % pid)
missing = ids - prev_ids
if missing:
    problems.append('no prevalence figure for %d form(s): %s'
                    % (len(missing), sorted(missing)[:8]))
print('forms with a prevalence figure: %d/%d' % (len(prev_ids & ids), len(ids)))

GONE = ['af244', 'af245', 'af246', 'af247', 'af248', 'af249', 'af251',
        'af252', 'af253', 'af254', 'af255', 'af256', 'af257', 'af144']
for g in GONE:
    if g in ids:
        problems.append('%s should have been collapsed but is still a form' % g)
for k, name in (('af250', 'Flamenco'), ('af260', 'Capoeira'),
                ('af268', 'Chinese Opera'), ('af053', 'Dance')):
    if k not in ids:
        problems.append('%s (%s) should have been kept but is gone' % (k, name))

print('hierarchy: %d parents, %d children'
      % (len(hier), sum(len(v) for v in hier.values())))
print('Dance children:', hier.get('af053'))
print('\n' + ('PROBLEMS (%d):\n%s' % (len(problems),
                                      '\n'.join('  - ' + p for p in problems))
              if problems else 'no dangling references'))

from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    br = pw.chromium.launch()
    pg = br.new_page()
    errs = []
    # 'Failed to load resource' is the Google Fonts request failing offline; not an app error.
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: errs.append('console.' + m.type + ': ' + m.text)
          if m.type == 'error' and 'Failed to load resource' not in m.text else None)
    pg.goto('file://' + APP_PATH)
    pg.wait_for_timeout(2000)
    n = pg.evaluate('ART_FORMS.length')
    rendered = pg.evaluate('document.querySelectorAll(".flower").length')
    pg.close()
    br.close()

print('app loads: ART_FORMS.length = %d, %d card flowers rendered' % (n, rendered))
if errs:
    print('RUNTIME ERRORS:')
    for e in errs[:10]:
        print('  -', e)

sys.exit(1 if (problems or errs or n != len(forms)) else 0)