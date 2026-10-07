# Holotype test toolkit

Run checks from the repository root. Start with `env_check.py` to find the Python executable
and browser dependencies. Tests use isolated browser profiles and synthetic sessions.

## Setup and structure
- `env_check.py`: checks Python and browser dependencies.
- `scan_order.py`: load-order violations (top-level references to a later module).
- `verify_sorts.py`, `verify_sort_integration.py`: every sort and filter on the Garden behaves.
- `build_report.py`: formats `run_tests.py` output into an HTML report, markdown definitions and a CSV.

## People (profiles and populations)
- `profiles.py`: 127 synthetic profiles in eight groups, each checking a particular model behavior.
- `archetypes.py`: 32 synthetic profiles covering common practices, beginners and edge cases.
- `population.py`: generates synthetic user profiles from the author's assumptions.
  Its assumptions (about 4.8 ratings per person, 45% under four) drive many headline figures.
- `run_tests.py`: feeds each profile through the app's own code and records everything.
  `python3 tests/run_tests.py index.html out/archetypes --profiles archetypes`
  Optional key prefixes run a subset. About 2 minutes for the archetypes, longer for all 127.
- `population_check.py`: N drawn people in one page load; does the reading correlate with who the
  person is? `python3 tests/population_check.py index.html 600 11` (add `--engaged` for people who rate more).
- `panel/`: 60 synthetic personas. See `panel/` files: `panel_profiles.py` (50, earlier model, not
  blind), `panel_profiles_extra.py` (10, Claude), `expectations.md` and `twins.md` (expectations frozen before testing, written by Claude),
  `run_panel.py` (runner).

## Focused checks (`audit/`)
See `audit/README.md`.

## Translation integration

`node tests/ui/verify_i18n.cjs` uses Node Playwright to check English/Spanish in both the folder and
portable apps: first-visit English, reset and reload, catalogue coverage, Spanish search/sort,
language switching, session language restoration,
PDF generation and phone layout. Use `HOLOTYPE_PLAYWRIGHT_MODULE` if your Node Playwright installation
is outside the normal module lookup. See [translation notes](../docs/translations.md).

## UI checks (`ui/`)
Layout, print, touch and render checks. Not part of the current audit; run only if the interface changes.

## Add a profile
Append a call to `profiles.py`:

    P("H01_my_case", "F", "Short title", "Who this is.", "Why this profile exists.",
      [("Painting", 6), ("Singing", 3, "optional note")])

Names are matched against the live catalogue (exact, then unique prefix, then unique substring); an
ambiguous or unknown name stops the run. Exact names are in `docs/catalogue_names.txt`.

## Ratings scale (the app's own definition)
1 = tried once or twice, or as a kid; 3 = casual dabbling; 5 = working hobbyist; 7 = quite good, serious
hobbyist or semi-pro; 10 = professional-level mastery.

## Profile groups in profiles.py
A common hobbyists, B working professionals, C polymaths/starters/dabblers, D minimal-engagement and
non-artistic, E cultural and regional practices, F edge cases and boundary tests, G setting variants
(reach, plant seed, exporter name), H sport, making and tech-art additions. `ART_FORMS.length` at run
time (292) is the authority on catalogue size, not any number in a comment.

## Known characteristics
- The page requests Google Fonts. Offline, the browser logs `Failed to load resource`; the tools here
  ignore that message. It is not an app error.
- The tools that need a browser launch headless Chromium through Playwright.

## Translation checks
- `ui/verify_i18n_coverage.py`: switches the app to a fake language that masks every translated string, drives every screen
  (`ui/i18n_drive.py`) and fails if any visible text, tooltip or aria-label still holds English. Run it after adding any
  user-facing text.
- `ui/i18n_drive.py`: the shared screen walker, also used by `tools/locales.py extract`.
- `python3 tools/locales.py check`: coverage and breakage (placeholders, HTML tags) per language.
