// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

/* LANGUAGES. English is the source language and the default. The text of the app is its own key: t("Garden") returns the
translation of "Garden" when another language is selected, and "Garden" itself when it is not, or when no translation exists
yet. Anything not yet translated therefore simply stays in English; nothing breaks.
   Languages are NOT listed in code. Every folder inside copy/ is a language, and copy/languages.js (made from those folders by
tools/locales.py build or by copy/Update-languages.html) defines HOLOTYPE_LOCALES, which this file reads. The English folder
is a language too: lines edited there replace the English wording without touching the code.
   See copy/README.md. To translate more of the app: wrap a string in t(...) in the code, or add data-i18n to an element in
index.html, then run `python3 tools/locales.py extract` so the new text appears in every language folder.
   Loads after copy/languages.js and before ui/state.js. The choice is saved in localStorage ("holotype_lang"). */

// The name a language calls itself, for languages whose language.json gives none: "es" -> "español".
function languageAutonym(code) {
  try {
    const name = new Intl.DisplayNames([code], { type: "language" }).of(code);
    return name ? name.charAt(0).toLocaleUpperCase(code) + name.slice(1) : code;
  } catch (e) {
    return code;
  }
}

const LANGUAGES = { en: "English" };
const TRANSLATIONS = {};
if (typeof HOLOTYPE_LOCALES !== "undefined") {
  Object.keys(HOLOTYPE_LOCALES)
    .sort()
    .forEach((code) => {
      TRANSLATIONS[code] = HOLOTYPE_LOCALES[code].strings;
      if (code !== "en") LANGUAGES[code] = HOLOTYPE_LOCALES[code].name || languageAutonym(code);
    });
}

let currentLang = "en";
try {
  const saved = localStorage.getItem("holotype_lang");
  if (saved && LANGUAGES[saved]) currentLang = saved;
} catch (e) {
  /* storage unavailable: stay in English */
}

// The text in the current language; `fallback` is the English source, returned when nothing is translated.
function t(text) {
  const table = TRANSLATIONS[currentLang];
  if (typeof text !== "string") return text;
  const translated = table && table[i18nKey(text)];
  return translated ? (text.match(/^\s*/) || [""])[0] + translated + (text.match(/\s*$/) || [""])[0] : text;
}

// Marks a plain English string that is shown later through a lookup the extractor cannot follow (the session parser builds
// its messages as text and translateSessionMessage() translates them on display). Returns the string unchanged; its only
// job is to be findable: tools/locales.py reads sourceText("...") the same way it reads t("...").
function sourceText(text) {
  return text;
}

// Same as t(), for a word whose translation depends on where it is used ("Moderate" is masculine for a cost and feminine
// for a learning curve in Spanish). Looks for the key "Context | Text" first and falls back to plain "Text", so a language
// only needs the contextual key where the plain one is not enough.
function tc(context, text) {
  const table = TRANSLATIONS[currentLang];
  const hit = table && table[i18nKey(`${context} | ${text}`)];
  return hit || t(text);
}

// Re-translates everything written in index.html. An element names the English text it carries in data-i18n (its text),
// or data-i18n-attr="placeholder|aria-label|title:English text" for attributes. The English is remembered on first sight.
function translateStatic() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    if (!el.dataset.en) el.dataset.en = el.dataset.i18n;
    el.textContent = t(el.dataset.en);
  });
  document.querySelectorAll("[data-i18n-attr]").forEach((el) => {
    el.dataset.i18nAttr.split(";").forEach((pair) => {
      const [attr, en] = pair.split("|");
      el.setAttribute(attr, t(en));
    });
  });
  document.querySelectorAll("#sortSelect option").forEach((o) => {
    if (!o.dataset.en) o.dataset.en = o.textContent;
    o.textContent = t(o.dataset.en);
  });
}

// Switches language: saves the choice, re-translates the page and redraws whatever is on screen.
function setLanguage(code) {
  if (!LANGUAGES[code]) return;
  const active = document.activeElement;
  const focusedId = active?.id;
  const modalScroll = document.querySelector(".modal")?.scrollTop || 0;
  const fullProfile = document.querySelector(".profile-wrap")?.open;
  const filterOpen = !!document.getElementById("filterPanel");
  const settingsOpen = !!document.getElementById("settingsPanel");
  const helpOpen = !!document.getElementById("helpCard");
  const glossaryOpen = helpOpen && !document.getElementById("helpGloss").hidden;
  const helpScroll = document.getElementById("helpCard")?.scrollTop || 0;
  const confirmOpen = !!document.getElementById("confirmRoot");
  currentLang = code;
  try { localStorage.setItem("holotype_lang", code); } catch (e) { /* visit-only choice */ }
  document.documentElement.lang = code;
  translateStatic();
  document.title = t("Holotype — find your next creative pursuit");
  document.querySelector('meta[name="description"]')?.setAttribute("content", t("Rate the creative things you have done; Holotype shows what is near them, what is far, and the shape your practice makes."));
  const sel = document.getElementById("langSelect");
  if (sel) sel.value = code;
  if (typeof renderGrid === "function") renderGrid();
  if (filterOpen) openFilterPanel();
  if (settingsOpen) openSettings();
  if (currentModalId) {
    openDetail(currentModalId, { quiet: true });
    document.querySelector(".modal").scrollTop = modalScroll;
    if (document.querySelector(".profile-wrap")) document.querySelector(".profile-wrap").open = !!fullProfile;
  }
  if (helpOpen) {
    closeHelp(); toggleHelp();
    if (glossaryOpen) document.getElementById("tabGloss").click();
    document.getElementById("helpCard").scrollTop = helpScroll;
  }
  if (confirmOpen) confirmReset();
  if (ui.mode === "profile") {
    if (pendingSession) renderSessionChoice();
    else if (sessionFeedback) restoreSessionFeedback();
  }
  if (document.getElementById("printExport").childElementCount) buildPrintExport();
  if (focusedId) document.getElementById(focusedId)?.focus({ preventScroll: true });
}
// English source keys stay unchanged; interpolation never translates user-entered data.
const i18nTemplateCache = new WeakMap();
const i18nEntityCache = new Map();
const i18nDecoder = document.createElement("textarea");

function i18nKey(text) {
  return String(text).replace(/\s+/g, " ").trim();
}

function i18nDecode(text) {
  if (!text.includes("&")) return text;
  if (!i18nEntityCache.has(text)) {
    i18nDecoder.innerHTML = text;
    i18nEntityCache.set(text, i18nDecoder.value);
  }
  return i18nEntityCache.get(text);
}

function i18nEscape(text) {
  return String(text).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

// Compile each source fragment once. Placeholders are numbered locally so adding an
// unrelated attribute or interpolation does not change the paragraph's translation key.
function i18nFragment(source, htmlText, richText = false) {
  const indices = [];
  const keySource = source.replace(/\uE000(\d+)\uE001/g, (_, index) => {
    indices.push(Number(index));
    return `{${indices.length - 1}}`;
  });
  const key = i18nKey(htmlText || richText ? i18nDecode(keySource) : keySource);
  const leading = (source.match(/^\s*/) || [""])[0];
  const trailing = (source.match(/\s*$/) || [""])[0];
  return (values) => {
    const translated = TRANSLATIONS[currentLang]?.[key];
    if (translated) {
      const text = htmlText ? i18nEscape(translated) : translated;
      return leading + text.replace(/\{(\d+)\}/g, (_, i) => String(values[indices[Number(i)]] ?? "")) + trailing;
    }
    return source.replace(/\uE000(\d+)\uE001/g, (_, index) => String(values[Number(index)] ?? ""));
  };
}

// Text-only templates: tx`Rated ${level} of 10`; ordinary source strings: tx(label).
function tx(source, ...values) {
  if (typeof source === "string") return t(source);
  let render = i18nTemplateCache.get(source);
  if (!render) {
    render = i18nFragment(source.map((s, i) => s + (i < source.length - 1 ? `\uE000${i}\uE001` : "")).join(""), false);
    i18nTemplateCache.set(source, render);
  }
  return render(values);
}

// HTML templates translate only source text and user-facing attributes. Interpolated
// markup is already built by the caller, with the same escaping rules as the English UI.
function i18nHTML(source, ...values) {
  let render = i18nTemplateCache.get(source);
  if (!render) {
    const text = source.map((s, i) => s + (i < source.length - 1 ? `\uE000${i}\uE001` : "")).join("");
    const chunks = text.split(/(<[^>]+>)/g).map((chunk) => {
      if (!chunk.startsWith("<")) return i18nFragment(chunk, true);
      const attrs = [];
      const tag = chunk.replace(/\b(title|aria-label|placeholder)="([^"]*)"/g, (_, attr, content) => {
        attrs.push(i18nFragment(content, true));
        return `${attr}="\uE002${attrs.length - 1}\uE003"`;
      });
      return (v) => tag.replace(/\uE002(\d+)\uE003/g, (_, i) => attrs[Number(i)](v))
        .replace(/\uE000(\d+)\uE001/g, (_, i) => String(v[Number(i)] ?? ""));
    });
    render = (v) => chunks.map((f) => f(v)).join("");
    i18nTemplateCache.set(source, render);
  }
  return render(values);
}

function i18nCount(n, singular, plural) {
  return `${n} ${t(n === 1 ? singular : plural)}`;
}

function compareArtNames(a, b) {
  return t(a.name).localeCompare(t(b.name), currentLang, { sensitivity: "base" });
}

function tagValueLabel(dimension, value) {
  if (dimension === "category") return t(value);
  const labels = {
    cost: { low: "Low", medium: "Moderate", high: "High" },
    space: { none: "None", small: "Small", studio: "A studio", large: "Large" },
    curve: { quick: "Quick", moderate: "Moderate", long: "Long" },
    self: { yes: "Works well", no: "Better with a teacher" },
  };
  const context = { cost: "Cost", space: "Space", curve: "Learning curve", self: "Self-taught friendly" }[dimension];
  return tc(context, labels[dimension]?.[value] || value);
}

function profileTitle(name, fallback = "Your Holotype") {
  return name ? tx`${name}'s Holotype` : t(fallback);
}


// Recover an exact source string for feedback that is shown again after a switch.
// Catalogue identity and user data never use this reverse lookup.
function i18nSourceText(text) {
  if (currentLang === "en") return text;
  const entry = Object.entries(TRANSLATIONS[currentLang] || {}).find(([, value]) => value === text);
  return entry ? entry[0] : text;
}

// Rich copy is a trusted, local translation containing inline <b>/<i> emphasis.
// Callers escape user values before interpolating, just as with i18nHTML.
function i18nRich(source, ...values) {
  let render = i18nTemplateCache.get(source);
  if (!render) {
    render = i18nFragment(source.map((s, i) => s + (i < source.length - 1 ? `\uE000${i}\uE001` : "")).join(""), false, true);
    i18nTemplateCache.set(source, render);
  }
  return render(values);
}
