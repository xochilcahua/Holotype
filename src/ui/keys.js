// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

/* KEYBOARD SHORTCUTS. One place, so the help window and the bindings cannot fall out
of step with each other.
   See docs/architecture.md. */

// ---------------- Keyboard shortcuts ----------------
document.addEventListener("keydown", (e) => {
  const tag = (e.target.tagName || "").toLowerCase();
  const typing = tag === "input" || tag === "select" || tag === "textarea";

  if (e.key === "Escape") {
    if (document.getElementById("confirmRoot")) return closeConfirm();
    if (currentModalId) return closeDetail();
    if (document.getElementById("filterPanel")) return closeFilterPanel();
    if (document.getElementById("settingsPanel")) return closeSettings();
    if (document.getElementById("helpCard")) return closeHelp();
    if (typing) e.target.blur();
    return;
  }
  if (typing || e.metaKey || e.ctrlKey || e.altKey) return;
  if (document.getElementById("confirmRoot") || currentModalId) return; // shortcuts must not act behind an open dialog

  if (e.key === "/") {
    e.preventDefault();
    document.getElementById("searchInput").focus();
  } else if (e.key === "f" || e.key === "F") {
    e.preventDefault();
    toggleFilterPanel();
  } else if (e.key === "c" || e.key === "C") {
    e.preventDefault();
    toggleSettings();
  } else if (e.key === "e" || e.key === "E") {
    e.preventDefault();
    toggleExport();
  } else if (e.key === "t" || e.key === "T") {
    e.preventDefault();
    document.getElementById("themeToggle").click();
  } else if (e.key === "?") {
    e.preventDefault();
    toggleHelp();
  }
});

document.getElementById("helpToggle").addEventListener("click", toggleHelp);

// Opens or closes the help window (How it works and Glossary).
function toggleHelp() {
  if (document.getElementById("helpCard")) {
    closeHelp();
    return;
  }
  document.getElementById("helpRoot").innerHTML = i18nHTML`
    <div class="help-backdrop" id="helpBackdrop">
      <div class="help-card" id="helpCard" role="dialog" aria-label="How Holotype works">
        <div class="help-tabs" role="tablist">
          <button type="button" class="help-tab" role="tab" id="tabHow" aria-selected="true" aria-controls="helpHow">How it works</button>
          <button type="button" class="help-tab" role="tab" id="tabGloss" aria-selected="false" aria-controls="helpGloss">Glossary</button>
        </div>
        <div id="helpHow" role="tabpanel" aria-labelledby="tabHow">
        <h3>How Holotype works</h3>
        <p class="help-intro">${i18nRich`Holotype takes what you already know and shows you what's near it, and what's genuinely far from it, across ${N} art forms. You rate what you've done, Holotype ranks the rest by how new it would be to you, and the Herbarium turns your ratings into a portrait of how you tend to work.`}</p>

        <div class="help-cols">
        <div>
        <h4>Two views: Garden and Herbarium</h4>
        <p>${i18nRich`The <b>Garden</b> is where you rate: every art form is a tile, with your rated ones collected at the top. The <b>Herbarium</b> is where what you have grown gets pressed, labeled and kept: your holotype, your growth habit, your rated and unexplored lists, and the PDF export, all built live from your ratings. Switch with the tabs in the top bar; nothing is lost when you do.`}</p>

        <h4>Reading a flower</h4>
        <p>${i18nRich`Each art form is drawn as a flower from its own profile. Pointed outer petals show how it is made and shared, rounded middle bars the field it serves, and inner dots the senses it uses. A longer shape is a stronger trait, so similar practices grow similar-looking flowers. The ink comes from its category, and since categories share four inks, the shape tells you more than the color.`}</p>

        <h4>Reading a tile</h4>
        <p>${i18nRich`Some art forms contain more specific ones. A small <b>+4</b> beside a name means four more specific forms sit inside it (Dance holds Flamenco, Capoeira, Chinese Opera and Pole Dance). Each of those has its own tile, with the larger form named in small type above its name. Open either side and you see the other: a larger form lists the forms inside it, and a specific form shows a <b>Part of a larger art form</b> section naming its parent, plus the other forms under the same parent. They are ordinary art forms, rated separately, so rate whichever level matches what you actually do.`}</p>

        <h4>Rating what you know</h4>
        <p>${i18nRich`Use the slider on a tile to rate anything you've actually done, from 1 to 10. There's no need to rate everything, and most people should use the low end of the scale far more than the high one: a 10 is a claim only someone doing it for a living should honestly make.`}</p>
        <div class="help-example"><b>1</b><span>Tried it once, maybe as a kid, or a single afternoon workshop. Barely there, but it still counts.</span></div>
        <div class="help-example"><b>3</b><span>You dabble now and then. No real proficiency, but you know your way around the basics.</span></div>
        <div class="help-example"><b>5</b><span>A working hobbyist. You do this somewhat regularly and are comfortable with the fundamentals.</span></div>
        <div class="help-example"><b>7</b><span>Quite good at this: a serious hobbyist or semi-pro, with real, transferable skill.</span></div>
        <div class="help-example"><b>10</b><span>Professional-level mastery. This is one of the practices that defines you.</span></div>

        <h4>The ring, its number and the three labels</h4>
        <p>${i18nRich`Once you've rated something, every other tile grows a ring showing how new it would be to you: the fuller the ring, the newer the ground. The number inside is the novelty score, from 1 to 100: a rough answer to "how much of this would I already recognize?" A higher rating of yours counts for more, and knowing several related things adds up to count for more than any one of them alone.`}</p>
        <div class="help-example help-tier"><b>1&ndash;40</b><span><b>Familiar</b>: close to something you know; most of the technique carries straight over.</span></div>
        <div class="help-example help-tier"><b>41&ndash;70</b><span><b>In between</b>: real overlap, but a genuine new skill you'd still have to build.</span></div>
        <div class="help-example help-tier"><b>71&ndash;100</b><span><b>New ground</b>: shares little with what you know. 100 means nothing you rated gives any evidence either way, not that it's impossible for you. The newest third of what's left also counts as new ground, so there's always somewhere new to look.</span></div>
        </div>

        <div>
        <h4>Sorting, search and filters</h4>
        <p>${i18nRich`The sort menu in the top bar orders the art forms you have not rated. It opens on <b>Most common first</b>: the art forms the most people have tried at some point, an estimated share of adults shown beside each one in the Herbarium list (a filled dot is a published survey figure, a hollow ring is an estimate). <b>Less common first</b> reverses it. <b>Closest to you first</b> and <b>Furthest from you first</b> need at least one rating to mean anything: closest leads with what is most like the things you rated, furthest is there if you would rather be surprised than be helped. <b>A to Z</b>, <b>By category</b> (grouped by field, nearest first within each) and <b>By tag</b> (grouped by your own color tags, so it needs some) complete the list. The Herbarium's "Not yet explored" list follows the same choice. Search by name at any time.`}</p>
        <p>${i18nRich`Filters narrow the catalogue by <b>category</b>, by how <b>new</b> something is to you (Familiar, In between, New ground), by which <b>half</b> you want to see (My garden, Not yet rated), and they hold the <b>reach</b> slider: turned up, everything you know counts for more, so more of it reads as familiar and the closest-first list tightens around your own field; turned down, only your nearest neighbours get credit and the rest of the catalog stays new ground.`}</p>
        <p>${i18nRich`All of these follow you across the app, not just the grid. Whatever you have filtered down to is what the <b>Herbarium page</b> lists and what the <b>PDF</b> contains, so a list you narrowed to five art forms exports as five rows rather than the whole catalog. Both halves are shown by default; switch one off and it leaves the page and the export too. When a filter is holding something back, the list heading says so, as "12 of ${N}", so a short list is never mistaken for the whole thing. <b>Clear all</b> puts everything back.`}</p>
        <p>${i18nRich`The Herbarium's lists open <b>condensed</b>: stacked full width and split into three columns each, which fits most of the catalogue on one screen. The <b>Comfortable spacing</b> button loosens them into two side-by-side lists, what you rated on the left and what you have not on the right. That choice is for reading only &mdash; it is not saved to your session and does not change the PDF.`}</p>

        <h4>Color tags</h4>
        <p>${i18nRich`Open the palette icon to give any trait a color: category, cost, space, learning curve, self-taught friendly, or <b>distance from your taste</b> (a range from 0, very familiar, to 100, very new; it appears once you've rated something). Matching tiles get a small colored mark, several tags can stack, and in your Herbarium they show only on art forms you haven't rated yet. You start with none.`}</p>

        <h4>Your Herbarium</h4>
        <p>${i18nRich`The page is your <b>holotype</b>. The flower at the top is a fingerprint of your ratings, inked by the category you lean into most. Below it, your <b>growth habit</b> names how you tend to work, as a plant. The big italic word is your <b>genus</b>, drawn as its own plant and given a tribe name. Beneath that, written the way botanists write a name, sit up to two short Latin notes: <i>var.</i> (variety) for how you handle chance, and <i>cf.</i> (compare) for up to two fields your ratings clearly favor, each spelled out in plain words just below. The five bars show where you sit on each axis compared with other people. With fewer than four ratings, or while nothing you rated is above a first try (3 or higher), you get a provisional genus only, with no variety or leans yet. The plant's shape and its colors follow your ratings, so both keep moving as you rate: the plant is inked with the same three colors as your holotype, with the one you lean into most leading. What stays put is the small companion beside the plant and the exact tone of the colors: they are chosen once for you and saved in your session file.`}</p>
        <p>${i18nRich`Botanical terms, and what they mean in biology as well as in Holotype, are explained in the <b>Glossary</b> tab of this window.`}</p>

        <h4>Save as PDF, and starting over</h4>
        <p>${i18nRich`On the Herbarium page, choose which sections to include and press Save as PDF; it uses your browser's own print dialog and nothing is uploaded. The sheet contains exactly the art forms your filters currently allow, and the subheading says how many of the catalogue it lists. Include the <b>This session's filters</b> section to have the sheet record which filters, sort and search produced it, so a shortened sheet can be explained later. You can also save your session as a small file (ratings, name, tags, filters, sort, and your plant's colors and companion) and load it in a later visit to pick up where you left off. Sessions saved in earlier versions still load. If an art form has since been renamed it is matched automatically, and if it was split or removed your rating is set aside and listed for you to place again, never silently dropped; art forms added since are simply unrated until you find and rate them. The circular arrow in the top bar wipes ratings, tags, name and plant so the next person on the same device starts fresh (after a confirmation).`}</p>

        <h4>Shortcuts</h4>
        <div class="help-row"><span>Search</span><kbd class="key-hint">/</kbd></div>
        <div class="help-row"><span>Filters</span><kbd class="key-hint">F</kbd></div>
        <div class="help-row"><span>Color tags</span><kbd class="key-hint">C</kbd></div>
        <div class="help-row"><span>Switch Garden / Herbarium</span><kbd class="key-hint">E</kbd></div>
        <div class="help-row"><span>Light or dark</span><kbd class="key-hint">T</kbd></div>
        <div class="help-row"><span>This help</span><kbd class="key-hint">?</kbd></div>
        <div class="help-row"><span>Close anything</span><kbd class="key-hint">Esc</kbd></div>
        </div>
        </div>
        </div>
        <div id="helpGloss" role="tabpanel" aria-labelledby="tabGloss" hidden>
          <h3>Glossary</h3>
          <p class="help-intro">${i18nRich`The botanical terms used in the Herbarium, with what each one means in Holotype and what it means in biology.`}</p>
          ${glossaryHTML()}
        </div>
      </div>
    </div>`;
  const showTab = (which) => {
    const how = which === "how";
    document.getElementById("helpHow").hidden = !how;
    document.getElementById("helpGloss").hidden = how;
    document.getElementById("tabHow").setAttribute("aria-selected", how);
    document.getElementById("tabGloss").setAttribute("aria-selected", !how);
    document.getElementById("helpCard").scrollTop = 0;
  };
  document.getElementById("tabHow").addEventListener("click", () => showTab("how"));
  document.getElementById("tabGloss").addEventListener("click", () => showTab("gloss"));
  document.getElementById("helpBackdrop").addEventListener("click", (e) => {
    if (e.target.id === "helpBackdrop") closeHelp();
  });
}
// Removes the help window.
function closeHelp() {
  document.getElementById("helpRoot").innerHTML = "";
}
