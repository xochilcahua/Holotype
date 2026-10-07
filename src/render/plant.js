// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

/* THE PERSONAL PLANT. One SVG string built from a profile: the genus picks an
archetype and base slider values, the regime picks leaf style and density, each lean
pushes its own sliders, and the palette plus one small detail (a bee, a ladybug) are
random per person from the seed. Self-contained: everything it needs is in here and
it publishes exactly one thing, window.HolotypePlant.
   See docs/architecture.md. */

/* plant.js — profile → personal plant illustration (SVG string).
   Built on FlowerGen.html: the shape library and the six parameter sliders (stem, leaf style, leaf density, primary/secondary/tertiary form) are the author's, unchanged.
   The taxonomy drives the SLIDERS, never the colors:
     genus       → archetype + base slider values
     regime      → leaf style, leaf density, tertiary detail   (ordinata = tidy, aleatoria = wild)
     leans (0–2) → each tribe pushes its own sliders          (see TRIBE_MOD)
     confidence  → 'early' = sapling (short, sparse, no fine detail)
   Colors + one tiny detail (bee/ladybug/…) are random PER PERSON from the seed: a palette from the author's vetted set, and the glyph.
   Usage: HolotypePlant.svg({genus:"Ficus", regime:"flexilis", domains:["Petal","Root"], confidence:"established", seed:"a8f3kq2z"}, {dark:false})
   Create the seed once with HolotypePlant.newSeed() and store it with the profile. Needs a DOM (getBBox auto-fit). Returns a self-contained <svg> string. */
(function (root) {
  const NS = "http://www.w3.org/2000/svg";

  // genus → [arch, stem, leafType, leafDens, primary, secondary, tertiary]
  // arch: 0 radiating flower, 1 cup/tulip, 2 stacked folk-art, 3 fungi, 4 foliage branch, 5 physarum/network
  const GENUS = {
    Selaginella: [4, 110, 1, 4, 2, 1, 0],
    Cuscuta: [5, 110, 0, 2, 2, 2, 1],
    Rafflesia: [0, 60, 0, 0, 1, 1, 1],
    Mimosa: [4, 150, 6, 5, 3, 3, 2],
    Lithops: [1, 50, 0, 0, 3, 0, 0],
    Pteris: [4, 170, 5, 6, 6, 2, 0],
    Drosera: [1, 120, 4, 2, 4, 1, 3],
    Helianthus: [0, 200, 3, 2, 2, 3, 1],
    Physarum: [5, 130, 0, 4, 4, 2, 2],
    Lemna: [5, 110, 2, 2, 3, 2, 0],
    Armillaria: [3, 90, 0, 0, 4, 3, 1],
    Taraxacum: [5, 130, 0, 3, 0, 2, 1],
    Lycopodium: [4, 190, 2, 6, 2, 0, 0],
    Bambusa: [2, 200, 2, 3, 2, 3, 3],
    Passiflora: [5, 150, 0, 4, 1, 1, 1],
    Ficus: [4, 200, 3, 5, 1, 4, 3],
  };
  const LIM = { stem: [40, 250], lType: [0, 7], lDens: [0, 6], prim: [0, 6], sec: [0, 5], tert: [0, 4] };
  const MAX_PRIM = [4, 4, 2, 4, 6, 4]; // per archetype; fungi capped at 4 so modifiers never push a cap into the odd crescent/cloud shapes

  // regime: 'lType' = forced leaf style (3 round/regular, 7 jagged/wild); the rest are slider offsets
  const REGIME = {
    ordinata: { lType: 3, lDens: -1, tert: -1 },
    flexilis: {},
    aleatoria: { lType: 7, lDens: 2, tert: 1, sec: 1 },
  };
  // lean tribe → slider offsets ('lType' = forced leaf style)
  const TRIBE_MOD = {
    Reed: { sec: 2 }, // rhythm/pattern → more repeated elements
    Vine: { stem: 40, lDens: 1 }, // sequence → longer, more leaves along it
    Petal: { prim: 1, tert: 1 }, // the visual → showier head
    Tendril: { lType: 5, sec: 1, lDens: 1 }, // body in motion → curling leaves, wider branching
    Nectar: { tert: 2 }, // sensory → more stamens / rings / spots
    Trellis: { stem: 20, prim: -1, sec: -1 }, // structure → taller, stricter form
    Root: { stem: -30, lDens: 1, tert: 1 }, // living systems → grounded, fuller
  };

  // the author's vetted palettes: [stem/dark, primary, secondary, tertiary, paper]; 1–5 are FlowerGen's own
  const PALETTES = [
    ["#2A4359", "#D14934", "#EBB638", "#516942", "#F2EFE9"],
    ["#4F6C56", "#B94B4B", "#DF8D3C", "#2A4359", "#EBE7DD"],
    ["#1C3144", "#CC5C4B", "#E9C25A", "#577860", "#F7F5F0"],
    ["#2B3E60", "#D66B59", "#E0A96D", "#395A75", "#EAE5DC"],
    ["#3A2F2A", "#C25953", "#E8C547", "#4D685A", "#F0EAD6"],
    ["#2F4A5A", "#C8472F", "#E0AE3E", "#5A7A4E", "#F3EFE3"],
    ["#3B4A5C", "#C4553E", "#DDA62F", "#4A6340", "#F1EDE0"],
    ["#2A4359", "#B5473A", "#E8C15A", "#6E8F73", "#F5F2E8"],
    ["#33475B", "#CF6A4E", "#E5B75E", "#4F6B4A", "#F3EFE3"],
  ];
  const GROUND = [0, 3, 5]; // detail glyphs that sit at the base instead of floating

  function hash(s) {
    let h = 2166136261;
    for (let i = 0; i < s.length; i++) {
      h ^= s.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return h >>> 0;
  }
  function rngFor(s) {
    let a = hash(s);
    return () => {
      a |= 0;
      a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function el(type, attrs, kids) {
    const e = document.createElementNS(NS, type);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    (kids || []).forEach((c) => e.appendChild(c));
    return e;
  }
  const clamp = (v, k, arch) => Math.max(LIM[k][0], Math.min(k === "prim" ? MAX_PRIM[arch] : LIM[k][1], v));

  // profile → the six sliders (this is where the taxonomy lives)
  function resolveParams(profile) {
    const b = GENUS[profile.genus] || GENUS.Ficus,
      arch = b[0];
    const p = { arch, stem: b[1], lType: b[2], lDens: b[3], prim: b[4], sec: b[5], tert: b[6] };
    const leafy = b[2] > 0 || arch === 5; // leafless genera stay leafless
    const early = profile.confidence === "early";
    const mods = early
      ? []
      : [REGIME[profile.regime] || {}].concat((profile.domains || []).slice(0, 2).map((d) => TRIBE_MOD[d] || {}));
    mods.forEach((m) => {
      for (const k in m) {
        if (k === "lType") {
          if (leafy) p.lType = m.lType;
        } else p[k] += m[k];
      }
    });
    if (early) {
      p.stem = Math.round((p.stem * 0.75) / 10) * 10;
      p.lDens = Math.min(p.lDens, 2);
      p.sec = Math.min(p.sec, 1);
      p.tert = 0;
    } // sapling
    for (const k in LIM) p[k] = clamp(p[k], k, arch);
    return p;
  }

  // per-person colors, chosen exactly the way FlowerGen's "Rnd Color" does (arch-specific slot mapping), but seeded
  // Every palette holds the same four inks (slate, terra, ochre, forest) in slightly different tones. The seed picks the tone.
  // When the profile carries the holotype's three inks (`inks`), the plant is coloured with them in the holotype's order:
  // petals = the ink the person leans into, then the holotype's second and third, and the stem takes the one ink the holotype
  // leaves out. That is a rule, not a per-person choice, so the plant and the holotype agree for everyone. Without `inks` the
  // old seed-only colouring is used, so callers that never knew about inks keep their look.
  const INK_REF = { slate: [42, 67, 89], terra: [200, 71, 47], ochre: [221, 166, 47], forest: [74, 99, 64] };
  function inkRoles(pal) {
    const rgb = (h) => {
      const n = parseInt(h.slice(1), 16);
      return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
    };
    const names = Object.keys(INK_REF),
      ents = [0, 1, 2, 3].map((i) => rgb(pal[i]));
    const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
    let best = null,
      bestCost = Infinity;
    const perm = (arr, cur) => {
      if (!arr.length) {
        const c = cur.reduce((s, ni, ei) => s + dist(ents[ei], INK_REF[names[ni]]), 0);
        if (c < bestCost) {
          bestCost = c;
          best = cur.slice();
        }
        return;
      }
      arr.forEach((v, i) =>
        perm(
          arr.filter((_, j) => j !== i),
          cur.concat(v)
        )
      );
    };
    perm([0, 1, 2, 3], []);
    const out = {};
    best.forEach((ni, ei) => {
      out[names[ni]] = pal[ei];
    });
    return out;
  }
  // Which colour slot carries the most area in each plant, most first (measured on the drawn plants and averaged over 13 regime, lean and confidence variants).
  // The holotype's main ink goes to the first slot, its second ink to the next, and so on, so the ink a person leans into is
  // the one that dominates their plant, as it dominates their holotype.
  const SLOT_ORDER = {
    Selaginella: ["stem", "c3", "c2", "c1"],
    Cuscuta: ["c2", "stem", "c1", "c3"],
    Rafflesia: ["c1", "stem", "c2", "c3"],
    Mimosa: ["c2", "c3", "stem", "c1"],
    Lithops: ["c1", "stem", "c2", "c3"],
    Pteris: ["stem", "c3", "c2", "c1"],
    Drosera: ["c1", "stem", "c2", "c3"],
    Helianthus: ["c1", "stem", "c2", "c3"],
    Physarum: ["c2", "stem", "c1", "c3"],
    Lemna: ["c2", "c1", "stem", "c3"],
    Armillaria: ["stem", "c1", "c2", "c3"],
    Taraxacum: ["c1", "c2", "stem", "c3"],
    Lycopodium: ["stem", "c3", "c2", "c1"],
    Bambusa: ["c1", "c3", "stem", "c2"],
    Passiflora: ["c1", "c2", "stem", "c3"],
    Ficus: ["c2", "stem", "c3", "c1"],
  };
  function personPalette(seed, arch, dark, inks, genus) {
    const pal = PALETTES[hash(seed + "|pal") % PALETTES.length];
    let stem,
      p1,
      p2,
      p3,
      p4 = pal[4],
      slateTone = pal[0];
    if (inks && inks.length === 3) {
      const roles = inkRoles(pal),
        rest = Object.keys(INK_REF).find((k) => !inks.includes(k));
      const ranked = [roles[inks[0]], roles[inks[1]], roles[inks[2]], roles[rest]],
        slot = {};
      (SLOT_ORDER[genus] || ["c1", "c2", "c3", "stem"]).forEach((sl, i) => {
        slot[sl] = ranked[i];
      });
      slateTone = roles.slate;
      stem = slot.stem;
      p1 = slot.c1;
      p2 = slot.c2;
      p3 = slot.c3;
      if (arch === 3) p3 = stem;
    } else if (arch === 3) {
      stem = pal[0];
      p1 = pal[1];
      p2 = pal[2];
      p3 = pal[0];
    } else if (arch === 5) {
      const r = rngFor(seed + "|shuf"),
        s = pal.slice(0, 4).sort(() => r() - 0.5);
      [stem, p1, p2, p3] = s;
    } else {
      stem = pal[0];
      p1 = pal[1];
      p2 = pal[2];
      p3 = pal[3];
    }
    // REVERTED 2026-10-01. A contrast guard used to sit here: it measured RGB distance
    // between the stem (pal[0]) and leaf/tertiary colour (pal[3]) and, below a threshold of
    // 58, reassigned p3 to whichever of p1/p2 was further from the stem.
    //
    // It was solving a real but tiny problem (a few palettes put a near-identical dark in
    // slots 0 and 3, so Pteris read as one flat navy mass) at the cost of wrecking the plates
    // that matter. On palette 4 (stem #2B3E60, p3 #395A75, distance 38) it fired and
    // recoloured c3 from dark blue to gold #E0A96D -- which erased the green "pupils" and
    // dashed veins on the arch 0 / prim 3 radiating flower, and on Helianthus it also
    // replaced the snail. Same geometry, worse picture: the plate lost the detail that made
    // it read as drawn rather than assembled. Author's colours are load-bearing; if Pteris
    // ever looks too flat again, fix that palette's leaf in place rather than recolouring
    // every form at draw time.
    const n = parseInt(stem.slice(1), 16),
      lum = (((n >> 16) & 255) * 299 + ((n >> 8) & 255) * 587 + (n & 255) * 114) / 1000;
    if (dark && lum < 90) stem = "#C9C4B2";
    // on the dark plate, any dark ink (not just the stem) is lifted toward white so the plant and its little extra detail stay readable
    const lift = (h) => {
      if (!dark) return h;
      const k = parseInt(h.slice(1), 16),
        r = (k >> 16) & 255,
        g = (k >> 8) & 255,
        b = k & 255;
      if ((r * 299 + g * 587 + b * 114) / 1000 >= 110) return h;
      return (
        "#" +
        [r, g, b]
          .map((v) =>
            Math.round(v + (255 - v) * 0.55)
              .toString(16)
              .padStart(2, "0")
          )
          .join("")
      );
    };
    // The dewdrop is the plant's own slate ink diluted with white, so even it belongs to the palette.
    const dilute = (h, t) => {
      const n = parseInt(h.slice(1), 16);
      return (
        "#" +
        [(n >> 16) & 255, (n >> 8) & 255, n & 255]
          .map((v) =>
            Math.round(v + (255 - v) * t)
              .toString(16)
              .padStart(2, "0")
          )
          .join("")
      );
    };
    return {
      stem,
      c1: lift(p1),
      c2: lift(p2),
      c3: lift(p3),
      dew: dilute(slateTone, dark ? 0.2 : 0.1),
      dewFill: dilute(slateTone, dark ? 0.55 : 0.82),
      paper: dark ? "#22252A" : p4,
    };
  }

  function buildPlant(p, C, isDark, uid, svgDefs) {
    const cStem = C.stem,
      c1 = C.c1,
      c2 = C.c2,
      c3 = C.c3,
      c4 = C.paper;
    const g = el("g", {});

    if (p.arch === 5) {
      const nG = el("g", { transform: `translate(0, ${-p.stem * 0.5})` });
      g.appendChild(nG);
      const r = p.stem;

      if (p.prim === 0) {
        const rays = 8 + p.lDens * 4;
        for (let i = 0; i < rays; i++) {
          const angle = (360 / rays) * i;
          const len = i % 2 === 0 ? r : r * 0.6;
          nG.appendChild(
            el("line", {
              x1: 0,
              y1: 0,
              x2: 0,
              y2: -len,
              stroke: cStem,
              "stroke-width": 4,
              transform: `rotate(${angle})`,
            })
          );
          nG.appendChild(
            el("circle", {
              cx: 0,
              cy: -len,
              r: 8 + p.sec * 2,
              fill: i % 2 === 0 ? c1 : c2,
              transform: `rotate(${angle})`,
            })
          );
          if (p.tert > 0)
            nG.appendChild(el("circle", { cx: 0, cy: -len * 0.5, r: 4, fill: c3, transform: `rotate(${angle})` }));
        }
        nG.appendChild(el("circle", { cx: 0, cy: 0, r: 16, fill: cStem }));
      } else if (p.prim === 1) {
        const layers = 3 + Math.floor(p.lDens / 2);
        for (let l = layers; l > 0; l--) {
          const layerR = (r / layers) * l;
          const petals = 6 + l * 4;
          for (let i = 0; i < petals; i++) {
            const angle = (360 / petals) * i;
            nG.appendChild(
              el("circle", {
                cx: 0,
                cy: -layerR,
                r: layerR * 0.5,
                fill: l % 2 === 0 ? c1 : c2,
                transform: `rotate(${angle})`,
              })
            );
            if (p.sec > 0)
              nG.appendChild(
                el("circle", { cx: 0, cy: -layerR, r: layerR * 0.2, fill: c3, transform: `rotate(${angle})` })
              );
          }
          nG.appendChild(el("circle", { cx: 0, cy: 0, r: layerR * 0.85, fill: l % 2 === 0 ? c2 : c1 }));
        }
        if (p.tert > 0) nG.appendChild(el("circle", { cx: 0, cy: 0, r: r * 0.1, fill: isDark ? "#22252A" : c4 }));
      } else if (p.prim === 2) {
        const arms = 4 + p.lDens;
        for (let i = 0; i < arms; i++) {
          const angle = (360 / arms) * i;
          nG.appendChild(
            el("line", {
              x1: 0,
              y1: 0,
              x2: 0,
              y2: -r * 0.5,
              stroke: cStem,
              "stroke-width": 6,
              transform: `rotate(${angle})`,
            })
          );
          nG.appendChild(
            el("line", {
              x1: 0,
              y1: -r * 0.5,
              x2: -r * 0.4,
              y2: -r,
              stroke: cStem,
              "stroke-width": 4,
              transform: `rotate(${angle})`,
            })
          );
          nG.appendChild(
            el("line", {
              x1: 0,
              y1: -r * 0.5,
              x2: r * 0.4,
              y2: -r,
              stroke: cStem,
              "stroke-width": 4,
              transform: `rotate(${angle})`,
            })
          );
          nG.appendChild(el("circle", { cx: 0, cy: -r * 0.5, r: 8, fill: c1, transform: `rotate(${angle})` }));
          if (p.sec > 0) {
            nG.appendChild(
              el("circle", { cx: -r * 0.4, cy: -r, r: 6 + p.sec, fill: c2, transform: `rotate(${angle})` })
            );
            nG.appendChild(
              el("circle", { cx: r * 0.4, cy: -r, r: 6 + p.sec, fill: c2, transform: `rotate(${angle})` })
            );
          }
        }
        nG.appendChild(el("circle", { cx: 0, cy: 0, r: 16, fill: c3 }));
      } else if (p.prim === 3) {
        const rings = 2 + p.lDens;
        for (let i = 1; i <= rings; i++) {
          const ringR = (r / rings) * i;
          nG.appendChild(el("circle", { cx: 0, cy: 0, r: ringR, stroke: cStem, "stroke-width": 4, fill: "none" }));
          if (p.sec > 0) {
            const dots = i * (4 + p.lType);
            for (let d = 0; d < dots; d++) {
              const a = (360 / dots) * d;
              nG.appendChild(
                el("circle", {
                  cx: 0,
                  cy: -ringR,
                  r: 4 + p.sec,
                  fill: i % 2 === 0 ? c1 : c2,
                  transform: `rotate(${a})`,
                })
              );
            }
          }
        }
        nG.appendChild(el("circle", { cx: 0, cy: 0, r: r * 0.1, fill: c3 }));
      } else {
        const cells = [
          { cx: 0, cy: 0, r: r * 0.4 },
          { cx: -r * 0.4, cy: -r * 0.4, r: r * 0.3 },
          { cx: r * 0.4, cy: -r * 0.4, r: r * 0.3 },
          { cx: -r * 0.4, cy: r * 0.4, r: r * 0.3 },
          { cx: r * 0.4, cy: r * 0.4, r: r * 0.3 },
          { cx: -r * 0.7, cy: 0, r: r * 0.2 },
          { cx: r * 0.7, cy: 0, r: r * 0.2 },
          { cx: 0, cy: -r * 0.7, r: r * 0.2 },
          { cx: 0, cy: r * 0.7, r: r * 0.2 },
        ];
        cells.forEach((c, idx) => {
          nG.appendChild(
            el("circle", { cx: c.cx, cy: c.cy, r: c.r, fill: idx === 0 ? c1 : c2, stroke: cStem, "stroke-width": 4 })
          );
          if (p.sec > 0) nG.appendChild(el("circle", { cx: c.cx, cy: c.cy, r: c.r * 0.3, fill: c3 }));
          if (p.tert > 0 && idx > 0) {
            nG.appendChild(
              el("line", {
                x1: 0,
                y1: 0,
                x2: c.cx,
                y2: c.cy,
                stroke: cStem,
                "stroke-width": 2,
                "stroke-dasharray": "4 4",
              })
            );
          }
        });
      }
    } else {
      const stemG = el("g", {});

      if (p.arch === 3) {
        const sW = 14;
        stemG.appendChild(
          el("path", { d: `M ${-sW} 0 L ${sW} 0 L ${sW - 3} ${-p.stem} L ${-sW + 3} ${-p.stem} Z`, fill: cStem })
        );
        if (p.tert === 1 || p.tert === 3) {
          const ringY = -p.stem * 0.65;
          stemG.appendChild(
            el("path", {
              d: "M -22 0 C -25 15, -10 20, 0 20 C 10 20, 25 15, 22 0 Z",
              fill: c2,
              transform: `translate(0, ${ringY})`,
            })
          );
        }
        if (p.tert >= 2) {
          stemG.appendChild(el("path", { d: "M -35 0 C -35 -25, -15 -35, 0 -35 C 15 -35, 35 -25, 35 0 Z", fill: c3 }));
        }
      } else {
        // REVERTED 2026-10-01. This arm was `else if (!sitting || p.sec >= 2)`, where
        // sitting meant "arch 1 and prim 3", added so the Lithops pair of pebbles
        // would rest on the ground rather than stand on a stalk. Every other
        // archetype got a full-height stalk; this one was shortened to nothing.
        // Reverted: a dome on a stem is how the original drew it, and the plate is
        // an emblem, not a botanical illustration of a Lithops.
        stemG.appendChild(
          el("line", { x1: 0, y1: 0, x2: 0, y2: -p.stem, stroke: cStem, "stroke-width": 8, "stroke-linecap": "round" })
        );
      }
      g.appendChild(stemG);

      let maxLeaves = Math.min(p.lDens, Math.floor(p.stem / 30));
      if (p.lType > 0 && maxLeaves > 0 && p.arch !== 3) {
        const minLeafY = -p.stem * 0.2;
        const maxLeafY = -p.stem * 0.7;
        const stepY = maxLeaves > 1 ? (maxLeafY - minLeafY) / (maxLeaves - 1) : 0;

        for (let i = 0; i < maxLeaves; i++) {
          const y = maxLeaves === 1 ? (maxLeafY + minLeafY) / 2 : minLeafY + stepY * i;
          const scale = (0.35 + 0.35 * (1 - i / Math.max(1, maxLeaves - 1))) * Math.min(1, p.stem / 120);
          // REVERTED 2026-10-01. A leaf spacing cap used to sit here:
          // `scale = Math.min(scale, Math.abs(stepY) / 52)`, added because on a
          // tall stem carrying few leaves the fixed scale let neighbouring blades
          // overlap into one mass (Ficus rendered 0.641 instead of 0.7).
          // It also changed the leaf, not just the spacing, which is not a
          // spacing fix. Leaves touching is how the original drew them.
          let lPath = "";

          if (p.lType === 1) lPath = "M 0 0 C 20 -20, 40 -10, 40 0 C 40 10, 20 20, 0 0 Z";
          // REVERTED 2026-10-01. lType 2 was "M 0 0 Q 20 -15 35 -30 Q 15 -5 0 0 Z", a
          // two-segment sliver. I replaced it with a fuller cubic blade
          // ("M 0 0 C 12 -18, 30 -27, 44 -24 C 30 -10, 14 -3, 0 0 Z") because the
          // sliver "read as an arrowhead". Every other leaf type here is one or two
          // short curves; this became a third, deeper one, and the leaf sat heavier
          // than its neighbours on the same stem.
          else if (p.lType === 2) lPath = "M 0 0 Q 20 -15 35 -30 Q 15 -5 0 0 Z";
          else if (p.lType === 3) lPath = "M 0 0 C 15 -30, 45 -30, 45 0 C 45 30, 15 30, 0 0 Z";
          else if (p.lType === 4) lPath = "M 0 0 Q 20 -30 0 -60 Q -5 -20 0 0 Z";
          else if (p.lType === 5) lPath = "M 0 0 C 15 -10, 30 -30, 50 -20 C 30 -5, 15 10, 0 0 Z";
          else if (p.lType === 6) lPath = "M 0 0 C 10 -20, 30 -10, 25 0 C 40 -5, 45 15, 30 15 C 35 30, 10 30, 0 0 Z";
          // REVERTED 2026-10-01. lType 7 was "M 0 0 L 10 -15 L 5 -5 L 20 -10 L 10 0 L 25 5 L 15 10 Z",
          // a short zigzag. I lengthened it into a serrated blade, reasoning that the
          // zigzag read as "three stacked arrows". It is a leaf drawn with a few
          // straight strokes, which is the whole idiom of this file: the plates are
          // built from circles, triangles and short polylines, and a longer outline
          // broke that grammar without making the leaf better.
          else if (p.lType === 7) lPath = "M 0 0 L 10 -15 L 5 -5 L 20 -10 L 10 0 L 25 5 L 15 10 Z";

          const angle = p.arch === 4 ? 15 + p.sec * 10 : 20;
          const lColor = p.arch === 4 && p.tert > 1 && i % 2 === 0 ? c2 : c3;
          g.appendChild(
            el("path", { d: lPath, fill: lColor, transform: `translate(0, ${y}) scale(${scale}) rotate(${-angle})` })
          );
          g.appendChild(
            el("path", {
              d: lPath,
              fill: lColor,
              transform: `translate(0, ${y}) scale(-${scale}, ${scale}) rotate(${-angle})`,
            })
          );
        }
      }

      const hG = el("g", { transform: `translate(0, ${-p.stem})` });
      g.appendChild(hG);

      if (p.arch === 0) {
        const pCount = 6 + p.sec * 4;
        for (let i = 0; i < pCount; i++) {
          let pPath = "";
          if (p.prim === 0) pPath = "M -10 -15 L 0 -50 L 10 -15 Z";
          else if (p.prim === 1) pPath = "M -12 -15 C -20 -40, 20 -40, 12 -15 Z";
          else if (p.prim === 2) pPath = "M -8 -15 Q -15 -45 0 -60 Q 15 -45 8 -15 Z";
          else if (p.prim === 3) pPath = "M -2 -15 L -2 -60 L 2 -60 L 2 -15 Z";
          else pPath = "M -15 -15 C -30 -30, 0 -65, 0 -65 C 0 -65, 30 -30, 15 -15 Z";
          hG.appendChild(el("path", { d: pPath, fill: c1, transform: `rotate(${(360 / pCount) * i})` }));
        }
        hG.appendChild(el("circle", { cx: 0, cy: 0, r: 18, fill: cStem }));
        hG.appendChild(el("circle", { cx: 0, cy: 0, r: p.tert === 0 ? 0 : 12, fill: c2 }));
      } else if (p.arch === 1) {
        if (p.sec > 0) hG.appendChild(el("path", { d: "M -25 0 L 25 0 L 0 20 Z", fill: cStem }));
        // REVERTED 2026-10-01. Three separate changes were made to this archetype, all
        // aimed at making the Lithops read more like a Lithops, and all reverted:
        //   - prim 3 was given a hand-built pair of pebble bodies with a 10-unit
        //     fissure and a lit window, replacing the single cup shape below;
        //   - the calyx wedge was suppressed on prim 3 ("M -25 0 L 25 0 L 0 20 Z");
        //   - the stamens were suppressed on prim 3.
        // The reasoning was sound in each case -- a dome on a stalk does look like a
        // mushroom -- but the cup is what this file draws, and Lithops is one of 16
        // genera. A bespoke silhouette for one genus broke the shared vocabulary
        // that makes the plates read as one set.
        let cupD = "";
        if (p.prim === 0) cupD = "M -35 0 C -35 -40, -25 -60, 0 -60 C 25 -60, 35 -40, 35 0 Z";
        else if (p.prim === 1) cupD = "M -30 0 L -40 -50 L -15 -40 L 0 -60 L 15 -40 L 40 -50 L 30 0 Z";
        else if (p.prim === 2)
          cupD =
            "M -25 0 C -40 -30, -30 -70, -30 -70 C -15 -50, -10 -40, 0 -30 C 10 -40, 15 -50, 30 -70 C 30 -70, 40 -30, 25 0 Z";
        else if (p.prim === 3) cupD = "M -40 0 C -40 -20, -20 -30, 0 -30 C 20 -30, 40 -20, 40 0 Z";
        else cupD = "M -20 0 L -30 -40 A 15 15 0 0 1 0 -40 A 15 15 0 0 1 30 -40 L 20 0 Z";

        hG.appendChild(el("path", { d: cupD, fill: c1 }));
        if (p.tert > 0) {
          for (let i = -1; i <= 1; i++) {
            if (i === 0 && p.tert === 1) continue;
            hG.appendChild(el("line", { x1: i * 12, y1: -30, x2: i * 20, y2: -75, stroke: cStem, "stroke-width": 3 }));
            hG.appendChild(el("circle", { cx: i * 20, cy: -75, r: 5, fill: c2 }));
          }
        }
      } else if (p.arch === 2) {
        // REVERTED 2026-10-01. This was rewritten as a segmented bamboo culm --
        // 2-4 node bands, 3-5 fanned blades, a spread that widened with the secondary
        // slider -- because "a stack of blocks and discs" "read as a red box with a ball
        // balanced on it". The original is a rect body with a rounded top, a trapezoid
        // foot, and one of four head shapes. It is the least plant-like of the six
        // archetypes, and that is a fact about the file, not a defect to redesign: the
        // archetype is what a given genus resolves to, and all sixteen genera draw in
        // the same short geometric vocabulary for good reason. Replaced below with the
        // original four lines.
        if (p.tert === 0) hG.appendChild(el("path", { d: "M -40 0 A 40 40 0 0 0 40 0 Z", fill: cStem }));
        else if (p.tert === 1) hG.appendChild(el("path", { d: "M -30 0 L 30 0 L 15 20 L -15 20 Z", fill: cStem }));
        else if (p.tert === 2) hG.appendChild(el("path", { d: "M -45 0 C -45 20, 45 20, 45 0 Z", fill: c3 }));
        else if (p.tert === 3) hG.appendChild(el("rect", { x: -25, y: 0, width: 50, height: 15, fill: c2 }));
        else hG.appendChild(el("polygon", { points: "-35,0 35,0 20,25 -20,25", fill: cStem }));

        let midH = p.sec * 10 + 20;
        hG.appendChild(el("rect", { x: -35, y: -midH, width: 70, height: midH, fill: c1, rx: p.sec === 4 ? 20 : 0 }));

        const tY = -midH;
        if (p.prim === 0) hG.appendChild(el("path", { d: `M -35 ${tY} A 35 35 0 0 1 35 ${tY} Z`, fill: c2 }));
        else if (p.prim === 1)
          hG.appendChild(
            el("path", { d: `M -35 ${tY} L -45 ${tY - 40} L 0 ${tY - 20} L 45 ${tY - 40} L 35 ${tY} Z`, fill: c2 })
          );
        else hG.appendChild(el("circle", { cx: 0, cy: tY - 25, r: 25, fill: c3 }));
      } else if (p.arch === 3) {
        let capD = "";
        if (p.prim === 0) capD = "M -60 0 A 60 60 0 0 1 60 0 Z";
        else if (p.prim === 1) capD = "M -45 0 C -45 -30, -20 -70, 0 -70 C 20 -70, 45 -30, 45 0 Z";
        else if (p.prim === 2) capD = "M -75 0 C -50 -20, -20 -30, 0 -30 C 20 -30, 50 -20, 75 0 Z";
        else if (p.prim === 3) capD = "M -35 0 C -35 -15, -15 -60, 0 -60 C 15 -60, 35 -15, 35 0 Z";
        else if (p.prim === 4) capD = "M -55 0 C -60 -55, 60 -55, 55 0 Z";
        else if (p.prim === 5) capD = "M -40 -30 C -20 0, 20 0, 40 -30 C 20 -20, -20 -20, -40 -30 Z";
        else capD = "M -50 0 L -50 -10 A 20 20 0 0 1 -10 -10 A 20 20 0 0 1 30 -10 L 50 0 Z";

        const cPath = el("clipPath", { id: uid });
        cPath.appendChild(el("path", { d: capD }));
        svgDefs.appendChild(cPath);
        hG.appendChild(el("path", { d: capD, fill: c1 }));

        if (p.sec > 0) {
          const detG = el("g", { "clip-path": "url(#" + uid + ")" });
          if (p.sec === 1 || p.sec === 2) {
            const maxSpots = p.sec === 1 ? 5 : 12;
            const organicSpots = [
              [-25, -15, 5],
              [25, -15, 5],
              [0, -30, 6],
              [-40, -35, 4],
              [40, -35, 4],
              [-15, -50, 5],
              [15, -50, 5],
              [-55, -15, 3],
              [55, -15, 3],
              [0, -10, 4],
            ];
            for (let i = 0; i < maxSpots; i++) {
              if (organicSpots[i]) {
                detG.appendChild(
                  el("circle", {
                    cx: organicSpots[i][0],
                    cy: organicSpots[i][1],
                    r: organicSpots[i][2],
                    fill: isDark ? "#22252A" : c4,
                  })
                );
              }
            }
          } else if (p.sec >= 3) {
            const rayCount = p.sec === 3 ? 12 : 24;
            for (let i = 0; i <= rayCount; i++) {
              let factor = -1 + (2 / rayCount) * i;
              let xEnd = factor * 75;
              let cpX = factor * 30;
              detG.appendChild(
                el("path", {
                  d: `M ${xEnd * 0.2} 0 Q ${cpX} -30 ${xEnd} -80`,
                  stroke: c3,
                  "stroke-width": 2.5,
                  fill: "none",
                })
              );
            }
          }
          hG.appendChild(detG);
        }
      } else if (p.arch === 4) {
        if (p.prim === 0) hG.appendChild(el("polygon", { points: "0,-20 -10,0 0,5 10,0", fill: c2 }));
        else if (p.prim === 1) hG.appendChild(el("circle", { cx: 0, cy: 0, r: 14, fill: c1 }));
        // REVERTED 2026-10-01. Arch 4 prim 2 was a bare triangle, "M -12 0 L 0 -30 L 12 0 Z",
        // which I replaced with three small blades because the triangle read as a
        // traffic cone. It did look more like new growth. But arch 4 prim 2 is Ficus,
        // and the triangle is a fig: a single fruit hanging off the stem, the one thing
        // that silhouette is for. Three blades on every Ficus is a hedge, not a fig.
        else if (p.prim === 2) hG.appendChild(el("path", { d: "M -12 0 L 0 -30 L 12 0 Z", fill: c2 }));
        else if (p.prim === 3) {
          hG.appendChild(el("circle", { cx: 0, cy: -18, r: 10, fill: c1 }));
          hG.appendChild(el("circle", { cx: -12, cy: -2, r: 10, fill: c1 }));
          hG.appendChild(el("circle", { cx: 12, cy: -2, r: 10, fill: c1 }));
        } else if (p.prim === 4) hG.appendChild(el("path", { d: "M -14 0 C -14 -25, 14 -25, 14 0 Z", fill: c3 }));
        else if (p.prim === 5) hG.appendChild(el("rect", { x: -10, y: -15, width: 20, height: 20, fill: c1, rx: 4 }));
        // REVERTED 2026-10-01. This was a stroked open crozier curve
        // ("M 0 2 C -12 -4, -13 -22, 0 -24 C 12 -26, 17 -12, 8 -8 C 1 -5, -6 -12, 0 -15"),
        // which I drew because the filled lens below read as "a mushroom cap sitting
        // on the stem, which is the one thing a fern is not". True, and it was the only
        // shape in the file drawn as a stroke rather than a fill. Every other form in
        // the archetype table is a solid shape; this one broke that, and a lone open
        // curl among sixteen filled plates looked less like the set, not more.
        else hG.appendChild(el("path", { d: "M -15 -10 Q 0 -30 15 -10 Q 0 10 -15 -10 Z", fill: cStem }));
      }
    }

    return g;
  }

  // the per-person detail: 8 tiny glyphs in unit space (~-1..1)
  function glyph(kind, C) {
    const { stem, c1, c2, c3, paper, dew } = C;
    switch (kind) {
      case 0:
        return el("g", {}, [
          el("ellipse", { cx: 0, cy: 0, rx: 1, ry: 0.8, fill: c1 }),
          el("circle", { cx: 0, cy: -0.85, r: 0.4, fill: stem }),
          el("line", { x1: 0, y1: -0.75, x2: 0, y2: 0.8, stroke: stem, "stroke-width": 0.12 }),
          el("circle", { cx: -0.4, cy: -0.1, r: 0.14, fill: stem }),
          el("circle", { cx: 0.4, cy: 0.15, r: 0.14, fill: stem }),
        ]); // ladybug
      case 1:
        return el("g", {}, [
          el("ellipse", { cx: 0, cy: -0.75, rx: 0.5, ry: 0.3, fill: paper, stroke: stem, "stroke-width": 0.06 }),
          el("ellipse", { cx: 0, cy: 0, rx: 1, ry: 0.65, fill: c2 }),
          el("line", { x1: -0.25, y1: -0.6, x2: -0.25, y2: 0.6, stroke: stem, "stroke-width": 0.28 }),
          el("line", { x1: 0.3, y1: -0.6, x2: 0.3, y2: 0.6, stroke: stem, "stroke-width": 0.28 }),
        ]); // bee
      case 2:
        return el("g", {}, [
          el("ellipse", { cx: -0.6, cy: -0.35, rx: 0.6, ry: 0.45, fill: c1 }),
          el("ellipse", { cx: 0.6, cy: -0.35, rx: 0.6, ry: 0.45, fill: c1 }),
          el("ellipse", { cx: -0.45, cy: 0.4, rx: 0.4, ry: 0.3, fill: c2 }),
          el("ellipse", { cx: 0.45, cy: 0.4, rx: 0.4, ry: 0.3, fill: c2 }),
          el("line", { x1: 0, y1: -0.6, x2: 0, y2: 0.7, stroke: stem, "stroke-width": 0.16 }),
        ]); // butterfly
      case 3:
        return el("g", {}, [
          el("ellipse", { cx: 0.1, cy: 0.55, rx: 1, ry: 0.28, fill: c3 }),
          el("circle", { cx: -0.2, cy: 0, r: 0.7, fill: c1 }),
          el("circle", { cx: -0.2, cy: 0, r: 0.35, fill: c2 }),
        ]); // snail
      case 4:
        return el("g", {}, [
          el("path", {
            d: "M 0 -1 C .7 -.1 .8 .3 .8 .4 A .8 .8 0 0 1 -.8 .4 C -.8 .3 -.7 -.1 0 -1 Z",
            fill: C.dewFill,
            stroke: C.dew,
            "stroke-width": 0.1,
          }),
          el("circle", { cx: -0.25, cy: 0.3, r: 0.15, fill: C.dew, opacity: 0.55 }),
        ]); // dewdrop
      case 5:
        return el("g", {}, [
          el("line", { x1: 0, y1: 1, x2: 0, y2: 0, stroke: stem, "stroke-width": 0.14 }),
          el("path", { d: "M 0 .1 Q .9 -.1 .8 -.8 Q 0 -.6 0 .1 Z", fill: c3 }),
          el("path", { d: "M 0 .1 Q .9 -.1 .8 -.8 Q 0 -.6 0 .1 Z", fill: c3, transform: "scale(-1,1)" }),
        ]); // sprout
      case 6:
        return el("polygon", { points: "0,-1 .25,-.25 1,0 .25,.25 0,1 -.25,.25 -1,0 -.25,-.25", fill: c2 }); // sparkle
      default:
        return el("path", { d: "M .3 -1 A 1 1 0 1 0 .3 1 A 1.35 1.35 0 0 1 .3 -1 Z", fill: c2 }); // crescent moon (the inner arc used r=.75, smaller than half the chord, so it retraced the outer arc and enclosed no area: one person in eight got no companion)
    }
  }

  function plantSVG(profile, opts) {
    opts = opts || {};
    const dark = !!opts.dark,
      name = GENUS[profile.genus] ? profile.genus : "Ficus",
      seed = String(profile.seed || "anon");
    const p = resolveParams(Object.assign({}, profile, { genus: name })),
      C = personPalette(seed, p.arch, dark, profile.inks, name),
      rd = rngFor(seed + "|detail");
    const uid = "bp" + (hash(seed + name) % 1e6);

    const host = document.createElement("div");
    host.style.cssText = "position:fixed;left:-9999px;top:0;visibility:hidden";
    const svg = el("svg", { width: 800, height: 800 }),
      defs = el("defs", {}),
      rootG = el("g", {});
    svg.appendChild(defs);
    svg.appendChild(rootG);
    host.appendChild(svg);
    document.body.appendChild(host);
    rootG.appendChild(buildPlant(p, C, dark, uid, defs));
    // The plant's own box, measured before the detail glyph is added, so the glyph can be
    // placed relative to the PLANT (beside it, above it, on the ground next to it) rather
    // than to the plate. The frame itself is measured later, on plant + glyph together --
    // see the frame comment there for why that matters.
    const plantBox = rootG.getBBox();

    // per-person detail: WHICH glyph, which side and roughly how high depend ONLY on the seed (same draws, same order
    // as ever), so the companion never changes as the profile evolves. Exactly WHERE it sits is worked out from the
    // plant's own drawing, so it never touches it and never floats off.
    const bb = plantBox,
      kind = Math.floor(rd() * 8),
      side = rd() < 0.5 ? -1 : 1,
      hf = 0.2 + rd() * 0.6,
      pick = rd();
    const round = bb.width >= bb.height * 0.85; // ring / disc plants: the companion rests below them
    // Companion size follows the plant: a tenth of a round plant's width, a tenth of a tall plant's height.
    const size = round ? Math.max(20, Math.min(56, bb.width * 0.13)) : Math.max(16, Math.min(30, bb.height * 0.1)),
      gc = Object.assign({}, C, { c1: pick < 0.5 ? C.c1 : C.c2, c2: pick < 0.5 ? C.c2 : C.c1 });
    const onGround = GROUND.indexOf(kind) > -1,
      jit = onGround ? rd() : 0;
    const cx = bb.x + bb.width / 2;

    // Where the plant is: one entry per drawn element (stroke included), in the plate's own units. Almost every element
    // is kept as its bounding rectangle, which is a safe over-estimate. A round element (a ring, a disc) is kept as a
    // circle instead, because its rectangle would also claim the empty corners a companion can rest in.
    const origin = svg.getBoundingClientRect(),
      shapes = [];
    rootG.querySelectorAll("path,ellipse,circle,line,polygon,polyline,rect").forEach((e) => {
      const r = e.getBoundingClientRect();
      if (!r.width && !r.height) return;
      const sw = parseFloat(e.getAttribute("stroke-width")) || 0;
      const x0 = r.left - origin.left - sw / 2,
        y0 = r.top - origin.top - sw / 2,
        x1 = r.right - origin.left + sw / 2,
        y1 = r.bottom - origin.top + sw / 2;
      const w = x1 - x0,
        h = y1 - y0,
        tag = e.tagName.toLowerCase();
      if ((tag === "circle" || tag === "ellipse") && Math.abs(w - h) < 0.08 * Math.max(w, h))
        shapes.push({ circle: true, x: (x0 + x1) / 2, y: (y0 + y1) / 2, r: Math.max(w, h) / 2 });
      else shapes.push({ x0, y0, x1, y1 });
    });
    // The plate the plant alone would get (see FRAME below). A companion that fits inside it costs the plant nothing;
    // one that does not would force the plate wider and the plant smaller, so the search avoids that where it can.
    const A = opts.aspect > 0 ? opts.aspect : 0.79; // width / height of the plate the SVG is shown in
    const pad = Math.max(bb.width, bb.height) * 0.085 + 6;
    const natTop = bb.y - pad * 0.75;
    let natBottom = bb.y + bb.height + pad * 1.25;
    if (round) natBottom = Math.max(natBottom, bb.y + bb.height + size * 1.9 + pad * 0.5);
    const natHalfW = Math.max(bb.width / 2 + pad, ((natBottom - natTop) / 2) * A);
    const gap = size * 0.4; // breathing room between companion and plant
    // The companion's footprint in unit space is about x -1..1, y -1.25..1 (the ladybug's head is the tallest part).
    const clear = (x, y) => {
      const L = x - size,
        R = x + size,
        T = y - size * 1.25,
        B = y + size;
      return !shapes.some((sh) => {
        if (sh.circle) {
          const nx = Math.max(L, Math.min(sh.x, R)),
            ny = Math.max(T, Math.min(sh.y, B));
          return Math.hypot(sh.x - nx, sh.y - ny) < sh.r + gap;
        }
        return R + gap > sh.x0 && L - gap < sh.x1 && B + gap > sh.y0 && T - gap < sh.y1;
      });
    };
    // Nearest clear spot on one side of the plant at height y: walk outwards from the stem until nothing is in the way.
    const reach = (y, sd) => {
      for (let d = size * 0.9; d < bb.width / 2 + size * 4; d += size * 0.12) if (clear(cx + sd * d, y)) return d;
      return Infinity;
    };
    // Ground companions (and everything on a round plant) rest at the foot of the plant; floating ones hover at head
    // height, where a tall plant is widest. Either way: the preferred side and height first, then the nearest clear spot.
    // A round plant's companion sits just below its lowest edge, tucked into the corner the ring leaves empty.
    const groundY = round ? bb.y + bb.height + size * 0.7 : bb.y + bb.height - size * 0.35;
    const prefY = bb.y + bb.height * (0.22 + 0.42 * hf);
    const heights =
      onGround || round
        ? [groundY]
        : [0.2, 0.28, 0.36, 0.44, 0.52, 0.6, 0.68, 0.76]
            .map((f) => bb.y + bb.height * f)
            .sort((u, v) => Math.abs(u - prefY) - Math.abs(v - prefY));
    let best = null;
    heights.forEach((y, i) => {
      [side, -side].forEach((sd) => {
        const d = reach(y, sd);
        if (d === Infinity) return;
        // prefer the seed's side and height, then whichever spot hugs the plant most closely
        const over = Math.max(0, d + size - (natHalfW - pad * 0.3)); // how far it would push the plate wider
        const cost = d + over * 4 + (sd === side ? 0 : size * 1.2) + i * size * 0.2;
        if (!best || cost < best.cost)
          best = { cost, x: cx + sd * (d + (onGround || round ? jit * size * 0.4 : 0)), y };
      });
    });
    const gx = best ? best.x : cx + side * (bb.width / 2 + size * 2),
      gy = best ? best.y : groundY;
    const gl = glyph(kind, gc);
    // A thin paper-coloured edge, drawn outside the fill, so a companion never merges into a part of its own colour.
    (gl.tagName === "g" ? [...gl.querySelectorAll("*")] : [gl]).forEach((e) => {
      if (e.hasAttribute("stroke")) return;
      e.setAttribute("stroke", C.paper);
      e.setAttribute("stroke-width", ".1");
      e.setAttribute("paint-order", "stroke");
      e.setAttribute("stroke-linejoin", "round");
    });
    // The glyph is drawn facing the side it is on (scale x by -1 on the left), so a snail or a ladybug looks inwards.
    const faces = gx < cx ? -1 : 1;
    gl.setAttribute(
      "transform",
      "translate(" +
        gx.toFixed(1) +
        "," +
        gy.toFixed(1) +
        ") scale(" +
        (faces * size).toFixed(1) +
        "," +
        size.toFixed(1) +
        ")"
    );
    rootG.appendChild(gl);

    // FRAME. The plate is centred on the PLANT and sized from the plant, so a given plant is always the same size and in
    // the same place whichever companion it has. Round plants reserve room below for their companion; for all other
    // plants the plate's own proportions (wider than the plant) leave room beside it. If a companion still would not
    // fit, the frame grows just enough to hold it.
    const gb = gl.getBBox(),
      gm = gl.transform.baseVal.consolidate().matrix;
    const gX = [gb.x * gm.a + gm.e, (gb.x + gb.width) * gm.a + gm.e],
      gY0 = gb.y * gm.d + gm.f,
      gY1 = (gb.y + gb.height) * gm.d + gm.f;
    let top = natTop,
      bottom = natBottom;
    let left = Math.min(cx - natHalfW, Math.min(...gX) - pad * 0.4),
      right = Math.max(cx + natHalfW, Math.max(...gX) + pad * 0.4);
    top = Math.min(top, gY0 - pad * 0.4);
    bottom = Math.max(bottom, gY1 + pad * 0.4);
    // keep the plant on the plate's vertical axis; widen symmetrically if the companion needed more room on one side
    const halfW = Math.max(cx - left, right - cx);
    let hw = halfW,
      hh = (bottom - top) / 2;
    const fcx = cx,
      fcy2 = (top + bottom) / 2;
    if (hw / hh < A) hw = hh * A;
    else hh = hw / A;
    const out =
      '<svg xmlns="' +
      NS +
      '" viewBox="' +
      [fcx - hw, fcy2 - hh, 2 * hw, 2 * hh].map((n) => n.toFixed(1)).join(" ") +
      '" class="plant" data-paper="' +
      C.paper +
      '" role="img" aria-label="' +
      name +
      ' plant">' +
      (defs.childNodes.length ? defs.outerHTML : "") +
      rootG.outerHTML +
      "</svg>";
    document.body.removeChild(host);
    return out;
  }

  root.HolotypePlant = {
    svg: plantSVG,
    params: resolveParams,
    newSeed: () => Math.random().toString(36).slice(2, 10),
    genera: Object.keys(GENUS),
    tribes: Object.keys(TRIBE_MOD),
    paletteCount: PALETTES.length,
  };
})(window);
