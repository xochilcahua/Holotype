# Architecture

Holotype runs in the browser without a backend. `index.html` loads the catalogue, model, interface scripts and stylesheets. `dist/Holotype.html` contains the same app with those scripts and styles inlined.

## Loading the app

The scripts are classic `<script src>` tags. This lets the folder version open from disk, where browsers restrict ES module imports. Scripts share a global scope and run in the order listed in `index.html`.

Top-level code must use definitions that have already loaded. If an event handler is defined in a later script, defer the reference with `() => confirmReset()` rather than passing `confirmReset` before it exists. `tests/scan_order.py` checks these references.

`copy/languages.js` loads before `src/i18n.js`, which reads the language tables. `src/main.js` loads last, builds the language menu and renders the initial view.

## Files

| Path | Role |
| --- | --- |
| `src/data/art-forms.js` | Catalogue records: IDs, names, vectors, descriptions and suggestions. |
| `src/data/prevalence.js` | Participation estimates and flags for figures based on published surveys. |
| `src/data/taxonomy.js` | Parent/child relationships between art forms. |
| `src/model/axes.js` | Axis definitions, distance weights and catalogue indexes. |
| `src/model/distances.js` | Raw distances (`DIST`) and corrected relatedness rankings (`REL`). |
| `src/model/novelty.js` | Familiarity scores for unrated forms. |
| `src/model/person-space.js` | Simulated reference profiles used to interpret ratings. |
| `src/model/classification.js` | Genus, variety, field leans and confidence. |
| `src/model/axis-copy.js`, `genus-copy.js`, `describe.js` | Source wording for axes and readings. |
| `src/render/plant.js` | SVG plant drawings. |
| `src/i18n.js` | Translation helpers and language selection. |
| `src/ui/state.js` | Browser storage, blank state and reset. |
| `src/ui/session.js` | Session files, migration, merge, import feedback and reset confirmation. |
| `src/ui/filters.js` | The shared catalogue filtering and sorting layer. |
| `src/ui/controls.js`, `color-tags.js`, `tag-dimensions.js` | Filter controls and color-tag rules. |
| `src/ui/flower-card.js`, `detail.js` | Catalogue flowers and detail sheets. |
| `src/ui/herbarium.js`, `profile-page.js`, `profile-blocks.js` | Profile view and shared screen/print blocks. |
| `src/ui/export-garden.js`, `print.js` | PDF content and browser printing. |
| `src/ui/theme.js`, `keys.js` | Theme switching, shortcuts and help. |
| `src/main.js` | Startup. |

`src/styles/tokens.css` defines shared colors and dimensions. Other stylesheets cover particular parts of the interface. `theme-folk.css` loads last; `print.css` supplies the print layout.

## State and sessions

`state` holds ratings, tags, the user's name, plant seed and preferences. Changes are saved under `holotype_state_v1` in localStorage. The loader also accepts the older `bloom_state_v1` key.

`ui` holds the current tab, search, sort and filters. It is not restored on a normal reload, so the app opens in the Garden without filters. A saved session file can include these view choices and restore them on import.

The language is stored separately under `holotype_lang`. A new browser starts in English. A chosen language survives reloads, a session file can restore its own language, and Reset returns to English. Reset also clears personal data and view filters while keeping theme and PDF-section preferences.

Unknown art-form ratings are preserved in parked data. Session migration can resolve renamed forms; split or missing forms remain available for review. Imported profile results are recomputed from ratings.

## Editing

| Change | Start here |
| --- | --- |
| Wording or translations | `copy/`; edit entry values, then rebuild `copy/languages.js`. |
| Add or change an art form | Its record in `src/data/art-forms.js`. |
| Distance or novelty behavior | `src/model/distances.js`, `axes.js` or `novelty.js`. |
| Profile classification | `src/model/classification.js` and `person-space.js`. |
| Colors and spacing | `src/styles/tokens.css`, then the relevant stylesheet. |
| Plant drawing | `src/render/plant.js`. |
| Saved fields | `src/ui/state.js` and `session.js`. |
| Hosting | `.github/workflows/pages.yml` and `tools/prepare_site.py`. |

## Model details to keep in mind

`DIST` drives novelty. `REL` corrects for crowded neighborhoods and ranks related forms. `REL` can exceed 1; it is not a normalized distance.

The distance model treats category-default context values as unknown. Its effective contribution from context therefore varies across pairs. The `a6` axis is displayed but does not belong to a distance group.

The personal vector uses technique, domain and sensory axes. Material and context axes can affect distances between art forms but do not enter the personal profile. Every rated form contributes to that vector; particular classification rules separately use ratings of 3 or above.

Changes to thresholds or reference populations need model checks as well as a browser check. Existing comments record measurements from particular test populations; rerun the relevant probes before relying on those numbers after a change.

## Builds and checks

`python3 tools/build_singlefile.py` rebuilds translations, writes `dist/Holotype.html`, and compares the folder and portable versions in Chromium. It compares catalogue counts, reference values, scores and drawings, using system fonts for a reproducible check.

Run `python3 tests/env_check.py` to find the Python executable and browser dependencies for this machine. [The test guide](../tests/README.md) lists focused checks.

The publishing workflow rebuilds and checks the portable app, then `tools/prepare_site.py` copies the browser files into `.site/` and adds the repository link to the footer. GitHub Pages serves that folder. Test output and local environments are excluded.
