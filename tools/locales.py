# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Holotype's copy tool. The words of the app live in copy/, one folder per language; this makes the app notice them.

    copy/English/        the app's text, in files named by topic (art-form-names.txt, how-to-use.txt ...)
    copy/Español/        the same files in another language; add a folder and the language exists

A browser opening the app from disk (file://) cannot list a folder, so the folders are read once, by this script or by
copy/Update-languages.html, and written to copy/languages.js, the one file the app loads.

    python3 tools/locales.py build      read every folder in copy/ and write copy/languages.js
    python3 tools/locales.py check      how much of each language is done, and mistakes that would break the page
    python3 tools/locales.py extract    re-read the app's text into copy/English, then update every other language
    python3 tools/locales.py sync       update every other language to match copy/English

`build`, `check` and `sync` need only Python 3. `extract` also needs Playwright with Chromium (as the tests do).
See copy/README.md for the contributor's side.
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COPY = os.path.join(ROOT, 'copy')
GENERATED = os.path.join(COPY, 'languages.js')
NAMES_TABLE = os.path.join(COPY, '_language-names.js')
ENGLISH = 'English'
META = 'language.txt'
OLD = '_old-copy.txt'          # translations of text that is no longer in the app; kept, never read by the app
EXTS = ('.txt', '.md', '.json')
OPTIONAL = 'word-variants'     # "Cost | Moderate": only needed where the plain word does not fit; never counted as missing
CODE_RE = re.compile(r'^[a-z]{2,3}(-[A-Za-z0-9]{2,8})*$')   # es, pt-BR, zh-Hans

# topic file -> what lands in it. Order is the order of the files the extractor writes.
STEMS = ['app-interface', 'how-to-use', 'herbarium-and-pdf', 'profiles-and-readings', 'categories',
         'art-form-names', 'art-form-taglines', 'art-form-descriptions', 'art-form-try-this', OPTIONAL]


PLACEHOLDER = re.compile(r'\{\d+\}')
TAG = re.compile(r'</?[a-zA-Z][^>]*>')


def squash(s):
    return re.sub(r'\s+', ' ', s).strip()


# ------------------------------------------------------------------------------------------ reading and writing copy
# A text file is entries separated by a blank line. In each entry the first line is the English text exactly as the
# app has it (never edit it: it is how the app finds the entry) and the lines under it are what to show instead.
# In copy/English the second line is the same as the first, and editing it changes the English copy.
# A line left identical to the English means "not translated yet".

def parse_text(text):
    entries = {}
    for block in re.split(r'\n\s*\n', text.replace('\r\n', '\n').replace('\ufeff', '').strip()):
        lines = [l for l in block.split('\n') if l.strip()]
        if not lines:
            continue
        key = squash(lines[0])
        entries.setdefault(key, squash(' '.join(lines[1:])) or key)
    return entries


def read_file(path):
    with open(path, encoding='utf-8') as fh:
        text = fh.read()
    if path.endswith('.json'):
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError('a .json copy file must be an object of "English text": "translation"')
        return {squash(k): (squash(v) if isinstance(v, str) and v.strip() else squash(k)) for k, v in data.items()}
    return parse_text(text)


def write_entries(path, entries):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write('\n\n'.join('%s\n%s' % (k, v) for k, v in entries.items()) + '\n')


def parse_meta(folder):
    meta = {}
    path = os.path.join(COPY, folder, META)
    if os.path.exists(path):
        with open(path, encoding='utf-8') as fh:
            for line in fh:
                if ':' in line:
                    k, v = line.split(':', 1)
                    meta[k.strip().lower()] = v.strip()
    return meta


def language_names():
    with open(NAMES_TABLE, encoding='utf-8') as fh:
        text = fh.read()
    return {k.casefold(): v for k, v in json.loads(text[text.index('{'):text.rindex('}') + 1]).items()}


def folders():
    return sorted(n for n in os.listdir(COPY)
                  if os.path.isdir(os.path.join(COPY, n)) and not n.startswith(('_', '.')))


def resolve(folder, meta, table):
    """-> language code for a folder: language.txt "code:", else a known language name, else the name if it is a code."""
    if meta.get('code'):
        return meta['code']
    if folder.casefold() in table:
        return table[folder.casefold()]
    if CODE_RE.match(folder.split('-')[0].lower()) and re.match(r'^[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})*$', folder):
        return folder
    return None


def content_files(folder):
    d = os.path.join(COPY, folder)
    return [f for f in sorted(os.listdir(d))
            if f.endswith(EXTS) and not f.startswith('_') and f != META]


def load_folder(folder, problems):
    """-> (entries {key: value}, where {key: file stem}). Unreadable files are reported, not raised."""
    entries, where = {}, {}
    for f in content_files(folder):
        try:
            data = read_file(os.path.join(COPY, folder, f))
        except ValueError as e:
            problems.append((folder, f, 'cannot be read: %s' % e))
            continue
        stem = os.path.splitext(f)[0]
        for k, v in data.items():
            if k in entries and entries[k] != v and (v != k):
                if entries[k] == k:
                    entries[k] = v
                    where[k] = stem
                else:
                    problems.append((folder, f, 'also translated in another file (first one wins): %s' % k[:70]))
                continue
            entries.setdefault(k, v)
            where.setdefault(k, stem)
    return entries, where


def placeholders(s):
    return sorted(PLACEHOLDER.findall(s))


def tags(s):
    return sorted(re.sub(r'\s+', ' ', t) for t in TAG.findall(s))


def key_mistakes(key, value):
    """Things that would break the page, as opposed to things that merely read oddly."""
    out = []
    if placeholders(key) != placeholders(value):
        out.append('the {0}-style placeholders differ: English has %s, this has %s' % (placeholders(key) or 'none', placeholders(value) or 'none'))
    if tags(key) != tags(value):
        out.append('the <b>/<i> tags differ: English has %s, this has %s' % (tags(key) or 'none', tags(value) or 'none'))
    return out


# ------------------------------------------------------------------------------------------------------------- build

def cmd_build(args):
    problems, built, skipped = [], {}, []
    table = language_names()
    for folder in folders():
        meta = parse_meta(folder)
        code = resolve(folder, meta, table)
        if code is None:
            skipped.append((folder, 'cannot tell which language this is: add a file language.txt containing a line like  code: hi'))
            continue
        if meta.get('hidden', '').lower() in ('yes', 'true', '1'):
            skipped.append((folder, 'hidden in language.txt'))
            continue
        entries, _ = load_folder(folder, problems)
        strings = {k: v for k, v in entries.items() if v != k}
        if not strings:
            skipped.append((folder, 'nothing translated yet, so it is not offered in the menu'))
            continue
        if code in built:
            skipped.append((folder, 'language code "%s" is already used by another folder' % code))
            continue
        name = meta.get('name') or ('' if folder.casefold() == code.casefold() else folder)
        built[code] = {'name': name, 'strings': strings}
    body = json.dumps(built, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    header = ('// GENERATED by tools/locales.py build (or copy/Update-languages.html) from the folders in copy/.\n'
              '// DO NOT EDIT: edit the text files and rebuild. Defines HOLOTYPE_LOCALES = { code: { name, strings } }.\n')
    with open(GENERATED, 'w', encoding='utf-8') as fh:
        fh.write(header + 'const HOLOTYPE_LOCALES = %s;\n' % body)
    print('built copy/languages.js: %d language%s' % (len(built), '' if len(built) == 1 else 's'))
    for code, v in built.items():
        print('  %-8s %-14s %5d strings that differ from the English' % (code, v['name'] or '(name from browser)', len(v['strings'])))
    for folder, why in skipped:
        print('  skipped %s: %s' % (folder, why))
    for folder, f, msg in problems:
        print('  warning %s/%s: %s' % (folder, f, msg))
    return 0


# ------------------------------------------------------------------------------------------------------------- check

def reference():
    if ENGLISH not in folders():
        sys.exit('copy/%s is missing: it lists every string the app has. Run `python3 tools/locales.py extract`.' % ENGLISH)
    problems = []
    entries, where = load_folder(ENGLISH, problems)
    return entries, where


def cmd_check(args):
    ref, ref_where = reference()
    table = language_names()
    errors = 0
    names = args.names or [f for f in folders() if f != ENGLISH]
    for folder in names:
        if folder not in folders():
            print('%s: no such folder in copy/' % folder)
            errors += 1
            continue
        problems = []
        meta = parse_meta(folder)
        code = resolve(folder, meta, table)
        entries, where = load_folder(folder, problems)
        required = [k for k in ref if ref_where[k] != OPTIONAL]
        done = [k for k in required if entries.get(k, k) != k]
        missing = [k for k in required if entries.get(k, k) == k]
        optional_left = sum(1 for k in ref if ref_where[k] == OPTIONAL and entries.get(k, k) == k)
        stale = [k for k in entries if k not in ref]
        pct = 100.0 * len(done) / max(1, len(required))
        print('%s (code %s): %d of %d strings translated, %.1f%%' % (folder, code or 'UNKNOWN', len(done), len(required), pct))
        if code is None:
            print('    ERROR: cannot tell which language this is: add language.txt with a line  code: xx')
            errors += 1
        if optional_left:
            print('    %s: %d optional (only where the plain word is wrong in that place)' % (OPTIONAL, optional_left))
        by_file = {}
        for k in missing:
            by_file[ref_where[k]] = by_file.get(ref_where[k], 0) + 1
        for stem, n in sorted(by_file.items()):
            print('    still to do in %-26s %5d' % (stem, n))
        if stale:
            print('    %d entr%s match no text in the app any more (run `sync` to move them to %s)' % (len(stale), 'y' if len(stale) == 1 else 'ies', OLD))
        for _f, f, msg in problems:
            print('    ERROR %s: %s' % (f, msg))
            errors += 1
        for k, v in entries.items():
            if v == k or k not in ref:
                continue
            for m in key_mistakes(k, v):
                print('    ERROR %s: %s\n           for: %s' % (where[k], m, k[:90]))
                errors += 1
        if args.list_missing:
            for k in missing:
                print('    - [%s] %s' % (ref_where[k], k[:110]))
    return 1 if errors else 0


# ------------------------------------------------------------------------------------------------------------- sync

def write_folder(folder, groups, existing):
    """Write one language's files from {stem: [keys]}: its own text where it has some, the English line otherwise."""
    for stem, keys in groups.items():
        write_entries(os.path.join(COPY, folder, stem + '.txt'), {k: existing.get(k, k) for k in keys})
    wanted = {k for keys in groups.values() for k in keys}
    parked = {k: v for k, v in existing.items() if k not in wanted and v != k}
    path = os.path.join(COPY, folder, OLD)
    if parked:
        write_entries(path, parked)
    elif os.path.exists(path):
        os.remove(path)
    return len(parked)


def existing_text(folder):
    """Everything this folder already says, including parked text, so a returning string gets its translation back."""
    entries, _ = load_folder(folder, [])
    old_path = os.path.join(COPY, folder, OLD)
    if os.path.exists(old_path):
        for k, v in read_file(old_path).items():
            if entries.get(k, k) == k:
                entries[k] = v
    return entries


def cmd_sync(args):
    ref, ref_where = reference()
    groups = {}
    for k in ref:
        groups.setdefault(ref_where[k], []).append(k)
    ordered = {s: groups[s] for s in STEMS if s in groups}
    ordered.update({s: g for s, g in groups.items() if s not in ordered})
    for folder in folders():
        if folder == ENGLISH:
            continue
        before = existing_text(folder)
        parked = write_folder(folder, ordered, before)
        new = sum(1 for k in ref if k not in before)
        print('%s: %d new entr%s added (English line), %d parked in %s' % (folder, new, 'y' if new == 1 else 'ies', parked, OLD))
    return 0


# ---------------------------------------------------------------------------------------------------- static scan

# carry text -- t("..."), tx("..."), tx`...`, i18nHTML`...`, i18nRich`...`, i18nCount(n, "a", "b"), data-i18n --
# and builds the same keys src/i18n.js builds at run time. The two are unioned.
import html as _html

ESCAPES = {'n': '\n', 't': '\t', 'r': '\r', 'b': '\b', 'f': '\f', 'v': '\v', '0': '\0'}


def _cook(raw):
    out, i = [], 0
    while i < len(raw):
        c = raw[i]
        if c != '\\' or i + 1 >= len(raw):
            out.append(c)
            i += 1
            continue
        n = raw[i + 1]
        if n == 'u' and raw[i + 2:i + 3] == '{':
            j = raw.index('}', i)
            out.append(chr(int(raw[i + 3:j], 16)))
            i = j + 1
        elif n == 'u':
            out.append(chr(int(raw[i + 2:i + 6], 16)))
            i += 6
        elif n == 'x':
            out.append(chr(int(raw[i + 2:i + 4], 16)))
            i += 4
        elif n == '\n':
            i += 2
        else:
            out.append(ESCAPES.get(n, n))
            i += 2
    return ''.join(out)


def _skip_string(src, i):
    q = src[i]
    i += 1
    while i < len(src) and src[i] != q:
        i += 2 if src[i] == '\\' else 1
    return i + 1


def _parse_template(src, i):
    """src[i] is a backtick. -> (quasis, end) with quasis the raw text between ${...} holes."""
    assert src[i] == '`'
    i += 1
    quasis, cur = [], []
    while i < len(src):
        c = src[i]
        if c == '\\':
            cur.append(src[i:i + 2])
            i += 2
        elif c == '`':
            quasis.append(''.join(cur))
            return quasis, i + 1
        elif c == '$' and src[i + 1:i + 2] == '{':
            quasis.append(''.join(cur))
            cur = []
            i += 2
            depth = 1
            while i < len(src) and depth:
                d = src[i]
                if d in '"\'':
                    i = _skip_string(src, i)
                    continue
                if d == '`':
                    _, i = _parse_template(src, i)
                    continue
                depth += d == '{'
                depth -= d == '}'
                i += 1
        else:
            cur.append(c)
            i += 1
    raise ValueError('unterminated template')


def _squash(s):
    return re.sub(r'\s+', ' ', s).strip()


def _fragment_key(text, decode):
    """text holds \ue000N\ue001 holes. Mirrors i18nFragment: holes renumbered locally, optionally HTML-decoded."""
    n = [0]

    def hole(_):
        n[0] += 1
        return '{%d}' % (n[0] - 1)

    text = re.sub('\ue000\\d+\ue001', hole, text)
    return _squash(_html.unescape(text) if decode else text)


def _with_holes(quasis):
    return ''.join(_cook(q) + ('\ue000%d\ue001' % i if i < len(quasis) - 1 else '') for i, q in enumerate(quasis))


def keys_from_source(src):
    keys = []
    for m in re.finditer(r'(?<![\w.$])(tx|i18nHTML|i18nRich)`', src):
        tag = m.group(1)
        try:
            quasis, _ = _parse_template(src, m.end() - 1)
        except (ValueError, AssertionError):
            continue
        text = _with_holes(quasis)
        if tag == 'tx':
            keys.append(_fragment_key(text, False))
        elif tag == 'i18nRich':
            keys.append(_fragment_key(text, True))
        else:
            for chunk in re.split(r'(<[^>]+>)', text):
                if not chunk.startswith('<'):
                    keys.append(_fragment_key(chunk, True))
                else:
                    for _attr, content in re.findall(r'\b(title|aria-label|placeholder)="([^"]*)"', chunk):
                        keys.append(_fragment_key(content, True))
    for m in re.finditer(r'(?<![\w.$])(?:t|tx|sourceText)\(\s*(["\'`])', src):
        q = m.group(1)
        i = m.end() - 1
        if q == '`':
            try:
                quasis, _ = _parse_template(src, i)
            except (ValueError, AssertionError):
                continue
            if len(quasis) == 1:
                keys.append(_squash(_cook(quasis[0])))
        else:
            j = _skip_string(src, i)
            keys.append(_squash(_cook(src[i + 1:j - 1])))
    for m in re.finditer(r'i18nCount\((?:[^,()]|\([^()]*\))+,\s*"([^"]*)"\s*,\s*"([^"]*)"', src):
        keys += [_squash(m.group(1)), _squash(m.group(2))]
    return [k for k in keys if key_ok(k)]


def keys_from_index_html(src):
    keys = [_squash(_html.unescape(m)) for m in re.findall(r'data-i18n="([^"]*)"', src)]
    for attrs in re.findall(r'data-i18n-attr="([^"]*)"', src):
        for pair in attrs.split(';'):
            if '|' in pair:
                keys.append(_squash(_html.unescape(pair.split('|', 1)[1])))
    sort_block = re.search(r'<select id="sortSelect".*?</select>', src, re.S)
    if sort_block:
        keys += [_squash(_html.unescape(o)) for o in re.findall(r'<option[^>]*>([^<]*)</option>', sort_block.group(0))]
    return [k for k in keys if key_ok(k)]


def static_keys():
    """-> {key: set(source file names)}"""
    found = {}
    base = os.path.join(ROOT, 'src')
    for dirpath, dirs, names in os.walk(base):
        dirs[:] = [d for d in dirs if d not in ('locales', 'data')]
        for name in names:
            if not name.endswith('.js') or name == 'i18n.js':
                continue
            with open(os.path.join(dirpath, name), encoding='utf-8') as fh:
                text = fh.read()
            text = re.sub(r'^\s*//.*$', '', text, flags=re.M)
            text = re.sub(r'function sessionSelfTest\(\) \{.*?\n\}\n', '', text, flags=re.S)   # developer self-test: names are not UI
            for k in keys_from_source(text):
                found.setdefault(k, set()).add(name)
    with open(os.path.join(ROOT, 'index.html'), encoding='utf-8') as fh:
        for k in keys_from_index_html(fh.read()):
            found.setdefault(k, set()).add('index.html')
    return found


HELP_FILES = {'keys.js'}
PROFILE_FILES = {'herbarium.js', 'profile-page.js', 'profile-blocks.js', 'print.js', 'classification.js', 'export-garden.js'}
SESSION_FILES = {'session.js'}

IN_PAGE_HOOK = r"""() => {
  window.__req = new Map();                      // key -> Set of caller files
  LANGUAGES.zz = 'ZZ';
  TRANSLATIONS.zz = new Proxy({}, { get: (_, k) => {
    if (typeof k !== 'string') return undefined;
    const frames = new Error().stack.split('\n').slice(1).map((l) => (l.match(/\/([\w.-]+\.js):\d+:\d+\)?$/) || [])[1]).filter((f) => f && f !== 'i18n.js');
    if (!window.__req.has(k)) window.__req.set(k, new Set());
    if (frames[0]) window.__req.get(k).add(frames[0]);
    return undefined;
  } });
  setLanguage('zz');
}"""

DATA_WALK = r"""(names) => {
  const out = [];
  const seen = new Set();
  const walk = (v) => {
    if (typeof v === 'string') { out.push(v); return; }
    if (!v || typeof v !== 'object' || seen.has(v)) return;
    seen.add(v);
    (Array.isArray(v) ? v : Object.values(v)).forEach(walk);
  };
  names.forEach((n) => { try { walk(eval(n)); } catch (e) { /* not defined in this build */ } });
  return out;
}"""


def key_ok(k):
    stripped = PLACEHOLDER.sub('', k)
    return bool(re.search(r'[A-Za-z]{2,}', stripped))


def collect_keys():
    sys.path.insert(0, os.path.join(ROOT, 'tests', 'ui'))
    import i18n_drive
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={'width': 1280, 'height': 900})
        errors = []
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.goto('file://' + os.path.join(ROOT, 'index.html'))
        pg.wait_for_timeout(400)
        pg.evaluate(IN_PAGE_HOOK)
        i18n_drive.drive(pg, lambda label, print_view=False: None, every_sheet=True)
        requested = pg.evaluate("() => [...window.__req.entries()].map(([k, v]) => [k, [...v]])")
        fields = pg.evaluate("""() => ({
          categories: [...new Set(ART_FORMS.map((a) => a.category))],
          names: ART_FORMS.map((a) => a.name).filter(Boolean),
          taglines: ART_FORMS.map((a) => a.tag).filter(Boolean),
          descriptions: ART_FORMS.map((a) => a.desc).filter(Boolean),
          tryfirst: ART_FORMS.map((a) => a.start).filter(Boolean) })""")
        names = []
        for f in ('genus-copy.js', 'axis-copy.js'):
            with open(os.path.join(ROOT, 'src', 'model', f), encoding='utf-8') as fh:
                names += re.findall(r'^const\s+([A-Z_][A-Z0-9_]*)\s*=', fh.read(), re.M)
        readings = pg.evaluate(DATA_WALK, names)
        br.close()
    if errors:
        sys.exit('the app threw while being driven: %s' % errors[:3])
    return requested, fields, readings



CONTEXT_KEY = re.compile(r'^[A-Z][A-Za-z -]* \| \S')


def classify(requested, fields, readings, static):
    """-> {stem: [keys]} for every string the app can show."""
    sets = {f: {squash(s) for s in v} for f, v in fields.items()}
    reading_set = {squash(s) for s in readings}
    callers_of = {}
    for k, callers in requested:
        # The session parser echoes the driver's sample file back as text ("af001: no usable rating"). Real
        # messages are marked in the source (sourceText / tx), so a session.js-only key that is not there is data.
        if callers and set(callers) <= SESSION_FILES and k not in static:
            continue
        callers_of.setdefault(k, set()).update(callers)
    for k, files in static.items():
        callers_of.setdefault(k, set()).update(files)
    groups = {s: {} for s in STEMS}
    field_stem = [('categories', 'categories'), ('names', 'art-form-names'), ('taglines', 'art-form-taglines'),
                  ('descriptions', 'art-form-descriptions'), ('tryfirst', 'art-form-try-this')]
    for k, callers in callers_of.items():
        if not key_ok(k):
            continue
        stem = next((st for f, st in field_stem if k in sets[f]), None)
        if stem is None:
            if k in reading_set:
                stem = 'profiles-and-readings'
            elif CONTEXT_KEY.match(k):
                stem = OPTIONAL
            elif callers and callers <= set(HELP_FILES):
                stem = 'how-to-use'
            elif callers and callers <= PROFILE_FILES:
                stem = 'herbarium-and-pdf'
            else:
                stem = 'app-interface'
        groups[stem][k] = ''
    # Catalogue text the sheets never asked for, and reading text no screen showed in this run, still belong.
    for f, st in field_stem:
        for s in fields[f]:
            if key_ok(squash(s)):
                groups[st][squash(s)] = ''
    for s in reading_set:
        if key_ok(s) and ' ' in s and not any(s in g for g in groups.values()):
            groups['profiles-and-readings'][s] = ''
    out = {}
    for st in STEMS:
        keys = list(groups[st])
        if st in dict(field_stem).values():
            field = next(f for f, x in field_stem if x == st)
            order = {squash(s): i for i, s in reversed(list(enumerate(fields[field])))}
            keys.sort(key=lambda k: order.get(k, 10 ** 9))
        out[st] = keys
    return out


def cmd_extract(args):
    requested, fields, readings = collect_keys()
    groups = classify(requested, fields, readings, static_keys())
    os.makedirs(os.path.join(COPY, ENGLISH), exist_ok=True)
    existing = existing_text(ENGLISH) if os.path.isdir(os.path.join(COPY, ENGLISH)) else {}
    write_folder(ENGLISH, groups, existing)
    print('copy/English: ' + ', '.join('%s %d' % (s, len(k)) for s, k in groups.items()) + ' = %d strings' % sum(len(k) for k in groups.values()))
    cmd_sync(args)
    return cmd_build(args)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('build').set_defaults(fn=cmd_build)
    c = sub.add_parser('check')
    c.add_argument('names', nargs='*', help='language folder names (default: all but English)')
    c.add_argument('--list-missing', action='store_true', help='print every untranslated string')
    c.set_defaults(fn=cmd_check)
    sub.add_parser('sync').set_defaults(fn=cmd_sync)
    sub.add_parser('extract').set_defaults(fn=cmd_extract)
    args = ap.parse_args()
    sys.exit(args.fn(args))


if __name__ == '__main__':
    main()
