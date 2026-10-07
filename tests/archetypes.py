# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""
Population-realistic profile definitions for the Holotype test harness.

This module is the complement to profiles.py. profiles.py holds designed edge cases - the
ones you build to make a specific number move. This module holds the people who actually
arrive: the singer who also doodles, the person whose parents made them learn piano, the
CGI artist who produces music on the side. They are not extreme, and they are not designed
to be. The question these answer is "does the app read a normal person correctly", which is
a different question from "does the app behave correctly at the edges".

Where a profile draws on a number, `basis` says which number. The main sources are the NEA
Survey of Public Participation in the Arts 2022 (12-month US adult participation: 52% made
art; social/artistic dancing 22%; singing 20%; photography 13%; sewing/crochet 12%;
instrument 11%; creative writing 7%) and YouGov work on instrument learning (66% of UK/US
adults have learned an instrument, about half starting between ages 6 and 10; ukulele and
harmonica mostly self-taught).

A NOTE ON RATING REALITY. Most real users rate between 3 and 8 things, not twenty. A person
does not have an opinion about all 306 art forms, and the app is right to work from what
they do rate. The short profiles here are therefore intentional, and the distribution of
"how many forms do real people rate" is modelled properly in population.py rather than
guessed at.

MAPPING REAL LIFE ONTO THE CATALOG. The catalog has one item for "Playing an Instrument", so
guitar, piano, drums, bass and ukulele all collapse into it - which is the single biggest
loss of fidelity in the app and is called out per-profile where it bites. The catalog also
has no item for running, cycling, swimming, yoga, board games, reading or playing video
games, so none of those can be rated at all. That gap is real and is documented rather than
papered over.

Same dict shape as profiles.py, resolved against the live catalog at run time:
  key, group, title, who, basis, ratings, mapping, discount, name
"""

GROUPS = [
    ("P", "The everyday people (built from participation statistics)"),
    ("Q", "Composite and crossover profiles (two lives, one person)"),
    ("R", "Non-artists and near-zero raters (the largest real user group)"),
    ("S", "Realistic edge cases (plausible people who stress a specific behaviour)"),
]

STATS_NOTE = (
    "NEA Survey of Public Participation in the Arts 2022 (12-month adult participation): 52% created or performed any "
    "art; social/artistic dancing 22%, singing 20%, taking photographs 13%, sewing/crocheting/needlework 12%, "
    "playing an instrument 11%, creative writing 7%, acting/performing 6%, pottery/ceramics 4%. Participation is "
    "higher at ages 18-34 (66% any art) than at 65+ (33%). YouGov (3,000 US adults): 66% have learned an "
    "instrument at some point; about half started between ages 6 and 10; ukulele and harmonica mostly self-taught.")

PROFILES = []
TRACE_PROFILES = []
DET_KEY = "P01_singer_guitar_doodles"


def P(key, group, title, who, basis, ratings, mapping="", discount=0.5, name=""):
    PROFILES.append(dict(key=key, group=group, title=title, who=who, basis=basis, ratings=ratings,
                         mapping=mapping, discount=discount, name=name))

# ================================================================================== P. everyday people
P("P01_singer_guitar_doodles", "P", "Singer who plays a bit of everything and doodles",
  "A singer. Also plays guitar, more than a little but not a lot. Has some drums and a bit of "
  "bass and a bit of ukulele. Likes to doodle and does watercolours. Dances, but not as an art form. "
  "Photographs things on their phone, and took an analog photography class many years ago.",
  "The single most common realistic shape in the app. Singing is 20% adult participation and instrument playing "
  "11% (NEA 2022), and multi-instrument amateurs are the norm rather than the exception (YouGov: 66% have "
  "learned some instrument; ukulele largely self-taught).",
  [("Singing", 7), ("Playing an Instrument", 5, "guitar moderate; drums/bass/ukulele minor - all collapse into one item"),
   ("Drawing", 3, "doodling"), ("Painting", 4, "watercolour"), ("Dance", 2, "has danced, not as an art form"),
   ("Photography", 3, "phone photos plus one old analog class, one item")],
  "The app has a single 'Playing an Instrument' item, so four different instruments become one rating. "
  "Watercolour maps to Painting; doodling to Drawing; phone and analog photography to one Photography item.")

P("P02_cgi_artist_music_side", "P", "CGI artist who makes music on the side",
  "A CGI / VFX artist. Produces music as a hobby. Plays a little MIDI keyboard and no other instrument. "
  "Once dabbled in guitar and dropped out.",
  "Digital art creation is captured in the NEA 2022 survey ('creating art using a computer or mobile device'; "
  "'creative coding and design for software or games' was added in 2022). The dropped-out guitar is extremely "
  "common and is the reason the app cannot see abandoned interests.",
  [("3D Modeling & Rendering", 8), ("3D Character Animation", 5), ("Visual Effects Compositing", 5),
   ("Look Development (Look Dev)", 4), ("Motion Graphics", 4), ("Music Production", 4),
   ("Playing an Instrument", 3, "MIDI keyboard only; the dropped guitar adds nothing separate"),
   ("Sound Design", 2)])

P("P03_phone_photographer", "P", "Phone photographer who has never called it photography",
  "Takes photos constantly on their phone. Has shot weddings as a favour. Has never read a manual. "
  "Posts a lot. Doodles occasionally. Owns no camera.",
  "Photography is 13% of adult participation (NEA 2022) and the survey notes that most of it is phone and "
  "everyday capture rather than camera work. This is arguably the app's most common true user, and the "
  "hardest to place, because the app has one Photography item for both phone snapshots and pro work.",
  [("Photography", 5, "phone capture is constant and competent; no camera work at all"),
   ("Short-Form Video & Social Content Creation", 4), ("Drawing", 2, "doodles")],
  "A real tension: constant phone photography is genuine experience, but the app's only Photography item is "
  "written for camera work, so this person is scored as a mid-level photographer when they are a prolific one.")

P("P04_social_dancer", "P", "Goes out dancing, would not call it dancing",
  "Dances socially several times a month - salsa, some ballroom. Has taken maybe twenty lessons. "
  "Does not perform, does not watch dance. Goes to the gym, which the app has no item for.",
  "Social/artistic dancing is the single most common art activity in the NEA 2022 data at 22%, above singing. "
  "The app's 'Dance' item now stands alone as the only row for dancing, which is closer to right "
  "for this person than the old spread of 40 dance rows was.",
  [("Dance", 6, "social and partner dancing, regularly"), ("Singing", 2, "karaoke-adjacent")],
  "Gym/fitness has no catalog item, so a large part of this person's artistic life is invisible to the app.")

P("P05_forced_piano_kid", "P", "Played piano for two years because their parents made them",
  "Learned piano from about age 7 to 9 because their parents insisted. Can still read music and play a "
  "simple piece badly. Has not touched it since. Does not enjoy it and would not describe themselves as musical. "
  "Takes photos on their phone. Doodles in meetings.",
  "One of the largest single groups the app will meet: the forced lesson. Most adult 'musicians' are people who "
  "stopped at fourteen. YouGov's finding that about half of people start an instrument between 6 and 10 is the "
  "mechanism that makes this group so large.",
  [("Playing an Instrument", 3, "two years of piano as a child; retains reading ability"),
   ("Photography", 2, "phone snapshots"), ("Drawing", 2, "doodles, no more than that")],
  "The app cannot distinguish 'piano for two years, hated it' from 'three years of lessons and still going'. "
  "Both are Playing an Instrument = 3.")

P("P06_sews_and_knits", "P", "Makes things, mostly for other people",
  "Sews and knits regularly. Makes clothes for her children, repairs things, occasionally makes a jumper that "
  "turns out well. Bakes a lot. Keeps a small vegetable patch that has not done well.",
  "Sewing, crocheting and needlework is 12% of adult participation (NEA 2022), ahead of instrument playing.",
  [("Knitting & Crochet", 6), ("Sewing & Tailoring", 5), ("Baking & Pastry", 4),
   ("Gardening & Plant Cultivation", 2), ("Cooking", 4)])

P("P07_gardener", "P", "Allotment gardener who photographs it",
  "Keeps an allotment. Photographs the plot obsessively. Has tried three times to keep a pollinator garden. "
  "Bakes bread. Reads about it more than he does it.",
  "Gardening is common and is one of the few genuinely everyday pursuits the catalog covers directly, though it "
  "is absent from the NEA frame entirely.",
  [("Gardening & Plant Cultivation", 6), ("Photography", 4), ("Baking & Pastry", 3),
   ("Floral Design", 2, "cut flowers for the house"), ("Fermentation & Pickling", 3, "kimchi and kombucha")])

P("P08_bedroom_guitarist", "P", "Self-taught guitarist, eighteen, in a band",
  "Plays guitar, mostly self-taught, in a band that plays a couple of times a month. Has written songs. "
  "Records things on a phone. Tries to make beats. Went to guitar lessons once and hated it.",
  "The modal young-adult musician. Instrument playing is 11% of adults overall and much higher at 18-34, and "
  "self-taught is the majority route (YouGov: 66% have learned an instrument, largely self-directed).",
  [("Playing an Instrument", 6), ("Songwriting", 4), ("Music Production", 3), ("Mixing & Mastering", 2),
   ("DJing", 2, "messes about making beats")])

P("P09_writes_on_the_side", "P", "Writes on the side, does not call it writing",
  "Writes at night, mostly in a notes app. Has finished nothing. Used to write for a school magazine. "
  "Takes photos of things he notices. Occasionally makes short videos of places.",
  "Creative writing is 7% of adult participation (NEA 2022) - the least common of the majors here, which is why "
  "it is worth checking that the app does not over-read it as a large commitment.",
  [("Fiction Writing", 5), ("Nonfiction & Journalism", 3, "zines and occasional journalism"),
   ("Photography", 3), ("Short-Form Video & Social Content Creation", 2)])

P("P10_cooks_a_lot", "P", "Cooks seriously, thinks of it as feeding people",
  "Cooks most nights, from scratch, no recipe after the first two years. Makes bread, pastry, a lot of "
  "fermented things. Occasionally photographs the food. Owns far too many jars.",
  "Cooking is absent from the NEA art frame but is one of the most common genuinely skilled creative pursuits in "
  "the app, and the catalog covers it unusually well - 19 forms from charcuterie to latte art.",
  [("Cooking", 7), ("Fermentation & Pickling", 5), ("Baking & Pastry", 5), ("Charcuterie & Butchery", 3),
   ("Coffee Roasting", 3), ("Photography", 2, "food photos")])

P("P11_one_thing_deeply", "P", "Deep in one thing, almost nothing else",
  "Has played the cello since she was eight and is genuinely good. Does not sing. Has never taken a photo "
  "for pleasure. Rates nothing else above a 2.",
  "The specialist shape. Around 11% of adults play an instrument (NEA 2022) but only a small fraction do it "
  "seriously; testing a deep-but-narrow person checks that the app does not read breadth as shallowness.",
  [("Playing an Instrument", 9, "cello, since age 8"), ("Singing", 3, "school choir, left at 14"),
   ("Music Composition", 2, "has written one piece"), ("Photography", 2, "family photos only"),
   ("Baking & Pastry", 1)])

P("P12_knows_what_they_dont_know", "P", "Rates almost everything, almost nothing",
  "Rates most things at 1 or 2 because they have genuinely tried most things once. Is not a beginner at "
  "anything and does not enjoy any of it particularly. Rates one thing - cooking - at 6.",
  "The 'omnivore with a low ceiling' shape, which is a distinct and common profile: broad experience, no depth. "
  "It is the clearest test of whether the app's breadth measure is reading variety of experience rather than "
  "commitment.",
  [("Cooking", 6), ("Drawing", 2), ("Photography", 2), ("Singing", 2), ("Poetry", 2),
   ("Gardening & Plant Cultivation", 2), ("Playing an Instrument", 1), ("Dance", 1),
   ("Knitting & Crochet", 1), ("Video Editing", 1), ("Baking & Pastry", 2)],
  "The app's 'breadth' bit counts categories touched, so a person who rates fourteen things at 1-2 is scored as "
  "WIDE - the same word the app uses for someone with real range and depth. This profile is the check on that.")

# ================================================================================== Q. composite people
P("Q01_polymath", "Q", "Polymath: one thing deep, one thing middling, a lot of things shallow",
  "Deep in landscape photography. Middling at guitar. Knows a bit of cooking, drawing, gardening, "
  "programming, running (no catalog item), board games (no catalog item). Touches about nine things.",
  "The user-described polymath shape. It is the clearest check on whether the app can hold a genuinely "
  "asymmetric profile, and whether the genus survives a heavy tail of 1s and 2s.",
  [("Photography", 8, "landscape, several years, prints and exhibits"),
   ("Playing an Instrument", 4, "guitar, can play chords, nothing more"),
   ("Cooking", 3), ("Drawing", 2), ("Gardening & Plant Cultivation", 2),
   ("UI & UX Design", 3, "tinkers with web things"), ("Nonfiction & Journalism", 3, "blog, mostly"),
   ("Baking & Pastry", 2), ("Printmaking", 2)],
  "Running and board games have no catalog item, so roughly a fifth of this person's life is unrateable. "
  "The app has no single 'writing' item either, so a writer has to pick a specific one.")

P("Q02_serial_starter", "Q", "Starts things, finishes nothing, enjoys starting",
  "Has tried: pottery, guitar, a language, a coding course, sourdough, watercolour, cold plunges. "
  "Each was given four months. Reads a lot about each. Enthusiastic about all of them, competent in none.",
  "The 'starter' archetype, which the user asked for specifically. The app has to give this person a tribe "
  "that does not insult them, and the growth-habit axis is where it should land.",
  [("Ceramics & Pottery", 3), ("Playing an Instrument", 3), ("Fiction Writing", 2),
   ("UI & UX Design", 3), ("Baking & Pastry", 3), ("Painting", 2), ("Gardening & Plant Cultivation", 2),
   ("Singing", 2), ("Video Editing", 2)],
  "A natural spread across six categories, so the breadth bit will read WIDE. The test is whether the app "
  "calls this scattery or handles it kindly.")

P("Q03_teacher_two_things", "Q", "Drama teacher who also sings badly in church",
  "Teaches drama at a secondary school. Directs school productions. Plays piano and guitar. "
  "Sings in a church choir, unconfidently. Photographs every school event. Never performs herself "
  "beyond the school play.",
  "A very common professional crossover: one art is the job, one is a lifetime habit, one is a social duty.",
  [("Directing Theater", 8), ("Acting", 6), ("Playing an Instrument", 5),
   ("Singing", 3, "church choir, unconfident"), ("Photography", 4, "school events"),
   ("Costume Design", 3), ("Playwriting & Screenwriting", 2)])

P("Q04_chef_who_plants", "Q", "Restaurant chef with a serious home garden",
  "Runs a kitchen. Ferments, bakes, butchery, all seriously. Grows an unreasonable amount of vegetables. "
  "Photographs every dish. Cooks for friends constantly.",
  "Cooking is 19 catalog forms and one of the app's strongest areas. A chef who also gardens is a genuinely "
  "two-category person, so it is a clean test of the focused/wide bit.",
  [("Cooking", 9), ("Fermentation & Pickling", 7), ("Charcuterie & Butchery", 6),
   ("Baking & Pastry", 6), ("Gardening & Plant Cultivation", 5), ("Photography", 3),
   ("Floral Design", 2), ("Mixology (Cocktail Craft)", 3)])

P("Q05_nurse_knits_and_sings", "Q", "Nurse who knits in a very specific way",
  "Works as a nurse. Knits constantly, and well, mostly socks and jumpers. Sings in a choir. "
  "Makes jewellery for friends. Does nothing else at all.",
  "A mid-depth, single-domain-crossover person. Nothing about this is extreme, which is the point.",
  [("Knitting & Crochet", 7), ("Singing", 4), ("Jewelry Making", 4), ("Fiction Writing", 3),
   ("Baking & Pastry", 2), ("Gardening & Plant Cultivation", 1)])

P("Q06_dev_sidelong_illustration", "Q", "Software developer who draws a lot, badly, on the side",
  "Writes software for a living. Draws most evenings, mainly characters for a game he will never finish. "
  "Doodles in meetings. Has tried three different art courses. Plays some music while working.",
  "The maker-with-a-day-job shape, extremely common in the 18-34 band where participation is 66% (NEA 2022). "
  "The point of the profile is that the drawing is real and serious, but the day job is the depth.",
  [("UI & UX Design", 7), ("Digital Painting", 4), ("Drawing", 5), ("Concept Art", 3),
   ("Playing an Instrument", 2, "background music"), ("Video Game Design", 2),
   ("3D Modeling & Rendering", 2)])

# ================================================================================== R. non-artists
# The largest real user group and the one the app is least designed for. NEA 2022 says roughly
# half of US adults made no art in the past year. These profiles are what that looks like.
P("R01_phone_and_doodle_only", "R", "Phone photos and a doodle pad, nothing else",
  "Takes photos on a phone. Doodles in a pad, mostly on trains. Does not enjoy either particularly. "
  "Has been asked about art and says 'I don't really do anything'.",
  "The most probable single user of an app like this. Photography is 13% of adults and most of that is phone "
  "capture; drawing is not in the NEA top list at all. Everything else is a 1.",
  [("Photography", 2, "phone snapshots, constant but shallow"), ("Drawing", 2, "doodles")],
  "Two ratings, so the app is in its 'early' band. The question is whether the page is still worth reading.")

P("R02_forced_piano_and_nothing_else", "R", "Forced piano, and nothing else at all",
  "Piano for two years as a child, forced. Has not touched it since. Does not sing, does not draw, does not "
  "photograph. Rates exactly one thing, because that is all the app will let them rate.",
  "The forced-lesson group again, in its purest form. Worth testing alone because it is the smallest possible "
  "input that still produces a page.",
  [("Playing an Instrument", 3, "two years of piano at age 7-9, abandoned")])

P("R03_rates_one_thing_high", "R", "Only one thing rated, and it is high",
  "Rates one thing at 9 and stops. Will not elaborate.",
  "A real pattern: some users find one thing and answer only that. Tests that the app does not treat a "
  "single rating as a full answer.",
  [("Gardening & Plant Cultivation", 9)])

P("R04_four_ones", "R", "Rates four things, all at the floor",
  "Tried each of these once. Would not do any again. Rates them at 1 and closes the app.",
  "The floor case that still clears the app's 'early' threshold of four ratings, so it is the smallest input "
  "that produces a settled-looking page. If that page reads confidently, the app is over-claiming.",
  [("Drawing", 1), ("Singing", 1), ("Playing an Instrument", 1), ("Cooking", 1),
   ("Photography", 1), ("Dance", 1)])

P("R05_dad_at_the_school_play", "R", "Parent who does the school play once a year",
  "Does the school play every year - props, or a small role, or just drives everyone. Has done it since the "
  "children were small. Takes photos of everything. Does not do anything else creative.",
  "A very common and very under-served profile: a large recurring creative commitment in one narrow area, "
  "with no depth anywhere. Tests whether a low-ceiling but high-breadth person reads as a scatterer.",
  [("Directing Theater", 2, "helps every year, never directs"), ("Acting", 2, "small roles"),
   ("Photography", 5, "every event, phone and camera"), ("Costume Design", 2),
   ("Prop & Armor Making", 2, "made scenery once")])

P("R06_gym_only", "R", "Rates the one thing closest to exercise, and apologises",
  "Exercises four times a week. Has looked for anything in the app remotely like running or cycling and "
  "found nothing, so has rated the closest thing, which is a sport form, at a 3.",
  "The catalog's largest coverage gap. There is Sport & Martial Arts with 18 forms, and not one of them is "
  "running, cycling, swimming, weight training or a gym class - the single most common way adults spend "
  "deliberate physical time. A person whose main creative-adjacent habit cannot be expressed is a real "
  "and common user, and this is what they type.",
  [("Martial Arts Forms (Kata, Taolu & Poomsae)", 3, "the nearest thing the app offers to a gym class"),
   ("Tai Chi & Qigong", 2, "tried a class once"), ("Parkour & Freerunning", 1, "closest the app comes to park fitness")],
  "This is a documented gap, not a typo. It is recorded so the gap is visible in the data rather than hidden.")

P("R07_reformed_office_worker", "R", "Stopped everything ten years ago, still thinks about it",
  "Used to play in a band and draw seriously. Stopped when work got busy. Has not done either for a decade. "
  "Still has the guitar in a cupboard and the sketchbooks. Occasionally buys a record and looks at old photos.",
  "The 'suspended life' group, and probably the most emotionally important one the app will meet: real "
  "experience, no current practice. It is a direct challenge to a system that infers current behaviour from "
  "rated history alone.",
  [("Playing an Instrument", 4, "band, years ago, rusty now"), ("Drawing", 4, "serious, years ago"),
   ("Photography", 3, "has started again recently"), ("Singing", 2, "used to sing in the band")])

# ================================================================================== S. realistic edges
# Each of these is a plausible person chosen because they break something specific.
P("S01_rates_forms_they_have_never_done", "S", "Rates things he has never done, at a 3",
  "Rates a great many things at 3, having never done most of them, on the understanding that 3 means "
  "'I'd give it a go' rather than 'I have done this'.",
  "The single most common way people misuse a self-rating scale, and the app's scale note does not warn "
  "against it. A user who reads 3 as 'open to trying' rather than 'casual dabbling' inflates their own "
  "z-scores and lands further from the truth than if they had rated nothing.",
  [("Drawing", 3), ("Singing", 3), ("Playing an Instrument", 3), ("Photography", 3),
   ("Dance", 3), ("Cooking", 3), ("Knitting & Crochet", 3), ("Poetry", 3),
   ("Fiction Writing", 3), ("Gardening & Plant Cultivation", 3), ("Ceramics & Pottery", 3)])

P("S02_two_professionals_one_person", "S", "Two professional practices, one person",
  "Is a working illustrator and a working musician, both at professional level. Rates both high and rates "
  "nothing else above 2.",
  "Not rare, and a direct stress test: the genus has to survive two genuinely high, conflicting domains "
  "rather than averaging them into a middling person.",
  [("Illustration", 9), ("Playing an Instrument", 8), ("Singing", 7), ("Drawing", 8),
   ("Songwriting", 6), ("Music Production", 5), ("Printmaking", 3), ("Photography", 2),
   ("Baking & Pastry", 1)])

P("S03_heritage_and_now", "S", "Heritage practice plus a modern one",
  "Practises a traditional art form taught by family since childhood, seriously. Also does contemporary "
  "digital work as a job. The two never mix and they do not know how to talk about them together.",
  "A very common and very specific double life, and the app's 'related forms' and novelty scoring has to "
  "hold both without pretending they are the same activity.",
  [("Mesoamerican Ritual Dance", 7, "family tradition, since childhood"),
   ("Digital Painting", 7, "day job"), ("Illustration", 5), ("Costume Design", 4),
   ("Calligraphy", 3), ("Music Composition", 2), ("Photography", 2)])

P("S04_deep_and_shallow_same_category", "S", "Deep and shallow inside one category",
  "Deep in one dance form since childhood. Has tried most other dance forms once each and rates them at 1-2. "
  "Re-expressed over the dance rows that survived the collapse: the point is deep-versus-shallow inside one "
  "category, which Ballet-as-a-separate-row used to provide.",
  "Tests whether the app's novelty and relatedness logic keeps proposing the shallow forms the person has "
  "already dismissed, or whether mastery is respected.",
  [("Flamenco", 8, "since age 7"), ("Capoeira", 2), ("Chinese Opera", 1), ("Noh", 1),
   ("Puppetry", 1),
   ("Costume Design", 2), ("Photography", 2)])

P("S05_all_ones_but_one", "S", "Everything at the floor except one thing",
  "Rates forty things at 1 and one thing at 8.",
  "The heavy-tail case in its extreme. If the genus is computed on means, one rating among forty should barely "
  "move the reading; if it does, the maths is wrong.",
  [("Gardening & Plant Cultivation", 8)] + [(n, 1) for n in
   ["Drawing", "Painting", "Singing", "Playing an Instrument", "Photography", "Dance", "Poetry",
    "Cooking", "Video Editing", "Sculpture", "Knitting & Crochet", "Woodworking", "Ceramics & Pottery"]])

P("S06_person_who_did_everything_slightly", "S", "Rates twenty forms at exactly 3",
  "Has done about twenty things at a shallow, competent, unremarkable level. Would describe all of them as "
  "'a bit'. Genuinely enjoys all of them and is bad at committing to any.",
  "The most uniform realistic profile there is. Every axis sits near the corpus mean at once, which is the "
  "hardest single case for a four-bit sign-test classification, and the clearest test of the dead-band.",
  [(n, 3) for n in
   ["Drawing", "Painting", "Singing", "Playing an Instrument", "Photography", "Dance", "Poetry",
    "Cooking", "Baking & Pastry", "Knitting & Crochet", "Gardening & Plant Cultivation", "Video Editing",
    "Woodworking", "Fiction Writing", "DJing", "Tai Chi & Qigong",
    "Ceramics & Pottery", "Printmaking", "Jewelry Making", "Songwriting"]])

P("S07_high_ratings_almost_everywhere", "S", "Rates almost everything highly",
  "Rates almost everything at 6-9. Believes they are good at things. Is not, on most of them, but is "
  "enthusiastic and does try them.",
  "The opposite skew to the floor cases, and the only profile where the app's corpus-normalised z-scores could "
  "plausibly push a person into a confident-looking wrong reading.",
  [(n, r) for n, r in
   [("Drawing", 7), ("Painting", 6), ("Singing", 8), ("Playing an Instrument", 7), ("Photography", 6),
    ("Dance", 7), ("Poetry", 6), ("Cooking", 7), ("Baking & Pastry", 6), ("Knitting & Crochet", 5),
    ("Gardening & Plant Cultivation", 5), ("Video Editing", 6), ("Woodworking", 6),
    ("Fiction Writing", 7), ("DJing", 6), ("Tai Chi & Qigong", 5), ("Ceramics & Pottery", 5),
    ("Printmaking", 6), ("Jewelry Making", 5), ("Songwriting", 7)]])

TRACE_PROFILES = ["P01_singer_guitar_doodles", "Q01_polymath", "R04_four_ones", "P12_knows_what_they_dont_know"]
