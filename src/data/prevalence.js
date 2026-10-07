// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

/* HOW COMMON EACH ART FORM IS. A participation figure per form, plus the few that sit on a
published figure. Pure data. Lives here, loaded straight after the catalogue, because the
person-space calibration (model/person-space.js, position 8) needs it and it used to sit in
ui/herbarium.js at position 20 where it was silently absent at that point.
   Gives PREVALENCE, PREVALENCE_ANCHORED. See docs/architecture.md. */

// ---------------- How common is this art form? ----------------
// The share of adults who have had a go at it AT ALL, at any age, however briefly - which is the
// same standard as the bottom of the rating scale, where 1 means "tried it once, maybe as a kid,
// or a single afternoon workshop. Barely there, but it still counts." Lifetime exposure, not
// current practice, is the only definition consistent with that scale.
//
// This matters, because the two questions give very different answers. The NEA's 2022 Survey of
// Public Participation in the Arts reports 11% of adults play an instrument in the past year and
// it measures making art, not having tried it; a YouGov survey of 3,000 US adults finds 66% have
// learned an instrument at some point. Same activity, six-fold difference, and the lifetime
// figure is the one that belongs next to a scale whose floor is "tried it once as a kid". The NEA
// 12-month figures (dancing 22%, singing 20%, photography 13%, needlework 12%) are therefore NOT
// used as anchors here - they answer a narrower question than this sort asks.
//
// Only lifetime-published figures are marked anchored. Almost nothing in the 306 has one, so the
// filled dots are few and the hollow rings are most of the list; the readings are modelled from
// each form's cost, space, equipment and learning-curve data plus what is generally known about
// how many people have tried it. Treat the numbers as an order of magnitude, good for ranking and
// not a claim of precision - the reading key says so on the page and the print sheet repeats it.
const PREVALENCE = {
  // Writing & Language
    af001: 70, af002: 60, af003: 6, af004: 35, af005: 4, af006: 30, af007: 3,
    af135: 25, af136: 8, af137: 45, af138: 30, af181: 65, af182: 12, af235: 18,
    af307: 20,
  // Visual Arts
    af008: 95, af009: 75, af010: 92, af011: 20, af012: 25, af013: 35, af014: 45,
    // af018 Graffiti & Street Art absorbs af144 Chalk & Pavement Art (was 45). The
    // figure has to describe the ROW, and a row that now covers drawing on pavements
    // cannot keep the 12% that only ever counted walls. 45 is the FLOOR: it is what
    // the larger absorbed row already claimed, and it deliberately does not add the
    // two together, because most people who draw in chalk have never touched a wall.
    af015: 8, af016: 6, af017: 40,
    af018: 45, af019: 30, af020: 10, af101: 12,
    af121: 4, af133: 6, af134: 6, af139: 12, af140: 25, af141: 12, af142: 25,
    af143: 4, af183: 2, af184: 8, af185: 5, af186: 8, af236: 20, af302: 8,
  // Craft & Sculpture
    af021: 50, af022: 2, af023: 45, af024: 50, af025: 6, af026: 30, af027: 30,
    af028: 20, af029: 55, af030: 70, af031: 5, af032: 12, af033: 8, af034: 20,
    af035: 3, af036: 12, af104: 4, af105: 35, af107: 8, af108: 10, af109: 45,
    af116: 10, af127: 15, af128: 12, af129: 30, af130: 12, af131: 5, af132: 4,
    af145: 60, af146: 20, af147: 45, af148: 40, af149: 35, af150: 25, af151: 5,
    af205: 3, af206: 10, af207: 5, af208: 2, af209: 10, af210: 12, af211: 3, af212: 3,
    af213: 4, af214: 4, af215: 40, af216: 15, af217: 20, af218: 20, af219: 20,
    af220: 10, af221: 1, af222: 3, af223: 25, af224: 6, af225: 15, af226: 8,
    af231: 60, af238: 10, af239: 35, af273: 1, af274: 3, af275: 2, af288: 30,
    af289: 12, af290: 10, af291: 10, af292: 10, af293: 6, af294: 10, af295: 8,
  // Music & Sound
    af037: 40, af038: 66, af039: 95, af040: 25, af041: 8, af042: 20, af043: 4,
    af044: 30, af045: 15, af046: 2, af047: 10, af048: 8, af118: 20, af171: 40,
    af172: 12, af173: 5, af187: 8, af188: 15, af189: 6, af237: 2, af265: 4,
  // Performance & Movement
    af049: 45, af050: 15, af051: 12, af052: 15, af053: 90, af054: 12, af055: 15,
    af056: 8, af057: 20, af058: 4, af059: 40, af100: 10, af110: 30, af112: 3,
    af126: 2, af174: 15, af176: 5, af177: 20, af178: 25, af190: 50, af191: 4,
    af192: 3, af193: 25, af194: 20, af240: 4, af241: 6, af242: 6,
    af250: 4, af258: 3, af259: 1,
    af266: 2, af267: 1, af268: 3, af269: 1, af270: 0.5, af271: 3, af272: 0.5,
    af303: 10, af304: 12, af305: 40,
  // Directing & Curating
    af060: 10, af061: 8, af062: 6, af063: 10, af064: 45, af065: 10, af066: 8,
    af117: 20, af161: 5, af162: 3,
  // Digital & Interactive
    af067: 15, af068: 20, af069: 8, af070: 6, af071: 4, af072: 1, af073: 6, af102: 12,
    af103: 30, af119: 3, af159: 30, af160: 12, af227: 25, af228: 20, af233: 12,
    af234: 4, af243: 55, af298: 12, af299: 15, af300: 10, af301: 6,
  // Design
    af074: 15, af075: 25, af106: 10, af152: 25, af153: 5, af154: 8, af155: 12,
    af156: 10, af157: 10, af158: 8, af296: 6, af297: 10,
  // Food, Scent & Plants
    af076: 85, af077: 65, af078: 4, af079: 20, af080: 6, af120: 5, af124: 20,
    af125: 35, af163: 25, af164: 6, af165: 20, af166: 35, af167: 15, af195: 30,
    af196: 15, af197: 12, af198: 25, af199: 8, af306: 52,
  // Land & Environment
    af081: 15, af082: 15, af083: 4, af084: 3, af085: 3, af086: 10, af087: 12,
    af088: 5, af113: 5, af123: 2, af168: 3, af169: 8, af170: 25, af200: 8, af201: 2,
    af202: 4, af203: 4, af204: 2, af232: 25,
  // Conceptual & Social
    af089: 3, af090: 25, af091: 5, af092: 8, af093: 3, af094: 4, af095: 2, af096: 12,
    af097: 4, af098: 10, af099: 4, af114: 6, af115: 3, af122: 3, af179: 12, af180: 4,
    af229: 3, af230: 8,
  // Sport & Martial Arts
    af175: 15, af260: 5, af261: 3, af262: 10, af263: 6, af264: 15, af276: 6,
    af277: 25, af278: 20, af279: 5, af280: 3, af281: 25, af282: 20, af283: 25,
    af284: 30, af285: 25, af286: 25, af287: 15,
};

// The forms that sit directly on a published NEA figure rather than on a modelled estimate.
const PREVALENCE_ANCHORED = new Set([
  "af008", "af009", "af010", "af039", "af053", "af076",
]);
