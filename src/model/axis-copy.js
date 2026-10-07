// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

/* THE PLAIN-LANGUAGE TEXT FOR EACH AXIS. The two ends of every axis in words, which
is what the detail sheet and the axis bars read. Its own file rather than part of
axes.js: it sits after the distance matrices in load order, because that is where
it lives in the original file, and it is only needed by describe.js and the UI.
   See docs/architecture.md. */

const AXIS_DESCRIPTORS = {
  a1: ["improvised in the moment", "planned well in advance"],
  a2: ["built from raw material you originate", "assembled by editing existing material"],
  a3: ["hand-controlled at every step", "driven by an autonomous system you set up"],
  a4: ["open to interpretation", "fixed and literal in meaning"],
  a5: ["grasped through direct sensory experience", "understood by decoding symbolic language"],
  a6: [null, null], // redundant with a13 and at its default for most items
  a7: ["built from words and semantic meaning", "built from tone, form, or pattern without words"],
  a8: ["made from organic or living material", "made from inert or manufactured material"],
  a9: ["centered on mark-making and rendering skill", null],
  a10: ["built to be used, not just looked at", "purely expressive rather than functional"],
  a11: ["rooted in ritual or tradition", null],
  a12: ["traditionally passed down through apprenticeship", "easy to teach yourself"],
  a13: ["made as singular physical objects or events", "easy to reproduce at scale"],
  b1: ["driven by fine, precise motion", "driven by full-body, gross motion"],
  b2: ["made with safe, forgiving materials", "made with hazardous or unforgiving materials"],
  b3: ["highly controlled and repeatable", "chance-driven and emergent"],
  b4: ["essentially flat and two-dimensional", "volumetric and spatial"],
  c1: [null, "a strongly visual medium"],
  c2: [null, "a strongly auditory medium"],
  c3: [null, "a strongly tactile medium"],
  c4: [null, "a strongly olfactory medium"],
  c5: [null, "a strongly gustatory medium"],
  d1: ["typically a solo pursuit", "structurally collaborative"],
  d2: ["closed off to audience influence", "shaped by audience participation"],
  d3: ["essentially irrevocable: one attempt", "endlessly revisable"],
  d4: ["ephemeral: the result doesn't last", "archival: the result persists"],
  e1: ["usually a solo or freelance pursuit", "typically practiced inside institutions or studios"],
  e2: ["a niche, hobbyist-scale pursuit", "an industry with large commercial scale"],
  p1: [null, "closely tied to music and sound"],
  p2: [null, "rooted in language and storytelling"],
  p3: [null, "in service of visual image-making"],
  p4: [null, "centered on movement and the body"],
  p5: [null, "part of food-and-drink culture"],
  p6: [null, "shaped around space and the built environment"],
  p7: [null, "bound up with nature and living systems"],
};

// Sense and purpose axes both describe "what medium/field", so only one of them is used per description.
function descriptorFamily(ax) {
  return ax[0] === "c" || ax[0] === "p" ? "medium" : ax;
}

// What is DISTINCTIVE about a practice is how far it sits from the typical art form on that axis,
// in standard deviations. (Raw extremeness would report that Fiction Writing is "made with safe
// materials", true but true of nearly everything non-physical.)
