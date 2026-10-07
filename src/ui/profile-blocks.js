// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

/* THE PLATE BLOCKS, SHARED BY THE SCREEN AND THE PDF. The plant, the genus word and
the two short Latin notes, written once and rendered in both places so the screen
and the printout cannot say different things.
   See docs/architecture.md. */

// What an axis bar says when the marker sits toward one pole: [leaning, strongly]. Each phrase is written out in
// full, in English, so every language gets one whole sentence-piece to translate instead of "Leans" + a lowercased
// pole word, which cannot work where gender, case or word order change the wording.
const AXIS_POLE_READING = {
  Focused: [sourceText("Leans focused"), sourceText("Strongly focused")],
  Wide: [sourceText("Leans wide"), sourceText("Strongly wide")],
  Improvised: [sourceText("Leans improvised"), sourceText("Strongly improvised")],
  Planned: [sourceText("Leans planned"), sourceText("Strongly planned")],
  Solo: [sourceText("Leans solo"), sourceText("Strongly solo")],
  Collaborative: [sourceText("Leans collaborative"), sourceText("Strongly collaborative")],
  Literal: [sourceText("Leans literal"), sourceText("Strongly literal")],
  Interpretive: [sourceText("Leans interpretive"), sourceText("Strongly interpretive")],
  Repeatable: [sourceText("Leans repeatable"), sourceText("Strongly repeatable")],
  "Chance-led": [sourceText("Leans chance-led"), sourceText("Strongly chance-led")],
};

// Shared by the Herbarium page (cls "prof") and the PDF (cls "pe"): plant + big genus name, the
// modifiers small beneath it, the readings, then the five axis bars with a plain-text reading
// each (text survives any print quirk that drops colored bar fills).
function growthPatternHTML(bc, cls, accent, dark) {
  const clampPct = (z) => Math.round(Math.max(0, Math.min(100, ((z + 2) / 4) * 100)));
  const close = new Set(bc.closeAxes || []);
  // Marker position: 50 is the midpoint. For the four z-scored axes it is where the person sits
  // relative to the AVERAGE PERSON - see PEOPLE_MEAN / PEOPLE_SD, which is why these are
  // person-space and not form-space. Breadth is anchored on the largest-field share, with the
  // classification cutoff (BREADTH.topShare) sitting exactly on the midpoint: left of centre =
  // Focused, right of centre = Wide. Same shape as before, but driven by the number the rule
  // actually uses, so the bar and the tribe can never disagree.
  const breadthPct = bc.breadthUnproven
    ? 50
    : bc.topShare >= BREADTH.topShare
      ? Math.max(0, Math.round((50 * (1 - bc.topShare)) / (1 - BREADTH.topShare)))
      : Math.min(100, Math.round(50 + (50 * (BREADTH.topShare - bc.topShare)) / (BREADTH.topShare - 0.3)));
  // The reading is words, not a percentage: these positions say where you sit among other people
  // on that axis, not a share of anything. "Close to the middle" is the dead-band case: the sign
  // test that picks this side of the line is inside its margin of error, so we say that instead of
  // claiming a leaning. It shows as an outlined marker rather than a filled one.
  const axisBar = (lo, hi, pct, close) => {
    const off = pct - 50,
      mag = Math.abs(off);
    const reading = close
      ? tx("Close to the middle")
      : mag < 6
        ? tx("Near the middle")
        : t(AXIS_POLE_READING[off > 0 ? hi : lo][mag < 20 ? 0 : 1]);
    const mark = close ? ` outline:2px solid ${accent};outline-offset:1px;` : ``;
    return `
    <div class="${cls}-axisbar-row">
      <span class="${cls}-axisbar-pole lo">${esc(t(lo))}</span>
      <span class="${cls}-axisbar-track"><span class="${cls}-axisbar-marker" style="left:${pct}%;background:${accent};${mark}"></span></span>
      <span class="${cls}-axisbar-pole hi">${esc(t(hi))}</span>
      <span class="${cls}-axisbar-val">${esc(t(reading))}</span>
    </div>`;
  };
  const leansPlain = bc.leans.map((t) => tx(TRIBE_PLAIN[t]));
  // Botanical style: rank abbreviation upright, Latin epithet in italics. Hover text gives the plain meaning.
  const mods = bc.early
    ? i18nHTML`<span class="mod" title="Too early to say: rate a few more art forms"><span class="mod-rank">var.</span> <i class="mod-name">indeterminata</i></span>`
    : i18nHTML`<span class="mod" title="Variety (var.): ${esc(t(bc.regime.label).toLowerCase())}"><span class="mod-rank">var.</span> <i class="mod-name">${esc(bc.regime.word)}</i></span>${bc.leans.length ? i18nHTML`<span class="mod" title="Compare (cf.): leans toward ${esc(leansPlain.join(t(" and ")))}"><span class="mod-rank">cf.</span> <i class="mod-name">${bc.leans.map((t) => esc(TRIBE_EPITHET[t])).join(' <span class="mod-and">et</span> ')}</i></span>` : ""}`;
  // The volume-gated copy. If this genus makes claims about how much the reader makes and the
  // reader has not kept enough to support one, the thin variant is used instead. See GENUS_VOLUME.
  const vol = !bc.early && !bc.keptEnough && GENUS_VOLUME[bc.genusId] ? GENUS_VOLUME[bc.genusId] : null;
  // GENUS_EXTRA first, then the thin variant on top, so the gated copy wins where it applies.
  const ex = Object.assign(
      {},
      GENUS_EXTRA[bc.genusId] || {},
      vol ? { more: vol.thinMore, thrives: vol.thinThrives, wilts: vol.thinWilts, gets: vol.thinGets } : {}
    ),
    plain = leansPlain.join(t(" and "));
  // Glosses the Latin epithet once, properly. The old line read "eloquens et fragrans — also
  // leaning toward language and food and scent", which asserted the same fact twice and left
  // "also" pointing at nothing. Now the epithet is simply translated, and the long-form gloss
  // lives in the tooltip.
  const glossShort = bc.leans.map((t) => tx(TRIBE_GLOSS[t] || TRIBE_PLAIN[t]).split(" \u2014 ")[0]);
  const glossLong = bc.leans.map((t) => tx(TRIBE_GLOSS[t] || TRIBE_PLAIN[t])).join("; ");
  const leanHead = `<b title="${esc(glossLong)}"><i>${bc.leans.map((t) => esc(TRIBE_EPITHET[t])).join(" et ")}</i> \u2014 ${esc(glossShort.join(", "))}.</b>`;
  // A lean resting on only two or three forms gets the descriptive form of the sentence, not the
  // disposition form. The lean is real either way - it clears the same lift and evidence gate -
  // but two forms is not enough to say what kind of person someone is.
  const leanThin =
    bc.leans.length > 0 && bc.leans.every((t) => (bc.domainZ.find((d) => DOMAIN_TRIBE[d.ax] === t) || {}).nHi <= 3);
  const readText = bc.leans.map((t) => tx(leanThin ? TRIBE_READ_THIN[t] : TRIBE_READ[t])).join(" ");
  let leanLine = bc.early
    ? i18nHTML`<b>Too early to say what you're drawn to</b> \u2014 rate a few more and this will fill in.`
    : bc.leans.length
      ? i18nHTML`${leanHead} ${esc(readText)} ${esc(t(REGIME_TIE[bc.regimeId]))} <span class="muted">This part reflects what you've rated so far more than who you are; it'll shift as you rate more.</span>`
      : i18nHTML`<b>No single domain stands out yet</b> \u2014 your ratings are spread fairly evenly across fields, which is its own kind of signal: you follow the idea, not the medium.`;
  // Spread across fields but with almost nothing behind it is not breadth, it is thinness. Say so
  // here rather than letting the bar sit on the midpoint unexplained.
  if (bc.breadthUnproven) {
    leanLine +=
      bc.breadthUnprovenWhy === "fields"
        ? i18nHTML` <b>Even, but across too little.</b> Nothing here holds more than ${Math.round(bc.topShare * 100)}% of what you rated, which would normally read as broad \u2014 but breadth needs at least ${BREADTH.minCats} fields you have kept doing (rated 3 or higher), and you have ${bc.keptCategories === 1 ? tx("one") : bc.keptCategories}. Two fields is a choice, not a range. It widens on its own as you rate things elsewhere.`
        : i18nHTML` <b>Spread wide but not far.</b> No single field holds more than ${Math.round(bc.topShare * 100)}% of what you have rated, which normally reads as broad \u2014 but ${bc.topKept === 0 ? tx("nothing") : bc.topKept === 1 ? tx("only one thing") : tx`only ${bc.topKept} things`} in the whole list ${t(bc.topKept === 1 ? "goes" : "go")} beyond a first try, so it counts as unproven rather than wide. Rate a few things you have actually kept doing and the width will mean something.`;
  }
  // Same idea for sociability: if everything rated is an umbrella item, there is nothing to say
  // about whether this person works alone or with others, and the page should say that.
  if (bc.socUmbrellaOnly) {
    leanLine += i18nHTML` <b>Alone or with others: not called.</b> Everything you have rated so far is a broad category rather than a specific practice, and those cannot say whether you work on your own or with people \u2014 a guitar in a bedroom and a guitar in an orchestra are the same answer here. Rate a specific form or two and this settles quickly.`;
  }
  // "Gets on with" was a dating-app reading and named exactly one other profile, which made the
  // other fifteen feel like near-misses. This is about how a working style meets other working
  // styles, so it names several and says what each one is actually for.
  const noteRows = ex.thrives
    ? [
        [tx("Thrives on"), ex.thrives],
        [tx("Wilts when"), ex.wilts],
        [tx("Shares ground with"), ex.gets],
      ]
    : [];
  const notes = !noteRows.length
    ? ""
    : cls === "prof"
      ? i18nHTML`<dl class="prof-fieldnotes"><div class="prof-fieldnotes-h">Field notes</div>${noteRows.map(([k, v]) => `<dt>${k}</dt><dd>${esc(t(v))}</dd>`).join("")}</dl>`
      : `<p class="pe-fieldnotes">${noteRows.map(([k, v]) => `<b>${k}:</b> ${esc(t(v))}`).join(" &middot; ")}</p>`;
  const note = growthEarlyNote(bc);
  // With very few ratings the genus paragraph is a confident paragraph about a person the app has barely
  // met. The tribe is still named - that is the point of the page, and a first guess is how a horoscope
  // works - but it opens as an invitation to keep going rather than as a disclaimer.
  // The genus paragraph itself also asserts volume ("Volume matters more than dwelling: making a
  // lot, quickly, is the point", "a dozen half-started projects"), so the thin variant replaces the
  // sentence rather than the paragraph. Same gate, same reason as GENUS_VOLUME.
  const thinGenus = vol
    ? {
        "1001":
          "You take things up quickly, alone, with no plan going in, playing loosely with the form each time rather than settling on one version of it. What separates this from simply being scattered is that you keep starting \u2014 the instinct is to begin, not to finish. Like the duckweed you are named for, you cover a surface rather than dig into it. The work is in finding the one worth digging into; until then, the range is real and the depth is not.",
        "1000":
          tx("You cover a wide range, alone, with no plan going in, taking things mostly at face value. The method resembles the slime mold you are named for: spread out, find the shortest route to something workable, keep what is useful and move on. That is not scatter, it is efficiency across a large territory. Because you move on before the long focus arrives, the range is easier to see than the depth \u2014 a written list of what you have tried tends to make it obvious."),
      }[bc.genusId]
    : null;
  const genusText = bc.early
    ? i18nHTML`<span class="${cls}-genus-hedge">Early days, but something is already showing \u2014 and it will sharpen as you rate more:</span> ${esc(t(bc.genus.text))}`
    : esc(t(thinGenus || bc.genus.text));
  return `
    ${note ? `<p class="${cls}-early-note-line muted">${esc(note)}</p>` : ""}
    <div class="${cls}-growth">
      ${cls === "prof" ? `<div class="prof-growth-side">${plantBlock(cls, bc, dark)}${notes}</div>` : plantBlock(cls, bc, dark)}
      <div class="${cls}-growth-main">
        <div class="${cls}-genus" style="color:${accent}">${esc(bc.genus.name)}</div>
        ${ex.tribe ? `<div class="${cls}-tribe">${esc(t(ex.tribe))}</div>` : ""}
        <div class="${cls}-mods">${mods}</div>
        <div class="${cls}-growth-body">
          <p>${genusText}</p>
          ${ex.more ? `<p>${esc(t(ex.more))}</p>` : ""}
          ${
            bc.early
              ? ""
              : bc.keptEnough
                ? `<p><b><i>${esc(bc.regime.word)}</i> \u2014 ${esc(t(bc.regime.label).toLowerCase())}.</b> ${esc(t(bc.regime.text))} ${esc(t(REGIME_EXTRA[bc.regimeId]))}</p>`
                : // Fewer than 5 forms at 3 or above: the paragraph's advice and its "the risk is that clients and
                  // schedulers..." are claims about how someone works, and a list of things tried once cannot
                  // carry them. Keep the one-line description, say what it rests on, drop the advice.
                  i18nHTML`<p><b><i>${esc(bc.regime.word)}</i> \u2014 ${esc(t(bc.regime.label).toLowerCase())}.</b> ${esc(t(bc.regime.text).split(". ")[0].replace(/\.$/, ""))}. <span class="muted">That rests on ${bc.topKept ? tx`${i18nCount(bc.topKept, "thing", "things")} you have kept` : tx("things you have mostly tried once")}, so treat it as a first guess.</span></p>`
          }
          <p class="${cls}-lean">${leanLine}</p>
          ${cls === "prof" ? "" : notes}
        </div>
      </div>
    </div>
    <div class="${cls}-axisbars">
      ${axisBar("Focused", "Wide", breadthPct, bc.breadthUnproven)}
      ${axisBar("Improvised", "Planned", clampPct(bc.zProcess), close.has("a1"))}
      ${axisBar("Solo", "Collaborative", clampPct(bc.zSoc), close.has("d1"))}
      ${axisBar("Literal", "Interpretive", clampPct(bc.zForm), close.has("a4"))}
      ${axisBar("Repeatable", "Chance-led", clampPct(bc.zRegime), false)}
      ${close.size && cls === "prof" ? i18nHTML`<p class="${cls}-axisbar-note muted">One or more of these sits right on the middle line, where the honest answer is ${close.size > 1 ? tx("both at once") : tx("a bit of both")}. That is a common place to land, not a flaw \u2014 and the type above still holds either way.</p>` : ""}
    </div>`;
}

// Print version: heading plus the shared block.
function classificationSection(bc, accent) {
  if (!bc) return "";
  return i18nHTML`<h2 style="border-bottom-color:${accent}">Growth Habit</h2>${growthPatternHTML(bc, "pe", accent, false)}`;
}

// ---------------------------------------------------------------------------
// PROFILE PAGE (on-screen): the full, comprehensive view - portrait, classification, tags,
// garden, filters - themed with the app's normal light/dark tokens rather than the print
// stylesheet, since this is a page you're meant to read on screen, not just print.

const EXPORT_SECTION_LABELS = {
  portrait: "Holotype & stats",
  classification: "Growth habit",
  filters: "Session filters",
  garden: "Your garden (rated list)",
  unexplored: "Not yet explored",
};
