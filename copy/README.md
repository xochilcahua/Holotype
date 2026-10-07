# Edit the app's wording

This folder holds the text shown in Holotype. You can edit it with a plain-text editor; no programming is needed.

```text
copy/
  English/                 English text
  Español/                 Spanish text
  _language-names.js       recognized language names
  Update-languages.html    browser tool for rebuilding the bundle
  languages.js             generated bundle loaded by the app
```

The files are grouped by topic: `app-interface`, `how-to-use`, `herbarium-and-pdf`, `profiles-and-readings`, `categories`, and four `art-form-*` files for names, taglines, descriptions and suggestions. `word-variants` holds context-dependent labels.

## Edit an entry

Each entry has a first line used to identify it and a second line shown in the app. Entries are separated by a blank line.

```text
Garden
Jardín

Search art forms
Buscar disciplinas
```

Leave the first line unchanged and edit the text underneath. The English folder uses the same format; its second line can differ from the original source wording. The edited English text appears whenever English is selected.

A value can span several lines, but keep blank lines between entries only. Files ending in `.txt`, `.md` and `.json` are supported. JSON files use an object mapping English source text to displayed text.

Keep placeholders such as `{0}` and `{1}`: the app fills them with numbers or names. You can move them within a sentence, but keep each one's count. Keep any `<b>` and `<i>` tags for emphasis, including their closing tags.

## Apply your changes

For a local folder, choose either method:

- Open `Update-languages.html`, choose the `copy` folder, fix any reported errors, and save the new `languages.js` here. Reload the app.
- Run `python3 tools/locales.py build` from the project root.

Use `python3 tools/locales.py check` to check entries and translation coverage. Rebuild `dist/Holotype.html` when you want the portable file updated too.

On GitHub, commit or push your changes to `main`. The publishing workflow rebuilds the translations and portable app before updating the website. It does not commit the generated files back into the source repository.

## Add or remove a language

1. Copy `English` inside `copy` and rename the folder to the language, such as Français or हिन्दी.
2. Translate each entry's second line. Unfinished entries can keep the English value.
3. If the folder name is not recognized, add `language.txt` with `code: hi`, for example. An optional `name: हिन्दी` sets the menu label.
4. Rebuild `languages.js` with the browser tool or Python command.

To remove a language, delete its folder and rebuild.

English is the default on a first visit and after Reset. A chosen language is remembered by the browser and can also be restored from a session file.

## Names, variants and plurals

The logo stays the same in every language. Other uses of the app's name can be translated; Spanish uses Holotipo. Latin plant names and anything a user types stay unchanged.

Some names, such as Origami and Flamenco, are the same in both languages. The coverage tool counts matching values as untranslated, so these entries can appear in its remaining count.

`word-variants` can distinguish labels that depend on context. For example, `Cost | Moderate` and `Learning curve | Moderate` can have different Spanish endings. When a contextual value is absent, the ordinary translation is used.

The app currently supports singular and plural only. Languages with additional plural forms need wording that works within those two forms.

## Change source text

Maintainers can add translatable source text with the helpers in [the translation guide](../docs/translations.md), then run:

```sh
python3 tools/locales.py extract
```

The extractor scans the app, updates the English entries and adds new keys to other languages. Existing edited values are preserved. Removed keys move to `_old-copy.txt`, which the app ignores. Changing a source key requires checking its translations, even when the edit is small.
