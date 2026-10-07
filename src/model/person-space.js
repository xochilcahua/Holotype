// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

/* THE REFERENCE EVERY READING IS SCORED AGAINST. AXIS_MEAN/SD is the spread across
individual FORMS and describes one practice; PEOPLE_MEAN/SD is the spread across
PEOPLE and reads one person. A person is an average over what they rated, so their
vector is far less spread than any single form -- dividing by the form-scale spread
put nearly everyone in the dead-band and made four people identical. Measured
numbers and the long version are in the comments below.
   See docs/architecture.md. */

const AXIS_MEAN = {},
  AXIS_SD = {},
  AXIS_MEDIAN = {};
// Median of a list of numbers (the upper middle value for even lengths).
const medianOf = (arr) => {
  const v = arr.slice().sort((a, b) => a - b);
  return v.length ? v[v.length >> 1] : 0;
};
AXES.forEach((ax) => {
  const vals = EFF.map((v) => v[ax]);
  const m = vals.reduce((s, x) => s + x, 0) / N;
  AXIS_MEAN[ax] = m;
  AXIS_SD[ax] = Math.sqrt(vals.reduce((s, x) => s + (x - m) * (x - m), 0) / N) || 1;
  AXIS_MEDIAN[ax] = medianOf(vals); // tie-break reference for the genus dead-band (see computeClassification)
});

// ---- Person-space moments: the reference for reading a PERSON, not a practice ----
//
// The three constants above answer "how unusual is this art form compared to the typical art
// form", which is the right question when describing a single practice (see describeArtForm).
// It was also being used to read a person, and that is the wrong comparison, for a reason worth
// writing down because it made almost every profile come out the same.
//
// A person's vector is not an art form's vector. It is a rating-weighted AVERAGE of the vectors
// of the forms that person happened to rate, and averaging shrinks deviation: the closer the
// average is to the centre, the more forms go into it. Measured over 900 simulated people,
// a person's spread on every axis is about a fifth of the spread across individual forms -
// 0.046 against 0.243 on a1, 0.053 against 0.265 on d1.
//
// Dividing a person by the form-scale SD therefore produces z-scores around 0.1 when they should
// be around 0.5, and every reading lands inside the 0.22 dead-band. Measured: 73-80% of people
// were inside it on each of the three genus axes, and 78% of all genus bits were being decided
// by the tie-break rather than by the person's own ratings. The tie-break then compares the
// median of a sample drawn from the catalog against the catalog median, which converges on the
// same answer for everybody - so four friends with 20, 53, 57 and 103 ratings were all handed
// the same tribe, Lemna, on evidence that had almost nothing to do with any of them.
//
// These are the mean and SD of PERSONS instead, so "one SD" means "one SD between people", which
// is the question the page is actually asking. Measured after the change: axes settled by the
// tie-break fall from 78% to 18%, and the reading is then decided by what the person rated.
//
// The sample is 500 plausible people drawn with a fixed seed, and it matters that they are not
// just 500 random draws from the catalog. A person rates a COHERENT set of related forms - a
// dancer rates dance, choreography and costume; a maker rates woodwork, welding and tools - not
// 306 unrelated ones, and rating a tight cluster pulls the vector much further from the centre
// than rating scattered items does. Calibrating on uniform random draws therefore understates
// the spread between people (person SD 0.051 on d1 against a real 0.123), which makes the sign
// test fire confidently in the wrong direction for anyone near the line. Measured on the 400
// person population model: random draws scored 93.7% against ground truth, clustered people
// 94.8% - the same as the original code, with the tie-break now handling 5% of decisions rather
// than 12%. So each simulated person rates a cluster of forms chosen by vector distance, and the
// ratings are bottom-heavy in the way a 1-10 self-rating on 306 items actually is.
//
// TWO THINGS WERE WRONG WITH THAT, and both are measured, not argued
// (the probes behind these numbers have since been removed):
//
// 1. HOW MANY. This sampler drew 8-97 forms per person, median 55. ASSUMPTION, NOT DATA: the
//    claim below that "real readers rate a median of 5" comes from population.py, a model the
//    author wrote, which draws about 4.8 ratings per person on average (population_check on
//    600 drawn). There is no measurement of real readers; the only real sessions available
//    (four, kept private) hold 20, 53, 57 and 103 ratings. Because
//    personalVector() AVERAGES, more forms means more shrinkage toward the catalogue centre, so
//    the reference was far more central than any real reader. That is not a subtle drift: it
//    left the mean sitting 2.38 SD away from the real population on a1, 1.11 on a4 and 0.59 on
//    d1. Since z = (value - PEOPLE_MEAN)/PEOPLE_SD, an offset of that size is a constant every
//    reader inherits, and it tilts the sign test for EVERYONE whatever they rated. Measured
//    effect: only 24% of real people landed on the positive side of the process test where a
//    fair test gives 50%, and the genus bits came out 26 / 27 / 71 instead of roughly even.
//    The count is now drawn to match a real reader's.
//
// 2. WHICH FORMS -- NOT DONE, and deliberately so. The reference also drew its seed form
//    UNIFORMLY from the catalogue, while the people who arrive are a skewed subset (phone
//    photography and singing are common, blacksmithing is not), so participation-weighting the
//    seed is the obvious second half of the fix. It was implemented and then removed, because
//    the participation table (PREVALENCE) lives in ui/herbarium.js, which loads at position 20,
//    and this file runs at position 8. A `typeof PREVALENCE` guard cannot catch that: typeof on
//    an undeclared name is "undefined" rather than an error, so the guard passes and a flat
//    fallback is used silently. Measured with a probe (since removed) that ran inside the real load
//    sequence: PREVALENCE is ABSENT when this file runs and present
//    afterwards. So the weighting would have looked applied while changing nothing -- and it was
//    worth little anyway: 0.558 SD mean offset without it, 0.536 with. Moving the participation
//    figures to where the catalogue data belongs is the right fix, and it is a data move, not a
//    model change. Left for the next pass rather than done silently and wrongly here.
//
// Together these take the mean absolute offset from 1.10 SD to 0.54 SD. That is a real
// improvement and it is NOT a complete one: the reference is still built from a uniform
// cluster, so a residual remains, and the bits still read 28 / 27 / 72 rather than evenly.
// Do not treat the remaining offset as settled: the change is UNPROVEN against real readers.
//
// It costs about 90 ms once at load. The moments are stable to three decimal places from 400
// people upward, so neither the seed nor the size is load-bearing.
// TRIED AND REVERTED (2026-10, measured with the four real sessions plus a 300-person
// prevalence-weighted simulation). PREVALENCE now loads before this file (data/prevalence.js), so the
// "participation-weighted seed" described in point 2 above is possible. It was implemented, for the
// seed and for the neighbours, at n = 2-8, 4-60 and 10-80 ratings per reference person. Effect on a
// simulated ordinary rater (~30 ratings): planned 22% -> 53-61%, collaborative 14% -> 44-46%, i.e. the
// bits stop skewing improvised and solo. Effect on the four real sessions: zSoc goes from
// -0.13/0.00/-0.09/-0.06 to +0.23/+0.39/+0.28/+0.31 in every variant, which reads ALL FOUR as
// collaborative, including one person known not to collaborate. The reference mean for
// d1 drops from 0.263 to ~0.205 because the common forms (drawing, photography, writing) are solo, and
// real long-list raters sit near the catalogue mean, so they land above it. The simulated population
// is built from this app's own prevalence table, so it cannot overrule a confirmed real person.
// Left flat. To settle it, collect labelled sessions (rater says "I do/don't work with others") and fit
// the d1 reference to those; tests/audit/ref_variants.py reruns the comparison.
const PEOPLE_MEAN = {},
  PEOPLE_SD = {},
  PEOPLE_MEDIAN = {};
(function calibratePersonSpace() {
  const axes = [...AXIS_GROUPS.technique, ...AXIS_GROUPS.domain, ...AXIS_GROUPS.sensory];
  const nForms = ART_FORMS.length;
  let seed = 31337;
  const rnd = () => (seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff;
  // a bottom-heavy self-rating: most things a little, a thin tail done well
  const drawRating = () => {
    const r = rnd();
    return r < 0.5
      ? 1 + Math.floor(rnd() * 2) // tried and dropped
      : r < 0.85
        ? 3 + Math.floor(rnd() * 3) // casual
        : 6 + Math.floor(rnd() * 3); // serious
  };
  const sample = [];
  // A cluster of 25 nearest forms is wide enough to include the forms someone who rates
  // the seed would plausibly also rate, and narrow enough that the cluster stays a cluster.
  // It used to be 20-140, which is most of a dense category and no longer a neighbourhood.
  const width = 25;
  for (let p = 0; p < 500; p++) {
    // an inline copy of personalVector's weighting, so this reads no real state
    let wSum = 0;
    const v = {};
    axes.forEach((ax) => (v[ax] = 0));
    const add = (f) => {
      const w = ratingWeight(drawRating());
      wSum += w;
      axes.forEach((ax) => (v[ax] += w * f[ax]));
    };
    // this person is a cluster: one seed form, then the nearest neighbours of it
    const seedF = EFF[Math.floor(rnd() * nForms)];
    const near = EFF.map((f) => {
      let s = 0;
      for (const ax of axes) {
        const d = f[ax] - seedF[ax];
        s += d * d;
      }
      return { f, d: Math.sqrt(s / axes.length) };
    }).sort((a, b) => a.d - b.d);
    // How MANY: ASSUMPTION, not data. population.py (a model the author wrote) draws a median of
    // 5 ratings and a mean of about 4.9, with 45% under four; no real-reader data exists.
    // The spread below keeps the reference from being a single point at exactly 5.
    const n = Math.max(2, Math.round(5 + (rnd() * 2 - 1) * 3));
    for (let i = 0; i < n; i++) add(near[Math.min(near.length - 1, Math.floor(rnd() * width))].f);
    if (wSum) {
      axes.forEach((ax) => (v[ax] /= wSum));
      sample.push(v);
    }
  }
  axes.forEach((ax) => {
    const vals = sample.map((v) => v[ax]);
    const m = vals.reduce((s, x) => s + x, 0) / vals.length;
    PEOPLE_MEAN[ax] = m;
    PEOPLE_SD[ax] = Math.sqrt(vals.reduce((s, x) => s + (x - m) * (x - m), 0) / vals.length) || 1;
    // The dead-band tie-break compares median to median, so it needs a person-space MEDIAN too,
    // not a mean. Using the mean here would be a median compared against something else.
    PEOPLE_MEDIAN[ax] = medianOf(vals);
  });
})();

// LENGTH-MATCHED, PARTICIPATION-WEIGHTED REFERENCE (V03).
// Two problems with the single flat reference above, both measured (tests/audit/ref_variants.py):
//   1. Its seed form is drawn uniformly, so the reference person is built from a catalogue that is mostly
//      niche, solo, rule-bound crafts. Ordinary raters pick common forms (singing, drawing, photography),
//      so almost everyone landed on the improvised, interpretive, solo side: 26 of 32 realistic test people
//      read interpretive, 24 improvised, 22 solo, and one genus (Cuscuta) took 10 of 32.
//   2. personalVector() averages, so a long list shrinks toward the catalogue centre. A single reference
//      cannot be right for both a 4-form list and a 100-form list. Long lists were being read as more
//      collaborative simply because they were long.
// So the reference is now drawn the way ordinary raters rate (seed and neighbours weighted by PREVALENCE)
// and is built separately for four list lengths. A reader is compared with people who rated about as many
// forms. Each bucket is ASSUMPTION-driven (no real-reader data exists); what it fixes is the balance of the
// bits, which is checkable. The flat PEOPLE_MEAN/SD above stay for tools that read them.
const PEOPLE_REF = [];
(function calibrateLengthMatched() {
  const axes = [...AXIS_GROUPS.technique, ...AXIS_GROUPS.domain, ...AXIS_GROUPS.sensory];
  const N = ART_FORMS.length;
  const W = ART_FORMS.map((f) => Math.max(0.5, (typeof PREVALENCE !== "undefined" && PREVALENCE[f.id]) || 0.5));
  const nearCache = {};
  const nearOf = (si) =>
    nearCache[si] ||
    (nearCache[si] = EFF.map((f, i) => {
      let q = 0;
      for (const ax of axes) {
        const d = f[ax] - EFF[si][ax];
        q += d * d;
      }
      return { f, i, d: Math.sqrt(q / axes.length) };
    }).sort((a, b) => a.d - b.d));
  const BUCKETS = [
    [1, 4, 3, 4],
    [5, 9, 5, 9],
    [10, 24, 10, 24],
    [25, 1000, 25, 60],
  ]; // [from, to, n low, n high] ratings per reference person
  BUCKETS.forEach(([lo, hi, nLo, nHi], bi) => {
    let seed = 31337 + bi * 101;
    const rnd = () => (seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff;
    const drawRating = () => {
      const r = rnd();
      return r < 0.5 ? 1 + Math.floor(rnd() * 2) : r < 0.85 ? 3 + Math.floor(rnd() * 3) : 6 + Math.floor(rnd() * 3);
    };
    const pickW = (arr, wt, tot) => {
      let t = rnd() * tot,
        k = 0;
      while (k < arr.length - 1 && (t -= wt[k]) > 0) k++;
      return k;
    };
    const totAll = W.reduce((a, b) => a + b, 0),
      idx = ART_FORMS.map((_, i) => i);
    const sample = [];
    for (let p = 0; p < 600; p++) {
      const si = pickW(idx, W, totAll),
        near = nearOf(si);
      const n = nLo + Math.floor(rnd() * (nHi - nLo + 1));
      const win = near.slice(0, Math.max(25, Math.ceil(n * 1.5))),
        wt = win.map((x) => W[x.i]),
        tot = wt.reduce((a, b) => a + b, 0);
      let wSum = 0;
      const v = {};
      axes.forEach((ax) => (v[ax] = 0));
      for (let i = 0; i < n; i++) {
        const f = win[pickW(win, wt, tot)].f,
          w = ratingWeight(drawRating());
        wSum += w;
        axes.forEach((ax) => (v[ax] += w * f[ax]));
      }
      if (wSum) {
        axes.forEach((ax) => (v[ax] /= wSum));
        sample.push(v);
      }
    }
    const MEAN = {},
      SD = {},
      MEDIAN = {};
    axes.forEach((ax) => {
      const vals = sample.map((v) => v[ax]),
        m = vals.reduce((s, x) => s + x, 0) / vals.length;
      MEAN[ax] = m;
      SD[ax] = Math.sqrt(vals.reduce((s, x) => s + (x - m) * (x - m), 0) / vals.length) || 1;
      MEDIAN[ax] = medianOf(vals);
    });
    // Sociability (d1) keeps the original flat reference. Weighting by participation moved it the wrong way on
    // every check that has an answer: the four real sessions all read collaborative (including one person who does
    // not collaborate) and agreement on the panel's Social bit fell from 80% to 74%. Process (a1) improved
    // (66% to 76%), so only d1 is held back.
    MEAN.d1 = PEOPLE_MEAN.d1;
    SD.d1 = PEOPLE_SD.d1;
    MEDIAN.d1 = PEOPLE_MEDIAN.d1;
    PEOPLE_REF.push({ lo, hi, MEAN, SD, MEDIAN });
  });
})();
// The reference population to score a person against, chosen by how many forms they rated (see PEOPLE_REF above).
function peopleRefFor(nRated) {
  return PEOPLE_REF.find((r) => nRated >= r.lo && nRated <= r.hi) || PEOPLE_REF[PEOPLE_REF.length - 1];
}
