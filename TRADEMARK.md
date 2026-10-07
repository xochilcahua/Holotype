# Holotype: name and logo

The code is free software under the AGPL (see [LICENSE](LICENSE)). The name and logo are not part of that licence. The
AGPL gives you rights over the code, and says nothing about who may call a program "Holotype". This page covers that.

"Holotype" (as the name of this app) and the wordmark with the flower are used by Teo Monroy as trademarks, unregistered
for now: Holotype™.

## You can, without asking

* Use, study, change and share the code under the AGPL.
* Say what your work is based on: "based on Holotype", "a fork of Holotype".
* Write about the project, review it, link to it, and refer to it by name.
* Run an unmodified copy and call it Holotype.
* Use the name to say what a tool works with ("a session viewer for Holotype").

## You can't, without permission

* Release a modified version under the name Holotype, or under a name or logo that could be mistaken for it.
* Suggest that your version or product is made, endorsed or approved by this project when it isn't.
* Use the wordmark or the flower logo as the identity of a different product.
* Register Holotype, or something confusingly close to it, as a trademark, company name, domain or app-store listing for
  software or creative-practice tools.

## If you fork it

Give your version its own name and logo. The places to change:

1. `index.html`: the `<title>`, the `.brand` markup (the wordmark) and the footer.
2. The strings that say "Holotype" in `src/ui/keys.js` (help window), `src/ui/print.js` and `src/ui/profile-page.js`
   (PDF export and profile page), and `src/model/genus-copy.js` (glossary).
3. The logo itself: `renderBrandMark()` in `src/ui/flower-card.js`, the wordmark rules in `src/styles/top-bar.css`, and
   the icons in `assets/icons/`.

`grep -ri holotype src index.html assets` finds them all. The code that draws the flower is part of the AGPL code and is
free to reuse; what is reserved is its use as this project's logo.

## Other uses

If you want to use the name in a way that isn't covered here, ask first (contact details are in the README). Reasonable
requests will usually get a yes. This page is only about the name and logo; it doesn't limit anything the AGPL lets you do
with the code.
