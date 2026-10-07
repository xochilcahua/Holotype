# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Load Holotype's data from the MODULES rather than from one HTML file.

The checkers used to slice const ART_FORMS = [...] straight out of the monolith. Now
that the data lives in src/data/art-forms.js behind a <script src> tag, that slice
finds nothing, and a checker that silently finds nothing reports success -- so the
loader is shared and asserts it actually got a catalogue before returning.
"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
APP_PATH = os.path.join(ROOT, "index.html")
import json
import re
import os

APP = ROOT   # the repo root: index.html and src/ live here


def _src(rel):
    with open(os.path.join(APP, rel), encoding='utf-8') as fh:
        return fh.read()


def forms():
    """The catalogue, as a list of records."""
    s = _src('src/data/art-forms.js')
    i = s.index('const ART_FORMS = [')
    j = s.index('\n];', i)
    return json.loads(s[i + len('const ART_FORMS = '):j + 2])


def const_int_map(src_rel, name):
    """Parse a JS object literal of af### -> integer, e.g. PREVALENCE.

    The table is commented with its categories ("// Visual Arts", and a multi-line
    note above af018), so comment text has to go before parsing or the last token
    before each colon becomes a bogus key.
    """
    s = _src(src_rel)
    i = s.index('const %s = {' % name)
    j = s.index('\n};', i)
    body = s[i + len('const %s = {' % name):j]
    # Drop line comments before splitting. Each category is labelled with one, and it
    # sits on the SAME comma-delimited chunk as that category's first entry, so without
    # this the first form in every category is lost -- 15 of them, silently.
    body = re.sub(r'//[^\n]*', '', body)
    out = {}
    for part in body.split(','):
        part = part.strip()
        m = re.match(r'^(af\d+):\s*(\d+(?:\.\d+)?)\s*$', part)
        if m:
            out[m.group(1)] = float(m.group(2))
    return out


def hierarchy():
    s = _src('src/data/taxonomy.js')
    i = s.index('const HIERARCHY = {')
    j = s.index('\n};', i)
    return s[i:j]


def parent_why():
    s = _src('src/data/taxonomy.js')
    i = s.index('const PARENT_WHY = {')
    j = s.index('\n};', i)
    return s[i:j]


if __name__ == '__main__':
    f = forms()
    print('art forms: %d' % len(f))
    print('prevalence entries: %d' % len(const_int_map('src/data/prevalence.js',
                                                        'PREVALENCE')))
    print('hierarchy block: %d lines' % hierarchy().count('\n'))
    print('parent_why block: %d lines' % parent_why().count('\n'))