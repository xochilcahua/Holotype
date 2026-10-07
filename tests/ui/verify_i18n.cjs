// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy
// Integration checks for both file:// entry points. Uses an isolated browser;
// never opens the reader's browser profile or changes app/session files.
const assert = require("node:assert/strict");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium } = require(process.env.HOLOTYPE_PLAYWRIGHT_MODULE || "playwright");
const root = path.resolve(__dirname, "../..");

async function check(browser, entry) {
  const page = await browser.newPage({ locale: "es-MX", viewport: { width: 1440, height: 1000 } });
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.route("https://fonts.googleapis.com/**", (route) => route.abort());
  await page.goto(pathToFileURL(path.join(root, entry)).href, { waitUntil: "domcontentloaded" });
  assert.equal(await page.locator("#langSelect").inputValue(), "en", "First visit should use English");
  assert.equal(await page.locator("html").getAttribute("lang"), "en");
  const total = await page.evaluate(() => ART_FORMS.length);
  assert.equal(await page.locator(".spec").count(), total);
  await page.selectOption("#langSelect", "es");

  const catalogue = await page.evaluate(() => {
    const missing = [];
    // These loanwords and proper names have the same spelling in Spanish.
    const sharedNames = new Set(["Collage", "Origami", "ASMR", "Cosplay", "Ikebana", "Quilling", "Decoupage", "Scrimshaw", "Kintsugi", "Flamenco", "Capoeira", "Kabuki", "Noh", "Kathakali", "Butoh"]);
    for (const a of ART_FORMS) {
      for (const key of ["name", "category", "tag", "desc", "start"]) {
        if (a[key] && !TRANSLATIONS.es[i18nKey(a[key])] && !(key === "name" && sharedNames.has(a[key]))) missing.push(`${a.id}:${key}`);
      }
      openDetail(a.id, { quiet: true });
      if (document.querySelector(".modal-title").textContent !== t(a.name)) throw Error(`Title: ${a.id}`);
      if (a.desc && document.querySelector(".modal-desc").textContent !== t(a.desc)) throw Error(`Description: ${a.id}`);
      if (a.start && document.querySelector(".try p").textContent !== t(a.start)) throw Error(`Prompt: ${a.id}`);
    }
    closeDetail();
    const searches = ["pintura", "dibujo", "canto", "ceramica", "fiction writing"].map((q) => search(q)[0]);
    return { missing, searches };
  });
  assert.deepEqual(catalogue.missing, []);
  assert.deepEqual(catalogue.searches, ["af009", "af008", "af039", "af023", "af001"]);

  await page.evaluate(() => openFilterPanel());
  assert.equal(await page.locator("#filterPanel").getAttribute("aria-label"), "Filtros");
  await page.selectOption("#langSelect", "en");
  assert.equal(await page.locator("#filterPanel").getAttribute("aria-label"), "Filters");
  await page.evaluate(() => { closeFilterPanel(); openDetail("af009"); });
  await page.selectOption("#langSelect", "es");
  assert.equal(await page.locator(".modal-title").textContent(), "Pintura");
  await page.evaluate(() => closeDetail());

  const model = await page.evaluate(() => {
    state.mastery = { af001: 7, af008: 5, af009: 4, af003: 6, af053: 3, af038: 8 };
    state.exporterName = "Garden <img src=x onerror=alert(1)> {0}";
    state.colorRules = [{ dimension: "cost", values: ["low"], color: "#7FA8B8" }];
    setMode("profile");
    const snapshot = () => JSON.stringify({ ratings: state.mastery, vector: personalVector(), genus: computeClassification().genusId, novelty: computeNovelty(state.mastery, state.discount) });
    const spanish = snapshot(); setLanguage("en"); const english = snapshot(); setLanguage("es");
    if (spanish !== english) throw Error("Language changed ratings or model output");
    const file = sessionFileData();
    if (file.ratings.find((r) => r.id === "af009").name !== "Painting") throw Error("Translated session identity");
    const selfTest = holotypeSessionSelfTest();
    if (selfTest.some((test) => !test.pass)) throw Error(JSON.stringify(selfTest));
    const bc = computeClassification();
    for (const genus of Object.keys(GENUS_TABLE)) {
      const source = GENUS_TABLE[genus].text;
      const host = document.createElement("div");
      host.innerHTML = growthPatternHTML({ ...bc, genusId: genus, genus: GENUS_TABLE[genus] }, "prof", "#234", false);
      if (host.textContent.includes(source)) throw Error(`English genus: ${genus}`);
    }
    return { snapshot: spanish, selfTests: selfTest.length };
  });
  assert.equal(await page.locator(".prof-title").textContent(), "Holotipo de Garden <img src=x onerror=alert(1)> {0}");
  assert.equal(await page.locator("#profileView img").count(), 0);

  await page.evaluate(() => openSettings());
  assert.equal(await page.locator("#settingsPanel").getAttribute("aria-label"), "Etiquetas de color");
  await page.selectOption("#langSelect", "en");
  assert.equal(await page.locator("#settingsPanel").getAttribute("aria-label"), "Color tags");
  await page.evaluate(() => closeSettings());
  await page.selectOption("#langSelect", "es");
  await page.evaluate(() => toggleHelp());
  await page.locator("#tabGloss").click();
  assert.equal(await page.locator(".gl-item").count(), 28);
  await page.selectOption("#langSelect", "en");
  assert.equal(await page.locator("#helpGloss").isVisible(), true);
  assert.equal(await page.locator("#tabGloss").textContent(), "Glossary");
  await page.selectOption("#langSelect", "es");
  assert.equal(await page.locator("#tabGloss").textContent(), "Glosario");
  await page.evaluate(() => closeHelp());
  await page.evaluate(() => confirmReset());
  assert.equal(await page.locator("#confirmTitle").textContent(), "¿Empezar de nuevo para la siguiente persona?");
  await page.selectOption("#langSelect", "en");
  assert.equal(await page.locator("#confirmTitle").textContent(), "Start over for the next person?");
  await page.evaluate(() => closeConfirm());
  await page.selectOption("#langSelect", "es");

  await page.evaluate(() => {
    ui.sort = "name_asc"; renderGrid();
    const names = computeVisibleList().map(({ a }) => t(a.name));
    const sorted = names.slice().sort((a, b) => a.localeCompare(b, "es", { sensitivity: "base" }));
    if (JSON.stringify(names) !== JSON.stringify(sorted)) throw Error("Spanish alphabetical order");
    setSessionStatus(() => tx`Saved ${"example.json"}.`);
    setLanguage("en");
    if (document.getElementById("sessionStatus").textContent !== "Saved example.json.") throw Error("English save feedback");
    setLanguage("es");
    pendingSession = parseSessionFile(JSON.stringify({ format: "holotype-session", schemaVersion: 2, name: "Persona", ratings: [{ id: "af009", name: "Painting", rating: 7 }] }));
    renderSessionChoice(); setLanguage("en"); setLanguage("es");
    document.getElementById("sessionMerge").click();
    if (state.mastery.af009 !== 7) throw Error("Pending import lost during language switch");
    setLanguage("en");
    if (!document.getElementById("sessionStatus").querySelector("p")) throw Error("Import report markup lost");
    setLanguage("es"); saveStore();
    ui.sort = "common_desc"; renderGrid(); buildPrintExport();
    if (!document.getElementById("printExport").textContent.includes("Herbario · ficha del ejemplar")) throw Error("English print header");
  });
  await page.emulateMedia({ media: "print" });
  assert.ok((await page.pdf({ format: "A4" })).length > 1000);
  await page.emulateMedia({ media: "screen" });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(() => renderProfilePage());
  assert.ok(await page.evaluate(() => document.body.scrollWidth <= innerWidth + 1), "Phone layout overflows");
  await page.reload({ waitUntil: "domcontentloaded" });
  assert.equal(await page.locator("#langSelect").inputValue(), "es");
  assert.equal(await page.evaluate(() => state.mastery.af009), 7);
  // A cancelled reset keeps the session; a confirmed reset starts in English.
  await page.locator("#resetToggle").click();
  await page.locator("#confirmCancel").click();
  assert.equal(await page.locator("#langSelect").inputValue(), "es");
  assert.equal(await page.evaluate(() => state.mastery.af009), 7);
  await page.locator("#resetToggle").click();
  await page.locator("#confirmOk").click();
  assert.equal(await page.locator("#langSelect").inputValue(), "en");
  assert.equal(await page.locator("html").getAttribute("lang"), "en");
  assert.equal(await page.locator("#tabGarden").textContent(), "Garden");
  assert.equal(await page.evaluate(() => Object.keys(state.mastery).length), 0);
  assert.equal(await page.evaluate(() => localStorage.getItem("holotype_lang")), "en");
  await page.reload({ waitUntil: "domcontentloaded" });
  assert.equal(await page.locator("#langSelect").inputValue(), "en");
  // A session can still restore its own language after a reset.
  await page.evaluate(() => {
    const parsed = parseSessionFile(JSON.stringify({ format: "holotype-session", schemaVersion: 2, language: "es", ratings: [{ id: "af009", rating: 7 }] }));
    if (parsed.error) throw Error(parsed.error);
    applySession(parsed.norm, parsed.report, "replace");
  });
  assert.equal(await page.locator("#langSelect").inputValue(), "es");
  assert.equal(await page.evaluate(() => state.mastery.af009), 7);
  assert.deepEqual(errors, []);
  await page.close();
  console.log(`${entry}: ${total} catalogue entries, 16 genera, ${model.selfTests} session checks, live language switching, PDF and phone layout passed`);
  return model.snapshot;
}

(async () => {
  const browser = await chromium.launch();
  try {
    const modular = await check(browser, "index.html");
    const portable = await check(browser, "dist/Holotype.html");
    assert.equal(modular, portable, "Modular and portable builds differ");
    console.log("PASS: English/Spanish integration and modular/portable parity");
  } finally { await browser.close(); }
})().catch((error) => { console.error(error); process.exitCode = 1; });
