// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

/* SAVED SESSIONS. What the reader has done lives in one state object, mirrored to
localStorage on every change; what they are LOOKING at lives in a separate object
that is never persisted, so a reload always lands on the garden with no filters
applied. A rating of an art form this build no longer has is moved aside with a
reason rather than dropped, so a session survives the catalogue changing.
   See docs/architecture.md. */

// ---------------- Persistence ----------------
// Everything the person has done lives in one `state` object, mirrored to localStorage
// under STORE_KEY on every change. The view does NOT: mode, query, sort and filters live in
// `ui`, which is never persisted, so a reload always lands on the garden with no filters
// applied. That is deliberate - a saved session is your ratings and tags, not a screenshot
// of where you happened to be looking.
//
// CATEGORY_RENAMES is the upgrade path for saved tags: fields were renamed during the
// build, and a saved tag still carrying an old name resolves to the new one rather than
// silently matching nothing.
const STORE_KEY = "holotype_state_v1";
// Before the rename the same data lived under this key. loadStore() falls back to it once, and the next save writes the new key,
// so ratings saved in someone's browser under the old name are not lost.
const LEGACY_STORE_KEY = "bloom_state_v1";
const CATEGORY_RENAMES = {
  "Language & Narrative": "Writing & Language",
  "Visual 2D Arts": "Visual Arts",
  "Volumetric & Physical Craft": "Craft & Sculpture",
  "Sonic & Musical": "Music & Sound",
  "Performance & Embodied": "Performance & Movement",
  "Directing & Meta-Architecture": "Directing & Curating",
  "Digital, Systemic & Interactive": "Digital & Interactive",
  "Functional & Product Design": "Design",
  "Culinary, Olfactory & Botanical": "Food, Scent & Plants",
  "Environmental & Land": "Land & Environment",
  "Conceptual, Social & Outsider": "Conceptual & Social",
};

// New sessions start with no colour tags.
function defaultColorRules() {
  return []; // start blank; people add their own color tags from the Color tags panel
}

// A rule may have been saved back when it held one value at a time ({value: "high"}); normalise
// it to the current {values: [...]} shape so old saved tags keep working after the upgrade.
function normalizeColorRule(r) {
  if (r.dimension === "distance") {
    const min = Math.max(0, Math.min(100, Math.round(Number(r.min) || 0)));
    const max = Math.max(min, Math.min(100, Math.round(r.max == null ? 100 : Number(r.max))));
    return { dimension: "distance", values: [], min, max, color: r.color };
  }
  let values = Array.isArray(r.values) ? r.values.slice() : r.value != null ? [r.value] : [];
  values = values.map((v) => (r.dimension === "category" && CATEGORY_RENAMES[v] ? CATEGORY_RENAMES[v] : v));
  if (!values.length) values = [TAG_DIMENSIONS[r.dimension].values[0]];
  return { dimension: r.dimension, values, color: r.color };
}

// Distance tags used to live in their own list; they are ordinary color tags now, so anything
// saved in the old list is carried over into colorRules the first time it loads.
function customRangeToRule(r) {
  return normalizeColorRule({ dimension: "distance", min: r.min, max: r.max, color: r.color || "#8a6d3b" });
}

// The one definition of "this device knows nothing about this person yet". The three
// extra buckets belong to the session system: anything a file referred to that this build
// cannot place is parked there rather than dropped, so nothing is ever lost silently.
function blank() {
  return {
    mastery: {},
    ratingExtras: {},
    parked: { ratings: [], tags: [] },
    sessionExtra: {},
    plantSeed: "",
    discount: 0.5,
    themeChoice: null,
    colorRules: defaultColorRules(),
    exporterName: "",
    exportSections: defaultExportSections(),
  };
}

// Reads the saved state from localStorage (falling back to the key used before the rename), validating every field.
// Ratings for art forms this build no longer has are set aside, not dropped.
function loadStore() {
  try {
    const raw = localStorage.getItem(STORE_KEY) || localStorage.getItem(LEGACY_STORE_KEY);
    if (!raw) throw new Error("empty");
    const parsed = JSON.parse(raw);
    // A rating of an art form this build no longer has is NOT dropped. It is moved aside
    // with a reason, so it can come back if the form returns, and so a save/load round
    // trip through a different build cannot quietly lose someone's work.
    const mastery = {},
      pk = parsed.parked && typeof parsed.parked === "object" ? parsed.parked : {};
    const parkedRatings = Array.isArray(pk.ratings) ? pk.ratings.slice(0, 5000) : [];
    Object.entries(parsed.mastery || {}).forEach(([id, v]) => {
      if (id in BY_ID) mastery[id] = v;
      else parkedRatings.push({ id, rating: v, reason: "unknown" });
    });
    return {
      mastery,
      ratingExtras: parsed.ratingExtras && typeof parsed.ratingExtras === "object" ? parsed.ratingExtras : {},
      parked: { ratings: parkedRatings, tags: Array.isArray(pk.tags) ? pk.tags : [] },
      sessionExtra: parsed.sessionExtra && typeof parsed.sessionExtra === "object" ? parsed.sessionExtra : {},
      plantSeed: typeof parsed.plantSeed === "string" ? parsed.plantSeed : "",
      discount: typeof parsed.discount === "number" ? parsed.discount : 0.5,
      themeChoice: parsed.themeChoice === "light" || parsed.themeChoice === "dark" ? parsed.themeChoice : null,
      colorRules: (parsed.colorRules || defaultColorRules())
        .map(normalizeColorRule)
        .concat((parsed.customRanges || []).map(customRangeToRule)),
      exporterName: typeof parsed.exporterName === "string" ? parsed.exporterName : "",
      exportSections: Object.assign(defaultExportSections(), parsed.exportSections || {}),
    };
  } catch {
    return blank();
  }
}

// Every section defaults on (opt-out), so a first-time export is exactly what it used to be;
// old saved state without this field gets every section filled in via Object.assign above.
function defaultExportSections() {
  return { portrait: true, classification: true, filters: true, garden: true, unexplored: true };
}

// Writes the state to localStorage. If storage is unavailable the app keeps working in memory.
function saveStore() {
  try {
    localStorage.setItem(STORE_KEY, JSON.stringify(state));
    localStorage.removeItem(LEGACY_STORE_KEY);
  } catch (e) {
    /* storage unavailable: the app keeps working in memory */
  }
}

// Starts a fresh garden in English. Keep the device's theme and export preferences.
function resetAllData() {
  sessionFeedback = null;
  pendingSession = null;
  state.mastery = {};
  state.ratingExtras = {};
  state.parked = { ratings: [], tags: [] };
  state.sessionExtra = {};
  state.plantSeed = HolotypePlant.newSeed(); // the next person gets their own plant
  state.colorRules = defaultColorRules();
  state.exporterName = "";
  state.discount = 0.5;
  saveStore();
  ui.query = "";
  ui.activeCategories = new Set();
  ui.activeTiers = new Set();
  ui.sort = "common_desc";
  ui.mode = "garden";
  ui.showRated = true;
  ui.showUnrated = true;
  if (document.getElementById("searchInput")) document.getElementById("searchInput").value = "";
  if (document.getElementById("sortSelect")) document.getElementById("sortSelect").value = "common_desc";
  closeFilterPanel();
  closeSettings();
  updateFilterCount();
  setMode("garden");
  setLanguage("en");
}

// Escapes text for safe insertion into HTML.
function esc(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
