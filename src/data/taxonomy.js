// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

/* PARENT AND CHILD RELATIONSHIPS. Dance sits over Flamenco, Capoeira and Chinese
Opera because those change what the practice IS; styles of dancing live inside
Dance instead. PARENT_WHY is the argument made when a row is asked why it has
children. Needs ART_FORMS. Gives HIERARCHY, PARENT_WHY, breadcrumb().
   See docs/architecture.md. */

// ---------------------------------------------------------------------------
const HIERARCHY = {
  // ---- Performance & Movement -------------------------------------------
  // Dance is the ROLE. Its children are only the traditions that change what the
  // practice physically is: Capoeira (a fight and a dance), Flamenco (song, dance
  // and guitar as one thing), Chinese Opera (voice, movement and acrobatics as one
  // thing). Ballet, hip-hop, tap, ballroom, belly, folk and the regional traditions
  // are NOT here: they are styles of the role and were collapsed into af053 itself,
  // where their keywords and their names still live.
  af053: ["af250", "af260", "af268", "af303"],

  // ---- Music & Sound ---------------------------------------------------
  af039: ["af265"],
  af037: ["af171", "af188", "af189"],
  af118: ["af042"],
  af041: ["af043"],
  af040: ["af046"],

  // ---- Visual Arts -----------------------------------------------------
  af009: ["af183", "af121", "af133", "af184"], // fresco, icon, sign, airbrush
  af008: ["af142", "af185", "af141", "af236"], // caricature, scratchboard, storyboard, mandala
  af013: ["af016", "af139", "af143"], // botanical, concept, editorial
  af010: ["af302"],
};

// Why each parent is still a row and not just a heading. A parent that names no practice
// of its own is a duplicate of its children and should be dropped; these do name one, and
// this is the argument, kept next to the map it defends so the two cannot drift apart.
// Read by holotype_audit/audit_umbrellas.py, which fails any 3+ child parent that appears
// here without also narrowing itself in its own tag.
const PARENT_WHY = {
  af053:
    "Moving to music without training in a named tradition. Ballet, Hip-Hop and Flamenco all require committing to one; dancing in your kitchen to a record does not. This is the row for someone who does not yet know which tradition they want.",

  af009:
    "Painting for its own sake, with a brush, to make a picture. Fresco, icon, sign and airbrush painting each have an application they serve; the plain row is painting that serves none of them.",
  af008:
    "Drawing from observation, for its own sake. Caricature exaggerates a likeness, Scratchboard cuts into a surface, Storyboarding serves a script and Mandala Art follows a fixed geometry. None of them is drawing a still life because you wanted to see it.",
  af013:
    "Making an image to sit beside someone else's words. Botanical, concept and editorial work each serve a particular brief; the plain row is illustrating for the pleasure of the pairing.",
  af039: "Singing, as singing. Scat Singing is one technique inside it, chosen for its own sake.",
  af037:
    "Writing the music. Arranging, orchestration and chiptune each start from someone else's material or a machine's constraints; the plain row is composing.",
  af118: "Getting a finished recording out of other people's performances.",
  af041: "Designing sound for a scene or a product. Foley is one method, made with the body in a room.",
  af040:
    "Making music in the moment with no score to read. Live coding is one way to do that, and the only one where the instrument is a program.",
  af010:
    "Recording what is in front of you. Astrophotography is a different craft -- long exposures, stacking, equipment -- but the row it belongs under is photography.",
};

// Attach parentId, and the child lists back onto the parents. Done as data
// rather than by editing 306 JSON objects by hand, so the map above is the single
// place to read and change the shape of the catalogue.
(function applyHierarchy() {
  const byId = Object.fromEntries(ART_FORMS.map((a) => [a.id, a]));
  for (const [parentId, childIds] of Object.entries(HIERARCHY)) {
    const parent = byId[parentId];
    if (!parent) {
      console.warn("Holotype: hierarchy parent " + parentId + " is not in the catalogue");
      continue;
    }
    parent.childIds = childIds.filter((cid) => byId[cid]);
    for (const cid of parent.childIds) {
      const child = byId[cid];
      child.parentId = parentId;
      // A child is always its parent's category. Catch a bad map at load, not in the UI.
      if (child.category !== parent.category) {
        console.warn(
          "Holotype: " +
            child.name +
            " (" +
            child.category +
            ") is filed under " +
            parent.name +
            " (" +
            parent.category +
            ")"
        );
      }
    }
  }
})();

// The breadcrumb trail, e.g. ["Dance", "Folk & Traditional Dance"].
function breadcrumb(a) {
  const trail = [];
  let cur = a,
    guard = 0;
  while (cur && cur.parentId && guard++ < 8) {
    const p = BY_ID[cur.parentId];
    if (!p) break;
    trail.unshift(p.name);
    cur = p;
  }
  return trail;
}
