# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""
Runs a sampled population through the app and asks the question the archetype profiles cannot:
does the reading CORRELATE with who the person actually is?

A single-profile gut check ("does Cuscuta sound right for this person?") is a matter of taste and
can only catch bad cases one at a time. This runs N synthetic people in one browser session and
looks at the aggregate, where taste becomes falsifiable:

  - makers are modelled solo-skewed, performers collaborative-skewed.
    Does the app's d1 bit actually track that, or is it noise?
  - people who rate 2-3 things should read focused, people who rate 15+ should read wide.
    Does the breadth bit track the thing it claims to measure?
  - serious practitioners should read more often as literal/structured than casual ones.
  - do the "floor" profiles (everything at 1-2) land somewhere sensible, or all collapse
    into one tribe?

usage: python3 population_check.py <app.html> [n] [seed] [--engaged]
prints a report. Fast: one page load, N classifications in-process.
"""
import sys, os, json, hashlib, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import population as POP

APP = os.path.abspath(sys.argv[1])
N = int(sys.argv[2]) if len(sys.argv) > 2 else 400
SEED = int(sys.argv[3]) if len(sys.argv) > 3 else 11
ENGAGED = "--engaged" in sys.argv

from playwright.sync_api import sync_playwright

RUN_JS = r"""
(specs) => {
  const BY = {}; ART_FORMS.forEach(a => BY[a.name] = a.id);
  const out = [];
  for (const ratings of specs) {
    state.mastery = {};
    for (const [name, v] of ratings) state.mastery[BY[name]] = v;
    renderGrid(); setMode('profile');
    const bc = computeClassification();
    if (!bc) { out.push(null); continue; }
    out.push({
      genusId: bc.genusId, genus: bc.genus.name, regime: bc.regimeId, regimeWord: bc.regime.word,
      leans: bc.leans.slice(), early: bc.early, hhi: bc.hhi,
      topShare: bc.topShare, topField: bc.topField, breadthUnproven: bc.breadthUnproven,
      socUmbrellaOnly: bc.socUmbrellaOnly,
      zProcess: bc.zProcess, zSoc: bc.zSoc, zForm: bc.zForm, zRegime: bc.zRegime,
      close: bc.closeAxes.slice(), nRated: bc.ratedCount,
    });
  }
  return out;
}
"""

people = POP.sample(N, seed=SEED, engaged=ENGAGED)
specs = [list(p["ratings"].items()) for p in people]

with sync_playwright() as pw:
    br = pw.chromium.launch()
    pg = br.new_page(viewport={"width": 1440, "height": 1200})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("file://" + APP)
    pg.wait_for_timeout(600)
    results = pg.evaluate(RUN_JS, specs)
    br.close()

rows = [dict(p, **r) for p, r in zip(people, results) if r]
json.dump(rows, open("/tmp/poprows.json", "w"), ensure_ascii=False)

print(f"app: {os.path.basename(APP)}  sha {hashlib.sha256(open(APP,'rb').read()).hexdigest()[:12]}")
print(f"{len(people)} people (seed {SEED}, engaged={ENGAGED}); {len(rows)} classified; errors {len(errs)}")
if errs:
    print("  page errors:", errs[:3])
print(f"mean forms rated {sum(r['nRated'] for r in rows)/len(rows):.1f}   "
      f"early (<4 ratings) {sum(1 for r in rows if r['early'])/len(rows)*100:.0f}%")


def pct(xs, cond):
    return (sum(1 for x in xs if cond(x)) / len(xs) * 100) if xs else float("nan")


def section(t):
    print("\n" + "=" * 78 + "\n" + t)


section("1. does the solo/collaborative bit track the type's real solo bias?")
print("   (d1 bit: 0 = solo, 1 = collaborative. solo_bias is ground truth from the model.)")
print("   A type with solo_bias of exactly 0 is genuinely mixed and is reported, not scored.")
by = collections.defaultdict(list)
for r in rows:
    by[r["type"]].append(r)
print("   %-22s %6s %5s %9s %8s" % ("type", "n", "solo_b", "expected", "actual"))
for t in sorted(by, key=lambda k: by[k][0]["solo_bias"]):
    rs = by[t]
    bias = rs[0]["solo_bias"]
    actual = pct(rs, lambda r: r["genusId"][2] == "1")
    if bias == 0:
        print("   %-22s %6d %+6.2f %9s %7.0f%%   (mixed, not scored)" % (t, len(rs), bias, "-", actual))
        continue
    exp = 100.0 if bias < 0 else 0.0
    bad = "  <-- INVERTED" if abs(exp - actual) > 30 and min(exp, actual) < 45 else ""
    print("   %-22s %6d %+6.2f %8.0f%% %7.0f%%%s" % (t, len(rs), bias, exp, actual, bad))
coll = [r for r in rows if r["solo_bias"] < 0]
solo = [r for r in rows if r["solo_bias"] > 0]
print("   all collaborative-skewed people: %3.0f%% get the collaborative bit"
      % pct(coll, lambda r: r["genusId"][2] == "1"))
print("   all solo-skewed people:          %3.0f%% get the solo bit"
      % pct(solo, lambda r: r["genusId"][2] == "0"))
both = coll + solo
print("   OVERALL agreement with ground truth: %.1f%%"
      % pct(both, lambda r: (r["genusId"][2] == "1") == (r["solo_bias"] < 0)))

section("2. does the breadth bit track how many things a person rates?")
buckets = collections.defaultdict(list)
for r in rows:
    buckets[min(4, r["nRated"])].append(r)
print("   %-12s %5s %10s" % ("forms rated", "n", "% 'wide'"))
for b in sorted(buckets):
    print("   %-12s %5d %9.0f%%" % ("%d-%s" % (b * 3, "+" if b == 4 else "-"), len(buckets[b]),
                                    pct(buckets[b], lambda r: r["genusId"][0] == "1")))

section("3. does depth track the literal/planned read?")
for d in (1, 2, 3):
    rs = [r for r in rows if r["depth"] == d]
    if rs:
        print("   depth %d (%3d people): %3.0f%% planned+literal   mean zForm %+.2f  mean zProcess %+.2f"
              % (d, len(rs), pct(rs, lambda r: r["genusId"][1] == "1" and r["genusId"][3] == "0"),
                 sum(r["zForm"] for r in rs)/len(rs), sum(r["zProcess"] for r in rs)/len(rs)))


section("4. genus distribution")
g = collections.Counter(r["genus"] for r in rows)
for k, v in g.most_common():
    print("   %-16s %4d  %5.1f%%" % (k, v, v / len(rows) * 100))
print("   %d distinct genera across %d people" % (len(g), len(rows)))

section("5. regime, leans, and near-boundary axes")
print("   regime: " + "  ".join("%s %d (%.0f%%)" % (k, v, v/len(rows)*100)
                                for k, v in collections.Counter(r["regime"] for r in rows).most_common()))
ln = collections.Counter(t for r in rows for t in r["leans"])
print("   leans:  " + ("  ".join("%s %d (%.0f%%)" % (k, v, v/len(rows)*100) for k, v in ln.most_common())
                              or "none at all"))
print("   people given no lean at all:        %.0f%%" % pct(rows, lambda r: not r["leans"]))
# That headline number was being read as "the lean rule rarely fires", which is a
# different claim. The lean is gated on !early: a person with fewer than four ratings
# is provisional and is EXCLUDED from leans on purpose, because three ratings cannot
# show a pattern. In this population that is most of the no-lean group. Splitting it
# out is the difference between a rule that is too strict and a population that has
# not rated enough yet.
settled = [r for r in rows if not r["early"]]
prov = [r for r in rows if r["early"]]
if settled:
    print("   of whom provisional (<4 ratings): %d (%.0f%%), excluded from leans by design"
          % (len(prov), 100.0 * len(prov) / len(rows)))
    print("   SETTLED people given a lean:       %.0f%%   <-- the rule's real fire rate"
          % (100.0 * sum(1 for r in settled if r["leans"]) / len(settled)))
if settled:
    thin = [r for r in settled if r["nRated"] <= 7]
    if thin:
        print("   settled but 4-7 ratings only:      %.0f%% given a lean  (n=%d)"
              % (100.0 * sum(1 for r in thin if r["leans"]) / len(thin), len(thin)))
ca = collections.Counter(a for r in rows for a in r["close"])
names = {"a1": "planned/improvised", "d1": "solo/collaborative", "a4": "literal/interpretive"}
print("   axes too close to call: " + "  ".join(
    "%s %d (%.0f%%)" % (names.get(k, k), v, v/len(rows)*100) for k, v in ca.most_common()))
print("   people with all three axes unclear:   %.0f%%" % pct(rows, lambda r: len(r["close"]) >= 3))

section("6. concentration")
lo = [r for r in rows if r["nRated"] >= 4]
print("   of the %d people with 4+ ratings, %d distinct genera appear" % (len(lo), len(set(r["genus"] for r in lo))))
print("   top genus overall: %s at %.0f%%" % (g.most_common(1)[0][0], g.most_common(1)[0][1]/len(rows)*100))
ts = [r["topShare"] for r in rows]
print("   largest-field share: %.2f-%.2f, median %.2f (cutoff %.2f)"
      % (min(ts), max(ts), sorted(ts)[len(ts)//2], 0.55))
near = sum(1 for r in rows if abs(r["topShare"] - 0.55) < 0.05)
print("   %d people (%.0f%%) sit within 0.05 of the breadth cutoff" % (near, near/len(rows)*100))
unp = sum(1 for r in rows if r.get("breadthUnproven"))
print("   breadth 'unproven' (too thin or too few fields to call): %d (%.0f%%)"
      % (unp, unp/len(rows)*100))

print("   %d distinct genera across %d people" % (len(g), len(rows)))
