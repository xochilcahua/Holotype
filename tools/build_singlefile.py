# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Build dist/Holotype.html: every module inlined into one portable file.

The app's source is modular -- index.html plus src/** -- but Holotype is meant to
be sent to someone as ONE file, and opening it from disk is a hard requirement (module
imports are blocked under file://, which is why the app uses classic script tags in the
first place). This is the reverse of the split: it walks the <link> and <script src>
tags and replaces each with its contents, producing dist/Holotype.html.

Verifying the round trip matters more than the build. This builds the file, loads it
in a browser, and compares its answers field by field against index.html. A build
that silently dropped a stylesheet or mis-nested a script would still open, so the check
is behavioural rather than a diff.

    python3 build_singlefile.py [--check]
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # repo root (this file lives in tools/)
APP = ROOT   # index.html and src/ sit at the root
ENTRY = os.path.join(ROOT, 'index.html')
DIST = os.path.join(ROOT, 'dist')


def inline(html):
    def css(m):
        with open(os.path.join(APP, m.group(1)), encoding='utf-8') as fh:
            return '<style>\n%s\n</style>' % fh.read().rstrip('\n')

    def js(m):
        with open(os.path.join(APP, m.group(1)), encoding='utf-8') as fh:
            return '<script>\n%s\n</script>' % fh.read().rstrip('\n')

    html = re.sub(r'<link rel="stylesheet" href="([^"]+)"\s*/?>', css, html)
    return re.sub(r'<script src="([^"]+)"\s*></script>', js, html)


def main():
    # Rebuild the language bundle before inlining it.
    import subprocess
    subprocess.check_call([sys.executable, os.path.join(ROOT, 'tools', 'locales.py'), 'build'])
    src = open(ENTRY, encoding='utf-8').read()
    out = inline(src)
    os.makedirs(DIST, exist_ok=True)
    path = os.path.join(DIST, 'Holotype.html')
    open(path, 'w', encoding='utf-8').write(out)
    print('built dist/Holotype.html: %d lines (source entry was %d)'
          % (out.count('\n'), src.count('\n')))
    print('  left to load from disk: %d' % out.count('src='))

    from playwright.sync_api import sync_playwright
    PROBE = """() => {
      state.mastery = { af001: 7, af008: 5, af009: 4, af003: 6, af053: 3, af038: 8 };
      const bc = computeClassification();
      const a = ART_FORMS.find(f => f.name === 'Painting');
      // The person-space reference and a full reading were NOT probed before, so a dist/ built from an
      // older person-space.js passed this check while reading every person differently.
      const nv = computeNovelty(state.mastery, state.discount);
      const ref = ['a1','d1','a4','b3'].map(k => PEOPLE_MEAN[k].toFixed(5) + '/' + PEOPLE_SD[k].toFixed(5) + '/' + PEOPLE_MEDIAN[k].toFixed(5)).join(' ');
      return { forms: ART_FORMS.length, cards: document.querySelectorAll('.flower').length,
               ref, zAll: [bc.zProcess, bc.zSoc, bc.zForm, bc.zRegime].map(x => +x.toFixed(5)).join(' '),
               noveltySum: ART_FORMS.reduce((t, f) => t + nv.byId[f.id].score, 0),
               prevalence: Object.keys(PREVALENCE).length,
               genus: bc.genusId, zSoc: +bc.zSoc.toFixed(4),
               dist: +DIST[0][1].toFixed(6), rel: +REL[0][1].toFixed(6),
               desc: describeArtForm(a), height: document.body.scrollHeight,
               plant: window.HolotypePlant.svg({genus: 'Ficus', regime: 'flexilis',
                        domains: ['Petal'], confidence: 'settled', seed: 't'}).length };
    }"""
    got = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        for label, url in (('modular', 'file://' + ENTRY),
                           ('dist', 'file://' + path)):
            pg = br.new_page()
            errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.on('console', lambda m: errs.append('console.error: ' + m.text)
                  if m.type == 'error' else None)
            # Check the app with system fonts so a font service outage cannot fail a build.
            pg.route('https://fonts.googleapis.com/**', lambda route: route.fulfill(
                status=200, content_type='text/css', body=''))
            pg.goto(url, wait_until='domcontentloaded')
            # NOT wait_until="load": the page pulls its fonts from fonts.googleapis.com,
            # so offline the load event never fires and the check times out on a network
            # stall rather than on anything the build did. Both pages get the same
            # treatment, so the comparison stays fair.
            pg.wait_for_timeout(2500)
            got[label] = pg.evaluate(PROBE)
            got[label + '_errors'] = errs
            pg.close()
        br.close()

    bad = [k for k in got['modular']
           if got['modular'][k] != got['dist'].get(k)]
    print('\nmodular vs dist: %s'
          % ('identical on all %d probed values' % len(got['modular']) if not bad
             else 'DIFFERENCES %s' % bad))
    for label in ('modular', 'dist'):
        if got[label + '_errors']:
            print('  %s errors: %s' % (label, got[label + '_errors'][:3]))
    return 1 if bad or got['dist_errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
