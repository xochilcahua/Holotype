// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

/* HOW FAR APART TWO FORMS ARE. Builds the effective vectors (a category default
means "unknown", not a shared trait), the raw DIST matrix novelty scores against,
and the hub-corrected REL matrix Related lists use. Full weighting documented
below. Needs ART_FORMS, axes.js. Loads BEFORE novelty.js: reads DIST at top level.
   See docs/architecture.md. */

const HUB_STRENGTH = 0.75; // 0 = off, 1 = full local scaling
const HUB_NEIGHBOURS = 8;

// Vectors used for distance: like the stored ones, but category-default context values -> global mean.
const EFF = (function buildEffectiveVectors() {
  const eff = ART_FORMS.map((a) => Object.assign({}, a.vector));
  const mean = {};
  for (const ax of AXIS_GROUPS.context) mean[ax] = ART_FORMS.reduce((s, a) => s + a.vector[ax], 0) / N;
  const byCategory = {};
  ART_FORMS.forEach((a, i) => {
    (byCategory[a.category] = byCategory[a.category] || []).push(i);
  });
  for (const members of Object.values(byCategory)) {
    if (members.length < 3) continue;
    for (const ax of AXIS_GROUPS.context) {
      const counts = new Map();
      members.forEach((i) => {
        const v = ART_FORMS[i].vector[ax];
        counts.set(v, (counts.get(v) || 0) + 1);
      });
      let modeValue = null,
        modeCount = 0;
      counts.forEach((c, v) => {
        if (c > modeCount) {
          modeCount = c;
          modeValue = v;
        }
      });
      if (modeCount >= 3)
        members.forEach((i) => {
          if (ART_FORMS[i].vector[ax] === modeValue) eff[i][ax] = mean[ax];
        });
    }
  }
  return eff;
})();

// Jaccard-style distance between two vectors over the given axes: 1 - (sum of minimums / sum of maximums). 0 means
// identical.
function jaccardDist(a, b, axes) {
  let mn = 0,
    mx = 0;
  for (const k of axes) {
    const x = a[k],
      y = b[k];
    if (x < y) {
      mn += x;
      mx += y;
    } else {
      mn += y;
      mx += x;
    }
  }
  return mx === 0 ? 0 : 1 - mn / mx;
}
// Root-mean-square difference between two vectors over the given axes.
function rmsDist(a, b, axes) {
  let s = 0;
  for (const k of axes) {
    const d = a[k] - b[k];
    s += d * d;
  }
  return Math.sqrt(s / axes.length);
}
// Mean absolute difference between two vectors over the given axes.
function l1Dist(a, b, axes) {
  let s = 0;
  for (const k of axes) s += Math.abs(a[k] - b[k]);
  return s / axes.length;
}

// c1-c5 are continuous magnitudes ("how far this practice leans on each sense"), not
// membership in a set, and jaccard is a set measure. On sparse magnitudes it fails in
// a specific and backwards way: it keys entirely on the ratio sum(min)/sum(max), so
// two forms that are BOTH barely sensory are reported as far apart as possible if they
// are bare on different axes. Measured: Fiction Writing sits at [0.0156, 0, 0.0061, 0, 0]
// and Poetry at [0.0156, 0.3, 0, 0, 0] -- both almost wholly non-sensory, both writing --
// and jaccard scored that 0.95, near its maximum, contributing 0.152 of their 0.199
// total distance. Two forms doing the same thing were pushed apart by the one axis
// neither of them uses. Across all 42486 pairs the term had median 0.595 and was zero
// for 0.1% of pairs, so it was behaving as a near-constant offset rather than evidence.
//
// l1 is the mean absolute difference, which is the honest question to ask of a
// magnitude ("how different are these levels, on average") and is what the technique
// and context groups already use for the same reason. Scored against a benchmark of
// declared near pairs and declared far pairs, it improves every measure at once:
// separation 4.35x -> 4.83x, forms whose nearest neighbour shares their category
// 91% -> 93%, and within-category distance separating further from between-category.
function computePairDistance(i, j) {
  const a = EFF[i],
    b = EFF[j],
    G = AXIS_GROUPS,
    W = GROUP_WEIGHTS;
  return (
    W.domain * (0.5 * jaccardDist(a, b, G.domain) + 0.5 * rmsDist(a, b, G.domain)) +
    W.sensory * l1Dist(a, b, G.sensory) +
    W.technique * l1Dist(a, b, G.technique) +
    W.material * rmsDist(a, b, G.material) +
    W.context * l1Dist(a, b, G.context) +
    W.category * (ART_FORMS[i].category === ART_FORMS[j].category ? 0 : 1)
  );
}

// DIST: raw symmetric matrix. REL: hub-corrected matrix for Related lists.
const DIST = ART_FORMS.map(() => new Float64Array(N));
for (let i = 0; i < N; i++)
  for (let j = i + 1; j < N; j++) {
    const d = computePairDistance(i, j);
    DIST[i][j] = d;
    DIST[j][i] = d;
  }

const LOCAL_SCALE = new Float64Array(N);
for (let i = 0; i < N; i++) {
  const row = [];
  for (let j = 0; j < N; j++) if (j !== i) row.push(DIST[i][j]);
  row.sort((x, y) => x - y);
  let s = 0;
  for (let q = 0; q < HUB_NEIGHBOURS; q++) s += row[q];
  LOCAL_SCALE[i] = s / HUB_NEIGHBOURS;
}
const REL = ART_FORMS.map(() => new Float64Array(N));
for (let i = 0; i < N; i++)
  for (let j = 0; j < N; j++) {
    if (i !== j) REL[i][j] = DIST[i][j] / Math.pow(LOCAL_SCALE[i] * LOCAL_SCALE[j], HUB_STRENGTH / 2);
  }

// ---------------------------------------------------------------------------
// NOVELTY: "how new would this be to me, given what I already know?"
//
// Each practice you rate contributes familiarity to every other art form:
//     familiarity = (rating / 10) ^ masteryExponent * 2 ^ -(d / s)^3
// d is the distance between the two art forms and s is that rated practice's own "reach".
//   - The kernel is steep, so only genuinely close practices count, and it never hits a hard cap:
//     farther art forms keep their order (the old score stopped at 100 and tied).
//   - The rating level scales the effect, so a 10 means much more than a 1 -- but the scaling is
//     NOT linear (masteryExponent < 1, see calibration note below): most people entering ratings
//     will use the low end of the slider far more than the high end, and a flat rating/10 made
//     that low end nearly inert (see CALIBRATION NOTE).
//   - s is the distance to the practice's 10th-nearest neighbour, blended mostly toward that
//     practice's OWN local density rather than the map-wide typical value (see CALIBRATION NOTE).
//     It depends only on the RATED practice, so isolated practices still read as new.
//   - Evidence combines: the strongest link counts fully and each further one at 40%, so knowing
//     five related skills counts for more than knowing one, without weak links piling up.
//   - "How far your ratings reach" (Filters) scales s.
// novelty = 100 * (1 - familiarity). Tiers: Familiar 40 or below, In between up to 70, New ground
// above that, plus the newest third of what is left, so the New ground list never runs dry.
//
// ---------------------------------------------------------------------------
// CALIBRATION NOTE (rating semantics & score semantics, and the two tuning fixes below)
// ---------------------------------------------------------------------------
// DATASET GROWTH (230 -> 242 -> 274 -> 306 art forms). The measurements below were taken on the
// earlier, smaller sets. Re-checked at 274 after the dance, sport-art, theater and ritual-carving
// additions: fairness across categories still holds (craft vs other Familiar ratio 1.1, every
// practice still recognizes at least one neighbour), and 234 of the 240 older practices are
// unchanged by 10+ points when rated alone. The exception is by design of the local-reach rule:
// Dance and Choreography now sit in a much denser neighbourhood, so their own reach is smaller
// and they vouch for fewer distant forms than before (e.g. Dance rated 7 -> Choreography 29
// became 57). No single global setting fixed that without hurting the craft fairness above, so it
// is left as is.
//
// VINTAGE: the catalog has since grown to 306 forms, so these figures are from the 274-form
// catalog and have NOT been re-measured at 306. One check has been re-run since: every form
// still has a finite distance to at least one other (0 stranded of 306), so nothing is an
// island. The fairness ratios are worth re-measuring with the same method before being relied
// on; do not compare them against a differently-computed ratio, the thresholds interact.
//
// What a RATING means, and who actually enters it:
//   1  = "I've tried this once or twice, or did it as a kid" -- weak but real signal, not noise.
//   3  = casual/occasional dabbling -- no real proficiency, some vocabulary and muscle memory.
//   5  = a working hobbyist -- does this somewhat regularly, comfortable with the basics.
//   7  = quite good at this -- serious hobbyist/semi-pro, meaningful transferable skill.
//   10 = professional-level mastery -- this is one of the practices that defines you.
// In practice, most people rate most things they enter at all in the 1-5 range: a 10 is a claim
// almost nobody outside working professionals should honestly make, while a 1 ("I tried pottery
// once at a friend's studio") is extremely common. A calibration that only behaves sensibly near
// 10 is therefore mis-tuned for the population that will actually use it.
//
// What a SCORE means: it's "how much of this would you already recognize", not raw distance.
//   1-10   = essentially the same skillset wearing a different name (e.g. Painting <-> Drawing).
//   11-40  = clearly adjacent -- most of the technique carries over ("Familiar" tier).
//   41-70  = some real overlap, but a genuine new skill to build ("In between" tier).
//   71-100 = shares little to nothing with what you know ("New ground" tier); 100 specifically
//            means "no meaningful evidence links this to anything you rated", not "impossible".
//
// The remainder of this block is a record of decisions taken at particular catalog sizes (230,
// then 242, then 274). The reasoning still holds and the constants still reflect it, but the
// counts quoted inside are from those catalogs, not from the current 306 - read them as "this was
// true when measured". To re-measure, use the method noted in the VINTAGE paragraph above rather
// than recomputing a differently-defined ratio; the thresholds interact and the numbers are not
// comparable across definitions.
//
// Two fixes made after auditing the engine against ~52,000 single-rating pairs and 43 realistic
// multi-rating profiles (common hobbyists, polymaths, niche combinations, adversarial edge cases):
//
// 1) localBlend 0.5 -> 0.9. At 0.5, a rated practice's "reach" (s) was still heavily pulled toward
//    the map-wide typical density, so the ~57 Craft & Sculpture practices -- which sit in the single
//    densest, most self-similar part of the map -- kept an outsized reach: rating one craft at 10
//    could mark 20-27 other art forms "Familiar" (out of 230), 3-4x the typical practice, while four
//    genuinely isolated practices (Perfumery, Social Practice Art, Japanese Tea Ceremony, Yarn
//    Bombing) marked literally nothing "Familiar" even at full mastery. Weighting each practice's
//    OWN local density much more heavily corrects this: the craft/other-category "Familiar" ratio
//    dropped from 2.82x to ~1.2x, every practice now recognizes at least one close neighbour, and
//    -- important -- the well-calibrated pairs (Painting<->Drawing, Knitting & Crochet<->Macrame,
//    Candle Making<->Soap Making) are untouched, still scoring 1. This only rebalances fairness
//    ACROSS practices; it doesn't change how novel the map feels overall (mean score is within 0.2
//    points of the old value).
//
// 2) A new masteryExponent, 0.75, applied as (rating/10)^masteryExponent instead of a flat
//    rating/10. Under the flat version, ratings of 2-3 (the realistic common case per the note
//    above) were nearly inert: a simulated "Dabbler" persona who rated twelve different hobbies at
//    2-3 barely dented the map (0 Familiar matches, 10 In-between, out of 229), while a "Wide-Shallow"
//    persona who rated eleven hobbies at a moderate 5 unlocked half the map (119 In-between) --
//    an ~12x jump in responsiveness for a slider move most users would read as "still a beginner"
//    to "comfortable hobbyist". An exponent below 1 keeps a 10 meaning exactly what it always did
//    (10^exponent = 10 regardless of exponent) while giving low ratings a real, proportionate
//    weight: that same Dabbler/Wide-Shallow gap is now ~2.3x, in line with the ~2x difference in
//    their actual rating levels, instead of ~12x. High-mastery profiles (8-10) are barely affected
//    (well under a 1-point mean-score shift) because the curve only bends noticeably below ~m=6.
