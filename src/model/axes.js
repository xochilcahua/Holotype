// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

/* THE AXES. Names the 35 axes, groups them into the six the distance model weighs,
and sets those weights. Also the index the whole app looks forms up by. Pure
declarations -- nothing here reads another module.
Needs ART_FORMS. Gives AXES, AXIS_GROUPS, GROUP_WEIGHTS, BY_ID, INDEX, N.
   See docs/architecture.md. */

// ---------------------------------------------------------------------------
// Holotype engine: distance, related lists, novelty scoring, search, descriptions.
//
// DISTANCE MODEL (symmetric: distance(A,B) === distance(B,A))
// The 35 axes fall into groups, each scored on its own scale and then blended:
//   domain    p1-p7            what field the practice serves     (co-presence, Jaccard + RMS)
//   sensory   c1-c5            which senses it engages            (co-presence, Jaccard)
//   technique a1-a5, b, d      how it is made and shared          (mean absolute difference)
//   material  a7, a8           words vs. tone, organic vs. inert  (RMS)
//   context   a9-a13, e1, e2   tradition, function, economy       (mean absolute difference)
//   category                   small bonus for sharing a category
// Co-presence matters for domain/sensory: two practices that are BOTH strongly musical are
// related; two practices that both lack a sense are not related for that reason.
//
// CATEGORY DEFAULTS ARE TREATED AS UNKNOWN. For the large majority of art forms the context axes hold
// their category's default value, so they say "same category", not "similar practice".
// Any context value that equals its category default (categories of 3+ items, default shared
// by 3+ items) is replaced by the global mean, while genuine per-item values still count.
// Axis a6 is left out: it duplicates a13 and sits at its default for most items.
//
// TWO DISTANCES, TWO JOBS
//   DIST  raw distance  -> novelty scoring ("how far is this from what I know?"), see NOVELTY below
//   REL   hub-corrected -> Related lists ("what resembles this?")
// REL divides each pair by the local density of both items (mean distance to their 8 nearest
// neighbours, strength 0.75). Without it, generic mid-range practices (Weaving, Papercraft,
// Jewelry...) turn up in a large share of everyone's Related list. It is NOT used for novelty,
// because it would make isolated, unusual practices look closer to everything.
// ---------------------------------------------------------------------------

// prettier-ignore
const AXES = [
  "a1", "a2", "a3", "a4", "a5", "a6", "a7", "a8", "a9", "a10", "a11", "a12", "a13", "b1", "b2", "b3", "b4", "c1",
  "c2", "c3", "c4", "c5", "d1", "d2", "d3", "d4", "e1", "e2", "p1", "p2", "p3", "p4", "p5", "p6", "p7",
];

const BY_ID = {};
const INDEX = {};
ART_FORMS.forEach((a, i) => {
  BY_ID[a.id] = a;
  INDEX[a.id] = i;
});
const N = ART_FORMS.length;

// meta.self was stored as "yes"/"no" (and once as a boolean); "no" is truthy in JS, so always
// go through this helper instead of testing a.meta.self directly.
function isSelfTaught(a) {
  return a.meta.self === true || a.meta.self === "yes";
}

const AXIS_GROUPS = {
  domain: ["p1", "p2", "p3", "p4", "p5", "p6", "p7"],
  sensory: ["c1", "c2", "c3", "c4", "c5"],
  technique: ["a1", "a2", "a3", "a4", "a5", "b1", "b2", "b3", "b4", "d1", "d2", "d3", "d4"],
  material: ["a7", "a8"],
  context: ["a9", "a10", "a11", "a12", "a13", "e1", "e2"],
};
const GROUP_WEIGHTS = { domain: 0.24, sensory: 0.16, technique: 0.3, material: 0.12, context: 0.13, category: 0.05 };

// HOW MUCH A RATING COUNTS TOWARD "HOW YOU WORK".
// A rating is experience (1 = tried once, 10 = professional), and a reading of how someone works should
// follow what they actually do, not what they sampled. With a linear weight, thirteen forms tried once
// outvote one form rated 9, so a professional photographer who has dabbled in 20 other things was read as
// a "Surface Spreader" ("a dozen half-started projects") on the strength of the dabbles. Squaring the
// rating lets one deep practice outweigh a pile of one-off tries (9 -> 81 against 1 -> 1) without letting
// a single form decide everything, as a cube would. Used by the person vector, the work-style means,
// the Breadth share, the lean share and the reference population in person-space.js, so the person and
// the reference they are compared with always use the same weighting. The category bars on the
// Herbarium are a description of where the ratings sit and stay linear.
const RATING_POWER = 2;
// How much a rating counts: a rating r is weighted r^RATING_POWER, so a 9 pulls a profile far harder than a 2.
function ratingWeight(r) {
  return Math.pow(r, RATING_POWER);
}
