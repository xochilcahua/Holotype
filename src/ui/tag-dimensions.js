// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

/* WHAT A COLOUR TAG CAN BE SORTED OR FILTERED ON. Category, cost, space, curve,
distance and the rest, with the older saved-shape upgrade that keeps tags from an
earlier build working. Needs nothing.
   See docs/architecture.md. */

// ---------------- Tag dimensions (filters and color tags) ----------------
const TAG_DIMENSIONS = {
  category: { label: tx("Category"), values: [...new Set(ART_FORMS.map((a) => a.category))].sort() },
  cost: { label: tx("Cost"), values: ["low", "medium", "high"] },
  space: { label: tx("Space"), values: ["none", "small", "studio", "large"] },
  curve: { label: tx("Learning curve"), values: ["quick", "moderate", "long"] },
  self: { label: tx("Self-taught friendly"), values: ["yes", "no"] },
};

// The tag values an art form carries on each dimension (category, cost, space, learning curve).
function tagValuesForArtForm(a) {
  return [
    { dimension: "category", value: a.category },
    { dimension: "cost", value: a.meta.cost },
    { dimension: "space", value: a.meta.space },
    { dimension: "curve", value: a.meta.curve },
    { dimension: "self", value: isSelfTaught(a) ? "yes" : "no" },
  ];
}

// A distance tag matches a novelty range (0 very familiar - 100 very new). Novelty is "how new is
// this compared with what you already like", so it only exists for art forms you have not rated.
function noveltyFor(a) {
  if (!hasRatings() || state.mastery[a.id] > 0) return null;
  const n = noveltyScore(a.id, state.mastery, state.discount);
  return n ? n.score : null;
}

// Does a colour rule apply to an art form with these tags and this novelty score?
function ruleMatches(rule, tags, nov) {
  if (rule.dimension === "distance") return nov != null && nov >= rule.min && nov <= rule.max;
  return tags.some((t) => t.dimension === rule.dimension && rule.values.includes(t.value));
}

// The colours of every colour rule that matches this art form.
function colorsForArtForm(a) {
  const tags = tagValuesForArtForm(a);
  const nov = state.colorRules.some((r) => r.dimension === "distance") ? noveltyFor(a) : null;
  return state.colorRules.filter((r) => ruleMatches(r, tags, nov)).map((r) => r.color);
}

// Human-readable text for a rule, as shown in the Colour tags panel.
function ruleLabel(rule) {
  if (rule.dimension === "distance") return tx`Distance from your taste: ${rule.min}\u2013${rule.max}`;
  return `${t(TAG_DIMENSIONS[rule.dimension].label)}: ${rule.values.map((v) => tagValueLabel(rule.dimension, v)).join(", ")}`;
}
