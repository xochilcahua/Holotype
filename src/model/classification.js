// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

/* WHAT HOLOTYPE SAYS ABOUT A PERSON. Four sign tests -- breadth, approach to chance,
collaboration, and how fixed the results are -- combined into a genus, plus the
regime and the field leans. The words it picks from live in model/genus-copy.js, which
loads first. Needs the person-space moments and personalStats().
   See docs/architecture.md. */

// ---------------------------------------------------------------------------
// CLASSIFICATION v3: a horoscope-style sorting layer, computed only here (export
// time / Herbarium tab), from the same personalVector() and AXIS_MEAN/AXIS_SD used everywhere
// else in the app. It is a different reading of the tensor that already exists and never
// feeds back into novelty scoring or distances.
//
// Core: a 16-way Genus (one hand-written paragraph each), from four axes chosen because
// they vary meaningfully *within* a domain rather than mostly restating *which* domain a
// person leans toward:
//   Breadth      - concentration of rated weight across the categories actually touched
//                  (Herfindahl-style index over personalStats().catBreakdown). Low = a
//                  focused practice, high = a wide one.
//   Process      - a1 (0 = improvised, 1 = planned).
//   Sociability  - d1 (0 = solo, 1 = collaborative).
//   Form         - a4, read in the opposite direction from how it is stored: in the data a
//                  HIGH a4 means fixed/literal, so a person whose ratings sit BELOW the
//                  corpus mean on a4 is the "open to interpretation" type (bit = 1).
// Approach to chance - b3 (controlled/repeatable <-> chance-driven/emergent), three levels,
// shown as a plain-language phrase.
// Domain lean (p1-p7) - up to two fields the ratings clearly favor. Purely descriptive: which
// domain a person rates highest mostly reflects exposure rather than disposition, so it never
// changes which genus someone gets.
//
// The genus names are real plant genera (plus one fungus and one slime mold) chosen to echo
// the combination. They are the identity of the type; the plain-language lines under the name
// carry everything else.

// Domain axis -> the internal lean name. plant.js keys its per-lean slider offsets on
// these names, so they stay stable even though the page shows plain words (TRIBE_PLAIN).
const DOMAIN_TRIBE = { p1: "Reed", p2: "Vine", p3: "Petal", p4: "Tendril", p5: "Nectar", p6: "Trellis", p7: "Root" };

// Breadth thresholds. Chosen by testing against plausible people, not derived from a formula.
//   topShare  - if more than this share of your rated weight sits in one field, you are focused.
//               0.55 sits just above the 50/50 split, so "a bit of two fields" reads wide and
//               "nearly all of one field" reads focused.
//   minField  - your deepest field has to hold at least this much. This is what stops "spread
//               thin" from counting as "spread wide": six things tried once each have perfectly
//               even shares across four fields and total six points, and that is not range.
//               It is deliberately relative (how deep is your deepest field?) rather than
//               absolute (how much have you rated?) so that a person who rates only three things
//               but rates them well is not penalised for being brief.
//   minCats   - you need at least this many fields before spreading across them means anything.
//   minKept   - how many things in your list you have gone back to more than once (rated 3+).
//              This used to be minField, a sum of rating POINTS in the largest field, and the
//              unit was wrong: four things tried once each sum to exactly 4 and cleared a bar
//              whose entire job was to stop "spread thin" being called "spread wide". Counting
//              the things fixes that, and 3+ is the line the app's own rating scale draws
//              ("casual dabbling" against "tried once or twice, or as a kid").
//
//              Chosen by measurement, not taste, against the 158 hand-written profiles, because
//              the 400 drawn people cannot calibrate it - population.py is unrealistically narrow
//              (median largest-field share 1.00), so only 5 of them ever reach the width test.
//              Against the cases that matter, "2 forms at 3+" was the only threshold that
//              accepted all eight genuinely-spread people while rejecting every tried-it-once
//              case. "2 forms at 4+" rejected the serial starter and the person who rates twenty
//              forms at 3, both of whom really are spread; "1 form at 4+" let the all-ones
//              profiles through.
const BREADTH = { topShare: 0.55, minKept: 2, minCats: 3 };

// Sociability has three items in the catalog that cannot answer the question, because each one
// stands in front of a set of specific forms that disagree with each other:
//
//   Playing an Instrument - one item for guitar, piano, drums, bass, ukulele, cello, sax. A
//                            bedroom guitarist and an orchestra member give the same number.
//   Singing               - one item for karaoke, a solo singer, a choir member and a band member.
//   Dance                 - one item in front of 40+ specific dance forms, and it is coded
//                            SOLO (0.12) while its own children run 0.40 to 0.95.
//
// That last one is why the axis used to under-read social dancers: someone who goes out dancing
// rates the umbrella plus partner-dance forms, and the umbrella pulled the average down.
//
// These are held back when deciding the sociability bit, so a specific form decides it. They are
// still counted everywhere else. If someone has rated nothing else, they are used anyway - an
// axis with no evidence at all is worse than one built on a weak item.
// Identifiable from the catalog alone, with no reference to any test result. Songwriting, Music
// Composition and Music Production are NOT umbrellas; they are distinct activities, and they stay.
const SOCIAL_UMBRELLAS = new Set(["Playing an Instrument", "Singing", "Dance"]);

// The same problem exists on the Process axis (a1: improvised <-> planned) for the two music umbrellas,
// and it is worse there than anywhere. "Playing an Instrument" and "Singing" are each coded a1 = 0.05,
// i.e. almost entirely improvised, but each stands in front of the sheet-music pianist and the
// play-by-ear guitarist alike. They are also two of the most commonly rated items in the catalogue
// (66 and 95), so a classical pianist who rates Playing an Instrument 9 was read as improvised at
// z = -2.2 on the strength of an item that cannot tell her from a busker. Measured before the change:
// Playing an Instrument 9 + Composition 2 + Conducting 2 + Singing 3 -> Process z -2.18 (improvised).
// Dance is left out of this set: its a1 is 0.55, so holding it back would change nothing.
// Same rule as sociability: held back when anything more specific was rated, used when it is all
// there is (and then the reading goes to the dead-band, where the page admits it is a toss-up).
const PROCESS_UMBRELLAS = new Set(["Playing an Instrument", "Singing"]);

// Re-entrancy guard. The fragility test below re-runs this function on a modified copy of the
// ratings, and that nested call must not start its own fragility test.
let classifying = false;

// Reads the current ratings and returns the whole reading: genus, regime, field leans, confidence and the numbers
// behind them (null when nothing is rated).
function computeClassification() {
  const pv = personalVector();
  if (!pv) return null;
  const ratedCount = ART_FORMS.filter((a) => state.mastery[a.id] > 0).length;
  const stats = personalStats();
  // Nothing rated 3 or above means every answer is a first try. That is not enough to describe how
  // someone works, so it is treated as early however many forms were rated (six ones used to get
  // a settled reading with "strongly" bars).
  const nothingKept = !ART_FORMS.some((a) => state.mastery[a.id] >= 3);
  const early = ratedCount < 4 || nothingKept;

  // Breadth: how much of this person's practice sits in any ONE field.
  //
  // This used to be a Herfindahl index over the categories touched, cut at 0.40. Two things
  // were wrong with that, both found by testing against plausible people rather than edge cases:
  //
  //   1. With only 3 categories the LOWEST possible HHI is 1/3 = 0.333. A perfectly even
  //      three-field person could therefore only just scrape under a 0.40 line, so "wide" was
  //      in practice a four-category test. A singer who also draws, paints, dances and
  //      photographs (50/42/8 across three fields, HHI 0.431) was called FOCUSED and handed
  //      Cuscuta - "you stay with a narrow set rather than roaming". The opposite of the truth.
  //   2. HHI only knows about *share*, never about *amount*. Six things tried once each and
  //      enjoyed not at all came out as evenly spread as a genuine polymath, so they were
  //      called wide too - the other direction of the same mistake.
  //
  // Largest-field share is the thing the word "wide" actually means: is your practice
  // concentrated in one corner, or spread across several? It is far steadier than HHI as well,
  // because adding one form to one field moves it a little instead of moving the sum of
  // squares a lot. The two extra conditions stop "spread thin" from counting as "spread wide":
  // you need some actual experience, and you need more than two fields to have spread across.
  // hhi is no longer used to decide anything. It is computed and returned because the test
  // tooling reports it, and because it is the obvious thing to reach for when checking whether
  // a breadth change moved a population - it is the number the old rule used, so it is the
  // cheapest way to confirm a change had the intended effect. Everything below decides on
  // topShare instead.
  const hhi = stats.catBreakdown.reduce((s, c) => s + c.pct * c.pct, 0);
  // Breadth is judged on what the person KEPT (rated 3 or above, the scale's own line between "tried it once
  // or twice" and "casual dabbling"), not on everything they ever touched. Counting dabbles made two kinds
  // of person read wrongly. A professional photographer who had tried twenty other things once was "wide"
  // ("a dozen half-started projects") because the twenty outnumbered the one; and a squared weight, the
  // first fix tried, overcorrected and called a hip-hop participant who raps, DJs, breaks and writes
  // graffiti "focused". Asking how concentrated the kept forms are, by rating, fixes both: the dabbles
  // drop out, and four serious fields are still four fields.
  const keptByCat = {};
  ART_FORMS.forEach((a) => {
    const r = state.mastery[a.id];
    if (r >= 3) keptByCat[a.category] = (keptByCat[a.category] || 0) + r;
  });
  const keptTotal = Object.values(keptByCat).reduce((x, y) => x + y, 0);
  const keptCategories = Object.keys(keptByCat).length;
  // With nothing kept yet there is no practice to measure, so fall back to everything rated (display only:
  // deepEnough below is false in that case, so Breadth is never claimed from it).
  const topShare = keptTotal
    ? Math.max(...Object.values(keptByCat)) / keptTotal
    : stats.catBreakdown.reduce((m, c) => Math.max(m, c.pct), 0);
  const topField = stats.catBreakdown.reduce((m, c) => Math.max(m, c.weight), 0);
  const totalWeight = stats.catBreakdown.reduce((s, c) => s + c.weight, 0);
  // One decision, computed once, so the tribe and the axis bar can never disagree. Earlier
  // versions computed "wide" in one place and drew the bar from the share in another, and they
  // came apart in three separate ways: spread-but-thin (R04), and not-enough-fields (F31, H11).
  const looksSpread = topShare < BREADTH.topShare;
  // Fields count only if something was KEPT in them (rated 3+). A dabble in a third field used to let a two-field person (music 55%, drawing 45%) read as wide.
  const enoughFields = keptCategories >= BREADTH.minCats;
  // How many things the person has gone back to, counted as FORMS rather than points, so that
  // six things tried once each can no longer clear the bar by summing to six.
  const topKept = ART_FORMS.filter((a) => state.mastery[a.id] >= 3).length;
  const deepEnough = topKept >= BREADTH.minKept;
  const breadth = looksSpread && enoughFields && deepEnough ? 1 : 0; // 1 = wide, 0 = focused
  // The shares look spread but breadth is not claimed - either there are too few fields to have
  // spread across, or nothing behind them goes past a dabble. Not "focused" either: too early to
  // call. The page parks the marker on the midpoint and says which reason applies.
  const breadthUnproven = looksSpread && !breadth;
  const breadthUnprovenWhy = breadth ? null : !deepEnough ? "depth" : !enoughFields ? "fields" : null;

  // The four genus bits are hard sign tests on a continuous score, which makes them the twitchiest
  // part of the app: a person can sit a hair from the line and be handed a different genus because one
  // rating moved. GENUS_BAND is a dead-band around each line.
  //   outside it -> the z-score sign decides
  //   inside it  -> the reading is genuinely too close to call, so instead of a coin-flip we re-ask the
  //                 same question with a median: the median of the rated items' own axis values against
  //                 the person-space median for that axis. A median ignores how much each rating counts
  //                 and shrugs off one outlier, so it holds its answer when the weighted mean swings.
  // Either way the person keeps a tribe; closeAxes says which readings were too close to call, so the
  // page can admit it. This is the same idea as the +/-0.35 window the approach-to-chance axis uses.
  //
  // Two things here are measured rather than assumed, both of them fixes for profiles that all came
  // out the same:
  //
  // 1. The z-scores are divided by PEOPLE_SD, not AXIS_SD. A person is an average over the forms they
  //    rated, so their spread is about a fifth of the spread across individual forms; dividing by the
  //    form-scale SD put nearly everyone inside the dead-band. See PEOPLE_SD for the long version.
  //    Axes now land outside the band 82% of the time instead of 20%, so the tribe is decided by the
  //    person's own ratings rather than by the tie-break.
  //
  // 2. The tie-break median now ignores drags. It used to take the median over EVERY rated item, which
  //    made a 1 count exactly as much as a 9, and since most people's ratings are 1s and 2s the
  //    median was largely a median of things they had already rejected. When there are at least four
  //    strong ratings (6+) the median is taken over those instead, which is the set of forms the
  //    person is actually claiming; below that threshold there is not enough to be selective, so it
  //    falls back to everything rather than pretending four items were a pattern.
  const GENUS_BAND = 0.22;
  const REF = peopleRefFor(ART_FORMS.filter((a) => state.mastery[a.id] > 0).length); // reference people who rated about as many forms
  const closeAxes = [];
  const ratedForms = ART_FORMS.filter((a) => state.mastery[a.id] > 0);
  const strongForms = ratedForms.filter((a) => state.mastery[a.id] >= 6);
  const medPool = strongForms.length >= 4 ? strongForms : ratedForms;
  // d1 is decided from the specific forms only; the umbrella items are held back (see
  // SOCIAL_UMBRELLAS). If the person has rated nothing but umbrella items they are used anyway,
  // because no evidence at all is worse than weak evidence.
  const socForms = ratedForms.filter((a) => !SOCIAL_UMBRELLAS.has(a.name));
  const socUsed = socForms.length ? socForms : ratedForms;
  const socUmbrellaOnly = socForms.length === 0 && ratedForms.length > 0;
  // MEASURED, NOT ASSUMED: restricting this mean to ratings of 3+ (the rule the tie-break
  // median uses) was tried and reverted. It was supposed to help a reader with 103 ratings
  // averaging 2.90, but it moved them the wrong way: zSoc +0.22 -> +0.33, flipping the reading
  // from solo to COLLABORATIVE.
  //
  // The reason is that drags are not noise here, they are the answer. Her list of things
  // rated 1-2 is the collaborative half of the catalogue -- Acting 1, Directing Film & TV 1,
  // Curating 1, Audio Drama 2 -- and what she KEPT is 3D Modeling, Music Production, Sound
  // Design, Video Editing, Color Grading, studio crafts done alone. Dropping the discarded
  // items therefore removes the only evidence she does not work with other people, and the
  // surviving average looks MORE collaborative, not less. A rating of 1 is a real claim
  // ("I tried this and it is not me"), so drags stay in, already down-weighted to 1 against
  // the 3-8 that keeps carry.
  const socWeight = socUsed.reduce((s, a) => s + ratingWeight(state.mastery[a.id]), 0);
  const socMean = socWeight
    ? socUsed.reduce((s, a) => s + ratingWeight(state.mastery[a.id]) * a.vector.d1, 0) / socWeight
    : pv.d1;
  const bitOf = (z, ax, flip, medVals) => {
    if (Math.abs(z) >= GENUS_BAND) return z >= 0 ? 1 : 0;
    closeAxes.push(ax);
    const med = medianOf(medVals || medPool.map((a) => a.vector[ax]));
    const d = flip ? REF.MEDIAN[ax] - med : med - REF.MEDIAN[ax];
    return d >= 0 ? 1 : 0;
  };

  const procForms = ratedForms.filter((a) => !PROCESS_UMBRELLAS.has(a.name));
  const procUsed = procForms.length ? procForms : ratedForms;
  const procUmbrellaOnly = procForms.length === 0 && ratedForms.length > 0;
  const procWeight = procUsed.reduce((s, a) => s + ratingWeight(state.mastery[a.id]), 0);
  const procMean = procWeight
    ? procUsed.reduce((s, a) => s + ratingWeight(state.mastery[a.id]) * a.vector.a1, 0) / procWeight
    : pv.a1;
  const zProcessRaw = (procMean - REF.MEAN.a1) / REF.SD.a1;
  const zProcess = procUmbrellaOnly ? 0 : zProcessRaw;
  const process = bitOf(
    zProcess,
    "a1",
    false,
    procUmbrellaOnly
      ? medPool.map((a) => a.vector.a1)
      : medPool.filter((a) => procUsed.includes(a)).map((a) => a.vector.a1)
  ); // 1 = planned, 0 = improvised
  // When the only thing rated is an umbrella item, there is no sociability evidence at all, so
  // the reading goes to the dead-band and the page admits it rather than asserting a position
  // from an item that cannot take one.
  const zSocRaw = (socMean - REF.MEAN.d1) / REF.SD.d1;
  const zSoc = socUmbrellaOnly ? 0 : zSocRaw;
  const sociability = bitOf(
    zSoc,
    "d1",
    false,
    medPool.filter((a) => socUsed.includes(a)).map((a) => a.vector.d1)
  ); // 1 = collaborative, 0 = solo
  const zForm = (REF.MEAN.a4 - pv.a4) / REF.SD.a4; // a4 is stored HIGH = literal, so flip it: positive z = open to interpretation
  const form = bitOf(zForm, "a4", true); // 1 = open to interpretation, 0 = fixed/literal

  const genusId = `${breadth}${process}${sociability}${form}`;
  const genus = GENUS_TABLE[genusId];

  const zRegime = (pv.b3 - REF.MEAN.b3) / REF.SD.b3;
  const regimeId = zRegime >= 0.35 ? "emergent" : zRegime <= -0.35 ? "ordered" : "adaptive";
  const regime = REGIME_LEVELS[regimeId];

  // MODIFIERS: 0 to 3, driven by how much evidence there is rather than always filling every slot.
  //   under 4 ratings       -> 0  (genus only: not enough behavior to claim an approach or a lean)
  //   4+ ratings            -> the approach to chance (always one), plus
  //     one domain lean     when a single domain clearly leads,
  //     two domain leans    when two are level with each other and both clearly ahead of the rest,
  //     none                when nothing stands out (interest is spread evenly).
  // Also person-normalised, for the same reason: a lean is a claim about a person, so "clearly leads"
  // has to mean clearly against other people. On the form scale the whole spread fitted inside the
  // 0.35 bar, and two of the four friends got no lean at all despite rating 53 and 103 things.
  // A domain lean says "of the things you have KEPT, an unusual share of them is this field".
  // It is deliberately NOT a z-score, and the reason is worth writing down because the z-score
  // version looked reasonable and was badly broken.
  //
  // The old rule compared (pv[ax] - PEOPLE_MEAN[ax]) / PEOPLE_SD[ax] across all seven domain axes
  // and took the largest. That assumes the seven z-scores are on a common scale. They are not, and
  // not by a small factor: PEOPLE_SD for p5 (food and scent) is 0.0247 while p1 (sound) is 0.1612,
  // a 6.5x difference, because p5 is a near-binary flag that barely moves between the clustered
  // people the moments were sampled from. Dividing by the small number inflates p5's z until it
  // wins every comparison. Measured: a person who rated all 306 forms at exactly 5 - no preference
  // of any kind - came out as a "food and scent" person, identically at rating 1, 3, 5, 7 and 10,
  // and was told they were drawn to what can be cooked, worn or consumed.
  //
  // So the lean is now a LIFT: the share of the person's rating weight sitting on forms that are
  // strongly in a field, divided by the share a catalog-wide rater would put there. The baseline is
  // per axis and comes from the catalog itself, so the two dense axes (visual 0.389, language
  // 0.173) are not penalised against the sparse one (food 0.046).
  //
  //   lift = 1.000 means exactly what the catalog average would give. It is a ratio against a
  //   within-person reference, not a z against other people, so it needs no PEOPLE_SD and does not
  //   inherit that axis's noise. A flat rater is 1.000 on all seven by construction.
  //
  // Two further conditions, both measured rather than guessed:
  //
  //   KEEP  Only ratings of 3+ count as evidence. personalVector weights every form by its rating,
  //         so a form rated 1 still contributes its full axis value at weight 1 - the same value a
  //         5 contributes, just less of it. Without this the lean was largely made of things the
  //         reader had already rejected: dropping every 1-2 removed one reader's lean entirely and
  //         removed one of another's two.
  //   nHi   At least 2 forms at 3+ actually on the axis. A lift of 3.0 built on one form is an
  //         accident, not a leaning, and people with 4-8 ratings were getting a lean 92% of the time.
  //
  // Measured over 149 drawn people with 4+ ratings: the old rule agreed with the reader's own
  // ratings 50% of the time, this one 80% - at the same fire rate (91% -> 50% of people, matching
  // the previous 51%) and with the flat-rater case fixed by construction. It is also more
  // discriminating, not less: a reader with Music Production 8, Sound Design 8 and Music Composition 7
  // now reads as sound and language, which is what they actually rated.
  const DOMAIN_HIGH = 0.6; // a form counts as "in" a field at or above this
  const DOMAIN_BASELINE = {};
  AXIS_GROUPS.domain.forEach((ax) => {
    DOMAIN_BASELINE[ax] = Math.max(1e-6, ART_FORMS.filter((a) => a.vector[ax] >= DOMAIN_HIGH).length / N);
  });
  const keptForms = ratedForms.filter((a) => state.mastery[a.id] >= 3);
  const keptWeight = keptForms.reduce((s, a) => s + state.mastery[a.id], 0);
  const domainShare = (ax) => {
    const on = keptForms.filter((a) => a.vector[ax] >= DOMAIN_HIGH);
    return { on, share: keptWeight ? on.reduce((s, a) => s + state.mastery[a.id], 0) / keptWeight : 0 };
  };
  const domainZ = AXIS_GROUPS.domain
    .map((ax) => {
      const { on, share } = domainShare(ax);
      // z is kept in the return value for the test harness and the axis bar, and is now a lift.
      return {
        ax,
        z: +(share / DOMAIN_BASELINE[ax]).toFixed(4),
        nHi: on.length,
        share: +share.toFixed(4),
        baseline: +DOMAIN_BASELINE[ax].toFixed(4),
      };
    })
    .sort((a, b) => b.z - a.z);
  // The PERSONAL MEAN: this person's own average share across the seven fields, so a field can
  // be scored against the spread of their own practice instead of only against a generic rater.
  //
  // Ranked by the catalogue lift alone, the rule cannot see a real difference between two people
  // whose weight sits in different fields. Measured on four real saved sessions: one reader keeps
  // 59% of their rating weight on visual forms and 41% on language, another keeps 55% on language and
  // 33% on visual -- they are opposites -- and both were told the same thing, "Vine", because
  // the visual baseline is 0.389 of the catalogue against language's 0.173. A visual lean is
  // almost unreachable: it needs 54% of a person's kept weight just to reach a lift of 1.40.
  //
  // Ranking by the personal mean instead names the first Petal and the second Vine, which is right. But it
  // cannot be done on its own, because the lift is what corrects for FIELD SIZE and that matters:
  // language is easy to accumulate, so a third reader - Music Production 8, Sound Design 8, Music
  // Composition 7 - carries 26% language against 24% sound, and a two-point gap that is noise.
  // Ranked purely on their own mean they read as a language person; ranked on the lift they correctly
  // read as sound. That was a measured fix and it is not being undone here.
  //
  // So the lift stays the GATE -- a field has to be over-represented against a generic rater before
  // it is anyone's leaning at all -- and the personal mean only decides the ORDER among fields that
  // already passed, and only when one of them clearly dominates the person's own spread. Two fields
  // within the same 0.35 the two-lean rule already uses are a genuine pair, and there the lift's
  // field-size correction is the better judge.
  const ownMean = domainZ.reduce((s, d) => s + d.share, 0) / domainZ.length;
  domainZ.forEach((d) => {
    d.own = +(ownMean ? d.share / ownMean : 0).toFixed(4);
  });
  const DOMAIN_LEAN = 1.4,
    DOMAIN_MIN_FORMS = 2;
  let leanAxes = [];
  if (!early) {
    const ok = domainZ.filter((d) => d.z >= DOMAIN_LEAN && d.nHi >= DOMAIN_MIN_FORMS);
    const byOwn = ok.slice().sort((a, b) => b.own - a.own);
    const byLift = ok.slice().sort((a, b) => b.z - a.z);
    // Only override the lift when one field genuinely leads the person's own spread.
    const ranked = byOwn.length >= 2 && byOwn[0].own - byOwn[1].own >= 0.35 ? byOwn : byLift;
    // Two only when the two are genuinely level; the old code compared z-scores from axes with
    // different units, which is the same mistake in a smaller place. (V03: the gap is now absolute. When the own-share
    // ordering put the lower-lift field first the difference came out negative and always passed, so a second
    // lean was handed out to people whose two fields were not level at all: 2.25 against 1.46.)
    if (ranked.length >= 2 && Math.abs(ranked[0].z - ranked[1].z) < 0.35) leanAxes = [ranked[0].ax, ranked[1].ax];
    else if (ranked.length) leanAxes = [ranked[0].ax];
  }
  const leans = leanAxes.map((ax) => DOMAIN_TRIBE[ax]);

  // Is this identity actually settled, or is it one rating away from being a different genus?
  //
  // The four bits are sign tests on continuous scores, so a person sitting near a line can be
  // handed a different identity because one rating of 306 moved. Measured over a drawn population,
  // only 31% of people keep their genus when any single rating is dropped.
  //
  // A binary "this is fragile" warning was the obvious shape and it is the wrong one: 69% of
  // people turn out to be one drop away from a different genus, so a flag that fires for two
  // people in three stops meaning anything. The page is therefore given the COUNT, not a verdict,
  // and the copy scales to it. That is a fact about the reader's own list, it is more interesting
  // than a warning, and it does not cry wolf.
  //
  // The test is drop-one over the five highest-rated forms, which measured 0 misses and 100%
  // precision against an exhaustive drop-one across every rated form: when a reading is going to
  // move, one of the ratings carrying the most weight is what moves it. Cost is five extra
  // classifications, and `classifying` stops the nested calls recursing.
  const genusMargin = Math.min(Math.abs(zProcess), Math.abs(zSocRaw === 0 ? GENUS_BAND + 1 : zSoc), Math.abs(zForm));
  let genusFlips = 0,
    genusProbe = 0;
  if (!early && ratedCount >= 4 && !classifying) {
    const load = ratedForms
      .slice()
      .sort((a, b) => state.mastery[b.id] - state.mastery[a.id])
      .slice(0, 5);
    const saved = state.mastery;
    genusProbe = load.length;
    for (const drop of load) {
      const m2 = Object.assign({}, saved);
      delete m2[drop.id];
      state.mastery = m2;
      classifying = true;
      let alt = null;
      try {
        alt = computeClassification();
      } catch (e) {
        alt = null;
      } finally {
        classifying = false;
        state.mastery = saved;
      }
      if (alt && alt.genusId !== genusId) genusFlips++;
    }
    // `state.mastery` is restored inside the loop, not after it: a nested call that threw or
    // returned early must not leave a stale variant behind for the next iteration to inherit.
    state.mastery = saved;
  }
  const genusFragile = genusFlips > 0;
  // Does this person have enough kept practice for a sentence about VOLUME to be earned? The wide
  // genera say things like "making a lot, quickly, is the point" and "a dozen half-started
  // projects", and a rating list records what and how well, never how much someone made. A person
  // who has rated twenty things and kept none of them past a 3 is not a prolific person, and the
  // page should not tell them they are one. `keptEnough` is the gate the copy uses; it is not a
  // new bit, and it never changes the genus.
  const keptEnough = topKept >= 5;
  const keptAny = topKept >= 1;

  return {
    genusId,
    genus,
    regimeId,
    regime,
    leans,
    domainZ,
    early,
    genusFragile,
    genusFlips,
    genusProbe,
    genusMargin,
    keptEnough,
    keptAny,
    nothingKept,
    keptCategories,
    confidence: early ? "early" : "settled",
    earlyClustered: stats.categoriesTouched <= 1,
    ratedCount,
    hhi,
    topShare,
    topField,
    totalWeight,
    zProcess,
    zSoc,
    zForm,
    zRegime,
    socUmbrellaOnly,
    socUsedCount: socUsed.length,
    closeAxes,
    genusBand: GENUS_BAND,
    breadthRule: BREADTH,
    breadthUnproven,
    breadthUnprovenWhy,
    topKept,
    categoriesTouched: stats.categoriesTouched,
  };
}

// Builds the Glossary tab: each term with what it means here and what it means in biology.
function glossaryHTML() {
  const terms = GLOSSARY.map(
    ([t, b, bio]) =>
      i18nHTML`<div class="gl-item"><dt>${esc(tx(t))}</dt><dd><span class="gl-k">In Holotype</span>${esc(tx(b))}</dd><dd><span class="gl-k">In biology</span>${esc(tx(bio))}</dd></div>`
  ).join("");
  const genera = Object.keys(GENUS_TABLE)
    .map((k) => {
      const n = GENUS_TABLE[k].name,
        x = GENUS_EXTRA[k] || {};
      return i18nHTML`<div class="gl-item"><dt><i>${esc(n)}</i></dt><dd><span class="gl-k">In Holotype</span>${esc(tx(x.tribe || ""))}</dd><dd><span class="gl-k">In biology</span>${esc(tx(GENUS_BIO[n] || ""))}</dd></div>`;
    })
    .join("");
  return i18nHTML`<h4 class="gl-head">Terms</h4><dl class="gl-grid">${terms}</dl><h4 class="gl-head">The 16 genera</h4><dl class="gl-grid">${genera}</dl>`;
}

// The person's own plant: genus picks the plant, regime / leans / confidence move its sliders, and
// the per-person seed (kept in state, renewed on reset) fixes its colors and its one tiny detail.
function personalPlantSVG(bc, dark) {
  try {
    return HolotypePlant.svg(
      {
        genus: bc.genus.name,
        regime: bc.early ? null : bc.regime.word,
        domains: bc.leans,
        confidence: bc.early ? "early" : "established",
        seed: state.plantSeed,
        inks: folkInks(personalHue(), 1), // the holotype's own three inks, in its order, so plant and holotype share colours
      },
      { dark: !!dark }
    );
  } catch (e) {
    console.warn("Holotype: plant could not be drawn", e);
    return "";
  }
}

// The framed plant plate (an SVG) for the screen or the PDF. `dark` picks the dark palette; the plant's paper
// colour is swapped for the page's own.
function plantBlock(cls, bc, dark) {
  let s = personalPlantSVG(bc, dark);
  s = s.replace(/aria-label="[^"]*"/, `aria-label="${esc(tx`Plant representing ${bc.genus.name}`)}"`);
  const paper = (s.match(/data-paper="(#[0-9A-Fa-f]{3,8})"/) || [])[1];
  if (paper) s = s.replace(new RegExp(paper, "gi"), dark ? "#23272C" : "#FDFBF6"); // plant's "paper" ink becomes the page's frame color
  return `<div class="${cls}-growth-plant">${s}</div>`;
}

// The caveat shown above the reading while it is provisional (few ratings, or nothing rated above a first try) or
// fragile (one different rating would flip it).
function growthEarlyNote(bc) {
  // How close this reading is to being a different one. Deliberately a COUNT and not a warning:
  // 69% of people are one rating away from a different genus, so a flag that fires for two people
  // in three would be noise. Stating the count is a fact about the reader's own list, and it
  // scales - one rating out of fifty is a different situation from three out of eight.
  const flipNote = () => {
    if (bc.early || !bc.genusProbe || !bc.genusFlips) return "";
    const one = bc.genusFlips === 1;
    if (bc.genusFlips === 1 && bc.genusProbe >= 5) {
      return tx` Worth knowing before you read the rest: one of the ${bc.genusProbe} ratings you gave most weight to would name a different plant if you took it back. ${bc.genus.name} is the better fit, not a settled fact.`;
    }
    return tx` Worth knowing before you read the rest: ${bc.genusFlips} of the ${bc.genusProbe} ratings you gave most weight to ${tx(one ? "would" : "would each")} name a different plant if you took ${tx(one ? "it" : "them")} back. ${bc.genus.name} is the better fit, not a settled fact.`;
  };
  const f = flipNote();
  if (!bc.early) return f;
  const one = bc.ratedCount === 1 ? "" : "s";
  // One or two ratings is a different situation from three. At that point the page is about to
  // tell someone something quite specific about their inner life - especially about whether they
  // need other people around - on the strength of a single answer. The tribe still gets named,
  // because a first guess is how a horoscope works, but the note has to admit the smallness of
  // the evidence without turning into a disclaimer.
  if (bc.nothingKept && bc.ratedCount >= 3) {
    return tx`Every rating so far is a first try, so ${bc.genus.name} is a starting guess drawn from what you have sampled, not from what you do. Rate something you have kept doing, at 3 or higher, and it will change.`;
  }
  if (bc.ratedCount <= 2) {
    return bc.earlyClustered
      ? tx`One rating so far. ${bc.genus.name} is the first name this flower gets, and it is drawn from that one answer more than from anything else. Rate a few things you have actually kept doing and it will change.`
      : tx`Only ${i18nCount(bc.ratedCount, "rating", "ratings")} so far. ${bc.genus.name} is a starting guess, not a verdict \u2014 it leans on what you have told us and not much else. Rate a few things you have actually kept doing and it will sharpen.`;
  }
  return bc.earlyClustered
    ? tx`Based on only ${i18nCount(bc.ratedCount, "rating", "ratings")} so far, all within one category. This is an early read, not a settled type, and the shape may open up as you rate things elsewhere.`
    : tx`Based on only ${i18nCount(bc.ratedCount, "rating", "ratings")} so far, already spread across a few categories. This is an early read, not a settled type, though the spread itself is a real signal.`;
}
