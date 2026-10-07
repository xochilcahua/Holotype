// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

/* THE GARDEN PDF. A sheet built around the reader's own flower rather than around any
single art form, so what comes out is a record of them and not of the catalogue.
   See docs/architecture.md. */

// ---------------------------------------------------------------------------
// GARDEN EXPORT: a PDF built around your own flower - not any single art form's, but the
// rating-weighted average of every axis across everything you've rated, so it's shaped by what
// you actually know and how well, the same visual language as the flowers on every card.

function personalVector() {
  const axes = [...AXIS_GROUPS.technique, ...AXIS_GROUPS.domain, ...AXIS_GROUPS.sensory];
  const rated = ART_FORMS.filter((a) => state.mastery[a.id] > 0);
  if (!rated.length) return null;
  const totalWeight = rated.reduce((s, a) => s + ratingWeight(state.mastery[a.id]), 0);
  const v = {};
  axes.forEach((ax) => {
    v[ax] = rated.reduce((s, a) => s + ratingWeight(state.mastery[a.id]) * a.vector[ax], 0) / totalWeight;
  });
  return v;
}

// The hue of whichever category carries the most weight in your ratings, so the portrait's
// color itself says something about where your practice is centred; a neutral default otherwise.
function personalHue() {
  const rated = ART_FORMS.filter((a) => state.mastery[a.id] > 0);
  if (!rated.length) return 38;
  const byCat = {};
  rated.forEach((a) => {
    byCat[a.category] = (byCat[a.category] || 0) + ratingWeight(state.mastery[a.id]);
  });
  return hueFor(Object.keys(byCat).reduce((best, c) => (byCat[c] > (byCat[best] || 0) ? c : best), null));
}

// Self-contained (own <style>, own color values) so it renders identically whether it's shown
// live in the panel or rasterised off-screen for the PDF, neither of which has access to the
// page's own stylesheet the way an on-page .flower does.
function holotypeSVG(sizePx) {
  const hue = personalHue(),
    pv = personalVector();
  const R = 48 * 0.66,
    cap = "font-family:var(--font-display);letter-spacing:.16em;";
  const flower = pv
    ? `<g class="rose">${flowerPetals(pv, 1)}${heartSVG(5)}</g>`
    : `<circle r="8" fill="none" stroke="var(--ink-3)" stroke-width="1.5" stroke-dasharray="3 3"/>`;
  const ticks = [0, 90, 180, 270]
    .map((d) => `<line x1="0" y1="${f1(-R - 1)}" x2="0" y2="${f1(-R - 4)}" transform="rotate(${d})"/>`)
    .join("");
  const item = (x, glyph, label) =>
    `<g transform="translate(${x} 45)">${glyph}</g><text x="${x + 3.6}" y="46.4" style="${cap}" font-size="4.2" fill="var(--ink-2)">${label}</text>`;
  return i18nHTML`<svg class="holotype-flower" xmlns="http://www.w3.org/2000/svg" width="${sizePx}" height="${sizePx}" viewBox="-60 -60 120 120" style="${folkStyle(hue, 1)}" role="img" aria-label="Your holotype: outer petals show how you make things, middle petals the fields you lean toward, inner pips the senses you use. Longer means stronger.">
    <rect x="-58" y="-58" width="116" height="116" fill="var(--surface)" stroke="var(--edge)" stroke-width=".9"/>
    <rect x="-55" y="-55" width="110" height="110" fill="none" stroke="var(--line-2)" stroke-width=".5"/>
    <text x="0" y="-47.6" text-anchor="middle" style="${cap}" font-size="4.6" font-weight="700" fill="var(--ink)">HOLOTYPE</text>
    <line x1="-40" y1="-44" x2="40" y2="-44" stroke="var(--line-2)" stroke-width=".4"/>
    <g transform="translate(0 -1)"><circle r="${f1(R)}" fill="none" stroke="var(--line-2)" stroke-width=".45" stroke-dasharray="1 1.6"/><g stroke="var(--ink-3)" stroke-width=".5">${ticks}</g><g transform="scale(.66)">${flower}</g></g>
    <line x1="-40" y1="39.5" x2="40" y2="39.5" stroke="var(--line-2)" stroke-width=".4"/>
    ${item(-42.5, '<path d="M0 3Q2.6 0 0 -3Q-2.6 0 0 3Z" fill="var(--c1)"/>', t("MADE"))}
    ${item(-13.5, '<rect x="-1.2" y="-3" width="2.4" height="6" rx="1.2" fill="var(--c2)"/>', t("FIELD"))}
    ${item(15.5, '<circle r="1.7" fill="var(--c3)"/>', t("SENSES"))}
    <text x="0" y="52.6" text-anchor="middle" font-size="3.6" fill="var(--ink-3)" style="font-family:var(--font-ui);font-style:italic">longer petal, stronger trait</text>
  </svg>`;
}
