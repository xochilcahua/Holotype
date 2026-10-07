# Twin pairs (written by Claude, before any run of the panel)

Written 2 October 2026 from panel_profiles.py, panel_profiles_extra.py and expectations.md only.
Do not edit after it is committed.

Purpose: does the app separate people who share a field, and does it leave alone people who should
read alike? Pairs are drawn from the panel itself, so no new authoring is needed. Depths differ
between some pairs; report each pair's depths and treat large depth gaps as a caveat.

PART 1 - pairs that should DIFFER on the named bits (the difference comes from expectations.md)
Format: first | second | bits expected to differ | the real difference in plain words
B06_choir_singer | B07_bedroom_guitarist | S | both sing or play; one only in a group, one only alone
B08_weekend_baker | A07_pastry_chef | S | both bake; one alone and for fun, one in a team doing competition work
A06_professional_cook | B08_weekend_baker | S | both cook; one in a team of eight, one alone at home
A01_retired_woodworker | B13_diy_maker | B | both build with wood; one stays in one trade, one spreads across wood, metal, bikes, electronics
C04_motion_designer | C07_colorist | S | both post-production; one works to directors in meetings, one alone on a screen
X03_intuitive_painter | D07_hand_letterer | P,F | both paint; one finds it as it goes and is abstract, one works to a specification and is literal
X01_jazz_improviser | B06_choir_singer | P | both musicians in groups; one improvises, one reads the score
X02_improv_comedian | B04_community_theatre_actor | P | both perform with others; one unscripted, one rehearsed to a script
X04_freestyle_rapper | B02_poet | P | both work with words; one makes lines up live, one is precise about form
X06_community_arts_organiser | X07_retired_teacher_did_a_class_in_everything | S,P,F | both rate 70+ forms across many fields; one collaborative and unplanned, one solitary and follows instruction
D01_collaborates_on_everything | D02_never_works_with_others | S,B | opposite working styles; one in ensembles in one field, one alone across several

PART 2 - pairs that should READ ALIKE (all four expected bits equal or EITHER)
B11_knitter | B12_hobby_sewist | none | pattern-based home textile makers, alone, functional
B01_novelist | B02_poet | none | solitary writers of open-ended work
A12_bookbinder | A03_printmaker | none | solitary exact paper-based traditional trades
C05_ux_designer | C09_technical_writer | none | structured functional work done with engineers

HOW TO SCORE (computed by the runner, not judged)
- Part 1: for each pair and each named bit, does the app's bit differ? Report hits out of total.
  A pair is a full hit only if every named bit differs.
- Part 2: identical genus? identical genus, regime and leans? Report hits out of 4.
- Every pair: the gap in each of the four z-values, and whether closeAxes (dead-band) contains the
  named bits for either person. A bit inside the dead-band is a coin-flip by design; report it
  separately instead of as a miss.
- Baseline: also report how many of 11 Part 1 pairs the app reads with identical genus, regime and
  leans, since that number is what "can the app separate similar people" is really asking.
