# How the model works

Holotype compares art forms to suggest things to try, and uses your ratings to make a botanical profile. Both start with the catalogue's numerical descriptions of each practice.

## Describing art forms

Each form in `src/data/art-forms.js` has 35 numbers between 0 and 1. These axes describe traits such as planning, collaboration, interpretation, chance, fields and senses.

`src/model/distances.js` builds two tables:

- `DIST` combines differences in technique, domain, senses, material and context, with a small adjustment for shared category. It drives novelty scores.
- `REL` adjusts `DIST` for how crowded each neighborhood is. It ranks related forms so broadly connected practices do not dominate every list.

Context values equal to a category's usual value are treated as unknown. The `a6` axis is displayed but has no distance weight.

## Suggesting something new

For each unrated form, `src/model/novelty.js` compares it with your ratings. Nearby forms and higher ratings contribute more familiarity, and experience in several related forms can add up.

The displayed score runs from 1 to 100. A higher score means less overlap with your recorded experience. With no ratings there is no personal novelty score, so the Garden starts with participation estimates instead.

| Score | Displayed band |
| --- | --- |
| 1–40 | Familiar |
| 41–70 | In between |
| 71–100 | New ground |

The least familiar third of unrated forms also counts as New ground. The reach slider changes how broadly your ratings contribute to familiarity. A high score says little in your ratings suggests familiarity; it cannot tell whether you would enjoy or excel at a practice.

## Making the profile

Your personal vector averages technique, domain and sensory axes, weighting each form by its rating squared. Four binary decisions select one of 16 genera:

| Decision | Based on |
| --- | --- |
| Breadth | Whether sustained ratings (3 or above) cover at least three categories, with none holding more than 55% of their weight. |
| Process | The planned/improvised axis (`a1`) relative to simulated reference profiles. |
| Social | The solo/collaborative axis (`d1`). |
| Form | The literal/interpretive axis (`a4`, reversed). |

A fifth axis, chance (`b3`), selects a variety: *ordinata* for control, *flexilis* for a mix, or *aleatoria* for chance. Field leans appear after `cf.` as Latin adjectives, with plain-language labels underneath.

With fewer than four ratings, or none at 3 or above, the reading is provisional. The app also flags a fragile reading when changing an influential rating could change the genus.

## References and limits

`src/model/person-space.js` generates reference profiles from the catalogue and the app's assumptions. It groups them by number of ratings: 1–4, 5–9, 10–24, and 25 or more. Process and Form use participation-weighted references; Social uses an unweighted reference.

These references are simulated. They are not measurements of real users. Tests check consistency and behavior across synthetic profiles, but the model has not been validated as a psychological instrument. Treat the reading as a prompt for reflection, and expect it to change as you rate more.

## Flowers and plants

A form's flower shows its technique, domain and sensory axes. Your holotype uses your personal vector and the colors of your leading category.

The genus selects a plant drawing, while variety and field leans adjust its details. A saved seed keeps the color tones and small companion consistent across visits and session imports. The main shape and palette change as your ratings change.
