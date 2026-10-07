// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

/* COLOUR TAGS. Adding, editing and removing the rules that colour rows by category,
cost, novelty and the rest. Needs the tag dimensions and the narrowed list.
   See docs/architecture.md. */

// ---------------- Color tags ----------------
document.getElementById("settingsToggle").addEventListener("click", toggleSettings);
document.querySelectorAll("#viewToggle button").forEach((b) =>
  b.addEventListener("click", () => {
    if (ui.mode !== b.dataset.mode) setMode(b.dataset.mode);
  })
);
document.getElementById("resetToggle").addEventListener("click", () => confirmReset());

// Opens or closes the Colour tags panel.
function toggleSettings() {
  if (document.getElementById("settingsPanel")) {
    closeSettings();
    return;
  }
  closeFilterPanel();
  openSettings();
}

// Builds and shows the Colour tags panel.
function openSettings() {
  document.getElementById("settingsRoot").innerHTML = i18nHTML`
    <div class="scrim" id="settingsScrim"></div>
    <aside class="settings-panel" id="settingsPanel" role="dialog" aria-label="Color tags">
      <button class="panel-close" id="settingsClose" aria-label="Close">&times;</button>
      <h2 class="settings-title">Color tags</h2>
      <p class="settings-sub">Pick a tag (category, cost, space, learning curve, self-taught, or how far an art form sits from your taste) and give it a color. Matching art forms get that color, in the garden and in your Herbarium, and several tags can apply at once.</p>
      <div id="ruleRows"></div>
      <button class="add-rule-btn" id="addRuleBtn">Add a color tag</button>
    </aside>`;
  document.getElementById("settingsClose").addEventListener("click", closeSettings);
  document.getElementById("settingsScrim").addEventListener("click", closeSettings);
  document.getElementById("addRuleBtn").addEventListener("click", () => {
    state.colorRules.push({ dimension: "category", values: [TAG_DIMENSIONS.category.values[0]], color: "#7FA8B8" });
    saveStore();
    renderRuleRows();
    renderGrid();
  });
  renderRuleRows();
}

// Holotype's own palette, reused so a tag's color always feels drawn from the same system as the
// category hues on every card rather than an arbitrary pick off a raw color wheel. Converted to
// hex lazily (and cached) since the stored rule format is a plain hex string.
const SWATCH_HUES = [10, 38, 68, 100, 140, 170, 200, 230, 270, 305, 335];
// rule.color is only ever used as a plain CSS color value (background-color, an inline custom
// property), so there's no need to resolve these to hex - oklch() works directly and stays in
// the same color space as everything else in the app. Hex is only required for the native
// <input type="color"> fallback, handled separately where that's built.
function swatchHexes() {
  return SWATCH_HUES.map((h) => `oklch(0.64 0.13 ${h})`);
}

// Re-render at most once per frame while a slider is being dragged.
let _renderQueued = false;
// Coalesces rapid edits into one re-render per animation frame.
function scheduleRender() {
  if (_renderQueued) return;
  _renderQueued = true;
  requestAnimationFrame(() => {
    _renderQueued = false;
    renderGrid();
  });
}

// Two-handle range slider for a distance tag: 0 = very familiar, 100 = very new. Two native range
// inputs sit on top of each other (only their thumbs take the pointer), so keyboard and touch work
// for free; the handles can meet but never cross.
function buildDualRange(rule, onChange) {
  const wrap = document.createElement("div");
  wrap.className = "dual-range";
  wrap.innerHTML = i18nHTML`
    <div class="dual-track"><div class="dual-fill"></div></div>
    <input type="range" class="dual-lo" min="0" max="100" step="1" aria-label="Closest to your taste (lowest novelty)">
    <input type="range" class="dual-hi" min="0" max="100" step="1" aria-label="Furthest from your taste (highest novelty)">
    <div class="dual-readout"><span class="dual-min"></span><span class="dual-mid">familiar &rarr; new</span><span class="dual-max"></span></div>`;
  const lo = wrap.querySelector(".dual-lo"),
    hi = wrap.querySelector(".dual-hi");
  const fill = wrap.querySelector(".dual-fill");
  const paint = () => {
    lo.value = rule.min;
    hi.value = rule.max;
    fill.style.left = rule.min + "%";
    fill.style.right = 100 - rule.max + "%";
    wrap.querySelector(".dual-min").textContent = rule.min;
    wrap.querySelector(".dual-max").textContent = rule.max;
    // whichever handle is nearer the far end sits on top, so two handles parked together can still be pulled apart
    lo.style.zIndex = rule.min > 50 ? 4 : 3;
    hi.style.zIndex = rule.min > 50 ? 3 : 4;
  };
  lo.addEventListener("input", () => {
    rule.min = Math.min(Number(lo.value), rule.max);
    paint();
    onChange();
  });
  hi.addEventListener("input", () => {
    rule.max = Math.max(Number(hi.value), rule.min);
    paint();
    onChange();
  });
  paint();
  return wrap;
}

// Draws one editable row for each colour rule.
function renderRuleRows() {
  const wrap = document.getElementById("ruleRows");
  if (!wrap) return;
  wrap.innerHTML = "";
  const swatches = swatchHexes();
  state.colorRules.forEach((rule, i) => {
    const row = document.createElement("div");
    row.className = "rule-row";
    row.style.setProperty("--rule-color", rule.color);

    const removeBtn = document.createElement("button");
    removeBtn.className = "rule-remove";
    removeBtn.innerHTML = "&times;";
    removeBtn.title = tx("Remove this tag");
    removeBtn.setAttribute("aria-label", tx("Remove this tag"));
    removeBtn.addEventListener("click", () => {
      state.colorRules.splice(i, 1);
      saveStore();
      renderRuleRows();
      renderGrid();
    });

    const preview = document.createElement("span");
    preview.className = "chip rule-preview";
    const previewDot = document.createElement("i");
    const previewLabel = document.createElement("span");
    preview.appendChild(previewDot);
    preview.appendChild(previewLabel);
    const updatePreview = () => {
      previewDot.style.background = rule.color;
      previewLabel.textContent = ruleLabel(rule);
      row.style.setProperty("--rule-color", rule.color);
    };

    const line1 = document.createElement("div");
    line1.className = "rule-row-line";
    const dimSelect = document.createElement("select");
    dimSelect.className = "rule-select";
    for (const key of Object.keys(TAG_DIMENSIONS)) {
      const opt = document.createElement("option");
      opt.value = key;
      opt.textContent = t(TAG_DIMENSIONS[key].label);
      if (key === rule.dimension) opt.selected = true;
      dimSelect.appendChild(opt);
    }
    const distOpt = document.createElement("option");
    distOpt.value = "distance";
    distOpt.textContent = tx("Distance from your taste");
    if (rule.dimension === "distance") distOpt.selected = true;
    dimSelect.appendChild(distOpt);
    line1.appendChild(dimSelect);

    // One tag can now cover several values of the same dimension at once (e.g. "Space: none,
    // small" as a single colored tag) instead of needing a separate rule per value - toggle any
    // number of these on, together or apart, at least one stays selected.
    const valueChips = document.createElement("div");
    valueChips.className = "value-chip-row";
    const renderValueChips = () => {
      valueChips.innerHTML = "";
      if (rule.dimension === "distance") {
        valueChips.appendChild(
          buildDualRange(rule, () => {
            updatePreview();
            saveStore();
            scheduleRender();
          })
        );
        const hint = document.createElement("p");
        hint.className = "hint-note";
        hint.style.flex = "1 1 100%";
        hint.textContent = hasRatings()
          ? tx("Marks art forms you haven't rated whose novelty score falls in this range.")
          : tx("Distance is measured from what you've rated, so this tag shows up once you rate at least one art form.");
        valueChips.appendChild(hint);
        return;
      }
      TAG_DIMENSIONS[rule.dimension].values.forEach((v) => {
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "value-chip" + (rule.values.includes(v) ? " active" : "");
        chip.textContent = tagValueLabel(rule.dimension, v);
        chip.addEventListener("click", () => {
          if (rule.values.includes(v)) {
            if (rule.values.length === 1) return;
            rule.values = rule.values.filter((x) => x !== v);
          } else {
            rule.values = [...rule.values, v];
          }
          renderValueChips();
          updatePreview();
          saveStore();
          renderGrid();
        });
        valueChips.appendChild(chip);
      });
    };
    renderValueChips();

    dimSelect.addEventListener("change", () => {
      rule.dimension = dimSelect.value;
      if (rule.dimension === "distance") {
        rule.values = [];
        rule.min = 25;
        rule.max = 60;
      } else {
        rule.values = [TAG_DIMENSIONS[rule.dimension].values[0]];
        delete rule.min;
        delete rule.max;
      }
      renderValueChips();
      updatePreview();
      saveStore();
      renderGrid();
    });

    const swatchRow = document.createElement("div");
    swatchRow.className = "swatch-row";
    const swatchBtns = [];
    swatches.forEach((hex) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "swatch-btn";
      btn.style.background = hex;
      btn.setAttribute("aria-label", tx("Use this color"));
      if (hex.toLowerCase() === rule.color.toLowerCase()) btn.classList.add("active");
      btn.addEventListener("click", () => {
        rule.color = hex;
        swatchBtns.forEach((b) => b.classList.toggle("active", b === btn));
        customSwatch.classList.remove("active");
        updatePreview();
        saveStore();
        renderGrid();
      });
      swatchBtns.push(btn);
      swatchRow.appendChild(btn);
    });
    const customSwatch = document.createElement("label");
    customSwatch.className = "swatch-btn swatch-custom";
    customSwatch.title = tx("Pick any color");
    if (!swatches.some((hex) => hex.toLowerCase() === rule.color.toLowerCase())) {
      customSwatch.classList.add("active");
      customSwatch.style.background = rule.color;
    }
    const colorInput = document.createElement("input");
    colorInput.type = "color";
    colorInput.value = /^#[0-9a-f]{6}$/i.test(rule.color) ? rule.color : "#7f8c99";
    colorInput.addEventListener("input", () => {
      rule.color = colorInput.value;
      customSwatch.style.background = rule.color;
      swatchBtns.forEach((b) => b.classList.remove("active"));
      customSwatch.classList.add("active");
      updatePreview();
      saveStore();
      renderGrid();
    });
    customSwatch.appendChild(colorInput);
    swatchRow.appendChild(customSwatch);

    updatePreview();
    row.appendChild(removeBtn);
    row.appendChild(preview);
    row.appendChild(line1);
    row.appendChild(valueChips);
    row.appendChild(swatchRow);
    wrap.appendChild(row);
  });
}
// Removes the Colour tags panel.
function closeSettings() {
  document.getElementById("settingsRoot").innerHTML = "";
}
