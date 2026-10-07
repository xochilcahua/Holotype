// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

/* LIGHT AND DARK, AND THE COLOUR EACH CATEGORY GETS. The accent a category is drawn
in and the small icon that stands for it live here, along with the theme switch.
   See docs/architecture.md. */

// ---------------- State and theme ----------------
let state = loadStore();
if (!state.plantSeed) {
  state.plantSeed = HolotypePlant.newSeed();
  saveStore();
} // one seed per person: fixes their plant's colors and tiny detail
// showRated / showUnrated are the "which half of the catalogue do I want to see" switches. Both
// default to true, so a first-time visitor sees everything exactly as before; turning one off
// hides that half everywhere at once - the Garden, the Herbarium page and the PDF together.
let ui = {
  query: "",
  activeCategories: new Set(),
  activeTiers: new Set(),
  sort: "common_desc",
  mode: "garden",
  showRated: true,
  showUnrated: true,
  dense: true,
};

// True when the operating system asks for a dark theme.
function systemPrefersDark() {
  return !!(window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);
}
// The theme in force: the person's own choice if they made one, otherwise the system's.
function effectiveTheme() {
  return state.themeChoice || (systemPrefersDark() ? "dark" : "light");
}

const SUN = `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>`;
const MOON = `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`;

// Writes the chosen theme onto <html>. No attribute means follow the system.
function applyTheme() {
  const root = document.documentElement;
  if (state.themeChoice) root.setAttribute("data-theme", state.themeChoice);
  else root.removeAttribute("data-theme");
  document.getElementById("themeToggle").innerHTML = effectiveTheme() === "dark" ? SUN : MOON;
}
document.getElementById("themeToggle").addEventListener("click", () => {
  state.themeChoice = effectiveTheme() === "dark" ? "light" : "dark";
  applyTheme();
  saveStore();
  if (ui.mode === "profile") renderProfilePage();
});
if (window.matchMedia) {
  const mq = window.matchMedia("(prefers-color-scheme: dark)");
  const onChange = () => applyTheme();
  if (mq.addEventListener) mq.addEventListener("change", onChange);
}
applyTheme();
