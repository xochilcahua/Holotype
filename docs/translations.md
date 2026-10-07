# Translations

English is the default on a first visit and after Reset. The language menu switches the whole app to Spanish, including catalogue details, filters, help, readings, session feedback and PDFs. A selected language is remembered separately from ratings; a loaded session can restore its saved language.

The language files are local. The app does not contact a translation service. `copy/languages.js` contains the generated tables, and the portable build includes the same bundle.

## Edit or add a language

Each language has a folder in `copy/`. Entry keys are the original English source text; values are the text to display. English can have edited values too. See [the copy guide](../copy/README.md) for examples and the browser editing tool.

```sh
python3 tools/locales.py check
python3 tools/locales.py build
```

The GitHub publishing workflow runs these tools and rebuilds the portable file before deployment. It publishes the generated result without committing it back to the repository.

## Render translated text

`src/i18n.js` supplies the following helpers:

| Helper | Use |
| --- | --- |
| `t(source)` or `tx(source)` | A label or fixed text. |
| `tx` tagged template | A sentence with interpolated values. |
| `i18nHTML` tagged template | HTML text and user-facing attributes. |
| `i18nRich` tagged template | A complete paragraph containing trusted inline emphasis. |
| `i18nCount` | A number with its singular or plural label. |
| `tc(context, source)` | A label that changes with context. |
| `sourceText(source)` | A source string translated later, such as a session parser message. |
| `data-i18n`, `data-i18n-attr` | Static page text and attributes. |

For example, ``tx`Rated ${level} of 10` `` produces the key `Rated {0} of 10`. Translate the full sentence so each language can choose its own word order. Preserve placeholders and emphasis tags. Escape user input before inserting it into HTML.

Catalogue IDs, source names used for matching, filter keys, session fields and Latin botanical names keep their canonical values. Translate displayed labels at render time. User-entered names and searches stay as entered.

Avoid assembling sentences from separate translated words or branching on a particular language. Use a complete source key or a context-specific label instead.

## Check a change

After adding source text or changing a key, run `python3 tools/locales.py extract`, review the language entries and rebuild the bundle. Existing edited English values are retained for unchanged keys.

`python3 tests/ui/verify_i18n_coverage.py` walks the interface with a test language to find text that bypasses translation helpers.

The browser integration check runs against both the folder and portable apps:

```sh
node tests/ui/verify_i18n.cjs
```

It covers first-visit English, reset and reload, remembered Spanish, session language restoration, catalogue text, search, sorting, live panels, profile readings, PDF generation and phone layout. Set `HOLOTYPE_PLAYWRIGHT_MODULE` if Playwright is installed outside Node's normal lookup paths. The check uses an isolated browser profile and leaves the user's saved data alone.
