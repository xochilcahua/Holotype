# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Independent population probe for Holotype's genus classifier.

Usage (repository root): python3 tests/audit/probe_population.py index.html [n=500] [seed=5]

Draws plausible people the way person-space.js calibrates PEOPLE_MEAN/SD (a cluster of
forms nearest a seed form, bottom-heavy ratings), but with 1-3 interest clusters and three
rating depths. Prints, per depth, only people with 4+ ratings (settled): genus entropy (max
4 bits), top genera, share of each bit, bit correlations, the share with d1 inside the
dead-band, and the entropy of the full signature (genus + regime + leans).

It is deliberately NOT the harness's population model. If its numbers disagree with
tests/population_check.py, the disagreement is the finding: find which population
assumption (size, breadth, rating mix, share of thin people) drives it. Neither population
is real data. NOTE: an earlier version of this probe dropped the lean labels from the signature
(leans are strings, it read .ax); that is fixed here, so signature entropy is higher than the
figures quoted in older notes.
"""
import sys, math, itertools, collections, pathlib
from playwright.sync_api import sync_playwright

JS = r"""
(a) => {
  let seed = a.seed;
  const rnd = () => (seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff;
  const N = ART_FORMS.length;
  const draw = () => { const r = rnd(); return r < 0.50 ? 1 + Math.floor(rnd()*2) : r < 0.85 ? 3 + Math.floor(rnd()*3) : 6 + Math.floor(rnd()*3); };
  const out = [];
  for (let p = 0; p < a.n; p++) {
    state.mastery = {};
    const nclu = 1 + Math.floor(rnd()*3);
    for (let c = 0; c < nclu; c++) {
      const s = Math.floor(rnd()*N);
      const size = Math.floor((a.lo + rnd()*(a.hi-a.lo))/nclu);
      ART_FORMS.map((f,i)=>[DIST[s][i], i]).sort((x,y)=>x[0]-y[0]).slice(0,size)
        .forEach(x => state.mastery[ART_FORMS[x[1]].id] = draw());
    }
    const c = computeClassification();
    out.push({ g:c.genusId, early:c.early, close:c.closeAxes, regime:c.regimeId,
               leans:(c.leans||[]).map(l => String(l)), flips:c.genusFlips||0 });
  }
  state.mastery = {};
  return out;
}
"""

def corr(a, b):
    ma, mb = sum(a)/len(a), sum(b)/len(b)
    cov = sum((x-ma)*(y-mb) for x, y in zip(a, b))
    va, vb = sum((x-ma)**2 for x in a), sum((y-mb)**2 for y in b)
    return cov/math.sqrt(va*vb) if va*vb else 0.0

def report(tag, rows):
    r = [x for x in rows if not x['early']]; n = len(r)
    c = collections.Counter(x['g'] for x in r)
    H = -sum(v/n*math.log2(v/n) for v in c.values())
    bits = [[int(x['g'][i]) for x in r] for i in range(4)]
    sig = collections.Counter((x['g'], x['regime'], tuple(sorted(x['leans']))) for x in r)
    Hs = -sum(v/n*math.log2(v/n) for v in sig.values())
    print(f"{tag}: settled={n}  genus entropy={H:.2f}/4  top={[(k, round(100*v/n)) for k, v in c.most_common(4)]}")
    print(f"   bit shares (B,P,S,F)={[round(sum(b)/n, 2) for b in bits]}  "
          f"corr={{{', '.join('BPSF'[i]+'BPSF'[j]+':'+format(corr(bits[i], bits[j]), '.2f') for i, j in itertools.combinations(range(4), 2))}}}")
    print(f"   d1 in dead-band={sum('d1' in x['close'] for x in r)/n:.2f}  signature distinct={len(sig)} entropy={Hs:.2f} bits  mean drop-one flips={sum(x['flips'] for x in r)/n:.2f}")

if __name__ == "__main__":
    app = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parents[2] / 'index.html').resolve()
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 500
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page()
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(app.as_uri()); pg.wait_for_timeout(800)
        for tag, lo, hi in (("small 8-20", 8, 20), ("medium 20-50", 20, 50), ("large 50-110", 50, 110)):
            report(tag, pg.evaluate(JS, {"n": n, "seed": seed, "lo": lo, "hi": hi}))
        print("page errors:", errs[:3] or "none")
        b.close()
