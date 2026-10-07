// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

/* ONE CARD IN THE GARDEN. Draws a single art-form row: the flower, the name, the
rating control and the tags it carries. Needs the catalogue and the svg kit.
   See docs/architecture.md. */

// ---------------- Flowers ----------------
// Every art form is drawn as a flower generated from its own profile. Three layers of petals:
//   outer   how it is made and shared (13 technique axes)
//   middle  which field it serves     (7 purpose axes)
//   inner   which senses it engages   (5 sense axes)
// Petal length is the axis value, so two art forms that are alike grow alike.
// Hue is set per category through --hue on an ancestor element.
// Spread around the wheel with the true-blue band (roughly 190-260) skipped entirely, so no
// cluster of categories renders blue; warm hues get more room since most categories sit there.
const CATEGORY_HUES = {
  "Visual Arts": 35,
  "Craft & Sculpture": 85,
  "Design": 245,
  "Food, Scent & Plants": 135,
  "Land & Environment": 135,
  "Digital & Interactive": 245,
  "Directing & Curating": 35,
  "Writing & Language": 245,
  "Music & Sound": 85,
  "Conceptual & Social": 35,
  "Performance & Movement": 85,
  "Sport & Martial Arts": 135,
};
// The hue for a category: fixed for the known categories, otherwise derived from the name so it is stable.
function hueFor(category) {
  if (category in CATEGORY_HUES) return CATEGORY_HUES[category];
  let h = 0;
  for (const ch of category) h = (h * 31 + ch.charCodeAt(0)) % 360;
  return [35, 85, 135, 245][h % 4];
}

// One line icon per category, tinted with the category's hue. Rows show only the icon (its name is
// in the tooltip / accessible label); the icon-to-name key appears once in the legend instead.
const CATEGORY_ICON_PATHS = {
  "Visual Arts":
    '<circle cx="13.5" cy="6.5" r=".6"/><circle cx="17.5" cy="10.5" r=".6"/><circle cx="8.5" cy="7.5" r=".6"/><circle cx="6.5" cy="12.5" r=".6"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.9 0 1.6-.7 1.6-1.7 0-.4-.2-.8-.4-1.1-.3-.3-.4-.7-.4-1.1a1.6 1.6 0 0 1 1.7-1.7H16c3 0 5.5-2.5 5.5-5.5C22 6 17.5 2 12 2z"/>',
  "Craft & Sculpture":
    '<circle cx="6" cy="6" r="3"/><path d="M8.12 8.12 12 12"/><path d="M20 4 8.12 15.88"/><circle cx="6" cy="18" r="3"/><path d="M14.8 14.8 20 20"/>',
  "Design":
    '<path d="M21.3 15.3a2.4 2.4 0 0 1 0 3.4l-2.6 2.6a2.4 2.4 0 0 1-3.4 0L2.7 8.7a2.4 2.4 0 0 1 0-3.4l2.6-2.6a2.4 2.4 0 0 1 3.4 0z"/><path d="m14.5 12.5 2-2"/><path d="m11.5 9.5 2-2"/><path d="m8.5 6.5 2-2"/><path d="m17.5 15.5 2-2"/>',
  "Food, Scent & Plants":
    '<path d="M7 20h10"/><path d="M10 20c5.5-2.5.8-6.4 3-10"/><path d="M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4 0 5.5.8z"/><path d="M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z"/>',
  "Land & Environment": '<path d="m8 3 4 8 5-5 5 15H2L8 3z"/>',
  "Digital & Interactive": '<rect width="20" height="14" x="2" y="3" rx="2"/><path d="M8 21h8"/><path d="M12 17v4"/>',
  "Directing & Curating":
    '<path d="M20.2 6 3 11l-.9-2.4c-.3-1.1.3-2.2 1.3-2.5l13.5-4c1.1-.3 2.2.3 2.5 1.3z"/><path d="m6.2 5.3 3.1 3.9"/><path d="m12.4 3.4 3.1 4"/><path d="M3 11h18v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
  "Writing & Language":
    '<path d="M20.24 12.24a6 6 0 0 0-8.49-8.49L5 10.5V19h8.5z"/><path d="M16 8 2 22"/><path d="M17.5 15H9"/>',
  "Music & Sound": '<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>',
  "Conceptual & Social": '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22z"/>',
  "Sport & Martial Arts": '<circle cx="12" cy="8" r="5"/><path d="M8.5 12.5 7 21l5-3 5 3-1.5-8.5"/>',
  "Performance & Movement":
    '<circle cx="12" cy="5" r="1"/><path d="m9 20 3-6 3 6"/><path d="m6 8 6 2 6-2"/><path d="M12 10v4"/>',
};
// The small SVG icon for a category.
function iconFor(category, size = 16) {
  const body = CATEGORY_ICON_PATHS[category] || '<circle cx="12" cy="12" r="8"/>';
  return `<svg class="cat-ico" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="color:oklch(0.5 0.12 ${hueFor(category)})" role="img" aria-label="${esc(t(category))}"><title>${esc(t(category))}</title>${body}</svg>`;
}

const FLOWER_LAYERS = [
  { key: "t", axes: AXIS_GROUPS.technique, rMin: 7, rMax: 48 },
  { key: "d", axes: AXIS_GROUPS.domain, rMin: 6, rMax: 43 },
  { key: "s", axes: AXIS_GROUPS.sensory, rMin: 5, rMax: 33 },
];
// Formats a number to one decimal place, which keeps the SVG strings short.
const f1 = (n) => n.toFixed(1);
// Flat folk-art geometry: outer ring = lancet (two symmetric arcs), middle ring = rounded bars,
// inner ring = round pips. Colors come from --c1..--c3 (the four folk-palette inks).
const FOLK_ORDER = {
  terra: ["terra", "ochre", "slate"],
  ochre: ["ochre", "terra", "forest"],
  forest: ["forest", "ochre", "terra"],
  slate: ["slate", "ochre", "terra"],
};
// The ink a hue belongs to, and the three inks the holotype draws with (MADE, FIELD, SENSES) in that order. The plant
// is coloured from this same list (see personPalette in plant.js), so the holotype and the plant always share colours.
function folkKey(hue) {
  const anchors = [
    [35, "terra"],
    [85, "ochre"],
    [135, "forest"],
    [245, "slate"],
  ];
  const d = (x, y) => Math.min(Math.abs(x - y), 360 - Math.abs(x - y));
  return anchors.reduce((b, c) => (d(hue, c[0]) < d(hue, b[0]) ? c : b))[1];
}
function folkInks(hue, seed) {
  const o = FOLK_ORDER[folkKey(hue)].slice();
  if (seed % 2) {
    const t = o[1];
    o[1] = o[2];
    o[2] = t;
  }
  return o;
}
function folkStyle(hue, seed) {
  const o = folkInks(hue, seed);
  return `--c1:var(--f-${o[0]});--c2:var(--f-${o[1]});--c3:var(--f-${o[2]})`;
}
// The CSS colour of the ink a hue belongs to (used for the category dots).
function folkInk(hue) {
  const anchors = [
    [35, "terra"],
    [85, "ochre"],
    [135, "forest"],
    [245, "slate"],
  ];
  const d = (x, y) => Math.min(Math.abs(x - y), 360 - Math.abs(x - y));
  return `var(--f-${anchors.reduce((b, c) => (d(hue, c[0]) < d(hue, b[0]) ? c : b))[1]})`;
}
function petalPath(kind, len, w) {
  if (kind === "t") return `M0 0Q${f1(w * 1.5)} ${f1(-len * 0.5)} 0 ${f1(-len)}Q${f1(-w * 1.5)} ${f1(-len * 0.5)} 0 0Z`;
  if (kind === "d") {
    const b = Math.max(1.1, w * 0.55);
    return `M${f1(-b)} 0V${f1(-(len - b))}A${f1(b)} ${f1(b)} 0 0 1 ${f1(b)} ${f1(-(len - b))}V0Z`;
  }
  const r = Math.max(1.5, Math.min(w * 0.9, len * 0.2)),
    y = -len * 0.74;
  return `M${f1(-r)} ${f1(y)}a${f1(r)} ${f1(r)} 0 1 0 ${f1(r * 2)} 0a${f1(r)} ${f1(r)} 0 1 0 ${f1(-r * 2)} 0Z`;
}
// The petals for a vector: three rings (technique, field, senses), each petal's length following its axis.
function flowerPetals(vector, seed, opts = {}) {
  let i = opts.start || 0,
    petals = "";
  FLOWER_LAYERS.forEach((L, li) => {
    const n = L.axes.length,
      offset = (seed * (29 + li * 17)) % 360;
    L.axes.forEach((ax, k) => {
      const v = vector[ax];
      const len = L.rMin + (L.rMax - L.rMin) * (0.05 + 0.95 * Math.pow(v, 0.8));
      const w = Math.max(1.4, Math.min(len * 0.28, ((Math.PI * 2 * len * 0.6) / n) * 0.55));
      const deg = offset + (k * 360) / n;
      petals += `<g transform="rotate(${f1(deg)})"><path class="pl pl-${L.key}" style="--i:${i++}" d="${petalPath(L.key, len, w)}"/></g>`;
    });
  });
  return petals;
}
// The three concentric circles at a flower's centre.
function heartSVG(r) {
  return `<circle class="heart" r="${r}"/><circle class="heart2" r="${f1(r * 0.55)}"/><circle class="heart3" r="${f1(r * 0.22)}"/>`;
}
// The SVG for one art form's flower. Seeded from the form's id, so it is always the same shape.
function flowerSVG(a, opts = {}) {
  const seed = parseInt(String(a.id).replace(/\D/g, ""), 10) || 1;
  const petals = flowerPetals(a.vector, seed, opts);
  return `<svg class="flower${opts.unfurl ? " unfurl" : ""}" viewBox="-50 -50 100 100" aria-hidden="true" style="${folkStyle(hueFor(a.category), seed)}"><g class="rose">${petals}${heartSVG(3.6)}</g></svg>`;
}

// A ring around the flower: how much of it is filled is the novelty score (or your own rating).
function ringSVG(pct) {
  const r = 53,
    c = 2 * Math.PI * r;
  const fill =
    pct > 0
      ? `<circle class="ring-fill" cx="56" cy="56" r="${r}" stroke-dasharray="${f1((c * pct) / 100)} ${f1(c)}" transform="rotate(-90 56 56)"/>`
      : "";
  return `<svg viewBox="0 0 112 112" aria-hidden="true"><circle class="ring-track" cx="56" cy="56" r="${r}"/>${fill}</svg>`;
}
// Until something is rated, every score would be 100, so the wall stays calm and shows no gauge.
function hasRatings() {
  return ART_FORMS.some((a) => state.mastery[a.id] > 0);
}

// The mark is not a stand-in flower: it is the garden's own average tensor profile, drawn with
// the same petal system as every other flower. Average every art form's technique, domain and
// sensory axes together and you get the one shape every individual flower is a variation of —
// literally a culmination of the whole collection, not an arbitrary decoration.
function brandVector() {
  const axes = [...AXIS_GROUPS.technique, ...AXIS_GROUPS.domain, ...AXIS_GROUPS.sensory];
  const v = {};
  axes.forEach((ax) => {
    v[ax] = ART_FORMS.reduce((s, a) => s + a.vector[ax], 0) / N;
  });
  return v;
}
// A reduced set of petals (at most eight per ring) for the flower inside the wordmark.
function logoPetals(vector) {
  const spans = { t: [38, 48], d: [26, 37], s: [15, 25] };
  let petals = "",
    i = 0;
  FLOWER_LAYERS.forEach((L, li) => {
    const axes = L.axes.filter((_, k) => k % Math.ceil(L.axes.length / 8) === 0),
      vals = axes.map((ax) => vector[ax]);
    const lo = Math.min(...vals),
      hi = Math.max(...vals),
      [r0, r1] = spans[L.key],
      n = axes.length;
    axes.forEach((ax, k) => {
      const t = hi > lo ? (vector[ax] - lo) / (hi - lo) : 0.5,
        len = r0 + (r1 - r0) * (0.35 + 0.65 * t);
      const w = Math.min(len * 0.42, ((Math.PI * 2 * len * 0.62) / n) * 0.6),
        deg = li * 23 + (k * 360) / n;
      petals += `<g transform="rotate(${f1(deg)})"><path class="pl pl-${L.key}" d="${petalPath(L.key, len, w)}"/></g>`;
    });
  });
  return petals;
}
// Draws the flower inside the wordmark, sized to a letter O once the web font has loaded.
function renderBrandMark() {
  const svg = document.getElementById("brandSvg"),
    g = document.getElementById("brandMark"),
    fs = parseFloat(getComputedStyle(svg.parentNode).fontSize) || 32;
  let m = { adv: 24, l: -1.4, r: 22.4, asc: 20.6, desc: 0.4 }; // fallback until the font is measured
  const measure = () => {
    try {
      const c = document.createElement("canvas").getContext("2d");
      c.font = `700 ${fs}px "Josefin Sans"`;
      const t = c.measureText("O");
      if (t.actualBoundingBoxAscent)
        m = {
          adv: t.width,
          l: t.actualBoundingBoxLeft,
          r: t.actualBoundingBoxRight,
          asc: t.actualBoundingBoxAscent,
          desc: t.actualBoundingBoxDescent,
        };
    } catch (e) {
      /* keep fallback */
    }
  };
  const draw = () => {
    const h = m.asc + m.desc,
      cx = (m.r - m.l) / 2,
      cy = (m.desc - m.asc) / 2,
      R = h / 2 - 1.3;
    const n = Math.max(12, Math.round((2 * Math.PI * R) / 2.9)),
      step = (2 * Math.PI * R) / n;
    svg.setAttribute("viewBox", `0 ${f1(-m.asc)} ${f1(m.adv)} ${f1(h)}`);
    svg.style.width = (m.adv / fs).toFixed(3) + "em";
    svg.style.height = (h / fs).toFixed(3) + "em";
    svg.style.verticalAlign = (-m.desc / fs).toFixed(3) + "em";
    g.setAttribute("style", folkStyle(38, 1));
    g.innerHTML = `<g transform="translate(${f1(cx)} ${f1(cy)})">
      <circle r="${f1(R)}" fill="none" stroke="var(--ink)" stroke-width="1.6" stroke-linecap="round" stroke-dasharray="0 ${step.toFixed(2)}"/>
      <g transform="scale(${((R - 1.7) / 44).toFixed(4)})"><g class="rose">${logoPetals(brandVector())}${heartSVG(6.5)}</g></g></g>`;
  };
  draw();
  if (document.fonts && document.fonts.load)
    document.fonts
      .load(`700 ${fs}px "Josefin Sans"`, "O")
      .then(() => {
        measure();
        draw();
      })
      .catch(() => {});
}
