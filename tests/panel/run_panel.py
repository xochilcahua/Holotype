# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Run the 60-person panel, the twin pairs and the depth ladder through the app, and compare
with the frozen expectations. Pure measurement: it changes nothing and judges nothing beyond
"does the reading equal the expectation".

usage (from the repository root):
    python3 tests/panel/run_panel.py                  # everything
    python3 tests/panel/run_panel.py --only X01 B11   # key prefixes, for a quick check
writes:
    out/panel/panel_results.json   every reading, machine-readable
    out/panel/panel_report.md      the numbers laid out as the notes sections need them

It calls the app's own computeClassification() in a headless browser. It does NOT
re-implement any app logic (earlier tools that did went stale and reported confident nonsense).

Expectations: tests/panel/expectations.md   (written before any run; do not edit)
Twin pairs:   tests/panel/twins.md           (same)
"""
import argparse, collections, json, os, pathlib, random, re, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from playwright.sync_api import sync_playwright
import panel_profiles
import panel_profiles_extra  # noqa: F401  (appends X01-X10 to panel_profiles.PROFILES)

PROFILES = panel_profiles.PROFILES
BITS = "BPSF"
AXIS = {"P": "a1", "S": "d1", "F": "a4"}          # B (breadth) has no single axis
ORDER_NOTE = "genus id digits are B,P,S,F; 1 = HIGH (wide / planned / social / open), 0 = LOW"

JS = r"""
(scenarios) => scenarios.map(sc => {
  state.mastery = {};
  const byName = new Map(ART_FORMS.map(a => [a.name, a]));
  const byId = new Map(ART_FORMS.map(a => [a.id, a]));
  let missing = 0;
  for (const [key, v] of sc.ratings) {
    const f = byName.get(key) || byId.get(key);
    if (!f) { missing++; continue; }
    state.mastery[f.id] = v;
  }
  const c = computeClassification();
  const pick = {};
  for (const k of ['genusId','early','closeAxes','regimeId','leans','genusFlips','zProcess','zSoc',
                   'zForm','zRegime','topShare','categoriesTouched','topKept','confidence',
                   'ratedCount','keptEnough','genusFragile'])
    pick[k] = c[k];
  pick.genusName = c.genus && c.genus.name;
  pick.missing = missing;
  state.mastery = {};
  return pick;
})
"""

def load_expectations():
    exp = {}
    for line in (HERE / "expectations.md").read_text(encoding="utf-8").splitlines():
        if " | B=" not in line or line.startswith("key |") or "<HIGH" in line:
            continue
        parts = [p.strip() for p in line.split(" | ")]
        d = {p[0]: p[2:] for p in parts[1:5]}          # 'B' -> 'HIGH'
        exp[parts[0]] = {"bits": d, "why": parts[5] if len(parts) > 5 else ""}
    return exp

def load_twins():
    part, differ, alike = 0, [], []
    for line in (HERE / "twins.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("PART 1"): part = 1; continue
        if line.startswith("PART 2"): part = 2; continue
        if line.startswith("HOW TO SCORE"): part = 0
        if part and " | " in line and not line.startswith(("Format", "#")):
            a, b, bits, why = [x.strip() for x in line.split(" | ", 3)]
            rec = {"a": a, "b": b, "bits": [] if bits == "none" else bits.split(","), "why": why}
            (differ if part == 1 else alike).append(rec)
    return differ, alike

def bit(res, b):
    return int(res["genusId"][BITS.index(b)])

def leans(res):
    return sorted(str(x) for x in (res["leans"] or []))

def same_reading(r1, r2):
    return (r1["genusId"] == r2["genusId"] and r1["regimeId"] == r2["regimeId"]
            and leans(r1) == leans(r2))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None, help="profile key prefixes")
    args = ap.parse_args()

    exp = load_expectations()
    keys = [p["key"] for p in PROFILES]
    if set(keys) != set(exp):
        sys.exit("STOP: profile keys and expectations.md keys differ: only in profiles %s; only in expectations %s"
                 % (sorted(set(keys) - set(exp)), sorted(set(exp) - set(keys))))
    chosen = [p for p in PROFILES if not args.only or any(p["key"].startswith(x) for x in args.only)]

    sessions = []
    for f in sorted(pathlib.Path(os.environ.get("HOLOTYPE_SESSIONS", ROOT / "tests" / "sample_sessions")).glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        sessions.append({"key": "REAL_" + f.stem.replace("holotype-session-", ""),
                         "ratings": [(r["id"], r["rating"]) for r in d["ratings"]]})

    with sync_playwright() as pw:
        br = pw.chromium.launch(); pg = br.new_page()
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto((ROOT / "index.html").as_uri()); pg.wait_for_timeout(1000)
        run = lambda sc: pg.evaluate(JS, sc)

        main_res = run([{"ratings": p["ratings"]} for p in chosen])
        for p, r in zip(chosen, main_res):
            r["key"] = p["key"]; r["n"] = len(p["ratings"])
            if r["missing"]:
                sys.exit("STOP: %s has %d names the app does not know" % (p["key"], r["missing"]))
        R = {r["key"]: r for r in main_res}

        # ---- twins -------------------------------------------------------------
        differ, alike = load_twins()
        tw_differ = []
        for t in differ:
            if t["a"] in R and t["b"] in R:
                a, b = R[t["a"]], R[t["b"]]
                hits = {x: bit(a, x) != bit(b, x) for x in t["bits"]}
                close = {x: (AXIS.get(x) in (a["closeAxes"] or []) or AXIS.get(x) in (b["closeAxes"] or [])) for x in t["bits"]}
                tw_differ.append({**t, "genus": [a["genusId"], b["genusId"]], "hits": hits,
                                  "full_hit": all(hits.values()), "in_deadband": close,
                                  "identical_reading": same_reading(a, b), "depths": [a["n"], b["n"]],
                                  "dz": {"P": round(a["zProcess"] - b["zProcess"], 3),
                                         "S": round(a["zSoc"] - b["zSoc"], 3),
                                         "F": round(a["zForm"] - b["zForm"], 3)}})
        tw_alike = []
        for t in alike:
            if t["a"] in R and t["b"] in R:
                a, b = R[t["a"]], R[t["b"]]
                tw_alike.append({**t, "genus": [a["genusId"], b["genusId"]],
                                 "identical_genus": a["genusId"] == b["genusId"],
                                 "identical_reading": same_reading(a, b), "depths": [a["n"], b["n"]]})

        # ---- depth ladder ------------------------------------------------------
        STEPS = [5, 12, 25]
        ladder = {"descending": {}, "shuffled": {}}
        pool = [(p["key"], p["ratings"]) for p in chosen if len(p["ratings"]) >= 20]
        pool += [(s["key"], s["ratings"]) for s in sessions if len(s["ratings"]) >= 20]
        rnd = random.Random(7)
        scen, tags = [], []
        for key, rt in pool:
            for order in ("descending", "shuffled"):
                seq = sorted(rt, key=lambda x: -x[1]) if order == "descending" else rnd.sample(rt, len(rt))
                for st in STEPS + ["all"]:
                    n = len(seq) if st == "all" else st
                    if st != "all" and n >= len(seq):
                        continue
                    scen.append({"ratings": seq[:n]}); tags.append((key, order, st))
        ladder_res = run(scen) if scen else []
        for (key, order, st), r in zip(tags, ladder_res):
            ladder[order].setdefault(key, {})[st] = r["genusId"]
        br.close()

    # ---- agreement with expectations ------------------------------------------
    agree = {}
    detail = []
    settled = [k for k in R if not R[k]["early"] or exp[k]["bits"]["B"] != "NONE"]
    for b in BITS:
        c = collections.Counter(); hi_ok = hi_n = lo_ok = lo_n = dead = 0
        for k, r in R.items():
            e = exp[k]["bits"][b]
            c[e] += 1
            if e in ("EITHER", "NONE") or r["early"]:
                continue
            got = bit(r, b)
            ok = (got == 1) == (e == "HIGH")
            if e == "HIGH": hi_n += 1; hi_ok += ok
            else: lo_n += 1; lo_ok += ok
            if not ok:
                detail.append({"key": k, "bit": b, "expected": e, "got": "HIGH" if got else "LOW",
                               "z": {"B": r["topShare"], "P": r["zProcess"], "S": r["zSoc"], "F": r["zForm"]}[b],
                               "ratings": len(r and [x for x in chosen if x["key"] == k][0]["ratings"]),
                               "top_rated": sorted([x for x in [p for p in chosen if p["key"] == k][0]["ratings"]],
                                                   key=lambda x: -x[1])[:5]})
            if AXIS.get(b) in (r["closeAxes"] or []): dead += 1
        n = hi_n + lo_n
        agree[b] = {"expected_counts": dict(c), "scored": n, "agree": hi_ok + lo_ok,
                    "agree_pct": round(100 * (hi_ok + lo_ok) / n, 1) if n else None,
                    "recall_HIGH": f"{hi_ok}/{hi_n}", "recall_LOW": f"{lo_ok}/{lo_n}",
                    "baseline_always_majority_pct": round(100 * max(hi_n, lo_n) / n, 1) if n else None,
                    "readings_in_deadband": dead}
    none_checks = {k: {"early": R[k]["early"], "genus": R[k]["genusId"], "confidence": R[k]["confidence"]}
                   for k in R if exp[k]["bits"]["B"] == "NONE"}

    # ---- distribution -----------------------------------------------------------
    full = [r for r in R.values() if not r["early"]]
    gc = collections.Counter(r["genusId"] for r in full)
    allg = [format(i, "04b") for i in range(16)]
    dist = {"people_with_genus": len(full), "counts": dict(gc.most_common()),
            "largest_share_pct": round(100 * gc.most_common(1)[0][1] / len(full), 1) if full else None,
            "never_reached": [g for g in allg if g not in gc],
            "share_with_any_deadband_pct": round(100 * sum(bool(r["closeAxes"]) for r in full) / len(full), 1) if full else None}

    # ---- ladder summary -----------------------------------------------------------
    lad_sum = {}
    for order, data in ladder.items():
        seq_steps = STEPS + ["all"]; rows = {}
        for i in range(1, len(seq_steps)):
            prev, cur = seq_steps[i - 1], seq_steps[i]
            both = [(k, v[prev], v[cur]) for k, v in data.items() if prev in v and cur in v]
            ch = [x for x in both if x[1] != x[2]]
            flips = collections.Counter()
            for _, g0, g1 in ch:
                for j, b in enumerate(BITS):
                    if g0[j] != g1[j]: flips[b] += 1
            rows[f"{prev}->{cur}"] = {"people": len(both), "genus_changed": len(ch),
                                      "share_pct": round(100 * len(ch) / len(both), 1) if both else None,
                                      "bit_flips": dict(flips)}
        late = [k for k, v in data.items() if 25 in v and "all" in v and v[25] != v["all"]]
        lad_sum[order] = {"steps": rows, "still_changing_25_to_all": late}

    out = {"note": ORDER_NOTE, "page_errors": errs[:3], "readings": R, "agreement": agree,
           "none_checks": none_checks, "disagreements": detail, "twins_differ": tw_differ,
           "twins_alike": tw_alike, "distribution": dist, "ladder": lad_sum, "ladder_raw": ladder}
    od = ROOT / "out" / "panel"; od.mkdir(parents=True, exist_ok=True)
    (od / "panel_results.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")

    # ---- markdown ------------------------------------------------------------------
    L = ["# Panel run (generated by run_panel.py; numbers only)", "", ORDER_NOTE, "",
         "profiles run: %d   page errors: %s" % (len(R), errs[:3] or "none"), "", "## Panel", ""]
    for p in chosen:
        r = R[p["key"]]
        L.append("- %s | ratings %d | genus %s (%s) | regime %s | leans %s | deadband %s%s"
                 % (p["key"], r["n"], r["genusId"], r["genusName"], r["regimeId"], leans(r) or "-",
                    r["closeAxes"] or "-", " | EARLY (provisional)" if r["early"] else ""))
    L += ["", "## Agreement with expectations", "",
          "EITHER and NONE are not scored. 'baseline' = always answering the more common expectation."]
    for b in BITS:
        a = agree[b]
        L.append("- %s: expected %s | scored %d | agree %d (%s%%) | recall HIGH %s, LOW %s | baseline %s%% | in dead-band %d"
                 % (b, a["expected_counts"], a["scored"], a["agree"], a["agree_pct"], a["recall_HIGH"],
                    a["recall_LOW"], a["baseline_always_majority_pct"], a["readings_in_deadband"]))
    L.append("- no-genus checks (expected NONE): %s" % none_checks)
    L += ["", "## Disagreements", ""]
    for d in detail:
        L.append("- %s bit %s: expected %s, app %s, z/share %.3f, ratings %d, top rated %s"
                 % (d["key"], d["bit"], d["expected"], d["got"], d["z"], d["ratings"], d["top_rated"]))
    L += ["", "## Twin test", "", "Pairs that should DIFFER:"]
    for t in tw_differ:
        L.append("- %s / %s | genus %s | named bits differ: %s | all named differ: %s | in dead-band: %s | identical reading: %s | dz %s | depths %s"
                 % (t["a"], t["b"], t["genus"], t["hits"], t["full_hit"], t["in_deadband"], t["identical_reading"], t["dz"], t["depths"]))
    L.append("")
    L.append("Differ-pairs: full hits %d/%d | identical genus+regime+leans %d/%d"
             % (sum(t["full_hit"] for t in tw_differ), len(tw_differ), sum(t["identical_reading"] for t in tw_differ), len(tw_differ)))
    L += ["", "Pairs that should READ ALIKE:"]
    for t in tw_alike:
        L.append("- %s / %s | genus %s | identical genus: %s | identical genus+regime+leans: %s | depths %s"
                 % (t["a"], t["b"], t["genus"], t["identical_genus"], t["identical_reading"], t["depths"]))
    L.append("")
    L.append("Alike-pairs: identical genus %d/%d | identical genus+regime+leans %d/%d"
             % (sum(t["identical_genus"] for t in tw_alike), len(tw_alike), sum(t["identical_reading"] for t in tw_alike), len(tw_alike)))
    L += ["", "## Depth ladder", "", "Steps 5, 12, 25, all. People: panel profiles with 20+ ratings plus any saved sessions in $HOLOTYPE_SESSIONS (guards; report only)."]
    for order, s in lad_sum.items():
        L.append("- order %s:" % order)
        for k, v in s["steps"].items():
            L.append("    %s: %s people, genus changed %s (%s%%), bit flips %s" % (k, v["people"], v["genus_changed"], v["share_pct"], v["bit_flips"]))
        L.append("    still changing between 25 and all: %s" % (s["still_changing_25_to_all"] or "none"))
    L += ["", "## Genus distribution on the panel", "", json.dumps(dist, indent=1)]
    (od / "panel_report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("wrote out/panel/panel_results.json and out/panel/panel_report.md")
    print("profiles %d | page errors %s" % (len(R), errs[:3] or "none"))

if __name__ == "__main__":
    main()
