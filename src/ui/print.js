// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

/* PRINT EXPORT. Builds the printable sheet entirely out of on-page DOM, so it needs
no server and uploads nothing. Needs the narrowing layer and the profile blocks.
   See docs/architecture.md. */

// ---------------------------------------------------------------------------
// PRINT EXPORT: builds the printable page entirely out of on-page DOM (no external library,
// no network request, no canvas rasterising) so "Save as PDF" is just the browser's own,
// always-available print-to-PDF pipeline pointed at content styled for print via @media print
// below. Only includes the sections currently checked in state.exportSections, so the export
// card on the profile page controls exactly what ends up in the PDF.
function buildPrintExport() {
  const sec = state.exportSections;
  const { rated, unrated } = ratedUnratedLists();
  const dateStr = new Date().toLocaleDateString(currentLang, { year: "numeric", month: "long", day: "numeric" });
  const summary = sessionSummaryLines();
  // The portrait and the classification describe who you are, so they are computed from every
  // rating, never from the filtered subset. The two tables below are the filtered part.
  const stats = personalStats();
  const name = (state.exporterName || "").trim();
  const hue = personalHue();
  const accent = `oklch(0.55 0.13 ${hue})`;

  const ratedRows = gardenRowsHTML(rated);
  const halfAt = Math.ceil(unrated.length / 2);
  const unratedAll = unexploredRows(unrated, true);
  const legendHTML = legendKeyHTML("pe", false);
  // The subtitle describes what this sheet actually contains. It used to report only the rated count,
  // so switching the garden off produced the baffling "0 of 12 rated (filtered)" on a sheet that was
  // mostly unexplored rows. Say both halves, and whether the filters shortened them.
  const allRated = ART_FORMS.filter((a) => state.mastery[a.id] > 0).length;
  const allUnrated = N - allRated;
  const listed = rated.length + unrated.length;
  const ratedCountStr =
    listed === N
      ? tx`${allRated} of ${N} art forms rated`
      : tx`${listed} of ${N} art forms listed — ${rated.length} rated, ${unrated.length} not yet`;
  const gardenTitle =
    rated.length === allRated
      ? tx`Your garden — ${rated.length} rated`
      : tx`Your garden — ${rated.length} of ${allRated} rated`;
  const unexploredTitle =
    unrated.length === allUnrated
      ? tx`Not yet explored — ${unrated.length}`
      : tx`Not yet explored — ${unrated.length} of ${allUnrated}`;

  const catBars = stats.catBreakdown
    .slice(0, 6)
    .map(
      (c) => `
    <div class="pe-catbar-row">
      <i class="pe-dot" style="background:${folkInk(c.hue)}"></i>
      <span class="name">${esc(t(c.category))}</span>
      <span class="pe-catbar-track"><span class="pe-catbar-fill" style="width:${Math.max(4, c.pct * 100).toFixed(0)}%;background:${folkInk(c.hue)}"></span></span>
      <span class="pct">${Math.round(c.pct * 100)}%</span>
    </div>`
    )
    .join("");

  const portraitHTML = sec.portrait
    ? i18nHTML`
    <div class="pe-about">
      <div class="pe-flower-wrap">${holotypeSVG(280)}</div>
      <div class="pe-about-text">
        <h3>What this shows</h3>
        <p>Every art form in Holotype grows its own flower from what it involves. Yours grows from what you've rated, so it works less like a flower and more like a fingerprint of your taste. Its ink comes from whichever category you lean into most.</p>
        ${
          stats.ratedCount
            ? i18nHTML`
        <div class="pe-stats">
          <div class="pe-stat"><b style="color:${accent}">${stats.ratedCount}</b><span>Rated</span></div>
          <div class="pe-stat"><b style="color:${accent}">${stats.avgRating.toLocaleString(currentLang, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</b><span>Avg. rating</span></div>
          <div class="pe-stat"><b style="color:${accent}">${stats.categoriesTouched}</b><span>Categories</span></div>
        </div>
        <div class="pe-catbars">${catBars}</div>`
            : i18nHTML`<p class="muted">Rate a few art forms in Holotype and this section will fill in with what your ratings lean toward.</p>`
        }
      </div>
    </div>`
    : "";

  const filtersHTML = sec.filters
    ? i18nHTML`
    <h3>This session's filters</h3>
    ${summary.length ? `<ul class="pe-summary">${summary.map((l) => `<li>${esc(l)}</li>`).join("")}</ul>` : i18nHTML`<p class="muted">No filters were active.</p>`}`
    : "";

  const gardenHTML =
    sec.garden && rated.length
      ? i18nHTML`
    <h2 style="border-bottom-color:${accent}">Your garden and unexplored flora</h2>
    ${legendHTML}
    <h4 class="pe-subhead">${gardenTitle}</h4>
    <table class="pe-table"><tbody>${ratedRows}</tbody></table>`
      : "";

  const unexploredHTML = sec.unexplored
    ? i18nHTML`
    ${gardenHTML ? "" : i18nHTML`<h2 style="border-bottom-color:${accent}">Your garden and unexplored flora</h2>${legendHTML}`}
    <h4 class="pe-subhead">${unexploredTitle} <span>sorted: ${esc(t(SORT_LABELS[ui.sort] || ui.sort))}</span></h4>
    <div class="pe-two"><table class="pe-table"><tbody>${unratedAll.slice(0, halfAt).join("")}</tbody></table><table class="pe-table"><tbody>${unratedAll.slice(halfAt).join("")}</tbody></table></div>`
    : "";

  const classificationHTML = sec.classification ? classificationSection(computeClassification(), accent) : "";

  document.getElementById("printExport").innerHTML = i18nHTML`
    <div class="pe-header-band">
      <div class="pe-eyebrow" style="color:${accent}">Herbarium · specimen sheet</div>
      <h1>${esc(profileTitle(name, "My Holotype"))}</h1>
      <div class="pe-accent-bar" style="background:${accent}"></div>
      <p class="pe-sub">Exported ${dateStr} · ${ratedCountStr}</p>
    </div>
    ${portraitHTML}
    ${classificationHTML}
    ${filtersHTML}
    ${gardenHTML}
    ${unexploredHTML}`;
}

// One entry point for both print routes, so the sheet and the document title are prepared
// identically however printing was started. beforeprint can fire more than once for a
// single print (and page.pdf()/automation drive it too), so the original title is stashed
// once and the afterprint restore is registered once: re-running this function used to
// capture the already-substituted title as the "previous" one, leaving it stuck on
// "<name> — Holotype" after printing.
let printPrevTitle = null;
// Builds the print layout and sets the document title to the reader's name, which becomes the PDF's file name.
function preparePrint() {
  buildPrintExport();
  const name = (state.exporterName || "").trim();
  if (printPrevTitle === null) {
    printPrevTitle = document.title;
    window.addEventListener(
      "afterprint",
      () => {
        document.title = printPrevTitle;
        printPrevTitle = null;
      },
      { once: true }
    );
  }
  document.title = name ? `${name} — Holotype` : tx("Holotype");
}

// Prepares the page and opens the browser's print dialog (choose Save as PDF).
function printGardenExport() {
  preparePrint();
  // Give the browser a tick to lay out the freshly-built print content before invoking print.
  requestAnimationFrame(() => requestAnimationFrame(() => window.print()));
}

// Cmd/Ctrl+P and the browser's own Print… menu item never reach printGardenExport, and
// #printExport is empty on a fresh page load, so the print stylesheet (which hides every
// sibling of #printExport) printed a blank page from that route. beforeprint fires for
// every entry point, so building here covers all of them. It rebuilds rather than reusing
// cached HTML, so the sheet always matches the ratings held in state at print time.
window.addEventListener("beforeprint", preparePrint);
