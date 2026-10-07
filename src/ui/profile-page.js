// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

/* THE HERBARIUM PAGE. Draws the whole profile tab from the current ratings: the holotype and its statistics, the growth
habit (plant, genus, variety, field notes, axis bars), the rated and not-yet-explored lists, and the "Export as PDF"
card beside them. Re-run by renderGrid() whenever the Herbarium is open.
   Needs state, classification (computeClassification, plantBlock) and the blocks in ui/profile-blocks.js.
   See docs/architecture.md. */

// The PDF export card: which sections to include, and the name field.
function exportCardHTML() {
  const checks = Object.keys(EXPORT_SECTION_LABELS)
    .map(
      (key) => `
    <label class="prof-check-row"><input type="checkbox" data-section="${key}" ${state.exportSections[key] ? "checked" : ""}> ${esc(t(EXPORT_SECTION_LABELS[key]))}</label>`
    )
    .join("");
  return i18nHTML`
    <div class="prof-export-card">
      <h3>Export as PDF</h3>
      <p class="sub">${i18nRich`Choose what to include: the PDF only contains the sections checked below, so it can stay as condensed or as complete as you want. Opens your browser's print dialog; choose <b>Save as PDF</b> (or "Print &gt; PDF" / "Microsoft Print to PDF") as the destination. Nothing is uploaded anywhere.`}</p>
      <label class="filter-label" for="exporterNameInput">Your name or alias (optional)</label>
      <input id="exporterNameInput" class="rule-select" style="width:100%;height:38px;max-width:320px" type="text" maxlength="60" placeholder="e.g. Alex" value="${esc(state.exporterName || "")}">
      <div class="prof-export-checks">${checks}</div>
      <button class="add-rule-btn" id="downloadGardenBtn" style="max-width:220px">Save as PDF</button>
    </div>
    <div class="prof-export-card">
      <h3>Save or load a session</h3>
      <p class="sub">Save your ratings, name, tags, filters and sort order as a small file. Load it on a later visit to pick up where you left off, then rate what you've learned since. Files from older versions load too, and anything this version can't place is kept aside, not deleted. Nothing is uploaded.</p>
      <div class="session-actions">
        <button type="button" class="add-rule-btn" id="saveSessionBtn">Save session (.json)</button>
        <button type="button" class="add-rule-btn" id="loadSessionBtn">Load session&hellip;</button>
        <input type="file" id="loadSessionInput" accept=".json,application/json" hidden>
      </div>
      <div id="sessionStatus" class="session-status" role="status" aria-live="polite"></div>
    </div>`;
}

// Attaches the handlers of the PDF export card.
function wireExportCard() {
  document.getElementById("exporterNameInput").addEventListener("input", (e) => {
    state.exporterName = e.target.value;
    saveStore();
    const titleEl = document.querySelector(".prof-title");
    if (titleEl) titleEl.textContent = profileTitle(state.exporterName);
  });
  document.querySelectorAll(".prof-export-checks input[type=checkbox]").forEach((cb) => {
    cb.addEventListener("change", (e) => {
      state.exportSections[e.target.dataset.section] = e.target.checked;
      saveStore();
    });
  });
  document.getElementById("downloadGardenBtn").addEventListener("click", printGardenExport);
  wireSessionCard();
}

// Renders the whole Herbarium page from the current ratings.
function renderProfilePage() {
  const stats = personalStats();
  const bc = computeClassification();
  const hue = personalHue();
  const accent = `oklch(0.55 0.13 ${hue})`;
  const { rated, unrated } = ratedUnratedLists();
  // The unfiltered totals, so a heading can say "3 of 9" instead of quietly claiming 3 is all there is.
  const allRated = ART_FORMS.filter((a) => state.mastery[a.id] > 0).length;
  const allUnrated = N - allRated;
  const summary = sessionSummaryLines();
  const known = hasRatings();

  const catBars = stats.catBreakdown
    .slice(0, 8)
    .map(
      (c) => `
    <div class="prof-catbar-row">
      <i class="pe-dot" style="background:${folkInk(c.hue)}"></i>
      <span class="name">${esc(t(c.category))}</span>
      <span class="prof-catbar-track"><span class="prof-catbar-fill" style="width:${Math.max(4, c.pct * 100).toFixed(0)}%;background:${folkInk(c.hue)}"></span></span>
      <span class="pct">${Math.round(c.pct * 100)}%</span>
    </div>`
    )
    .join("");

  // Garden (rated): icon + name + rating only - a tag about interest says little about something
  // you've already rated. Unexplored: icon + name + tag dots + novelty score, closest first.
  const ratedRows = gardenRowsHTML(rated);
  const unratedRows = unexploredRows(unrated, false).join("");
  const legendHTML = legendKeyHTML("prof", true);

  // The head row for the unexplored list, built separately: it nests a button inside a
  // ternary, and inlining all of that inside the page template made it unreadable.
  const unexploredHead = i18nHTML`<thead><tr><th class="ico-cell"></th><th>Art form</th><th class="dot-cell">Tags</th><th class="num">${known ? i18nHTML`<button type="button" class="th-sort" id="noveltySort" title="Sort by novelty" aria-label="Sort by novelty, currently ${ui.sort === "novelty_asc" ? tx("closest first") : tx("furthest first")}">Novelty${ui.sort === "novelty_desc" ? " \u2193" : ui.sort === "novelty_asc" ? " \u2191" : ""}</button>` : tx("Novelty")}</th>${isCommonSort() ? i18nHTML`<th class="num pct-cell" title="Roughly how many adults have had a go at this at some point in their lives, including once as a kid. A filled dot is a published lifetime figure; a hollow ring is modelled.">How common</th>` : ""}</tr></thead>`;

  const classifyHTML = bc
    ? i18nHTML`
    <div class="prof-section">
      <h2>Growth Habit</h2>
      <p class="lede">In botany, a plant's habit is its characteristic way of growing. Yours is how you tend to work, read from the same fingerprint as your holotype. It describes a style, not how good you are at anything, and it sharpens as you rate more.</p>
      ${growthPatternHTML(bc, "prof", accent, effectiveTheme() === "dark")}
    </div>`
    : i18nHTML`
    <div class="prof-section">
      <h2>Growth Habit</h2>
      <p class="lede">Rate a few art forms and your growth habit appears here: a plant of your own, named for how you tend to work.</p>
    </div>`;

  document.getElementById("profileView").innerHTML = i18nHTML`
    <div class="prof-hero">
      <div class="prof-flower-wrap">${holotypeSVG(220)}</div>
      <div class="prof-hero-text">
        <div class="prof-eyebrow" style="color:${accent}">Herbarium · specimen sheet</div>
        <h1 class="prof-title">${esc(profileTitle(state.exporterName))}</h1>
        <p class="prof-hero-desc">Every art form in Holotype grows its own flower from what it involves. Yours grows from what you've rated, so it works less like a flower and more like a fingerprint of your taste, drawn in the same visual language as everything else here. Its ink comes from whichever category you lean into most.</p>
        ${
          stats.ratedCount
            ? i18nHTML`
        <div class="prof-stats">
          <div class="prof-stat"><b style="color:${accent}">${stats.ratedCount}</b><span>Rated</span></div>
          <div class="prof-stat"><b style="color:${accent}">${stats.avgRating.toLocaleString(currentLang, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</b><span>Avg. rating</span></div>
          <div class="prof-stat"><b style="color:${accent}">${stats.categoriesTouched}</b><span>Categories</span></div>
        </div>`
            : i18nHTML`<p class="prof-hero-desc"><i>Rate a few art forms in your garden and this page fills in.</i></p>`
        }
      </div>
      ${stats.ratedCount ? `<div class="prof-catbars">${catBars}</div>` : ""}
    </div>

    <div class="prof-main">
      <div class="prof-main-l">${classifyHTML}</div>
      <aside class="prof-main-r">
        ${exportCardHTML()}
        <div class="prof-filters-mini">
          <h4>This session's filters</h4>
          ${summary.length ? `<ul>${summary.map((l) => `<li>${esc(l)}</li>`).join("")}</ul>` : i18nHTML`<p>No filters are active right now.</p>`}
        </div>
      </aside>
    </div>

    <div class="prof-section">
      <div class="prof-density-row">
        <h2>Your garden and unexplored flora</h2>
        <button type="button" class="pill-btn prof-density-btn" id="densityToggle" aria-pressed="${ui.dense}">${ui.dense ? tx("Comfortable spacing") : tx("Condensed spacing")}</button>
      </div>
      <p class="prof-density-note">${i18nRich`Both lists follow your filters, so switching off <b>Not yet rated</b> leaves only what you've rated.`}</p>
      ${legendHTML}
      <div class="prof-lists">
      ${
        rated.length
          ? `
      <div class="prof-block">
      <h4 class="prof-subhead">${rated.length === allRated ? tx`Your garden — ${rated.length} rated` : tx`Your garden — ${rated.length} of ${allRated} rated`}</h4>
      ${splitTableRows(ratedRows, "prof-table prof-table-rated", i18nHTML`<thead><tr><th class="ico-cell"></th><th>Art form</th><th class="num">Rating</th></tr></thead>`, ratedColumnCount(rated.length), true)}</div>`
          : i18nHTML`<div class="prof-block"><h4 class="prof-subhead">Your garden</h4><p class="lede">${ui.showRated ? tx("Nothing rated yet.") : tx("Your garden is hidden by the filter.")}</p></div>`
      }

      <div class="prof-block">
      <h4 class="prof-subhead">${unrated.length === allUnrated ? tx`Not yet explored — ${unrated.length}` : tx`Not yet explored — ${unrated.length} of ${allUnrated}`} <span class="muted" style="text-transform:none;letter-spacing:0;font-weight:500">· sorted: ${esc(t(SORT_LABELS[ui.sort] || ui.sort))}${tagSortInert() ? tx(" (add colour tags to group by them)") : ""}</span></h4>
      ${
        unrated.length
          ? splitTableRows(unratedRows, "prof-table prof-table-unexplored", unexploredHead, tableColumnCount(), true)
          : `<p class="lede">${ui.showUnrated ? tx("Nothing left in this category.") : tx("Not yet explored is hidden by the filter.")}</p>`
      }
      </div>
      </div>
    </div>
  `;

  wireExportCard();
  // Density is a reading preference for this list only, so it stays out of the session file and out
  // of the PDF: the sheet has its own print-sized spacing.
  document.getElementById("profileView").classList.toggle("dense", !!ui.dense);
  const density = document.getElementById("densityToggle");
  if (density)
    density.addEventListener("click", () => {
      ui.dense = !ui.dense;
      renderProfilePage();
    });
  const noveltySort = document.getElementById("noveltySort");
  if (noveltySort)
    noveltySort.addEventListener("click", () => {
      ui.sort = ui.sort === "novelty_desc" ? "novelty_asc" : "novelty_desc"; // same state the top-bar sort menu uses
      sortSelect.value = ui.sort;
      renderGrid();
      document.getElementById("noveltySort").focus();
    });
}
