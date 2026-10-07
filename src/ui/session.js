// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

/* SAVE, LOAD AND RESET. Writes the reader's ratings, name, tags, filters, sort and plant seed to a
small JSON file, and reads one back -- including files saved by earlier versions (and by the
app's former name, Bloom), which still load. Anything it cannot place is set aside, never dropped.
Also holds the in-console self-test and the "start over" confirmation. The Herbarium page itself is ui/profile-page.js.
   See docs/architecture.md. */

// ---------------------------------------------------------------------------
// SESSION FILE: save the person's ratings, name, tags, filters and sort as JSON, and
// load one back. Files carry a schema version, are migrated forward on load, and park
// anything this build cannot place instead of dropping it, so a file written by a
// different version of Holotype never loses data silently.
const SESSION_FORMAT = "holotype-session";
// The app was called Bloom before it was called Holotype. Files saved by that version carry the old format tag; they are
// read exactly like new ones, and anything the app writes from now on uses the new tag.
const SESSION_FORMATS_ACCEPTED = [SESSION_FORMAT, "bloom-session"];
const SESSION_SCHEMA = 2; // bump ONLY when a change of meaning would make old readers misread a file
const SESSION_FEATURES = []; // feature tokens this build understands, checked against a file's `requires`
const APP_VERSION = "2026.10"; // informational only, never used for compatibility decisions
const SESSION_LIMITS = { bytes: 5000000, ratings: 5000, itemJson: 2000, name: 60 };
// prettier-ignore
const SESSION_KNOWN_KEYS = [
  "format", "schemaVersion", "version", "appVersion", "exportedAt", "requires", "name", "ratings", "tags",
  "distanceReach", "filters", "sort", "exportSections", "plantSeed", "language", "parked",
];
const SESSION_DERIVED_KEYS = ["profile", "holotype", "classification", "genus", "derived", "stats"]; // informational in files, recomputed here, never trusted
const SESSION_ENTRY_RESERVED = ["id", "name", "rating", "reason", "suggest"];
// Names that changed or disappeared. Append-only: entries are never edited or removed, so old files keep resolving.
const SESSION_ALIASES = {
  renames: { "Horology": "Horology (Watchmaking)", "Sand Mandala": "Ritual Mandala (Sand Painting)" },
  replaced: { "Circus Arts": ["Aerial Arts", "Clowning", "Fire Performance & Flow Arts"] },
};
// One tiny upgrader per schema step, applied in order. Each takes a shallow copy and returns it.
const SESSION_MIGRATIONS = {
  1: (r) => {
    r.schemaVersion = 2;
    return r;
  },
};

let sessionFeedback = null;
let pendingSession = null,
  _sessionNames = null;
// Lowercased art-form name -> id, built once, used to place ratings from files that carry names.
function sessionNameIndex() {
  if (!_sessionNames) {
    _sessionNames = {};
    ART_FORMS.forEach((a) => {
      _sessionNames[String(a.name).trim().toLowerCase()] = a.id;
    });
  }
  return _sessionNames;
}
// The current name of an art-form id ('' when unknown).
function sessionArtName(id) {
  const a = ART_FORMS.find((x) => x.id === id);
  return a ? a.name : "";
}

// id first, then name, then rename alias. Anything else is parked with a suggestion, never dropped.
function sessionResolve(e) {
  if (typeof e.id === "string" && e.id in BY_ID) return { id: e.id };
  const nm = typeof e.name === "string" ? e.name.trim() : "",
    idx = sessionNameIndex();
  if (nm && idx[nm.toLowerCase()]) return { id: idx[nm.toLowerCase()] };
  const ren = SESSION_ALIASES.renames[nm];
  if (ren && idx[ren.toLowerCase()]) return { id: idx[ren.toLowerCase()] };
  if (SESSION_ALIASES.replaced[nm]) return { park: "replaced", suggest: SESSION_ALIASES.replaced[nm].slice() };
  return { park: "unknown" };
}
// Splits a file's ratings into those that resolve to an art form here and those that must be set aside, with
// reasons.
function sessionRatingEntries(list, report) {
  const resolved = [],
    parked = [];
  list.slice(0, SESSION_LIMITS.ratings).forEach((e) => {
    if (!e || typeof e !== "object") {
      report.ignored.push("a rating entry that was not an object");
      return;
    }
    const label = e.name || e.id || sourceText("an entry"),
      v = Math.round(Number(e.rating));
    if (!(v >= 1 && v <= 10)) {
      report.ignored.push(`${label}: no usable rating`);
      return;
    }
    const extras = {};
    Object.keys(e).forEach((k) => {
      if (!SESSION_ENTRY_RESERVED.includes(k)) {
        try {
          if (JSON.stringify(e[k]).length <= SESSION_LIMITS.itemJson) extras[k] = e[k];
        } catch (_) {
          /* skip */
        }
      }
    });
    const r = sessionResolve(e);
    if (r.id) resolved.push({ id: r.id, rating: v, extras });
    else
      parked.push(
        Object.assign(
          {
            id: typeof e.id === "string" ? e.id : undefined,
            name: typeof e.name === "string" ? e.name : undefined,
            rating: v,
            reason: r.park,
            suggest: r.suggest,
          },
          extras
        )
      );
  });
  return { resolved, parked };
}
// Validates one colour tag from a file. Returns the rule, or {park: reason}.
function sessionTagRule(t) {
  if (!t || typeof t !== "object") return { park: sourceText("not a tag rule") };
  const color = typeof t.color === "string" && /^#[0-9a-f]{3,8}$/i.test(t.color) ? t.color : "#8a6d3b";
  if (t.dimension === "distance")
    return { rule: normalizeColorRule({ dimension: "distance", min: t.min, max: t.max, color }) };
  const D = TAG_DIMENSIONS[t.dimension];
  if (!D) return { park: sourceText("unknown dimension") };
  let vals = Array.isArray(t.values) ? t.values : t.value != null ? [t.value] : [];
  vals = vals.map((v) => (t.dimension === "category" && CATEGORY_RENAMES[v] ? CATEGORY_RENAMES[v] : v));
  const known = vals.filter((v) => D.values.includes(v)),
    unknown = vals.filter((v) => !D.values.includes(v));
  if (!known.length) return { park: sourceText("no recognised values") };
  return {
    rule: { dimension: t.dimension, values: known, color },
    leftover: unknown.length
      ? { dimension: t.dimension, values: unknown, color, reason: sourceText("some values not recognised") }
      : null,
  };
}

// Pure: text -> { norm, report } | { error }. `norm` holds ONLY the sections the file contains.
function sessionNormalize(raw) {
  const report = {
    schema: { from: null, to: SESSION_SCHEMA, newer: false, upgraded: false },
    loaded: {},
    parked: [],
    ignored: [],
    unknownFields: [],
    refused: null,
  };
  if (!raw || typeof raw !== "object" || Array.isArray(raw) || !SESSION_FORMATS_ACCEPTED.includes(raw.format))
    return { error: sourceText("That doesn't look like a Holotype session file.") };
  const req = Array.isArray(raw.requires) ? raw.requires.filter((x) => typeof x === "string") : [];
  const missing = req.filter((x) => !SESSION_FEATURES.includes(x));
  if (missing.length)
    return {
      error: `This file needs features this version of Holotype doesn't have (${missing.slice(0, 5).join(", ")}). Nothing was changed.`,
    };
  let ver = Number.isInteger(raw.schemaVersion) ? raw.schemaVersion : Number.isInteger(raw.version) ? raw.version : 1;
  report.schema.from = ver;
  let doc = Object.assign({}, raw);
  if (ver > SESSION_SCHEMA) report.schema.newer = true;
  else
    while (ver < SESSION_SCHEMA) {
      try {
        if (SESSION_MIGRATIONS[ver]) doc = SESSION_MIGRATIONS[ver](doc);
      } catch (_) {
        /* tolerant: carry on with what we have */
      }
      ver++;
      report.schema.upgraded = true;
    }
  const norm = { extra: {} };
  if (typeof doc.name === "string") norm.name = doc.name.trim().slice(0, SESSION_LIMITS.name);
  const pk = doc.parked && typeof doc.parked === "object" && !Array.isArray(doc.parked) ? doc.parked : {};
  const rList = (Array.isArray(doc.ratings) ? doc.ratings : []).concat(Array.isArray(pk.ratings) ? pk.ratings : []);
  if (Array.isArray(doc.ratings) || Array.isArray(pk.ratings)) {
    const { resolved, parked } = sessionRatingEntries(rList, report);
    norm.ratings = { resolved, parked };
    report.loaded.ratings = resolved.length;
    parked.forEach((p) =>
      report.parked.push({ name: p.name || p.id || "unnamed", rating: p.rating, reason: p.reason, suggest: p.suggest })
    );
  }
  const tList = (Array.isArray(doc.tags) ? doc.tags : []).concat(Array.isArray(pk.tags) ? pk.tags : []);
  if (Array.isArray(doc.tags) || Array.isArray(pk.tags)) {
    const rules = [],
      parkedTags = [];
    tList.forEach((t) => {
      let r;
      try {
        r = sessionTagRule(t);
      } catch (_) {
        r = { park: sourceText("could not be read") };
      }
      if (r.rule) {
        rules.push(r.rule);
        if (r.leftover) parkedTags.push(r.leftover);
      } else if (t && typeof t === "object") parkedTags.push(Object.assign({}, t, { reason: r.park }));
      else report.ignored.push("a tag that was not an object");
    });
    norm.tags = { rules, parked: parkedTags };
    report.loaded.tags = rules.length;
    if (parkedTags.length)
      report.ignored.push(
        `${parkedTags.length} tag rule${parkedTags.length === 1 ? "" : "s"} this version can't place (kept aside)`
      );
  }
  if (Number.isFinite(doc.distanceReach)) norm.distanceReach = Math.min(1, Math.max(0, doc.distanceReach));
  if (doc.filters && typeof doc.filters === "object") {
    const f = doc.filters,
      out = {};
    if (typeof f.search === "string") out.query = f.search.slice(0, 200);
    if (Array.isArray(f.categories)) {
      out.categories = f.categories.filter((c) => TAG_DIMENSIONS.category.values.includes(c));
      if (out.categories.length < f.categories.length) report.ignored.push("some category filters no longer exist");
    }
    if (Array.isArray(f.familiarity)) {
      out.tiers = f.familiarity.filter((t) => t in TIER_LABELS);
      if (out.tiers.length < f.familiarity.length) report.ignored.push("some familiarity filters not recognised");
    }
    // `show` is newer than the session format. A file without it keeps both halves visible, which
    // is the same thing the pre-switch app did, so old sessions open looking exactly as they saved.
    if (f.show && typeof f.show === "object") {
      if (typeof f.show.rated === "boolean") out.showRated = f.show.rated;
      if (typeof f.show.unrated === "boolean") out.showUnrated = f.show.unrated;
    }
    norm.filters = out;
  }
  if (typeof doc.sort === "string") {
    if (doc.sort in SORT_LABELS) norm.sort = doc.sort;
    else report.ignored.push(`sort order "${String(doc.sort).slice(0, 30)}" not recognised`);
  }
  if (doc.exportSections && typeof doc.exportSections === "object") {
    const base = defaultExportSections(),
      out = {};
    Object.keys(base).forEach((k) => {
      if (typeof doc.exportSections[k] === "boolean") out[k] = doc.exportSections[k];
    });
    norm.exportSections = out;
  }
  if (typeof doc.plantSeed === "string" && doc.plantSeed) norm.plantSeed = doc.plantSeed.slice(0, 100);
  // The language the file was saved in. Files from before this field carry none, and loading one leaves the language alone.
  if (typeof doc.language === "string" && doc.language) {
    if (doc.language in LANGUAGES) norm.language = doc.language;
    else report.ignored.push(`language "${doc.language.slice(0, 20)}" not available`);
  }
  Object.keys(doc).forEach((k) => {
    if (SESSION_KNOWN_KEYS.includes(k) || SESSION_DERIVED_KEYS.includes(k)) return;
    try {
      if (JSON.stringify(doc[k]).length <= 50000) {
        norm.extra[k] = doc[k];
        report.unknownFields.push(k);
      }
    } catch (_) {
      /* skip */
    }
  });
  return { norm, report };
}
// File text -> parsed and normalised session, or {error}. Refuses oversized or non-JSON files.
function parseSessionFile(text) {
  if (typeof text !== "string" || text.length > SESSION_LIMITS.bytes)
    return { error: sourceText("That file is too large to be a Holotype session.") };
  let raw;
  try {
    raw = JSON.parse(text);
  } catch (_) {
    return { error: sourceText("That file isn't valid JSON.") };
  }
  return sessionNormalize(raw);
}

// The current state as a plain object, for building a file or merging.
function sessionSnapshot() {
  return {
    mastery: state.mastery,
    ratingExtras: state.ratingExtras || {},
    parked: state.parked || { ratings: [], tags: [] },
    sessionExtra: state.sessionExtra || {},
    colorRules: state.colorRules,
    exporterName: state.exporterName,
    discount: state.discount,
    exportSections: state.exportSections,
    plantSeed: state.plantSeed,
    language: currentLang,
    ui: {
      query: ui.query,
      categories: [...ui.activeCategories],
      tiers: [...ui.activeTiers],
      sort: ui.sort,
      showRated: ui.showRated,
      showUnrated: ui.showUnrated,
    },
  };
}
// Pure: (current, norm, mode) -> next. Only sections present in `norm` are touched. mode: "replace" | "merge".
function sessionMerge(cur, norm, mode) {
  const next = JSON.parse(JSON.stringify(cur)),
    merge = mode === "merge";
  const dedupeKey = (p) => String(p.id || p.name || JSON.stringify(p));
  if (norm.ratings) {
    if (!merge) {
      next.mastery = {};
      next.ratingExtras = {};
      next.parked.ratings = [];
    }
    norm.ratings.resolved.forEach((r) => {
      next.mastery[r.id] = r.rating;
      next.ratingExtras[r.id] = r.extras;
    });
    const seen = new Map(next.parked.ratings.map((p) => [dedupeKey(p), p]));
    norm.ratings.parked.forEach((p) => seen.set(dedupeKey(p), p));
    next.parked.ratings = [...seen.values()].filter((p) => !(typeof p.id === "string" && p.id in next.mastery));
  }
  if (norm.tags) {
    if (!merge) {
      next.colorRules = norm.tags.rules.slice();
      next.parked.tags = norm.tags.parked.slice();
    } else {
      const keyOf = (r) => r.dimension + "|" + JSON.stringify(r.values) + "|" + (r.min ?? "") + "|" + (r.max ?? "");
      norm.tags.rules.forEach((r) => {
        const hit = next.colorRules.find((x) => keyOf(x) === keyOf(r));
        if (hit) hit.color = r.color;
        else next.colorRules.push(r);
      });
      next.parked.tags = next.parked.tags.concat(norm.tags.parked);
    }
  }
  if (typeof norm.name === "string" && (!merge || norm.name)) next.exporterName = norm.name;
  if (norm.distanceReach !== undefined) next.discount = norm.distanceReach;
  if (norm.exportSections) Object.assign(next.exportSections, norm.exportSections);
  if (norm.language) next.language = norm.language;
  if (norm.plantSeed) next.plantSeed = norm.plantSeed;
  else if (!merge && norm.ratings) {
    // Files saved before the seed was written carry none, so every such file loaded on one device inherited that
    // device's seed: same palette and same small companion for every person. Derive one from the file instead.
    let h = 2166136261;
    const key = (norm.name || "") + "|" + Object.keys(next.mastery).sort().join(",");
    for (let i = 0; i < key.length; i++) {
      h ^= key.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    next.plantSeed = "f" + (h >>> 0).toString(36);
  }
  if (norm.filters) {
    const u = next.ui,
      f = norm.filters;
    if (f.query !== undefined) u.query = f.query;
    if (f.categories) u.categories = f.categories;
    if (f.tiers) u.tiers = f.tiers;
    if (typeof f.showRated === "boolean") u.showRated = f.showRated;
    if (typeof f.showUnrated === "boolean") u.showUnrated = f.showUnrated;
  }
  if (norm.sort) next.ui.sort = norm.sort;
  next.sessionExtra = merge ? Object.assign({}, next.sessionExtra, norm.extra) : Object.assign({}, norm.extra);
  return next;
}
// Pure: snapshot -> the file object. Unknown keys seen earlier are written back FIRST so known keys always win.
function sessionBuild(cur) {
  const out = {};
  Object.keys(cur.sessionExtra || {}).forEach((k) => {
    if (!SESSION_KNOWN_KEYS.includes(k)) out[k] = cur.sessionExtra[k];
  });
  Object.assign(out, {
    format: SESSION_FORMAT,
    schemaVersion: SESSION_SCHEMA,
    appVersion: APP_VERSION,
    exportedAt: new Date().toISOString(),
    requires: [],
    name: cur.exporterName || "",
    ratings: Object.entries(cur.mastery)
      .filter(([id, v]) => v > 0 && id in BY_ID)
      .map(([id, v]) => Object.assign({ id, name: sessionArtName(id), rating: v }, cur.ratingExtras[id] || {})),
    tags: cur.colorRules,
    distanceReach: cur.discount,
    filters: {
      search: cur.ui.query,
      categories: cur.ui.categories,
      familiarity: cur.ui.tiers,
      show: { rated: cur.ui.showRated !== false, unrated: cur.ui.showUnrated !== false },
    },
    sort: cur.ui.sort,
    exportSections: cur.exportSections,
    plantSeed: cur.plantSeed,
    language: cur.language || "en",
  });
  const pr = cur.parked.ratings,
    pt = cur.parked.tags;
  if (pr.length || pt.length)
    out.parked = Object.assign({}, pr.length ? { ratings: pr } : {}, pt.length ? { tags: pt } : {});
  return out;
}
// The object that is written to a session file.
function sessionFileData() {
  return sessionBuild(sessionSnapshot());
}

// Retry aside-kept ratings whenever the app starts or a file loads: an art form that came back, or an alias added in a newer
// build, re-attaches its rating. Existing ratings are never overwritten by a retried one.
function sessionReconcile() {
  if (!state.parked) state.parked = { ratings: [], tags: [] };
  if (!state.ratingExtras) state.ratingExtras = {};
  const rep = { ignored: [] },
    list = state.parked.ratings;
  if (!list.length) return 0;
  const { resolved, parked } = sessionRatingEntries(list, rep);
  let moved = 0;
  resolved.forEach((r) => {
    if (!(r.id in state.mastery)) {
      state.mastery[r.id] = r.rating;
      state.ratingExtras[r.id] = r.extras;
      moved++;
    }
  });
  state.parked.ratings = parked;
  if (moved) saveStore();
  return moved;
}
sessionReconcile();

// Shows a message under the session buttons.
function setSessionStatus(msg, isErr) {
  const key = typeof msg === "function" ? null : i18nSourceText(msg);
  sessionFeedback = { render: typeof msg === "function" ? msg : () => translateSessionMessage(key), html: false, isErr };
  msg = sessionFeedback.render();
  const el = document.getElementById("sessionStatus");
  if (!el) return;
  el.className = "session-status" + (isErr ? " err" : "");
  el.textContent = msg;
}
// HTML for the load report: what was loaded, set aside or ignored.
function sessionReportHTML(report, headline) {
  const li = (arr) => arr.map((x) => `<li>${esc(x)}</li>`).join("");
  let h = `<p>${esc(headline)}</p>`;
  if (report.schema.newer)
    h += i18nHTML`<p class="muted">This file was made by a newer version of Holotype. Everything this version understands was loaded, and the rest was kept aside.</p>`;
  else if (report.schema.upgraded)
    h += i18nHTML`<p class="muted">This file came from an older version; it was upgraded as it loaded.</p>`;
  if (report.parked.length)
    h += i18nHTML`<details><summary>${i18nCount(report.parked.length, "rating", "ratings")} kept aside</summary><p class="muted">These art forms aren't in this version. They stay in your session and come back if the art form returns.</p><ul>${li(report.parked.map((p) => `${p.name} (${p.rating}/10)${p.suggest ? tx(", replaced by ") + p.suggest.join(", ") : ""}`))}</ul></details>`;
  if (report.ignored.length)
    h += i18nHTML`<details><summary>${i18nCount(report.ignored.length, "item", "items")} skipped</summary><ul>${li(report.ignored.slice(0, 20).map(translateSessionMessage))}</ul></details>`;
  if (report.unknownFields.length)
    h += i18nHTML`<p class="muted">${i18nCount(report.unknownFields.length, "unfamiliar field", "unfamiliar fields")} (${esc(report.unknownFields.slice(0, 5).join(", "))}) were kept and will be included when you save again.</p>`;
  return h;
}
// Applies a normalised file to the app. `mode` is 'replace' or 'merge'.
function applySession(norm, report, mode) {
  const next = sessionMerge(sessionSnapshot(), norm, mode);
  state.mastery = next.mastery;
  state.ratingExtras = next.ratingExtras;
  state.parked = next.parked;
  state.sessionExtra = next.sessionExtra;
  state.colorRules = next.colorRules;
  state.exporterName = next.exporterName;
  state.discount = next.discount;
  state.exportSections = next.exportSections;
  state.plantSeed = next.plantSeed;
  ui.query = next.ui.query;
  ui.activeCategories = new Set(next.ui.categories);
  ui.activeTiers = new Set(next.ui.tiers);
  ui.sort = next.ui.sort;
  // Older session files predate these switches, so fall back to visible rather than to hidden.
  ui.showRated = next.ui.showRated !== false;
  ui.showUnrated = next.ui.showUnrated !== false;
  sessionReconcile();
  saveStore();
  document.getElementById("searchInput").value = ui.query;
  if (next.language && next.language !== currentLang) setLanguage(next.language);
  sortSelect.value = ui.sort;
  closeFilterPanel();
  closeSettings();
  updateFilterCount();
  renderGrid();
  renderProfilePage();
  const headline = () => {
  const parts = [];
  if (norm.ratings)
    parts.push(`${i18nCount(norm.ratings.resolved.length, "rating", "ratings")}`);
  if (norm.tags) parts.push(`${i18nCount(norm.tags.rules.length, "tag", "tags")}`);
  if (norm.filters || norm.sort) parts.push(tx("filters and sort order"));
  if (typeof norm.name === "string" && norm.name) parts.push(tx`the name ${norm.name}`);
  return parts.length
        ? tx`${mode === "merge" ? tx("Merged") : tx("Loaded")} ${parts.join(", ")}. Anything the file didn't mention was left as it was.`
        : tx("That file had nothing this version could use. Nothing was changed.");
  };
  const el = document.getElementById("sessionStatus");
  if (el) {
    el.className = "session-status";
    sessionFeedback = { render: () => sessionReportHTML(report, headline()), html: true, isErr: false };
    el.innerHTML = sessionFeedback.render();
  }
}
// Downloads the session as holotype-session-<name>-<date>.json.
async function saveSessionFile() {
  const json = JSON.stringify(sessionFileData(), null, 2);
  const nm = (state.exporterName || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
  const filename = `holotype-session${nm ? "-" + nm : ""}-${new Date().toISOString().slice(0, 10)}.json`;
  try {
    const dl = window.claude && window.claude.use ? await window.claude.use("downloads") : null;
    if (dl) {
      await dl.save({ filename, data: json });
      setSessionStatus(() => tx`Saved ${filename}.`);
      return;
    }
  } catch (err) {
    if (err && err.code === "declined") {
      setSessionStatus(tx("Save cancelled."));
      return;
    }
  }
  try {
    const url = URL.createObjectURL(new Blob([json], { type: "application/json" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
    setSessionStatus(() => tx`Saved ${filename}.`);
  } catch (_) {
    setSessionStatus(tx("Couldn't save the file in this browser."), true);
  }
}
// Attaches the save, load and clear handlers of the session card.
function wireSessionCard() {
  const input = document.getElementById("loadSessionInput");
  document.getElementById("saveSessionBtn").addEventListener("click", saveSessionFile);
  document.getElementById("loadSessionBtn").addEventListener("click", () => input.click());
  input.addEventListener("change", async () => {
    const file = input.files[0];
    input.value = "";
    if (!file) return;
    let res;
    try {
      res = parseSessionFile(await file.text());
    } catch (_) {
      res = { error: tx("Couldn't read that file.") };
    }
    if (res.error) {
      setSessionStatus(res.error, true);
      return;
    }
    const cur = Object.keys(state.mastery).length;
    if (!cur || !res.norm.ratings) {
      applySession(res.norm, res.report, "replace");
      return;
    }
    pendingSession = res;
    renderSessionChoice();
  });
}

// Conformance checks, runnable from the console: holotypeSessionSelfTest(). They use only the pure functions, so they never touch your data.
function sessionSelfTest() {
  const blank = () => ({
    mastery: {},
    ratingExtras: {},
    parked: { ratings: [], tags: [] },
    sessionExtra: {},
    colorRules: [],
    exporterName: "",
    discount: 0.5,
    exportSections: defaultExportSections(),
    plantSeed: "",
    ui: { query: "", categories: [], tiers: [], sort: "novelty_desc", showRated: true, showUnrated: true },
  });
  const [a, b] = [ART_FORMS[0], ART_FORMS[1]],
    res = [],
    t = (name, pass) => res.push({ name, pass: !!pass });
  const run = (o, cur, mode) => {
    const r = sessionNormalize(o);
    return r.error ? r : Object.assign(r, { next: sessionMerge(cur || blank(), r.norm, mode || "replace") });
  };
  const legacy = run({
    format: SESSION_FORMAT,
    version: 1,
    name: "L",
    ratings: [
      { id: a.id, name: a.name, rating: 5 },
      { name: "Horology", rating: 4 },
      { name: "Circus Arts", rating: 3 },
      { name: "No Such Thing", rating: 2 },
    ],
    tags: [{ dimension: "cost", values: ["low"], color: "#ff0000" }],
    sort: "name_asc",
  });
  t("v1 file loads and upgrades", !legacy.error && legacy.report.schema.upgraded && legacy.report.schema.from === 1);
  t(
    "renamed art form resolves by alias",
    legacy.next.mastery[ART_FORMS.find((x) => x.name === "Horology (Watchmaking)").id] === 4
  );
  t(
    "replaced art form is parked with suggestions",
    legacy.next.parked.ratings.some((p) => p.name === "Circus Arts" && p.suggest && p.suggest.length === 3)
  );
  t(
    "unknown art form is parked, not dropped",
    legacy.next.parked.ratings.some((p) => p.name === "No Such Thing")
  );
  const fut = run({
    format: SESSION_FORMAT,
    schemaVersion: 9,
    mood: "x",
    ratings: [{ id: a.id, rating: 7, liking: 9 }, null, { id: b.id, rating: "abc" }],
    tags: [
      { dimension: "vibe", values: ["x"], color: "#000" },
      { dimension: "cost", values: ["low", "galactic"], color: "#00ff00" },
    ],
    sort: "zzz",
    filters: { categories: ["Nope"] },
  });
  t("newer schema still loads", !fut.error && fut.report.schema.newer && fut.next.mastery[a.id] === 7);
  t("unknown per-rating field is kept", fut.next.ratingExtras[a.id].liking === 9);
  t("unknown top-level field is kept", fut.next.sessionExtra.mood === "x");
  t("bad entries are skipped without failing", fut.report.ignored.length >= 2 && !(b.id in fut.next.mastery));
  t(
    "unknown tag dimension and value are kept aside",
    fut.next.parked.tags.length === 2 &&
      fut.next.colorRules.length === 1 &&
      fut.next.colorRules[0].values.join() === "low"
  );
  t("unknown sort is ignored, not applied", fut.next.ui.sort === "novelty_desc");
  const out = sessionBuild(fut.next);
  t(
    "round trip preserves extras, unknown fields and parked data",
    out.mood === "x" &&
      out.ratings[0].liking === 9 &&
      out.parked.tags.length === 2 &&
      out.schemaVersion === SESSION_SCHEMA
  );
  const again = run(out);
  t(
    "re-reading our own output is lossless",
    !again.error && again.next.ratingExtras[a.id].liking === 9 && again.next.parked.tags.length === 2
  );
  const req = sessionNormalize({ format: SESSION_FORMAT, requires: ["quantum-ratings"] });
  t("unsupported required feature is refused", !!req.error);
  const cur = blank();
  cur.mastery[a.id] = 3;
  cur.mastery[b.id] = 8;
  cur.exporterName = "Keep";
  const part = run({ format: SESSION_FORMAT, name: "Z" }, cur);
  t("partial file touches only what it contains", part.next.mastery[b.id] === 8 && part.next.exporterName === "Z");
  const mg = run({ format: SESSION_FORMAT, ratings: [{ id: a.id, rating: 6 }] }, cur, "merge"),
    rp = run({ format: SESSION_FORMAT, ratings: [{ id: a.id, rating: 6 }] }, cur, "replace");
  t("merge keeps other ratings and lets the file win", mg.next.mastery[a.id] === 6 && mg.next.mastery[b.id] === 8);
  t("replace swaps the ratings section", rp.next.mastery[a.id] === 6 && !(b.id in rp.next.mastery));
  t("non-session JSON is rejected", !!sessionNormalize({ hello: 1 }).error && !!parseSessionFile("nope").error);
  return res;
}
window.holotypeSessionSelfTest = sessionSelfTest;

// Destructive, so it sits alone as an icon in the header and is gated behind a confirmation that
// names exactly what gets cleared - meant for handing a shared device to the next person.
function confirmReset() {
  const n = ART_FORMS.filter((a) => state.mastery[a.id] > 0).length;
  closeConfirm();
  const root = document.createElement("div");
  root.id = "confirmRoot";
  root.innerHTML = i18nHTML`
    <div class="confirm-backdrop" id="confirmBackdrop">
      <div class="confirm-box" role="alertdialog" aria-modal="true" aria-labelledby="confirmTitle" aria-describedby="confirmBody">
        <h3 id="confirmTitle">Start over for the next person?</h3>
        <p id="confirmBody">This clears ${i18nCount(n, "rating", "ratings")}, all color and distance tags, and the name on this device, so the next person starts with a blank garden. Your light/dark and export settings stay. This can't be undone.</p>
        <div class="confirm-actions">
          <button type="button" class="confirm-cancel" id="confirmCancel">Keep everything</button>
          <button type="button" class="confirm-ok" id="confirmOk">Reset</button>
        </div>
      </div>
    </div>`;
  document.body.appendChild(root);
  document.getElementById("confirmCancel").addEventListener("click", closeConfirm);
  document.getElementById("confirmBackdrop").addEventListener("click", (e) => {
    if (e.target.id === "confirmBackdrop") closeConfirm();
  });
  document.getElementById("confirmOk").addEventListener("click", () => {
    closeConfirm();
    resetAllData();
  });
  document.getElementById("confirmCancel").focus();
}
// Removes the confirmation dialog.
function closeConfirm() {
  const r = document.getElementById("confirmRoot");
  if (r) r.remove();
}

function renderSessionChoice() {
  if (!pendingSession) return;
    const n = pendingSession.norm.ratings.resolved.length,
      el = document.getElementById("sessionStatus");
    el.className = "session-status";
    el.innerHTML = i18nHTML`<p>The file has ${i18nCount(n, "rating", "ratings")}${pendingSession.norm.name ? tx` for ${esc(pendingSession.norm.name)}` : ""}, and you have ${Object.keys(state.mastery).length}. <b>Replace</b> swaps in everything the file contains. <b>Merge</b> adds its ratings to yours and lets the file win where both rate the same art form. Anything the file doesn't mention is left alone either way.</p><div class="session-actions"><button type="button" class="add-rule-btn" id="sessionReplace">Replace</button><button type="button" class="add-rule-btn" id="sessionMerge">Merge</button><button type="button" class="add-rule-btn" id="sessionCancel">Cancel</button></div>`;
    const go = (mode) => {
      const s = pendingSession;
      pendingSession = null;
      applySession(s.norm, s.report, mode);
    };
    document.getElementById("sessionReplace").addEventListener("click", () => go("replace"));
    document.getElementById("sessionMerge").addEventListener("click", () => go("merge"));
    document.getElementById("sessionCancel").addEventListener("click", () => {
      pendingSession = null;
      setSessionStatus(tx("Load cancelled. Nothing changed."));
    });
}

// Re-render saved feedback without losing a pending import or encoding its HTML.
function restoreSessionFeedback() {
  const el = document.getElementById("sessionStatus");
  if (!el || !sessionFeedback) return;
  el.className = "session-status" + (sessionFeedback.isErr ? " err" : "");
  if (sessionFeedback.html) el.innerHTML = sessionFeedback.render();
  else el.textContent = sessionFeedback.render();
}

// Parsers and compatibility reports remain canonical English data. Localize only
// their presentation, preserving IDs, unrecognized fields and user-provided names.
function translateSessionMessage(message) {
  if (currentLang === "en") return message;
  const exact = t(message);
  if (exact !== message) return exact;
  let m;
  if ((m = message.match(/^(.*): no usable rating$/))) return tx`${m[1]}: no usable rating`;
  if ((m = message.match(/^language "(.*)" not available$/))) return tx`language "${m[1]}" not available`;
  if ((m = message.match(/^sort order "(.*)" not recognised$/))) return tx`sort order "${m[1]}" not recognised`;
  if ((m = message.match(/^(\d+) tag rules? this version can't place \(kept aside\)$/))) return tx`${i18nCount(Number(m[1]), "tag rule", "tag rules")} this version can't place (kept aside)`;
  if ((m = message.match(/^This file needs features this version of Holotype doesn't have \((.*)\)\. Nothing was changed\.$/))) return tx`This file needs features this version of Holotype doesn't have (${m[1]}). Nothing was changed.`;
  return message;
}
