# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Copy the browser app into .site for GitHub Pages, with a link to its source."""

from pathlib import Path
import os
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / '.site'
repository = os.environ.get('GITHUB_REPOSITORY', '')
if repository and not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
    raise SystemExit('GITHUB_REPOSITORY must be owner/repository')

DEST.mkdir(exist_ok=True)
for folder in ['src', 'assets', 'copy', 'dist']:
    target = DEST / folder
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(ROOT / folder, target, ignore=shutil.ignore_patterns('.DS_Store'))
for filename in ['index.html', '.nojekyll', 'LICENSE', 'TRADEMARK.md']:
    shutil.copy2(ROOT / filename, DEST / filename)

if repository:
    for page in [DEST / 'index.html', DEST / 'dist/Holotype.html']:
        html = page.read_text(encoding='utf-8')
        html = html.replace('id="sourceWrap" hidden', 'id="sourceWrap"')
        html = html.replace('id="sourceLink" href="#"', f'id="sourceLink" href="https://github.com/{repository}"')
        page.write_text(html, encoding='utf-8')
print('Website prepared in .site/')
