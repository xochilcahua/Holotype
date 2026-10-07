// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

/* THE SHEET THAT OPENS WHEN YOU CLICK A FORM. Describes the practice, shows who its
children are, what it is confusable with, what it is close to, and how common it is.
Needs the catalogue, the model and the wall.
   See docs/architecture.md. */

// ---------------- Detail sheet ----------------
// The modal you get by clicking any flower. Shows the description, the full 33-axis
// fingerprint with the axes that actually distinguish this form called out, the forms
// nearest to it, and the slider. currentModalId survives a re-render so a rating made
// here does not lose the reader's place.
let currentModalId = null;

// Axis labels, in scoring order. The first of each group is the one the classification
// uses; the rest are shown for description only. a6 is explicitly not scored.
const AXIS_LABELS = {
  a1: "Improvised vs. planned",
  a2: "Originates vs. edits",
  a3: "Hand- vs. system-controlled",
  a4: "Interpretive vs. literal",
  a5: "Sensory vs. symbolic",
  a6: "Unique vs. editionable (not used in scoring)",
  a7: "Linguistic vs. tonal/formal content",
  a8: "Organic/living vs. inert/manufactured material",
  a9: "Mark-making/rendering vs. non-rendering skill",
  a10: "Functional/useful vs. purely contemplative",
  a11: "Ritual/traditional vs. secular/exhibition context",
  a12: "Apprenticeship-transmitted vs. self-taught",
  a13: "Physically singular vs. mass-reproducible",
  b1: "Fine vs. gross motor",
  b2: "Safe vs. hazardous materials",
  b3: "Controlled vs. chance-driven",
  b4: "Flat vs. volumetric",
  c1: "Visual",
  c2: "Auditory",
  c3: "Tactile",
  c4: "Olfactory",
  c5: "Gustatory",
  d1: "Solo vs. collaborative",
  d2: "Closed vs. audience-shaped",
  d3: "Irrevocable vs. revisable",
  d4: "Ephemeral vs. archival",
  e1: "Solo/freelance vs. institutional",
  e2: "Niche/hobbyist vs. large commercial scale",
  p1: "Serves music/sound",
  p2: "Serves narrative/literature",
  p3: "Serves visual image-making",
  p4: "Serves movement/the body",
  p5: "Serves food & drink",
  p6: "Serves space/architecture",
  p7: "Serves nature/living systems",
};
// The bar shows how far an art form leans toward the named end.
const AXIS_SHORT = {
  p1: "Music and sound",
  p2: "Story",
  p3: "Image-making",
  p4: "Movement",
  p5: "Food and drink",
  p6: "Space",
  p7: "Nature",
  c1: "Sight",
  c2: "Hearing",
  c3: "Touch",
  c4: "Smell",
  c5: "Taste",
  a1: "Planned ahead",
  a2: "Edits existing",
  a3: "System-driven",
  a4: "Literal",
  a5: "Symbolic",
  b1: "Full-body motion",
  b2: "Hazardous",
  b3: "Chance-driven",
  b4: "Three-dimensional",
  d1: "Collaborative",
  d2: "Audience-shaped",
  d3: "Revisable",
  d4: "Long-lasting",
  a7: "Tone over words",
  a8: "Inert material",
  a9: "Not rendering",
  a10: "Purely expressive",
  a11: "Secular setting",
  a12: "Self-taught",
  a13: "Reproducible",
  e1: "Institutional",
  e2: "Large industry",
};
const PROFILE_GROUPS = [
  { title: "What it serves", axes: ["p1", "p2", "p3", "p4", "p5", "p6", "p7"] },
  { title: "Senses it engages", axes: ["c1", "c2", "c3", "c4", "c5"] },
  { title: "How it is made", axes: ["a1", "a2", "a3", "a4", "a5", "b1", "b2", "b3", "b4", "d1", "d2", "d3", "d4"] },
  { title: "Materials and setting", axes: ["a7", "a8", "a9", "a10", "a11", "a12", "a13", "e1", "e2"] },
];

// The quick facts at the foot of the detail sheet: cost, space needed, learning curve and whether it can be
// self-taught.
// The fact labels reuse the tag dimensions' names as translation context, so "Moderate" has one key per dimension
// ("Cost | Moderate", "Learning curve | Moderate") whether it is shown here or in the filters and colour tags.
const FACT_CONTEXT = { Cost: "Cost", "Space needed": "Space", "Learning curve": "Learning curve", "Teach yourself": "Self-taught friendly" };
function factList(a) {
  const cost = { low: "Low", medium: "Moderate", high: "High" }[a.meta.cost];
  const space = { none: "None", small: "Small", studio: "A studio", large: "Large" }[a.meta.space];
  const curve = { quick: "Quick", moderate: "Moderate", long: "Long" }[a.meta.curve];
  return [
    ["Cost", cost],
    ["Space needed", space],
    ["Learning curve", curve],
    ["Teach yourself", isSelfTaught(a) ? "Works well" : "Better with a teacher"],
  ]
    .map(([k, v]) => `<div><dt>${esc(t(k))}</dt><dd>${esc(tc(FACT_CONTEXT[k], v))}</dd></div>`)
    .join("");
}

// Opens the detail sheet for one art form: description, its family (parent, children, siblings), related and
// easily-confused forms, and a rating slider.
function openDetail(id, opts = {}) {
  currentModalId = id;
  const a = BY_ID[id];
  const nov = noveltyScore(id, state.mastery, state.discount);
  const { score, tier, nearestId } = nov;
  const level = state.mastery[id] || 0;
  const isRated = level > 0;
  const neutral = !isRated && !hasRatings();
  const hue = hueFor(a.category);
  // Family: a child names its parent and its siblings; a parent names its children. Each is listed once, so they are
  // left out of "Related" below, which is then topped back up to five.
  const parent = a.parentId ? BY_ID[a.parentId] : null;
  const sibs = parent ? (parent.childIds || []).filter((x) => x !== id) : [];
  const inFamily = (r) => (a.childIds || []).includes(r) || r === a.parentId || sibs.includes(r);
  const related = relatedByVector(id, 5 + (a.childIds || []).length + sibs.length + 1)
    .filter((r) => !inFamily(r))
    .slice(0, 5);
  const confusable = confusableByName(id, 0.18, 5);
  // A child is listed once. Since the children block above already shows them in the
  // author's order, repeating them in "Related" (which sorts by vector distance) just
  // makes the same form appear twice on one screen. Related keeps its full 5 otherwise.
  const kids = a.childIds || [];
  const relatedNotKids = related;
  const confusableNotKids = confusable.filter((r) => !inFamily(r));

  const readout = isRated
    ? i18nHTML`<strong>Rated ${level} of 10</strong><small>Counts as familiar because you know it.</small>`
    : neutral
      ? i18nHTML`<strong>Not measured yet</strong><small>Rate what you know to see how new this is to you.</small>`
      : i18nHTML`<strong>${tierLabel(tier, nov.promoted)}</strong><span>Novelty ${score} of 100</span>` +
        (nov.promoted ? i18nHTML`<small>Among the newest third of what you have not rated.</small>` : "") +
        (nearestId ? i18nHTML`<small>Closest to ${esc(t(BY_ID[nearestId].name))}, which you rated.</small>` : "");

  const groups = PROFILE_GROUPS.map(
    (g) => `
    <div class="pgroup"><h4>${esc(t(g.title))}</h4>${g.axes
      .map((ax) => {
        const v = a.vector[ax];
        return `<div class="prow" title="${esc(t(AXIS_LABELS[ax]))}"><span>${esc(t(AXIS_SHORT[ax]))}</span><div class="pbar"><i style="width:${Math.round(v * 100)}%"></i></div><em>${Math.round(v * 100)}</em></div>`;
      })
      .join("")}</div>`
  ).join("");

  document.getElementById("modalRoot").innerHTML = i18nHTML`
    <div class="modal-backdrop" id="modalBackdrop">
      <div class="modal" role="dialog" aria-modal="true" aria-label="${esc(t(a.name))} details" style="--hue:${hue}">
        <button class="modal-close" id="modalClose" aria-label="Close">&times;</button>
        <div class="modal-top">
          <div class="modal-side">
            <div class="mark modal-mark">${ringSVG(isRated ? level * 10 : neutral ? 0 : score)}${flowerSVG(a, { unfurl: !opts.quiet })}</div>
            <div class="modal-read">${readout}</div>
          </div>
          <div>
            <div class="modal-cat">${esc(t(a.category))}</div>
            <h2 class="modal-title">${esc(t(a.name))}</h2>
            <p class="modal-tag">${esc(t(a.tag || ""))}</p>
            ${breadcrumb(a).length ? i18nHTML`<p class="modal-trail" id="modalParent">A kind of ${breadcrumb(a).map((name) => esc(t(name))).join(" › ")}</p>` : ""}
            <p class="modal-desc">${esc(t(a.desc || safeDescribe(a)))}</p>
            ${a.start ? i18nHTML`<div class="try"><h3>Try this first</h3><p>${esc(t(a.start))}</p></div>` : ""}
            <dl class="facts">${factList(a)}</dl>
            ${
              parent
                ? i18nHTML`<div class="child-wrap">
              <h3 class="section-label">Part of a larger art form</h3>
              <ul class="related-list" id="parentList"></ul>
              ${sibs.length ? i18nHTML`<h3 class="section-label">Also under ${esc(t(parent.name))}</h3><ul class="related-list" id="siblingList"></ul>` : ""}
            </div>`
                : ""
            }
            ${
              a.childIds && a.childIds.length
                ? i18nHTML`<div class="child-wrap">
              <h3 class="section-label">More specific forms under this</h3>
              <ul class="related-list" id="childList"></ul>
            </div>`
                : ""
            }
            <div class="related-wrap">
              <h3 class="section-label">Related art forms</h3>
              <ul class="related-list" id="relatedList"></ul>
              ${confusable.length ? i18nHTML`<h3 class="section-label">Easily confused by name</h3><ul class="related-list" id="confusableList"></ul>` : ""}
            </div>
          </div>
        </div>
        <details class="profile-wrap"><summary>Full profile</summary><div class="profile">${groups}</div></details>
        <div class="mastery-block">
          <h3>How well do you know it?</h3>
          <span class="rate-wrap"><input type="range" class="rate" id="modalMasterySlider" min="0" max="10" step="1" value="${level}" style="--pct:${level * 10}%" aria-label="How well you know ${esc(t(a.name))}"></span>
          <span class="mastery-num" id="modalMasteryVal">${level}</span>
        </div>
      </div>
    </div>`;

  const fillList = (listEl, ids) => {
    if (!listEl) return;
    listEl.innerHTML = "";
    for (const rid of ids) {
      const ra = BY_ID[rid];
      const li = document.createElement("li");
      li.className = "related-item";
      li.tabIndex = 0;
      li.setAttribute("role", "button");
      li.style.setProperty("--hue", hueFor(ra.category));
      li.innerHTML = `${flowerSVG(ra)}<span><b>${esc(t(ra.name))}</b><small>${esc(t(ra.tag || ra.category))}</small></span>`;
      li.addEventListener("click", () => openDetail(rid));
      li.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          openDetail(rid);
        }
      });
      listEl.appendChild(li);
    }
  };
  fillList(document.getElementById("relatedList"), relatedNotKids);
  fillList(document.getElementById("confusableList"), confusableNotKids);
  // The children list is the same component as "Related", but ordered as the hierarchy
  // defines it rather than by vector distance -- a parent should list its own children
  // in the author's order, not reshuffled by similarity.
  if (kids.length) fillList(document.getElementById("childList"), kids);
  if (parent) {
    fillList(document.getElementById("parentList"), [parent.id]);
    fillList(document.getElementById("siblingList"), sibs);
  }

  // Clicking the trail steps up to the parent, so walking Ballet -> Dance -> back works
  // without closing the sheet.
  const trailEl = document.getElementById("modalParent");
  if (trailEl && a.parentId && BY_ID[a.parentId]) {
    trailEl.classList.add("is-link");
    trailEl.tabIndex = 0;
    trailEl.setAttribute("role", "button");
    const goUp = () => openDetail(a.parentId);
    trailEl.addEventListener("click", goUp);
    trailEl.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        goUp();
      }
    });
  }

  document.getElementById("modalClose").addEventListener("click", closeDetail);
  document.getElementById("modalBackdrop").addEventListener("click", (e) => {
    if (e.target.id === "modalBackdrop") closeDetail();
  });

  const mSlider = document.getElementById("modalMasterySlider");
  const mVal = document.getElementById("modalMasteryVal");
  bindRateReadout(mSlider, {
    onInput: (v) => {
      v = parseInt(v, 10);
      mVal.textContent = v;
      setRateFill(mSlider);
      if (v > 0) state.mastery[id] = v;
      else delete state.mastery[id];
      saveStore();
    },
    onCommit: () => {
      renderGrid();
      openDetail(id, { quiet: true });
    },
  });

  if (!opts.quiet) document.getElementById("modalClose").focus({ preventScroll: true });
  document.body.style.overflow = "hidden";
}

// Closes the detail sheet and restores page scrolling.
function closeDetail() {
  currentModalId = null;
  document.getElementById("modalRoot").innerHTML = "";
  document.body.style.overflow = "";
}
