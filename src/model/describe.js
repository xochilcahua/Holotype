// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

/* ONE SENTENCE ABOUT A SINGLE PRACTICE. describeArtForm() finds the axis a form is
most unusual on, in standard deviations, and says it in words. Separate from
person-space.js because it answers the opposite question: how unusual is THIS
THING, not how unusual is THIS PERSON. Needs person-space.js. Gives
describeArtForm().
   See docs/architecture.md. */

function describeArtForm(a) {
  const vec = INDEX[a.id] !== undefined ? EFF[INDEX[a.id]] : a.vector; // category defaults don't count as traits
  const candidates = [];
  for (const ax of AXES) {
    const d = AXIS_DESCRIPTORS[ax];
    if (!d) continue; // unknown axis: skip rather than crash
    const [lo, hi] = d,
      v = vec[ax];
    const z = (v - AXIS_MEAN[ax]) / AXIS_SD[ax];
    // Distinctive AND clearly on that side: a middling value is not worth stating.
    if (z >= 0 && hi && v >= 0.65) candidates.push({ ax, text: hi, score: z });
    else if (z < 0 && lo && v <= 0.35) candidates.push({ ax, text: lo, score: -z });
  }
  candidates.sort((x, y) => y.score - x.score);
  if (candidates.length === 0 || candidates[0].score < 0.5)
    return tx`${tx(a.name)} sits near the middle of most axes, a generalist practice.`;
  const first = candidates[0];
  const second = candidates.find(
    (c) => c !== first && c.score >= 0.8 && descriptorFamily(c.ax) !== descriptorFamily(first.ax)
  );
  return second ? `${tx(a.name)} is ${tx(first.text)}, and ${tx(second.text)}.` : `${tx(a.name)} is ${tx(first.text)}.`;
}

// Developer safety net: warn (don't crash) if an axis has no descriptor entry.
AXES.filter((ax) => !(ax in AXIS_DESCRIPTORS)).forEach((ax) =>
  console.warn("Holotype: no description text for axis " + ax)
);
