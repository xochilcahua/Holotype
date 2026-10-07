// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

// Start the app after its data, model and interface scripts have loaded.
renderBrandMark();
// Language menu: one option per language in LANGUAGES, then apply the saved choice (English unless the reader picked another).
const langSelect = document.getElementById("langSelect");
Object.keys(LANGUAGES).forEach((code) => langSelect.add(new Option(LANGUAGES[code], code)));
langSelect.addEventListener("change", () => setLanguage(langSelect.value));
setLanguage(currentLang);
renderGrid();
updateFilterCount();
