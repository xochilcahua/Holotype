# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Split-half reliability of the genus bits, on saved sessions ($HOLOTYPE_SESSIONS, default tests/sample_sessions).

QUESTION: if one person's ratings are split at random into two halves and each half is read on its own,
do the two halves agree? A reading that changes with which half of your list it saw is mostly measuring
which forms you happened to mention. Each half has half the data, so this UNDERSTATES a full-list
retest; it is a floor, and the trend across bits matters more than the absolute number.

Measured on the original build (2026-10): whole-genus agreement 16% (a 103-rating session), 29%
(57 ratings), 39% (53 ratings). Breadth agrees 100% because it is nearly constant for anyone with a long list;
Process, Social and Form range 41%-99%.

Usage:  python3 tests/audit/split_half.py [trials=150] [seed=11]
Exit code is always 0: this reports a number, it does not pass or fail one. If you want a gate, pick a
threshold deliberately and say why.
"""
import glob, json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from appdriver import App

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRIALS = int(sys.argv[1]) if len(sys.argv) > 1 else 150
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 11
JS = "(m)=>{state.mastery=m; const b=computeClassification(); return b?b.genusId:null}"

app = App()
print("%-10s %4s   %s   %s" % ("session", "n", "agreement per bit [Breadth Process Social Form]", "whole genus"))
for f in sorted(glob.glob(os.path.join(os.environ.get("HOLOTYPE_SESSIONS", os.path.join(ROOT, "tests", "sample_sessions")), "*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    full = {r["id"]: r["rating"] for r in d["ratings"]}
    ids = list(full)
    if len(ids) < 20:
        print("%-10s %4d   skipped (under 20 ratings: halves would be under 10)" % (d["name"][:10], len(ids)))
        continue
    random.seed(SEED)
    agree, whole = [0, 0, 0, 0], 0
    for _ in range(TRIALS):
        random.shuffle(ids)
        h = len(ids) // 2
        g1 = app.ev(JS, {k: full[k] for k in ids[:h]})
        g2 = app.ev(JS, {k: full[k] for k in ids[h:2 * h]})
        for i in range(4):
            agree[i] += g1[i] == g2[i]
        whole += g1 == g2
    print("%-10s %4d   %s   %3.0f%%" % (d["name"][:10], len(ids),
          "  ".join("%3.0f%%" % (100.0 * x / TRIALS) for x in agree), 100.0 * whole / TRIALS))
app.close()
