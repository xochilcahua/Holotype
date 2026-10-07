# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Run every tool against the new layout and report what breaks, without stopping.

The app was once a single file and is now index.html plus modules under src/. A tool that hardcodes
the old path, or that sliced ART_FORMS out of the HTML
inline, are now silently broken in two different ways: some throw, and some are worse
-- they parse nothing and report success on empty input. Running everything is the only
way to tell those apart, so this runs each tool in its own subprocess with a timeout
and classifies the result as PASS, FAIL or SILENT (exited zero but printed nothing
useful, which is the category worth looking at first).

Nothing is fixed here. This only produces the list.
"""
import glob
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VENV = os.path.join(ROOT, '.venv_audit', 'bin', 'python')
if not os.path.exists(VENV):
    VENV = sys.executable

# Tools that need an argument they cannot invent, or that take minutes, are listed
# separately rather than run blind.
SLOW = {'archetype_grid.py', 'population_check.py', 'run_tests.py', 'build_report.py'}
# Not run by default: the UI tools below take arguments or minutes; they are under tests/ui/.

# Data modules. These define profiles and import cleanly; there is nothing to run, so
# "printed nothing" is the correct outcome, not a failure. Calling them SILENT made the
# sweep cry wolf about two files that are working exactly as intended.
LIBRARY = {'profiles.py', 'archetypes.py', 'population.py', 'loadapp.py'}

# Tools that take required arguments. They are checked for importability here and run
# for real elsewhere; running them with no arguments only proves argparse exists.
NEEDS_ARGS = {'audit_shot.py', 'print_shot.py', 'verify_render.py',
              'verify_responsive.py', 'verify_states.py', 'verify_touch.py',
              'verify_print.py', 'bar_measure.py', 'probe.py', 'tap_probe.py',
              'longname_probe.py', 'verify_sorts.py', 'verify_sort_integration.py'}

SKIP = {'__pycache__', 'audit_all_tools.py'}

rows = []
for path in sorted(glob.glob(os.path.join(ROOT, 'tests', '*.py'))
                   + glob.glob(os.path.join(ROOT, 'tests', 'audit', '*.py'))
                   + glob.glob(os.path.join(ROOT, 'tests', 'ui', '*.py'))):
    name = os.path.basename(path)
    if name in SKIP or name.endswith('.pyc'):
        continue
    rel = os.path.relpath(path, ROOT)
    if name in SLOW:
        rows.append((rel, 'run separately', '', ''))
        continue
    if name in LIBRARY:
        rows.append((rel, 'library', 'defines data, nothing to run', ''))
        continue
    if name in NEEDS_ARGS:
        # Prove it at least imports and exposes a main, without executing it.
        try:
            p = subprocess.run([VENV, '-c',
                                'import runpy,sys; sys.argv=["x"]; runpy.run_path(%r, '
                                'run_name="__probe__")' % rel],
                               cwd=ROOT, capture_output=True, text=True, timeout=30)
            ok = 'Traceback' not in (p.stderr or '')
            rows.append((rel, 'imports' if ok else 'IMPORT ERROR',
                         'needs arguments', p.stderr.strip().splitlines()[-1]
                         if not ok else ''))
        except subprocess.TimeoutExpired:
            rows.append((rel, 'TIMEOUT', 'exceeded 30s', ''))
        continue
    try:
        # Pass the PATH, not the bare name: subprocess does not search the script's
        # own directory, so "python3 scan_order.py" with cwd=repo root looks for the
        # file in the repository root and reports "can't open file" for every tool.
        p = subprocess.run([VENV, os.path.relpath(path, ROOT)], cwd=ROOT,
                           capture_output=True, text=True, timeout=90)
        out = (p.stdout or '').strip()
        err = (p.stderr or '').strip()
        verdict = 'pass' if p.returncode == 0 and out else (
            'SILENT' if p.returncode == 0 else 'FAIL')
        last = out.splitlines()[-1][:60] if out else (
            err.splitlines()[-1][:60] if err else '')
        rows.append((rel, verdict, last, err))
    except subprocess.TimeoutExpired:
        rows.append((rel, 'TIMEOUT', 'exceeded 90s', ''))

OK = ('pass', 'library', 'imports', 'run separately')
w = max(len(r[0]) for r in rows)
bad = [r for r in rows if r[1] not in OK]
print('%-*s  %-13s %s' % (w, 'tool', 'verdict', 'last line'))
print('-' * (w + 17))
for rel, verdict, last, _ in rows:
    print('%-*s  %-13s %s' % (w, rel, verdict, last))
print('\n%d fine, %d need attention' % (len(rows) - len(bad), len(bad)))

for rel, verdict, _, err in bad:
    if err:
        tail = [l for l in err.splitlines() if l.strip()][-3:]
        print('\n--- %s (%s)' % (rel, verdict))
        for l in tail:
            print('    ' + l[:110])