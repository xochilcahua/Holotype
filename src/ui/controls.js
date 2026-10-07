// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

/* THE BAR ACROSS THE TOP. Category and tier chips, the sort menu, the show/hide
switches and the rating readout, plus the rule the garden and the Herbarium share
so a sheet always records the filters that produced it.
   See docs/architecture.md. */

// ---------------- Controls: chips, sort, filters ----------------
function renderCategoryChips() {
  const wrap = document.getElementById("categoryChips");
  if (!wrap) return;
  wrap.innerHTML = "";
  for (const cat of TAG_DIMENSIONS.category.values) {
    const chip = document.createElement("button");
    chip.className = "chip" + (ui.activeCategories.has(cat) ? " active" : "");
    chip.style.setProperty("--hue", hueFor(cat));
    chip.innerHTML = `<i></i>${esc(t(cat))}`;
    chip.addEventListener("click", () => {
      ui.activeCategories.has(cat) ? ui.activeCategories.delete(cat) : ui.activeCategories.add(cat);
      renderCategoryChips();
      updateFilterCount();
      renderGrid();
    });
    wrap.appendChild(chip);
  }
}

const TIER_LABELS = { high_overlap: "Familiar", borderline: "In between", uncharted: "New ground" };
// A form promoted into New ground by the "newest third" rule can score 41-70, so printing "New ground"
// next to a number the help text calls "In between" read as a contradiction. The tier still drives the
// filter chips; only the label shown beside the number tells the truth about why it is there.
function tierLabel(tier, promoted) {
  return t(promoted ? "Newest third" : TIER_LABELS[tier]);
}
// Draws the familiarity chips (the novelty bands) used to filter the grid.
function renderTierChips() {
  const wrap = document.getElementById("tierChips");
  if (!wrap) return;
  wrap.innerHTML = "";
  for (const tier of Object.keys(TIER_LABELS)) {
    const chip = document.createElement("button");
    chip.className = "chip" + (ui.activeTiers.has(tier) ? " active" : "");
    chip.textContent = t(TIER_LABELS[tier]);
    chip.addEventListener("click", () => {
      ui.activeTiers.has(tier) ? ui.activeTiers.delete(tier) : ui.activeTiers.add(tier);
      renderTierChips();
      updateFilterCount();
      renderGrid();
    });
    wrap.appendChild(chip);
  }
}

document.getElementById("searchInput").addEventListener("input", (e) => {
  ui.query = e.target.value;
  renderGrid();
});

const sortSelect = document.getElementById("sortSelect");
sortSelect.value = ui.sort;
sortSelect.addEventListener("change", () => {
  ui.sort = sortSelect.value;
  renderGrid();
});

// Two switches for the halves of the catalogue: your own garden, and everything you haven't rated
// yet. Both start ON, so nothing is hidden until you ask for it. They apply to the Garden, the
// Herbarium page and the PDF at the same time - that is the point of them.
const SHOW_LABELS = { showRated: "My garden (rated)", showUnrated: "Not yet rated" };
// Draws the show/hide switches for the rated and unrated halves.
function renderShowChips() {
  const wrap = document.getElementById("showChips");
  if (!wrap) return;
  wrap.innerHTML = "";
  for (const key of Object.keys(SHOW_LABELS)) {
    const chip = document.createElement("button");
    chip.className = "chip" + (ui[key] ? " active" : "");
    chip.textContent = t(SHOW_LABELS[key]);
    // A plain toggle, so it announces its state rather than just looking pressed.
    chip.setAttribute("aria-pressed", String(!!ui[key]));
    chip.addEventListener("click", () => {
      ui[key] = !ui[key];
      renderShowChips();
      updateFilterCount();
      renderGrid();
    });
    wrap.appendChild(chip);
  }
}

// Updates the number badge on the Filters button.
function updateFilterCount() {
  // The badge counts what is actively narrowing the view. A half that is switched OFF is a filter
  // (it hides things), so it counts; both halves on is the default and counts for nothing.
  const hidden = (ui.showRated ? 0 : 1) + (ui.showUnrated ? 0 : 1);
  const n = ui.activeCategories.size + ui.activeTiers.size + hidden + (state.discount !== 0.5 ? 1 : 0);
  const badge = document.getElementById("filterCount");
  if (n > 0) {
    badge.hidden = false;
    badge.textContent = n;
  } else {
    badge.hidden = true;
  }
}

// Resets search, categories, familiarity and the show/hide switches to their defaults.
function clearAllFilters() {
  ui.query = "";
  document.getElementById("searchInput").value = "";
  ui.activeCategories.clear();
  ui.activeTiers.clear();
  ui.showRated = true;
  ui.showUnrated = true;
  renderCategoryChips();
  renderTierChips();
  renderShowChips();
  updateFilterCount();
  renderGrid();
}

document.getElementById("filterToggle").addEventListener("click", toggleFilterPanel);

// Opens or closes the Filters panel.
function toggleFilterPanel() {
  if (document.getElementById("filterPanel")) {
    closeFilterPanel();
    return;
  }
  closeSettings();
  openFilterPanel();
}

// A small pill that floats above a range slider's thumb and shows the live value while the
// person is dragging or using the keyboard, so they see what they are about to set before they
// commit to it. Hidden the rest of the time so the UI stays quiet.
function bindRateReadout(slider, { onInput, onCommit, format } = {}) {
  const pill = document.createElement("span");
  pill.className = "rate-live";
  pill.setAttribute("aria-hidden", "true");
  slider.insertAdjacentElement("afterend", pill);
  const fmt = format || ((v) => v);
  const place = () => {
    const min = parseFloat(slider.min || 0),
      max = parseFloat(slider.max || 100);
    const pct = max > min ? (parseFloat(slider.value) - min) / (max - min) : 0;
    pill.style.left = pct * 100 + "%";
    pill.textContent = fmt(slider.value);
  };
  const show = () => {
    place();
    pill.classList.add("show");
  };
  const hide = () => pill.classList.remove("show");
  slider.addEventListener("input", () => {
    place();
    if (onInput) onInput(slider.value);
  });
  slider.addEventListener("pointerdown", show);
  slider.addEventListener("keydown", show);
  slider.addEventListener("focus", show);
  slider.addEventListener("pointerup", hide);
  slider.addEventListener("touchend", hide);
  slider.addEventListener("blur", hide);
  slider.addEventListener("change", () => {
    hide();
    if (onCommit) onCommit(slider.value);
  });
  place();
  return { place };
}

// Paints the filled part of a rating slider to match its value.
function setRateFill(input) {
  input.style.setProperty(
    "--pct",
    ((parseFloat(input.value) - parseFloat(input.min || 0)) / (parseFloat(input.max) - parseFloat(input.min || 0))) *
      100 +
      "%"
  );
}

// Builds and shows the Filters panel.
function openFilterPanel() {
  const root = document.getElementById("filterRoot");
  root.innerHTML = i18nHTML`
    <div class="scrim" id="filterScrim"></div>
    <aside class="settings-panel" id="filterPanel" role="dialog" aria-label="Filters">
      <button class="panel-close" id="filterClose" aria-label="Close">&times;</button>
      <h2 class="settings-title">Filters</h2>
      <p class="settings-sub">Narrow the catalogue by category, by which half you want to see, or by how new something is to you. The first two apply to the Garden, your Herbarium and the PDF alike.</p>
      <div class="panel-block"><p class="filter-label">Show</p><div id="showChips" class="chip-row"></div>
        <p class="settings-sub" style="margin:8px 0 0;">Both are on by default. Switch one off to leave that half out of the page and the export.</p></div>
      <div class="panel-block"><p class="filter-label">Category</p><div id="categoryChips" class="chip-row"></div></div>
      <div class="panel-block"><p class="filter-label">How new it is</p><div id="tierChips" class="chip-row"></div>
        <p class="settings-sub" style="margin:8px 0 0;">These bands cover the art forms you have not rated, and they narrow the page and the export as well as the Garden.</p></div>
      <div class="panel-block">
        <p class="filter-label">How far your ratings reach</p>
        <div class="discount-row">
          <span class="rate-wrap"><input id="discountSlider" aria-label="How far your ratings reach" class="rate" type="range" min="0" max="1" step="0.05" value="${state.discount}"></span>
          <span id="discountValue" class="discount-value">${state.discount.toFixed(2)}</span>
        </div>
        <p class="settings-sub" style="margin:8px 0 0;">Higher means each practice you know also counts toward more distant art forms. The middle is the default.</p>
      </div>
    </aside>`;
  document.getElementById("filterClose").addEventListener("click", closeFilterPanel);
  document.getElementById("filterScrim").addEventListener("click", closeFilterPanel);
  renderCategoryChips();
  renderTierChips();
  renderShowChips();

  const slider = document.getElementById("discountSlider");
  const value = document.getElementById("discountValue");
  setRateFill(slider);
  bindRateReadout(slider, {
    format: (v) => parseFloat(v).toFixed(2),
    onInput: (v) => {
      state.discount = parseFloat(v);
      value.textContent = state.discount.toFixed(2);
      setRateFill(slider);
      saveStore();
      updateFilterCount();
      renderGrid();
      if (currentModalId) openDetail(currentModalId, { quiet: true });
    },
  });
}
// Removes the Filters panel.
function closeFilterPanel() {
  document.getElementById("filterRoot").innerHTML = "";
}
