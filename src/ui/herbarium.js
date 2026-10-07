// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

/* THE HERBARIUM TAB AND EVERY ROW ON IT. The second page: the holotype plate, the
growth-habit plant, the classification and its rows and legend, and how common each
practice is. Takes its rows from the same narrowing layer as the garden.
   See docs/architecture.md. */

// ---------------------------------------------------------------------------
// PROFILE TAB: switches the main content between the garden grid and a full page showing
// everything an export would contain - portrait, classification, tags, garden, filters - live,
// before you ever open the print dialog. "Export" now lives at the bottom of this page as a
// section picker, rather than being its own side panel.

function setMode(mode) {
  ui.mode = mode;
  const isProfile = mode === "profile";
  document.getElementById("gardenView").hidden = isProfile;
  document.getElementById("profileView").hidden = !isProfile;
  document
    .querySelectorAll("#viewToggle button")
    .forEach((b) => b.setAttribute("aria-selected", String(b.dataset.mode === mode)));
  if (isProfile) {
    renderProfilePage();
    window.scrollTo(0, 0);
  }
}
// The E shortcut flips between the two tabs.
function toggleExport() {
  setMode(ui.mode === "profile" ? "garden" : "profile");
}

// Lines naming the active sort and filters, printed on the Herbarium page and the PDF.
function sessionSummaryLines() {
  const lines = [];
  lines.push(tx`Sort: ${t(SORT_LABELS[ui.sort] || ui.sort)}`);
  // Printed on the sheet, so the reader of a PDF meets the same caveat the screen gives.
  if (isCommonSort())
    lines.push(
      tx("How common: estimated share of US adults who have tried this at some point in their lives, including once as a kid (filled dot = published lifetime figure, hollow = estimated)")
    );
  if (ui.query) lines.push(tx`Search: "${ui.query}"`);
  if (ui.activeCategories.size) lines.push(tx`Category filter: ${[...ui.activeCategories].map((c) => t(c)).join(", ")}`);
  if (ui.activeTiers.size)
    lines.push(tx`Familiarity filter: ${[...ui.activeTiers].map((tier) => t(TIER_LABELS[tier])).join(", ")}`);
  // Only mention a half that is switched off. This text is printed on the sheet itself, so it is
  // what tells a reader why a list is shorter than the catalogue.
  const hidden = [];
  if (!ui.showRated) hidden.push(tx("your garden (rated)"));
  if (!ui.showUnrated) hidden.push(tx("not yet rated"));
  if (hidden.length) lines.push(tx`Hidden: ${hidden.join(", ")}`);
  if (state.discount !== 0.5) lines.push(tx`How far ratings reach: ${state.discount.toFixed(2)}`);
  return lines;
}

// Rows and legend shared by the Herbarium page and the print export. Rows carry only the category
// icon (its meaning is spelled out once, in the legend); tags color the row's edge and add dots.
// Split a list of <tr> strings across N side-by-side tables. The on-screen Herbarium and the print
// sheet both use this, so a 294-row list is a readable couple of columns instead of one very long
// one. The sub-tables repeat the head row so each column still says what its numbers mean, and each
// carries the same class so row-based tooling is unaffected.
// `n` is capped by the row count: splitting 3 rows into 3 columns just makes three stub tables.
// `headOnce` renders the head row only on the first table. That matters when the head contains an
// interactive control, because repeating it would duplicate its id and make it a second tab stop
// pointing at the same element.
// Accepts an array of rows or one already-joined string (both call sites exist: the profile page
// joins its rows up front, the print sheet keeps them split to halve them).
function splitTableRows(rows, cls, headHTML, n, headOnce) {
  const list = typeof rows === "string" ? (rows ? rows.match(/<tr[\s\S]*?<\/tr>/g) || [] : []) : rows;
  const cols = Math.max(1, Math.min(n, list.length));
  if (cols === 1) return `<table class="${cls}">${headHTML}<tbody>${list.join("")}</tbody></table>`;
  const per = Math.ceil(list.length / cols);
  let h = `<div class="prof-multi" style="--cols:${cols}">`;
  for (let i = 0; i < cols; i++) {
    const slice = list.slice(i * per, (i + 1) * per);
    if (!slice.length) continue;
    h += `<table class="${cls}">${headOnce && i > 0 ? "" : headHTML}<tbody>${slice.join("")}</tbody></table>`;
  }
  return h + `</div>`;
}

// The number of columns a list is split into, read from the window width once per render rather
// than per row; a resize just needs the next render to pick it up.
//
// Comfortable mode puts the two lists side by side, one column each - they are different halves of
// the catalogue, and setting them beside each other is how the sheet reads as a specimen sheet
// rather than as two stacked tables. A single column also has room for the long art-form names
// ("Social Partner Dance (Tango, Swing, Salsa)", 343px) with room to spare, so nothing wraps.
//
// Condensed mode stacks them and gives each three columns, which is the point of condensed: the
// same information in roughly a third of the vertical space. Three is safe here because the rows
// are 23px tall rather than 30.5px and sit on the full 1400px content width rather than half of it.
function tableColumnCount() {
  const w = window.innerWidth || document.documentElement.clientWidth || 1400;
  if (!ui.dense) return 1;
  return w >= 1180 ? 3 : w >= 780 ? 2 : 1;
}

// The rated list is usually much shorter than the unexplored one, so it gets fewer columns: a
// garden of 14 rows split three ways reads as fragments rather than as a list. Below ~10 rows a
// single column is clearer than two short ones.
function ratedColumnCount(n) {
  const max = tableColumnCount();
  if (max < 2 || n < 10) return 1;
  return n < 24 ? 2 : max;
}

// The rows of the rated list.
function gardenRowsHTML(rated) {
  return rated
    .map(
      (a) =>
        `<tr><td class="ico-cell">${iconFor(a.category)}</td><td>${esc(t(a.name))}</td><td class="num">${state.mastery[a.id]}/10</td></tr>`
    )
    .join("");
}

const SORT_LABELS = {
  novelty_asc: "Closest to you first",
  novelty_desc: "Furthest from you first",
  name_asc: "A to Z",
  category: "By category",
  common_desc: "Most common first",
  common_asc: "Less common first",
  tag: "By tag",
};

// (PREVALENCE and PREVALENCE_ANCHORED now live in data/prevalence.js - see the note there.)

// Share as a percentage string. Sub-1% forms are real but too rare for a whole number, and
// rounding them all to "0%" would flatten the bottom sixty or so into one indistinguishable blob.
function prevalencePct(a) {
  const v = PREVALENCE[a.id];
  if (v == null) return null;
  if (v >= 10) return String(Math.round(v));
  if (v >= 1) return v.toFixed(1).replace(/\.0$/, "");
  return v.toFixed(2).replace(/^0/, "");
}

// "By tag" groups by your own colour tags, so it needs each art form's first matching rule in rule
// order (stable, and it matches the dot order on the row). Untagged forms sort last rather than
// first: the point of the sort is to gather your own groups together.
function tagSortKey(a) {
  const tags = tagValuesForArtForm(a);
  const nov = state.colorRules.some((r) => r.dimension === "distance") ? noveltyFor(a) : null;
  for (let i = 0; i < state.colorRules.length; i++) {
    if (ruleMatches(state.colorRules[i], tags, nov)) return i;
  }
  return state.colorRules.length;
}

// The structural part of a sort: the three orders that are about the catalogue rather than about
// this reader (how common it is, what category it is in, which of your tags it carries). Returns
// only that first key, so each caller can chain its own tie-breaker - a novelty score in one list,
// a rating in the other - and end with the name, which is the only total order available.
// null means "this sort is not structural here; keep your own order".
function structuralKey(a, b) {
  if (isCommonSort()) {
    const d = (PREVALENCE[a.id] ?? 0) - (PREVALENCE[b.id] ?? 0);
    return ui.sort === "common_desc" ? -d : d;
  }
  // "By tag" with no tags defined has nothing to group by. Returning null leaves the caller's own
  // order in place and lets the page say so, rather than presenting a novelty list under a heading
  // that claims it is grouped by tag.
  if (ui.sort === "tag") return state.colorRules.length ? tagSortKey(a) - tagSortKey(b) : null;
  if (ui.sort === "category") return t(a.category).localeCompare(t(b.category), currentLang);
  return null;
}

// True when "By tag" is selected but there are no colour tags to group by, which the page states
// plainly instead of quietly sorting by something else.
function tagSortInert() {
  return ui.sort === "tag" && !state.colorRules.length;
}

// True when the list is sorted by how common an art form is.
function isCommonSort() {
  return ui.sort === "common_desc" || ui.sort === "common_asc";
}
// One extra cell on the unexplored rows, and only while a commonness sort is on: the estimate and
// whether it is a published figure. A filled dot is anchored to a survey number; a hollow ring is
// modelled. The column is worth its width only while it is the thing being sorted on, so it is not
// rendered for the other five sorts - the row markup is shared by the screen and the print sheet.
function commonCellHTML(a) {
  if (!isCommonSort()) return "";
  const p = prevalencePct(a);
  if (p == null) return "";
  const anchored = PREVALENCE_ANCHORED.has(a.id);
  const title = anchored
    ? tx`About ${p}% of adults have had a go at this at some point in their lives.`
    : tx`About ${p}% of adults have had a go at this at some point in their lives (estimated, not a published figure).`;
  return `<td class="num pct-cell" title="${esc(title)}"><i class="pc-dot${anchored ? "" : " pc-est"}" aria-hidden="true"></i>${esc(p)}%<span class="sr-only">${anchored ? tx(", survey figure") : tx(", estimated")}</span></td>`;
}

// Compare by the structural key, then whatever the caller cares about next, then the name.
function bySortThen(a, b, tie) {
  const k = structuralKey(a, b);
  return (k !== null ? k : 0) || tie || compareArtNames(a, b);
}

// Returns one <tr> string per unrated art form, in the same order as the top-bar sort
// (Closest to you first / Furthest from you first / A to Z). `compact` drops the
// "Familiar / In between / New ground" wording (the legend gives the bands instead).
function unexploredRows(unrated, compact) {
  const known = hasRatings();
  const nov = known ? computeNovelty(state.mastery, state.discount) : null;
  const rows = unrated.map((a) => ({ a, n: nov ? nov.byId[a.id] : null }));
  // An active search is a lookup: the caller already handed these over in search order, so leave it
  // alone. Re-sorting by novelty here used to bury the exact row you typed.
  if (!ui.query)
    rows.sort((x, y) => {
      // A structural sort (commonness, category, tag) leads; novelty orders within the group, so a
      // grouped list still reads closest-first inside each section.
      const k = structuralKey(x.a, y.a);
      if (k !== null)
        return k || (nov ? y.n.raw - x.n.raw || y.n.tie - x.n.tie : 0) || compareArtNames(x.a, y.a);
      if (!nov || ui.sort === "name_asc") return compareArtNames(x.a, y.a);
      const d =
        ui.sort === "novelty_asc" ? x.n.raw - y.n.raw || x.n.tie - y.n.tie : y.n.raw - x.n.raw || y.n.tie - x.n.tie;
      return d || compareArtNames(x.a, y.a);
    });
  return rows.map(({ a, n }) => {
    const cols = colorsForArtForm(a);
    const dots = cols.map((c) => `<i class="pe-dot" style="background:${esc(c)}"></i>`).join("");
    const novCell = n
      ? `${n.score}${compact ? "" : `<span class="muted"> &middot; ${esc(t(TIER_LABELS[n.tier]))}</span>`}`
      : `<span class="muted">&ndash;</span>`;
    return `<tr${cols.length ? ` class="tagged" style="--tag:${esc(cols[0])}"` : ""}><td class="ico-cell">${iconFor(a.category)}</td><td>${esc(t(a.name))}</td><td class="dot-cell">${dots}</td><td class="num">${novCell}</td>${commonCellHTML(a)}</tr>`;
  });
}

// Explains the icons and colour dots in the list legend.
function legendNoteText() {
  // Two whole sentences-with-numbers, each one translation key, so a translator can reorder them freely.
  const base = i18nHTML`Each row's icon is its category (key below). Dots and colored edges are your own tags, and they only appear on art forms you haven't rated yet. The number is your rating out of 10 in the garden; in the unexplored list it is a novelty score from 1 (very familiar) to 100 (very new): ${NOVELTY.familiarMax} or less is familiar, ${NOVELTY.familiarMax + 1}-${NOVELTY.newMin} in between, above ${NOVELTY.newMin} new ground.`;
  const common = isCommonSort()
    ? i18nHTML` <b>How common</b> is roughly how many adults have had a go at it at all, at any age, even once as a kid &mdash; the same bar as rating it a 1. So singing, drawing and cooking sit near the top. Hollow rings are estimates, so read those as an order of magnitude.`
    : "";
  return base + common;
}

// The icon/tag key. `collapsible` wraps it in a closed <details> for the on-screen page, where it
// is reference material sitting above a long list; the print sheet passes false and always shows it,
// because a PDF reader cannot click a disclosure open.
function legendKeyHTML(cls, collapsible) {
  const cats = TAG_DIMENSIONS.category.values
    .map((c) => `<span class="${cls}-key">${iconFor(c, 15)}${esc(t(c))}</span>`)
    .join("");
  const tags = state.colorRules
    .map(
      (r) =>
        `<span class="${cls}-key"><i class="pe-dot pe-dot-lg" style="background:${esc(r.color)}"></i>${esc(ruleLabel(r))}</span>`
    )
    .join("");
  const body = i18nHTML`<div class="${cls}-legend-body"><p class="${cls}-legend-note">${legendNoteText()}</p><div class="${cls}-legend-row"><b>Categories</b>${cats}</div>${tags ? i18nHTML`<div class="${cls}-legend-row"><b>Your tags</b>${tags}</div>` : ""}</div>`;
  if (!collapsible) return `<div class="${cls}-legend">${body}</div>`;
  return i18nHTML`<details class="${cls}-legend"><summary>How to read these lists</summary>${body}</details>`;
}

// The Herbarium page and the PDF export both build their two lists here, so they narrow by exactly
// the same rules as the Garden - same search, same categories, same show/hide switches. Previously
// this filtered on nothing at all, which is why a category picked in the Garden still exported the
// whole catalogue. `rank` (search order) is honoured so a lookup behaves the same on both tabs.
function ratedUnratedLists() {
  const { rated, unrated, rank } = narrowedCatalog();
  if (rank) return { rated, unrated }; // already in search order; sorting would fight the query
  rated.sort((a, b) => bySortThen(a, b, state.mastery[b.id] - state.mastery[a.id]));
  // The sheet follows the same sort as the screen. unratedRows() already ordered these, so only
  // re-sort when the print sheet's own row list disagrees - it keeps rows split across tables.
  if (isCommonSort() || ui.sort === "tag") unrated.sort((a, b) => bySortThen(a, b, 0));
  return { rated, unrated };
}

// What your ratings are actually weighted toward, by category, so the export says something
// real about you rather than just showing a shape and a list.
function personalStats() {
  const rated = ART_FORMS.filter((a) => state.mastery[a.id] > 0);
  const totalWeight = rated.reduce((s, a) => s + state.mastery[a.id], 0);
  const byCat = {};
  rated.forEach((a) => {
    byCat[a.category] = (byCat[a.category] || 0) + state.mastery[a.id];
  });
  const catBreakdown = Object.keys(byCat)
    .map((c) => ({ category: c, weight: byCat[c], pct: totalWeight ? byCat[c] / totalWeight : 0, hue: hueFor(c) }))
    .sort((a, b) => b.weight - a.weight);
  const avgRating = rated.length ? totalWeight / rated.length : 0;
  return { ratedCount: rated.length, avgRating, categoriesTouched: catBreakdown.length, catBreakdown };
}
