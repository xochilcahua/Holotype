# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Is this machine able to run the Holotype tools? Run this first.

usage:  python3 tests/env_check.py
Prints one line per check and, at the end, the exact python command to use for every other
tool. It changes nothing. If something is missing it says which command installs it.
"""
import importlib, os, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
venv = ROOT / ".venv_audit" / "bin" / "python"
print("python running this check:", sys.executable, sys.version.split()[0])
print(".venv_audit present:", venv.exists(), "(", venv, ")")

def check(mod):
    try:
        importlib.import_module(mod); return True
    except Exception as e:
        return False

ok_pw, ok_pil = check("playwright"), check("PIL")
print("playwright importable:", ok_pw)
print("Pillow importable:", ok_pil)
chromium = False
if ok_pw:
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            b = pw.chromium.launch(); pg = b.new_page()
            pg.goto((ROOT / "index.html").as_uri()); pg.wait_for_timeout(800)
            n = pg.evaluate("ART_FORMS.length")
            print("headless Chromium opens index.html: yes; ART_FORMS.length =", n)
            chromium = True; b.close()
    except Exception as e:
        print("headless Chromium: FAILED:", str(e).splitlines()[0][:160])
print()
if ok_pw and chromium:
    print("USE THIS PYTHON FOR EVERY TOOL:", sys.executable)
    print("RESULT: READY" + ("" if ok_pil else " (Pillow missing: only run_tests.py screenshots need it)"))
else:
    print("RESULT: NOT READY. Fix with, from the repository root:")
    print("   python3 -m venv .venv_audit && .venv_audit/bin/pip install playwright Pillow && .venv_audit/bin/playwright install chromium")
    print("then run:  .venv_audit/bin/python tests/env_check.py")
