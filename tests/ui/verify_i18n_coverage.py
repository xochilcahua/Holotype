# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Is any visible English left when a language is on?

Switches the app to a made-up language whose translation of EVERY text is the same text with each English word
replaced by x's ("Garden" -> "xxxxxx"), tags and {0} placeholders kept. Then walks every screen (see i18n_drive.py)
and reports any visible text, tooltip, aria-label or placeholder that still holds a real English word. Such a string
is not going through t()/tx()/i18nHTML, so no language file can ever translate it.

Allowed to stay as it is: the brand (logo, "Holotype" aria-label), the contact handle, language names, and the
Latin botanical names (genus, variety and tribe epithets), which are canonical on purpose.

    python3 tests/ui/verify_i18n_coverage.py        exit 1 if anything is left
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import i18n_drive
from playwright.sync_api import sync_playwright

HOOK = r"""() => {
  LANGUAGES.zz = 'ZZ';
  const mask = (k) => k.replace(/(<[^>]+>|\{\d+\}|&[a-z#0-9]+;)|([A-Za-z]+)/g, (m, keep, w) => keep ? keep : 'x'.repeat(w.length));
  TRANSLATIONS.zz = new Proxy({}, { get: (_, k) => typeof k === 'string' ? mask(k) : undefined });
  setLanguage('zz');
}"""

LATIN = r"""() => {
  const words = new Set();
  const take = (v) => { if (typeof v === 'string') v.split(/[^A-Za-z]+/).forEach((w) => w && words.add(w.toLowerCase())); };
  const walk = (o, depth = 0) => { if (!o || depth > 4) return; if (typeof o === 'string') return take(o); Object.values(o).forEach((v) => walk(v, depth + 1)); };
  try { Object.values(GENUS_TABLE).forEach((g) => take(g.name)); } catch (e) {}
  ['TRIBE_EPITHET'].forEach((n) => { try { walk(eval(n)); } catch (e) {} });
  // Latin variety words ("ordinata", "flexilis"): every `word:` field in the reading tables.
  try { Object.values(REGIME_LEVELS).forEach((r) => take(r.word)); } catch (e) {}
  // The fake language has no date format of its own, so the date falls back to English month names.
  for (let m = 0; m < 12; m++) take(new Date(2026, m, 1).toLocaleDateString('en', { month: 'long' }));

  return [...words];
}"""

WALK = r"""(allowed) => {
  const out = [];
  const ok = new Set(allowed);
  const words = (s) => (s.replace(/\bx+\b/g, ' ').match(/[A-Za-z]{3,}/g) || []).filter((w) => !ok.has(w.toLowerCase()));
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = w.nextNode())) {
    const p = n.parentElement;
    if (!p || ['SCRIPT', 'STYLE', 'NOSCRIPT'].includes(p.tagName)) continue;
    const s = n.nodeValue.replace(/\s+/g, ' ').trim();
    const left = words(s);
    if (left.length && getComputedStyle(p).display !== 'none') out.push(['text', s.slice(0, 110), left.join(' ')]);
  }
  document.querySelectorAll('[title],[aria-label],[placeholder],[alt]').forEach((el) => {
    for (const a of ['title', 'aria-label', 'placeholder', 'alt']) {
      const v = el.getAttribute(a);
      const left = v ? words(v) : [];
      if (left.length) out.push([a, v.slice(0, 110), left.join(' ')]);
    }
  });
  return out;
}"""


def main():
    root = i18n_drive.ROOT
    found = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={'width': 1280, 'height': 900})
        errors = []
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.goto('file://' + os.path.join(root, 'index.html'))
        pg.wait_for_timeout(400)
        pg.evaluate(HOOK)
        # 'ada' is the reader name the driver types in: user data, not text
        allowed = {'holotype', 'hol', 'type', 'xochilcahua', 'english', 'ada'} | set(pg.evaluate(LATIN))
        allowed |= {w.lower() for w in re.findall(r'[A-Za-z]{3,}', ' '.join(pg.evaluate("() => Object.values(LANGUAGES)")))}

        def visit(label, print_view=False):
            if print_view:
                pg.add_style_tag(content='#printExport{display:block !important}')
            for kind, text, left in pg.evaluate(WALK, sorted(allowed)):
                found.setdefault((kind, text, left), set()).add(label)

        i18n_drive.drive(pg, visit)
        br.close()
    if errors:
        print('page errors:', errors[:3])
    for (kind, text, left), views in sorted(found.items()):
        print('[%s] %s\n    English left: %s   (seen in: %s)' % (kind, text, left, ', '.join(sorted(views))[:80]))
    print('%d untranslatable string(s) found' % len(found))
    sys.exit(1 if found or errors else 0)


if __name__ == '__main__':
    main()
