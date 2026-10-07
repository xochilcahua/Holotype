// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

/* THE ONE NARROWING LAYER. Search, category, familiarity and tag filters are applied
in exactly one place, and every list in the app -- garden, Herbarium and both PDFs --
reads its rows from here so they can never disagree about what is on screen.
   See docs/architecture.md. */

// ---------------- The wall ----------------
// ONE narrowing layer, shared by every list in the app.
//
// There used to be three separate list builders - the unrated wall, the rated block above it, and
// the Herbarium/export pair - and only the first two honoured the filters. So a category you picked
// narrowed the Garden while the Herbarium page and the PDF still listed the whole catalogue. Any
// new list added here must go through this function or it will drift out of step again.
//
// Applies: search, category, the familiarity tiers, and the show/hide switches. The tiers only make
// sense for things you have not rated - a rated form is familiar by definition - so they narrow the
// unrated half only, and are skipped when there are no ratings to compare against (with nothing
// rated, every form would land in one tier and the filter would look arbitrary).
//
// Returns the two halves already split by rating, already filtered, and already sorted. `rank` lets a
// caller that needs search order keep it.
function narrowedCatalog() {
  const ids = ui.query ? search(ui.query) : ART_FORMS.map((a) => a.id);
  let items = ids.map((id) => BY_ID[id]);
  if (ui.activeCategories.size > 0) items = items.filter((a) => ui.activeCategories.has(a.category));
  const rank = ui.query ? new Map(ids.map((id, i) => [id, i])) : null;
  let unrated = ui.showUnrated ? items.filter((a) => !(state.mastery[a.id] > 0)) : [];
  if (unrated.length && ui.activeTiers.size > 0 && hasRatings()) {
    const nov = computeNovelty(state.mastery, state.discount);
    unrated = unrated.filter((a) => ui.activeTiers.has(nov.byId[a.id].tier));
  }
  return {
    rated: ui.showRated ? items.filter((a) => state.mastery[a.id] > 0) : [],
    unrated,
    rank,
    searching: !!ui.query,
  };
}

// The unrated art forms to show, in the order the current sort asks for.
function computeVisibleList() {
  if (!ui.showUnrated) return [];
  const { unrated, rank } = narrowedCatalog();
  const nov = computeNovelty(state.mastery, state.discount);
  let scored = unrated.map((a) => ({ a, ...nov.byId[a.id] }));
  // The familiarity tiers were already applied by narrowedCatalog, along with search, category and
  // the show/hide switches. Scoring here just attaches the numbers the sort needs.
  // Searching is a lookup, not a browse. Someone who types "ikebana" wants
  // Ikebana first and does not care that Floral Design is closer to their taste,
  // so while a query is active the order search() produced is kept as-is. The
  // sort control still governs the unsearched wall.
  if (rank) {
    scored.sort((x, y) => rank.get(x.a.id) - rank.get(y.a.id));
    return scored;
  }
  // Order by the unrounded novelty, then by how far the art form is from anything you know, so
  // art forms that display the same score still come out in a meaningful order.
  scored.sort((x, y) => {
    // Inside a group (category, tag) or a commonness run, novelty still orders the rows - closest
    // first - so a grouped list is a novelty list cut into sections rather than a flat A-Z.
    const tie = ui.sort === "novelty_desc" ? y.raw - x.raw || y.tie - x.tie : x.raw - y.raw || x.tie - y.tie;
    const k = structuralKey(x.a, y.a);
    if (k !== null) return k || tie || compareArtNames(x.a, y.a);
    if (ui.sort === "novelty_desc") return y.raw - x.raw || y.tie - x.tie || compareArtNames(x.a, y.a);
    if (ui.sort === "novelty_asc") return x.raw - y.raw || x.tie - y.tie || compareArtNames(x.a, y.a);
    return compareArtNames(x.a, y.a);
  });
  return scored;
}

// The rated art forms to show, after the filters and the sort.
function computeRatedList() {
  if (!ui.showRated) return [];
  const { rated, rank } = narrowedCatalog();
  let items = rated;
  // Same rule as the unrated wall: an active query is a lookup, so keep search order.
  if (rank) {
    items.sort((a, b) => rank.get(a.id) - rank.get(b.id));
    return items;
  }
  // Within whatever group the sort defines, the garden still reads strongest first: rating is the
  // tie-breaker, and the name is the final (total) order.
  items.sort((a, b) => bySortThen(a, b, state.mastery[b.id] - state.mastery[a.id]));
  return items;
}

// Draws the 'rated' block above the grid, or hides it when there is nothing to show.
function renderRatedSection() {
  const root = document.getElementById("ratedSection");
  const rated = computeRatedList();
  if (rated.length === 0) {
    root.innerHTML = "";
    return;
  }
  // The heading counts what is actually below it. When a filter hides some of your garden it says
  // "3 of 9", so the number never quietly disagrees with the tiles on screen.
  const total = ART_FORMS.filter((a) => state.mastery[a.id] > 0).length;
  const label = rated.length === total ? tx`${total} rated` : tx`${rated.length} of ${total} rated`;
  root.innerHTML = i18nHTML`<h2 class="group-title">Your garden<span>${label}</span></h2><div class="grid garden" id="ratedGrid"></div><div class="divider"></div>`;
  const grid = document.getElementById("ratedGrid");
  for (const a of rated) grid.appendChild(renderSpec(a, null, null, true));
}

// Redraws whatever is on screen: the garden grid, and the Herbarium page too when it is open.
function renderGrid() {
  renderGardenGrid();
  if (ui.mode === "profile") renderProfilePage();
}
// Draws the rated block, then the grid of unrated art forms.
function renderGardenGrid() {
  renderRatedSection();
  const list = computeVisibleList();
  const grid = document.getElementById("grid");
  const ratedCount = ART_FORMS.filter((a) => state.mastery[a.id] > 0).length;
  const unrated = ART_FORMS.length - ratedCount;
  // Only report "N of M" when something is actually being held back, so the default reads cleanly.
  document.getElementById("resultCount").textContent =
    list.length === unrated ? tx`${unrated} art forms` : tx`${list.length} of ${unrated} art forms`;
  document.getElementById("rateHint").textContent =
    ratedCount === 0
      ? tx("Rate what you already know with the sliders, and Holotype ranks the rest by how new it is to you.")
      : "";

  grid.innerHTML = "";
  if (list.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.style.setProperty("--hue", 262);
    // With "not yet rated" switched off, an empty wall is the switch talking, not a failed search -
    // so it gets its own message pointing at the control that caused it.
    empty.innerHTML = !ui.showUnrated
      ? i18nHTML`${flowerSVG(ART_FORMS[0])}<p>You've switched off <b>Not yet rated</b>, so there's nothing left here. Your rated art forms are still above.</p><button class="pill-btn" id="clearFilters">Show everything again</button>`
      : i18nHTML`${flowerSVG(ART_FORMS[0])}<p>Nothing matches. Clear a filter or try a different search.</p><button class="pill-btn" id="clearFilters">Clear filters and search</button>`;
    grid.appendChild(empty);
    empty.querySelector("#clearFilters").addEventListener("click", clearAllFilters);
    return;
  }
  for (const { a, score, tier, promoted } of list) grid.appendChild(renderSpec(a, score, tier, false, promoted));
}

// One tile (rated or unrated): flower, name, +N badge, tagline, rating slider and tag dots.
function renderSpec(a, score, tier, isRated, promoted) {
  const level = state.mastery[a.id] || 0;
  const neutral = !isRated && !hasRatings();
  const el = document.createElement("article");
  el.className = "spec" + (isRated ? " is-rated" : "");
  el.style.setProperty("--hue", hueFor(a.category));
  el.tabIndex = 0;
  el.setAttribute("role", "button");
  el.setAttribute("aria-label", tx`Open details for ${t(a.name)}`);
  const read = isRated ? i18nHTML`Rated <b>${level}</b>/10` : neutral ? "" : `${tierLabel(tier, promoted)} <b>${score}</b>`;
  // A child form says what it is a kind of, so a wall of 306 rows does not read as 306
  // unrelated options. Depth is carried by the trail's length, not by a numeric prefix.
  const trail = breadcrumb(a);
  const kids = a.childIds ? a.childIds.length : 0;
  el.innerHTML = i18nHTML`
    <div class="mark" title="${esc(t(a.category))}">${ringSVG(isRated ? level * 10 : neutral ? 0 : score)}${flowerSVG(a)}</div>
    <div class="spec-body">
      ${trail.length ? `<p class="spec-trail" data-depth="${trail.length}">${trail.map((name) => esc(t(name))).join(' <span aria-hidden="true">›</span> ')}</p>` : ""}
      <h3 class="spec-name">${esc(t(a.name))}${kids ? i18nHTML`<span class="spec-kids" title="${i18nCount(kids, "more specific form", "more specific forms")} inside this one, shown as their own cards" aria-label="${i18nCount(kids, "more specific form", "more specific forms")} inside this one">+${kids}</span>` : ""}</h3>
      <p class="spec-tag">${esc(t(a.tag || ""))}</p>
      <div class="spec-foot">
        ${read ? `<span class="spec-read" title="${isRated ? tx("Your own rating") : tx("Novelty out of 100: how new this would be to you") + (promoted ? tx(". Among the newest third of what you have not rated.") : "")}">${read}</span>` : ""}
        <span class="rate-wrap"><input class="rate spec-rate" type="range" min="0" max="10" step="1" value="${level}" style="--pct:${level * 10}%" data-id="${a.id}" aria-label="How well you know ${esc(t(a.name))}"></span>
      </div>
    </div>`;

  const colors = colorsForArtForm(a);
  if (colors.length) {
    const tags = document.createElement("span");
    tags.className = "spec-tags";
    tags.innerHTML = colors.map((c) => `<i style="background:${esc(c)}"></i>`).join("");
    el.classList.add("has-tags");
    el.querySelector(".mark").appendChild(tags); // under the ring: that column is empty, so nothing can overlap the name or text
  }

  const slider = el.querySelector("input");
  slider.addEventListener("click", (e) => e.stopPropagation());
  slider.addEventListener("pointerdown", (e) => e.stopPropagation());
  bindRateReadout(slider, {
    format: (v) => `${v}/10`,
    onInput: (v) => {
      v = parseInt(v, 10);
      slider.style.setProperty("--pct", v * 10 + "%");
      if (v > 0) state.mastery[a.id] = v;
      else delete state.mastery[a.id];
      saveStore();
    },
    // Committing re-sorts the grid, which rebuilds every card and used to drop keyboard focus on
    // <body>: the first arrow press rated the form and every press after it did nothing. If this
    // slider held focus, hand it to the rebuilt slider for the same form (it may now be in the
    // rated section). Mouse and touch never hold focus here, so they are unaffected.
    onCommit: () => {
      const hadFocus = document.activeElement === slider;
      renderGrid();
      if (hadFocus) {
        const next = document.querySelector(`input.spec-rate[data-id="${a.id}"]`);
        if (next) next.focus();
      }
    },
  });

  el.addEventListener("click", () => openDetail(a.id));
  el.addEventListener("keydown", (e) => {
    if (e.target !== el) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      openDetail(a.id);
    }
  });
  return el;
}

// The detail view must always open, so a problem in the description text can never take it down.
function safeDescribe(a) {
  try {
    return describeArtForm(a);
  } catch (e) {
    console.warn(tx("Holotype: could not build description for ") + a.name, e);
    return a.name + ".";
  }
}
