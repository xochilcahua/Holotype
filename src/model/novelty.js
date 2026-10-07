// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

/* "HOW NEW WOULD THIS BE TO ME?" Scores every unrated form against what the reader
already has, so the garden can sort by how much of their practice a thing opens
up. Needs DIST. Gives NOVELTY, computeNovelty(), tierFor().
   See docs/architecture.md. */

// ---------------------------------------------------------------------------
const NOVELTY = {
  neighbours: 10,
  localBlend: 0.9,
  kernelPower: 3,
  extraEvidence: 0.4,
  familiarMax: 40,
  newMin: 70,
  newestShare: 1 / 3,
  masteryExponent: 0.75,
};

const NEIGHBOUR_DISTANCE = ART_FORMS.map((_, i) => {
  const row = [];
  for (let j = 0; j < N; j++) if (j !== i) row.push(DIST[i][j]);
  row.sort((x, y) => x - y);
  return row[NOVELTY.neighbours - 1];
});
// The median of NEIGHBOUR_DISTANCE across the catalogue: how far apart neighbouring forms normally are. Used to
// scale novelty scores.
const TYPICAL_NEIGHBOUR_DISTANCE = (() => {
  const v = NEIGHBOUR_DISTANCE.slice().sort((x, y) => x - y);
  return (v[(N - 1) >> 1] + v[N >> 1]) / 2;
})();
/* ==========================================================================
   SEARCH AND NOVELTY
   --------------------------------------------------------------------------
   Two separate jobs, often confused:
     search()          "did I type a name?" - a lookup. Name hits outrank alias
                       hits, prefix outranks mid-word. See its own note.
     computeNovelty()  "what is near my taste?" - the real question. For every
                       unrated form, a distance to the rated ones, blended so a
                       strong rating pulls harder than a faint one, then turned
                       into a 0-1 "how much do I already know this" score.
   The reach slider is `discount`: it scales how far a rating reaches, so turning
   it down makes everything look further away and the "closest first" list
   tightens around your own field.
   ========================================================================== */
const BANDWIDTH = NEIGHBOUR_DISTANCE.map(
  (k) => Math.pow(k, NOVELTY.localBlend) * Math.pow(TYPICAL_NEIGHBOUR_DISTANCE, 1 - NOVELTY.localBlend)
);
// Maps the 'reach' slider (0 to 1, default 0.5) to a distance scale between 0.6 and 1.4.
function reachScale(discount) {
  return 0.6 + 0.8 * discount;
} // slider 0..1, default 0.5 -> 1.0

// Names the band a novelty score falls in: familiar (up to 40), borderline, or uncharted (over 70).
function tierFor(score) {
  if (score <= NOVELTY.familiarMax) return "high_overlap";
  if (score <= NOVELTY.newMin) return "borderline";
  return "uncharted";
}

let _noveltyKey = null,
  _noveltyCache = null;
// Returns { byId: { id: { score, raw, tier, nearestId, tie } }, order: [ids, newest first] }.
// mastery: { artFormId: 0-10 }. The result is cached until the ratings or the reach setting change.
function computeNovelty(mastery, discount) {
  const rated = [];
  for (const id of Object.keys(mastery)) if (mastery[id] > 0 && id in INDEX) rated.push([INDEX[id], mastery[id]]);
  rated.sort((a, b) => a[0] - b[0]);
  const key = rated.map((r) => r[0] + ":" + r[1]).join(",") + "|" + discount;
  if (key === _noveltyKey) return _noveltyCache;

  const byId = {},
    scale = reachScale(discount),
    isRated = new Set(rated.map((r) => r[0])),
    cands = [];
  for (let x = 0; x < N; x++) {
    const a = ART_FORMS[x];
    if (isRated.has(x)) {
      // something you rated reads as familiar because you know it
      const score = Math.max(1, Math.round((10 - mastery[a.id]) * 10));
      byId[a.id] = { score, raw: score, tier: tierFor(score), nearestId: null, tie: 0, promoted: false };
      continue;
    }
    if (rated.length === 0) {
      byId[a.id] = { score: 100, raw: 100, tier: "uncharted", nearestId: null, tie: Infinity, promoted: false };
      cands.push(a.id);
      continue;
    }
    let best = 0,
      bestR = -1,
      minRel = Infinity;
    const f = [];
    for (const [r, m] of rated) {
      const rel = DIST[x][r] / (BANDWIDTH[r] * scale);
      const fam = Math.pow(m / 10, NOVELTY.masteryExponent) * Math.pow(2, -Math.pow(rel, NOVELTY.kernelPower));
      f.push(fam);
      if (fam > best) {
        best = fam;
        bestR = r;
      }
      if (rel < minRel) minRel = rel;
    }
    let rest = 1,
      skipped = false;
    for (const fam of f) {
      if (!skipped && fam === best) {
        skipped = true;
        continue;
      }
      rest *= 1 - NOVELTY.extraEvidence * fam;
    }
    const raw = 100 * (1 - best) * rest;
    const score = Math.max(1, Math.min(100, Math.round(raw)));
    byId[a.id] = {
      score,
      raw,
      tier: tierFor(score),
      nearestId: bestR >= 0 ? ART_FORMS[bestR].id : null,
      tie: minRel,
      promoted: false,
    };
    cands.push(a.id);
  }
  const order = cands
    .slice()
    .sort((p, q) => byId[q].raw - byId[p].raw || byId[q].tie - byId[p].tie || (p < q ? -1 : 1));
  if (rated.length > 0) {
    // keep the New ground list from running dry as you rate more
    const promote = Math.ceil(cands.length * NOVELTY.newestShare);
    let taken = 0;
    for (const id of order) {
      if (taken >= promote) break;
      if (byId[id].score > NOVELTY.familiarMax) {
        if (byId[id].tier !== "uncharted") byId[id].promoted = true;
        byId[id].tier = "uncharted";
        taken++;
      }
    }
  }
  _noveltyKey = key;
  _noveltyCache = { byId, order };
  return _noveltyCache;
}

// Returns { score, raw, tier, nearestId, tie } for one art form.
function noveltyScore(candidateId, mastery, masteryDiscount) {
  return computeNovelty(mastery, masteryDiscount).byId[candidateId];
}

// Closest OTHER art forms for the "Related" list (hub-corrected, symmetric).
function relatedByVector(candidateId, n = 5) {
  const ci = INDEX[candidateId];
  const out = [];
  for (let j = 0; j < N; j++) if (j !== ci) out.push({ d: REL[ci][j], id: ART_FORMS[j].id });
  out.sort((x, y) => x.d - y.d);
  return out.slice(0, n).map((x) => x.id);
}

// ---- Search ----
// Matches the name (anywhere), the hidden alias list (start of a word), and the one-line summary
// (start of a word, 3+ letters). Typos of up to 2 letters are tolerated on name and alias words.
function levenshtein(a, b, maxDist) {
  if (Math.abs(a.length - b.length) > maxDist) return maxDist + 1;
  let prev = new Array(b.length + 1);
  for (let j = 0; j <= b.length; j++) prev[j] = j;
  for (let i = 1; i <= a.length; i++) {
    const cur = new Array(b.length + 1);
    cur[0] = i;
    for (let j = 1; j <= b.length; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost);
    }
    prev = cur;
  }
  return prev[b.length];
}

// How many typos a search term may contain, by its length: none up to 3 letters, one up to 5, otherwise two.
function boundedEditDistanceForQuery(qlen) {
  if (qlen <= 3) return 0;
  if (qlen <= 5) return 1;
  return 2;
}

// True when `q` occurs at the start of a word in `text`.
function startsAWord(text, q) {
  let i = text.indexOf(q);
  while (i !== -1) {
    if (i === 0 || /[^a-z0-9]/.test(text[i - 1])) return true;
    i = text.indexOf(q, i + 1);
  }
  return false;
}

// Case-, accent- and apostrophe-insensitive form used for all matching ("mache" finds Papier-Mâché).
function fold(s) {
  return String(s)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/['\u2019\u02bb`]/g, "")
    .toLowerCase();
}

// Free-text search over names and aliases with typo tolerance. Returns art-form ids, best match first.
function search(query, limit = 200) {
  const q = fold(query.trim());
  if (!q) return ART_FORMS.map((a) => a.id);
  // Rank a hit on the form's own NAME above a hit on someone else's alias that
  // happens to contain the same word. Without this, searching "Ikebana" put
  // Floral Design first (its alias says "Japanese flower arrangement"), and
  // searching "Opera" put Cinematography first. The results were still there,
  // just below an unrelated form, which reads as "this catalog has no Ikebana".
  const direct = ART_FORMS.filter((a) => {
    const name = fold(a.name + " " + t(a.name)),
      aka = fold(a.aka || ""),
      tag = fold((a.tag || "") + " " + t(a.tag || ""));
    return name.includes(q) || startsAWord(aka, q) || (q.length >= 3 && startsAWord(tag, q));
  })
    .sort((a, b) => {
      const an = fold(t(a.name)).includes(q) || fold(a.name).includes(q) ? 0 : 1;
      const bn = fold(t(b.name)).includes(q) || fold(b.name).includes(q) ? 0 : 1;
      if (an !== bn) return an - bn;
      // then a prefix hit beats a hit buried mid-name ("dance" in "folk and traditional dance")
      const ap = fold(t(a.name)).startsWith(q) || fold(a.name).startsWith(q) ? 0 : 1;
      const bp = fold(t(b.name)).startsWith(q) || fold(b.name).startsWith(q) ? 0 : 1;
      return ap - bp;
    })
    .map((a) => a.id);
  if (direct.length > 0) return direct.slice(0, limit);
  // Nothing matched directly: tolerate typos.
  const maxEdit = boundedEditDistanceForQuery(q.length);
  if (maxEdit === 0) return [];
  return ART_FORMS.filter((a) => {
    const tokens = fold(a.name + " " + t(a.name) + " " + (a.aka || ""))
      .split(/[\s/&,()·-]+/)
      .filter(Boolean);
    return tokens.some((tok) => levenshtein(q, tok, maxEdit) <= maxEdit);
  })
    .map((a) => a.id)
    .slice(0, limit);
}

// ---- Easily-confused-by-name: word-token overlap on the NAME only, not the vector ----
function nameTokens(name) {
  return new Set(
    fold(name)
      .split(/[^a-z]+/)
      .filter((w) => w.length >= 4)
  );
}

// Other art forms whose names share words with this one: the candidates for 'easily confused with'.
function confusableByName(candidateId, threshold = 0.18, n = 5) {
  const candidateTokens = nameTokens(BY_ID[candidateId].name);
  const scored = [];
  for (const a of ART_FORMS) {
    if (a.id === candidateId) continue;
    const otherTokens = nameTokens(a.name);
    if (candidateTokens.size === 0 || otherTokens.size === 0) continue;
    const overlap = [...candidateTokens].filter((t) => otherTokens.has(t));
    if (overlap.length === 0) continue;
    const union = new Set([...candidateTokens, ...otherTokens]);
    const jaccard = overlap.length / union.size;
    if (jaccard >= threshold) scored.push({ sim: jaccard, id: a.id });
  }
  scored.sort((x, y) => y.sim - x.sim);
  return scored.slice(0, n).map((x) => x.id);
}

// ---- Auto-generated short description from the most distinctive axis values ----
// Each entry is [text when the axis is LOW, text when it is HIGH]; null means that end says
// nothing useful ("not an especially visual medium") and is never used.
// Polarity below was checked against the data (e.g. Improv Theater is a1 = 0.006, so a1 LOW = improvised).
// Every axis must have an entry here; describeArtForm skips any that don't, so adding an axis
// can no longer break the detail view.
