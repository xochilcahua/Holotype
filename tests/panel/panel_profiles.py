# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""A hand-written panel of 60 varied, realistic people.

WHY THIS EXISTS. Every synthetic population so far comes from a generator, and the
generators share one author's assumptions. Real sessions, when provided, are a small non-random sample.
Neither tells you whether the app reads DIFFERENT KINDS of person sensibly. This
panel is hand-written from plain descriptions, so each person's ratings were chosen
before anything was measured and cannot be bent toward a result.

AUTHORSHIP, STATED PLAINLY. Profiles A01-G01 (50 people) were written by an earlier
model that had already seen app output in the same session, so they are NOT blind.
Profiles X01-X10 (panel_profiles_extra.py), expectations.md and twins.md were written
by Claude before any app output on those people was seen. Names were checked against
src/data/art-forms.js. Nothing here is edited after the expectations are committed;
if a rating turns out to be wrong, the notes say so.

FORMAT. Same shape as archetypes.py, so the existing harness can consume it.
`ratings` is a list of (name, value). A person is described as they are, not as
the app would score them.

DEPTH SPREAD of the 60 (50 here, 10 in panel_profiles_extra.py): about 33 people rate
5-9 things, 21 rate 10-25, 4 rate 26-60, 2 rate 70+. The 70+ band is thin on purpose
of nothing but time; X06 and X07 carry seeded tails of one-off tries to fill it.
"""

PROFILES = []


def P(key, group, title, who, ratings, mapping=""):
    PROFILES.append(dict(key=key, group=group, title=title, who=who,
                         basis="hand-written for the persona panel; not derived from "
                               "any participation statistic",
                         ratings=[(n, v) for n, v in ratings],
                         mapping=mapping, discount=0.5, name=""))


def R(*pairs):
    """Compact rating list: R("Woodworking", 9, "Wood Turning", 7, ...)"""
    return list(zip(*[iter(pairs)] * 2))


# ============================================ A. heavy in one craft, mostly alone
P("A01_retired_woodworker", "A", "Retired cabinetmaker, forty years of one bench",
  "Made furniture professionally for four decades: benches, tables, boxes, a stair "
  "rail. Hand tools whenever the job allowed. Finished with turning and does it for "
  "pleasure rather than output.",
  R("Woodworking", 9, "Wood Turning", 7, "Furniture Design", 5, "Marquetry", 5,
    "Pyrography", 4, "Gilding", 3, "Basket Weaving", 3, "Sculpture", 3,
    "Metal Casting", 2, "Photography", 2, "Gardening & Plant Cultivation", 1))

P("A03_printmaker", "A", "Relief printmaker, editioned runs, teaches Saturdays",
  "Cuts lino and woodblocks and prints by hand in editions of about thirty. Teaches "
  "a beginner class every Saturday, which she enjoys more than the printing. The "
  "catalogue has one printmaking item, so her whole trade is a single rating.",
  R("Printmaking", 10, "Papermaking (Handmade Paper)", 6, "Illustration", 5,
    "Bookbinding", 4, "Calligraphy", 4, "Paper Marbling", 3, "Papercraft", 3,
    "Drawing", 3, "Zine Making", 2, "Book Carving", 2, "Photography", 2,
    "Cooking", 1))


P("A04_glassblower", "A", "Glassblower working hot, alone in a shed",
  "Blows glass for a living. Alone in a small hot shop six days a week. Hot, "
  "physical, repetitive, precise. Makes a bit of jewellery in winter when the shop "
  "is closed. Has photographed the process but never posted it.",
  R("Glassblowing", 10, "Flameworking & Lampworking (Glass)", 6,
    "Stained & Fused Glass", 5, "Jewelry Making", 4, "Sculpture", 3,
    "Ceramics & Pottery", 3, "Photography", 3, "Woodworking", 2,
    "Metal Casting", 2, "Architecture", 1, "Calligraphy", 1))

P("A05_leatherworker", "A", "Leatherworker making bags and mending other people's",
  "Tans, cuts and stitches leather. Bags and belts to order, plus a lot of repair for "
  "other people. Learned on the job mending a saddle. Small workshop, alone, but in "
  "constant contact with customers.",
  R("Leatherworking", 10, "Shoemaking & Cobbling", 6, "Bookbinding", 4,
    "Jewelry Making", 3, "Woodworking", 3, "Weaving", 2, "Sewing & Tailoring", 2,
    "Metal Casting", 2, "Sculpture", 2, "Photography", 1, "Cooking", 1,
    "Gardening & Plant Cultivation", 1))

P("A06_professional_cook", "A", "Restaurant sous-chef, every service with a team",
  "Cooks professionally in a busy kitchen. Every service alongside a team of eight, "
  "handed a section. Same menu repeatedly, which he likes. Cakes are a separate "
  "thing he does at home on Sundays.",
  R("Cooking", 10, "Baking & Pastry", 6, "Chocolate Making & Confectionery", 5,
    "Charcuterie & Butchery", 4, "Cheese Making", 3,
    "Fermentation & Pickling", 3, "Mixology (Cocktail Craft)", 2,
    "Gardening & Plant Cultivation", 2, "Photography", 1, "Singing", 1))

P("A07_pastry_chef", "A", "Pastry chef, sugar and chocolate, judges competitions",
  "Pastry chef. Sugar work, chocolate, laminated dough, cakes for events. Enters cake "
  "decorating competitions and wins some. Judges two a year. Team of three, teaches an "
  "apprentice.",
  R("Cake Decorating & Sugar Art", 10, "Baking & Pastry", 9,
    "Chocolate Making & Confectionery", 8, "Cooking", 4, "Mixology (Cocktail Craft)", 3,
    "Photography", 3, "Gardening & Plant Cultivation", 1, "Drawing", 1))

P("A08_wedding_photographer", "A", "Wedding photographer, alone with a camera for six hours",
  "Shoots weddings professionally. During a wedding he is alone with a camera for six "
  "hours and directs everyone else in the room. Then a weekend in a dark room "
  "grading, which is the part he actually enjoys.",
  R("Photography", 10, "Color Grading", 6, "Lighting Design", 5,
    "Documentary Filmmaking", 3, "Cinematography", 3, "Video Editing", 3,
    "Graphic Design", 2, "Painting", 2, "Cooking", 1,
    "Gardening & Plant Cultivation", 1))

P("A09_sculptor", "A", "Figurative sculptor, weeks alone in a yard studio",
  "Figurative sculpture. Carves stone and models in clay, mostly alone in a yard "
  "studio, weeks at a time on one piece. Casts in bronze occasionally. Two small "
  "open studios a year, no promotion.",
  R("Sculpture", 10, "Stone Carving", 7, "Drawing", 5, "Metal Casting", 6,
    "Ceramics & Pottery", 4, "Woodworking", 4, "Mosaic", 3, "Painting", 2,
    "Photography", 2, "Architecture", 1, "Gardening & Plant Cultivation", 1))

P("A10_sailmaker", "A", "Sailmaker and canvas worker, one pair of hands",
  "Makes and repairs sails and canvas covers by hand. Lofting, sewing heavy cloth. "
  "One person in the loft, talks to customers, then two weeks alone with a machine. "
  "The catalogue has no sailmaking item, so boatbuilding carries his whole trade.",
  R("Boatbuilding", 10, "Textile Dyeing", 5, "Weaving", 4, "Sewing & Tailoring", 4,
    "Woodworking", 4, "Leatherworking", 3, "Quilting", 3, "Embroidery", 3,
    "Metal Casting", 2, "Photography", 1, "Cooking", 1, "Sculpture", 1))


P("B01_novelist", "B", "Novelist, two books out, writes every morning",
  "Writes novels. Two published, a third on the go. Writes every morning before work. "
  "Occasional short story, occasional essay. Does not rate reading at all.",
  R("Fiction Writing", 10, "Nonfiction & Journalism", 5, "Poetry", 4,
    "Copywriting", 3, "Playwriting & Screenwriting", 2, "Stand-Up Comedy", 2,
    "Improv Theater", 1, "Photography", 1, "Cooking", 1))

P("B02_poet", "B", "Poet with two collections, performs occasionally",
  "Writes poetry, two collections out. Sends work to magazines, reads at small open "
  "mics twice a year and dislikes them. Precise about form. There is no reading item, "
  "so the reading that shapes her is simply not rateable.",
  R("Poetry", 10, "Fiction Writing", 4, "Spoken Word & Rap", 3, "Calligraphy", 3,
    "Playwriting & Screenwriting", 2, "Stand-Up Comedy", 2, "Zine Making", 2,
    "Improv Theater", 1, "Photography", 1, "Cooking", 1))


P("B03_journalist", "B", "Local journalist, features not news, writes to a deadline",
  "Local newspaper, features rather than news. Writes to a deadline, edits other "
  "people constantly. Has a blog nobody reads. Photographs everything for the paper. "
  "Wants to write more fiction and has not.",
  R("Nonfiction & Journalism", 10, "Copywriting", 6, "Photography", 5,
    "Fiction Writing", 3, "Comedy & Humor Writing", 2, "Poetry", 2,
    "Zine Making", 2, "Drawing", 1, "Cooking", 1))

P("B04_community_theatre_actor", "B", "Community theatre actor, musical twice a year",
  "Acts in amateur theatre. Two or three productions a year, mostly musical. Rehearses "
  "twice a week, which is the only reason he does it. Directs the youth group. Would "
  "call it a hobby twice a week, though he has been in it twenty years.",
  R("Acting", 8, "Musical Theater", 7, "Directing Theater", 5, "Singing", 5,
    "Dance", 3, "Improv Theater", 3, "Voice Acting", 2, "Stand-Up Comedy", 2,
    "Costume Design", 2, "Playwriting & Screenwriting", 1, "Photography", 1))

P("B05_standup_comic", "B", "Stand-up comic, five minutes a month, hates open mics",
  "Does stand-up. Five to ten minutes a month in small rooms, mostly in his own "
  "writing rather than others'. Writes a lot, performs little. Considers it a writing "
  "job he occasionally does in public.",
  R("Stand-Up Comedy", 9, "Comedy & Humor Writing", 7, "Spoken Word & Rap", 4,
    "Improv Theater", 3, "Acting", 2, "Fiction Writing", 2,
    "Directing Theater", 1, "Music Production", 1, "Photography", 1))

P("B09_cocktail_maker", "B", "Cocktail maker, bars on weekends, precise about ice",
  "Makes cocktails properly. Reads up on them, owns a jigger and good ice. Bar staff "
  "at weekends, a real job, very physical. Sweet baking is a separate thing she does "
  "at Christmas.",
  R("Mixology (Cocktail Craft)", 9, "Baking & Pastry", 5, "Cooking", 3,
    "Distilling", 3, "Coffee Roasting", 3, "Brewing, Wine & Spirits", 2,
    "Fermentation & Pickling", 2, "Gardening & Plant Cultivation", 1, "Singing", 1))

P("B10_florist", "B", "Florist, does weddings, works with her hands all day",
  "Florist with a shop. Arranges for weddings, stressful and collaborative by nature. "
  "Grows a lot of her own stock. The physical arranging is the part she loves; the "
  "shop and the wedding politics are the part she does not.",
  R("Floral Design", 10, "Gardening & Plant Cultivation", 7, "Ikebana", 4,
    "Drawing", 3, "Photography", 3, "Calligraphy", 2, "Interior Design", 2,
    "Cooking", 2, "Fiction Writing", 1))

P("B11_knitter", "B", "Knitter, shawls for friends, enjoys the maths",
  "Knits and crochets. Shawls, hats, a jumper a year. Follows patterns exactly and "
  "likes that there is a right answer. Knits in the evenings, on trains, in front of "
  "the television. Gives everything away.",
  R("Knitting & Crochet", 10, "Quilting", 4, "Sewing & Tailoring", 4, "Weaving", 3,
    "Embroidery", 3, "Rug Hooking & Tufting", 2, "Macrame", 2, "Cooking", 1,
    "Photography", 1))

P("B12_hobby_sewist", "B", "Hobby sewist, clothes for herself, some repairs",
  "Sews for herself and the children. A dress pattern she altered, curtains, and a "
  "lot of repairs. Made most of her own clothes until the children outgrew them. Not "
  "interested in making other people's clothes for money.",
  R("Sewing & Tailoring", 9, "Clothing Customization & Upcycling", 4, "Quilting", 4,
    "Knitting & Crochet", 3, "Embroidery", 3, "Weaving", 2, "Leatherworking", 2,
    "Fashion Design", 2, "Cooking", 1, "Photography", 1,
    "Gardening & Plant Cultivation", 1))

P("B13_diy_maker", "B", "DIY and small making, everything built twice",
  "Builds and fixes things. Flat-pack furniture, shelving, a bike he rebuilt. "
  "Everything gets made once badly and then again better. Learned from a father who "
  "would not let him throw anything away. Welding came later and he is proud of it.",
  R("Woodworking", 8, "Metal Casting", 5, "Custom Bicycle & Motorcycle Building", 4,
    "Creative Electronics & PCB Design", 4,
    "Digital Fabrication (3D Printing, Laser Cutting & CNC)", 3,
    "Leatherworking", 2, "Shoemaking & Cobbling", 2, "Jewelry Making", 2,
    "Cooking", 2, "Gardening & Plant Cultivation", 3))

P("B14_architect", "B", "Architect, housing, works in a practice of twelve",
  "Architect in a practice of twelve. Works on housing mostly, in a team, through long "
  "drawing stages. Draws constantly and precisely. Drove an architecture student once "
  "and never stopped. Photography is a habit rather than a practice.",
  R("Architecture", 10, "Drawing", 7, "Furniture Design", 4, "Interior Design", 4,
    "Photography", 4, "Landscape Design", 3, "Calligraphy", 2, "Painting", 2,
    "Sculpture", 1, "Cooking", 1))

P("B15_muralist", "B", "Muralist, large pieces, always with a crew",
  "Paints large murals on buildings. Always with a crew, on scaffolding, in bad "
  "weather, to a deadline set by a building. Preliminary art and colour work is the "
  "part she plans alone for weeks. The catalogue has no mural item, so sign painting "
  "carries it.",
  R("Sign Painting", 10, "Painting", 8, "Airbrush Art", 6, "Fresco Painting", 4,
    "Illustration", 4, "Drawing", 4, "Calligraphy", 3, "Mosaic", 3,
    "Papermaking (Handmade Paper)", 3, "Graffiti & Street Art", 2, "Photography", 3))


P("B06_choir_singer", "B", "Choir singer, alto, two services a week",
  "Sings alto in a community choir and a smaller chamber group. Two services a week "
  "plus Thursday rehearsal. Reads music well, cannot transpose. Solo is not really a "
  "thing she does, even in the car.",
  R("Singing", 9, "Musical Theater", 5, "Playing an Instrument", 3, "Poetry", 2,
    "Acting", 2, "Music Composition", 2, "Improv Theater", 1, "Scat Singing", 1,
    "Zine Making", 1, "Photography", 1, "Cooking", 1))


P("B07_bedroom_guitarist", "B", "Bedroom guitarist, plays covers, never performs",
  "Plays guitar, self-taught, mostly covers. Hasn't played for anyone in about a "
  "decade. Knows no music theory and does not want to. Plays because it is the first "
  "thing he does when he gets in.",
  R("Playing an Instrument", 9, "Singing", 4, "DJing", 2, "Music Composition", 2,
    "Music Production", 1, "Poetry", 1, "Drawing", 1, "Cooking", 1, "Photography", 1))

P("B08_weekend_baker", "B", "Weekend baker, sourdough most weeks",
  "Bakes at weekends. Sourdough most weeks because it is easier than it looks, plus a "
  "lot of pastry when there is a reason. Gives a lot of it away. Has never worked in a "
  "kitchen professionally and would not want to.",
  R("Baking & Pastry", 9, "Cake Decorating & Sugar Art", 5, "Cooking", 4,
    "Chocolate Making & Confectionery", 4, "Coffee Roasting", 3,
    "Gardening & Plant Cultivation", 2, "Mixology (Cocktail Craft)", 1,
    "Embroidery", 3, "Photography", 1, "Cooking", 1, "Sculpture", 1))

P("A11_luthier", "A", "Luthier, one guitar at a time, commissions only",
  "Builds acoustic guitars by hand, two or three years per instrument, on commission. "
  "Alone in a small shop, deals directly with the people who buy them. Plays a little "
  "to test the results, not much beyond that.",
  R("Instrument Making (Lutherie)", 10, "Woodworking", 7, "Wood Turning", 4,
    "Sculpture", 3, "Playing an Instrument", 3, "Metal Casting", 1, "Photography", 1,
    "Furniture Design", 1))

P("A12_bookbinder", "A", "Bookbinder restoring for libraries, works alone",
  "Restores and rebinds damaged books for libraries and private collectors. Hand "
  "sewing, hand paste, marbled endpapers. Almost all alone in a bindery. One evening "
  "class a month.",
  R("Bookbinding", 10, "Papermaking (Handmade Paper)", 8, "Paper Marbling", 6,
    "Calligraphy", 4, "Illustration", 4, "Book Carving", 3,
    "Paper Cutting (Kirigami & Scherenschnitte)", 3, "Textile Dyeing", 2,
    "Woodworking", 2, "Leatherworking", 2, "Photography", 2, "Cooking", 1))

# ===== C. digital, mostly solo, no other life -- SHORT lists, 5-8 things
P("C01_game_dev", "C", "Indie game developer, solo, ships every year",
  "Makes small games alone. Programming, art, audio, level design, all the same "
  "person. Releases yearly, never finishes anything longer. Plays other people's "
  "games constantly and thinks of them as work.",
  R("Video Game Design", 10, "Pixel Art", 6, "3D Modeling & Rendering", 3,
    "Mosaic", 1, "Singing", 2, "Cooking", 2))

P("C02_vj", "C", "VJ, two hours a week, alone in a dark room",
  "Visuals for other people's music. Learns the tracks, builds the set, performs the "
  "show. Alone in a dark room most of the working day. Never plays anything himself. "
  "Started from still-image work.",
  R("VJing (Live Visuals)", 10, "Video Editing", 6, "Motion Graphics", 5,
    "DJing", 4, "Digital Painting", 3, "Music Production", 3, "Photography", 2))

P("C03_generative_coder", "C", "Generative art coder, maths first, image second",
  "Writes code that makes images. Thinks of it as mathematics that happens to be "
  "visible. Some output is a lifetime, some is a sketch. Exhibits online, has never "
  "made anything with an audience in the room.",
  R("Generative Art", 10, "Data Visualization & Infographic Design", 6,
    "AI & Machine Learning Art", 5, "Interactive Fiction", 4, "Digital Painting", 3,
    "Mosaic", 1, "Cooking", 1))

P("C04_motion_designer", "C", "Motion designer, title sequences, tight briefs",
  "Motion design for titles and broadcast. Every job has a brief, a deadline, and a "
  "director in a review meeting. Precise timing is the whole skill. Was a graphic "
  "designer first and still thinks in layouts.",
  R("Motion Graphics", 10, "Visual Effects Compositing", 5, "Graphic Design", 6,
    "3D Modeling & Rendering", 4, "Video Editing", 4, "Type Design", 3,
    "Photography", 1))

P("C05_ux_designer", "C", "UX designer, research-heavy, ships with engineers",
  "User experience design. Talks to users constantly, which is the part she likes. "
  "Ships inside a product team, so every decision is negotiated with developers. "
  "Thinks in flows and states rather than screens.",
  R("UI & UX Design", 10, "Data Visualization & Infographic Design", 3,
    "Graphic Design", 5, "Short-Form Video & Social Content Creation", 2,
    "Illustration", 2, "Cooking", 2))

P("C06_sound_designer", "C", "Sound designer, film and games, mostly alone",
  "Designs sound for film and games. Layers, edits, mixes, foley sometimes. Works "
  "from a picture alone in a room. Rarely on set and does not want to be. Fussy about "
  "every single sound.",
  R("Sound Design", 10, "Foley Sound Effects", 8, "Music Production", 4,
    "Video Editing", 3, "DJing", 2, "Cooking", 1))

P("C07_colorist", "C", "Colourist, grading other people's films in the dark",
  "Grades. Takes other people's footage and makes it look intentional. Enormous, "
  "subjective, self-contained job on a calibrated screen. Talks to directors by phone, "
  "almost never in person. Photography was the training ground.",
  R("Color Grading", 10, "Video Editing", 6, "Photography", 5,
    "Visual Effects Compositing", 5, "Digital Painting", 4, "Cooking", 1))

P("C08_webdev_illustrator", "C", "Developer who draws constantly and well",
  "Writes software for a living. Draws in the evenings, properly, not doodles. Has "
  "sold three paintings. The two practices barely touch. Learned programming before "
  "drawing.",
  R("UI & UX Design", 8, "Illustration", 7, "Pixel Art", 4, "Digital Painting", 4,
    "Comics", 4, "Cooking", 3))

P("C09_technical_writer", "C", "Technical writer, documentation, very precise",
  "Writes documentation. Enormously precise about structure and examples, hates being "
  "asked to write a blog post. Works with engineers and is embedded with them for "
  "accuracy.",
  R("Instruction Pieces", 10, "Copywriting", 5, "Nonfiction & Journalism", 4,
    "Letter Writing", 3, "Comedy & Humor Writing", 2, "Cooking", 3))

P("C10_electronics_maker", "C", "Electronics and PCB designer, hobbyist who got serious",
  "Designs circuit boards. Started as a teenager and it never stopped, it just got "
  "more expensive. Works at a kitchen table. Enclosures are the part he is worst at. "
  "Would never call it engineering.",
  R("Creative Electronics & PCB Design", 10, "Circuit Bending", 6,
    "Woodworking", 3, "Jewelry Making", 2, "Cooking", 2))

# ===== D. collaborators, loners, and the brief's named cases -- SHORT, 5-8 things
P("D01_collaborates_on_everything", "D", "Collaborates on absolutely everything",
  "Nothing is made alone. Band, theatre company, film crew, choir, collective studio. "
  "Would not know what to do with a solo afternoon. Genuinely good at it, not bad at "
  "being alone.",
  R("Musical Theater", 7, "Acting", 7, "Improv Theater", 6, "Singing", 6, "Dance", 5,
    "Directing Theater", 5, "Choreography", 4, "Photography", 2))

P("D02_never_works_with_others", "D", "Works alone and prefers it, on principle",
  "Everything is made alone in a small room and always has been. Collaborative work is "
  "not on the list. Has turned down work that would have required it. Not unfriendly, "
  "just prefers the work to be his own.",
  R("Painting", 8, "Fiction Writing", 7, "Printmaking", 5, "Photography", 4,
    "Bookbinding", 3, "Zine Making", 3))

P("D03_thirty_things_kept_two", "D", "Tried thirty things, kept two",
  "Rates thirty forms, nearly all low. Two are high and everything else is a 1 or a 2. "
  "Enjoyed a great deal of this and finished almost none of it. Rates honestly, "
  "including the things she was bad at.",
  R("Fiction Writing", 8, "Ceramics & Pottery", 7, "Painting", 2, "Drawing", 2,
    "Photography", 2, "Knitting & Crochet", 2, "Baking & Pastry", 1, "Cooking", 1,
    "Singing", 2, "Playing an Instrument", 1, "Dance", 1, "Printmaking", 1,
    "Calligraphy", 1, "Jewelry Making", 1, "Gardening & Plant Cultivation", 1,
    "Poetry", 1, "Woodworking", 1, "Metal Casting", 1, "Embroidery", 1,
    "Beekeeping", 1, "Beadwork", 1, "Mosaic", 1, "Papercraft", 1, "DJing", 1))

P("D04_one_thing_at_ten", "D", "One thing at 10 and nothing else",
  "Rates exactly one form, at the top of the scale. Has given this a decade. Does not "
  "rate anything adjacent, not even the things she has tried. Either the rating means "
  "something specific or it is the only opinion she has.",
  R("Fiction Writing", 10))

P("D05_model_maker", "D", "Model maker, precise, one bench",
  "Builds architectural models to a drawing, in card and foam, at a scale where "
  "everything has to be exact. Days alone at a bench. Deadlines set by a site visit.",
  R("Miniatures & Dioramas", 9, "Paper Cutting (Kirigami & Scherenschnitte)", 6,
    "3D Modeling & Rendering", 5, "Sculpture", 3, "Photography", 2))

P("D06_puppet_maker", "D", "Puppet maker, strings and rod, performs too",
  "Makes string and rod puppets and performs with them. Carves, strings, paints, "
  "rehearses, performs to small houses. Solitary at the point of making, "
  "collaborative at the point of performing.",
  R("Puppetry", 9, "Wood Turning", 6, "Sculpture", 5, "Costume Design", 4,
    "Illustration", 3))

P("D07_hand_letterer", "D", "Hand-letterer, shop signs, one pair of hands",
  "Paints and draws shop signs and hand lettering by hand. Repeatable work to a "
  "specification, mostly alone in a workshop with a small crew on the big jobs.",
  R("Sign Painting", 9, "Calligraphy", 8, "Type Design", 5, "Illustration", 4,
    "Vinyl Cutting & Sign Craft", 2, "Photography", 2))

P("D08_dance_notator", "D", "Notates other people's dance, alone at a desk",
  "Records dance as notation. Sits in on rehearsals, then spends days alone "
  "transcribing. Works with performers constantly and makes nothing performable herself.",
  R("Choreography", 8, "Dance", 6, "Drawing", 4,
    "Photography", 2))

P("D09_theatre_tech", "D", "Runs the tech, builds the set",
  "Builds and runs the set for a small theatre. Carpentry, lighting, props, a bit of "
  "everything. Works with a director and a designer closely. Would not describe any of "
  "it as art.",
  R("Production & Set Design", 9, "Woodworking", 6, "Lighting Design", 5,
    "Metal Casting", 3, "Stage Magic", 1))

P("D10_enameller", "D", "Enamels and cloisonne, alone, one kiln",
  "Applies vitreous enamel to metal and does cloisonne. Fires a kiln every few days and "
  "loses work to it regularly. Small pieces, sold to one dealer. Almost entirely "
  "solitary.",
  R("Enameling", 10, "Jewelry Making", 6, "Metal Casting", 5, "Bookbinding", 2,
    "Glassblowing", 3))

# ===== E. working professionals with long lists -- 30-60 ratings each
P("E01_working_illustrator", "E", "Commissioned illustrator, forty years",
  "Draws pictures for publishers to brief and deadline, usually ink and watercolour. "
  "Precise, fast, reads a brief closely. Very long tail of everything tried and "
  "dropped over four decades. There is no catalogue item for ink drawing or "
  "watercolour, so those collapse into Drawing and Painting.",
  R("Illustration", 10, "Drawing", 6, "Calligraphy", 6, "Printmaking", 5,
    "Storyboarding", 5, "Painting", 4, "Comics", 3, "Graphic Design", 3,
    "Photography", 3, "Bookbinding", 4, "Paper Marbling", 2, "Papercraft", 2,
    "Zine Making", 2, "Book Carving", 2, "Mosaic", 2, "Ceramics & Pottery", 2,
    "Sculpture", 2,
    "Caricature", 2, "Editorial Cartooning", 1, "Motion Graphics", 1,
    "Collage", 2, "Papermaking (Handmade Paper)", 2, "Botanical & Scientific Illustration", 2, "Cooking", 3, "Gardening & Plant Cultivation", 2,
    "Live Coding Music", 1, "Tabletop Game Design", 2, "Nonfiction & Journalism", 2))


P("E02_studio_potter", "E", "Studio potter with a firing cycle",
  "Runs a small studio making functional pots. Throws, trims, handles, glazes, fires. "
  "Books orders, packs, posts, teaches two evenings a week. A long list because a potter "
  "tries every clay. Glazing and kiln firing are not catalogue items, so they collapse "
  "into Ceramics and Sculpture.",
  R("Ceramics & Pottery", 10, "Sculpture", 6, "Paper Marbling", 5,
    "Stained & Fused Glass", 5, "Drawing", 3, "Photography", 4, "Jewelry Making", 3,
    "Woodworking", 3, "Metal Casting", 3, "Mosaic", 2, "Bookbinding", 2,
    "Textile Dyeing", 2, "Weaving", 2, "Knitting & Crochet", 2, "Quilting", 1,
    "Embroidery", 1, "Beekeeping", 2, "Leatherworking", 2,
    "Papermaking (Handmade Paper)", 2, "Papercraft", 2, "Origami", 2,
    "Calligraphy", 2, "Sewing & Tailoring", 2, "Tattooing", 1, "Assemblage", 1,
    "Cooking", 4, "Baking & Pastry", 4, "Gardening & Plant Cultivation", 5,
    "Fermentation & Pickling", 2, "Coffee Roasting", 2, "Mixology (Cocktail Craft)", 1,
    "Botanical & Scientific Illustration", 2, "Zine Making", 2,
    "Landscape Design", 1, "Dry Stone Walling", 1, "Basket Weaving", 1,
    "Cheese Making", 1, "Cooking", 4))


P("E03_documentary_editor", "E", "Documentary editor, cuts for a living",
  "Cuts documentaries. Shaves hours down to ninety minutes and defends every cut to a "
  "director. Works alone in a suite, then in screenings with producers. Technical, "
  "taste-led, allergic to sentiment. Film editing and sound recording are not catalogue "
  "items; Video Editing and Sound Design carry them.",
  R("Video Editing", 10, "Documentary Filmmaking", 6, "Color Grading", 6,
    "Sound Design", 5, "Cinematography", 5, "Mixing & Mastering", 4,
    "Motion Graphics", 4, "Short-Form Video & Social Content Creation", 3,
    "Photography", 4, "Foley Sound Effects", 2, "Music Composition", 3,
    "Live Coding Music", 1, "Fiction Writing", 3, "Nonfiction & Journalism", 3,
    "Copywriting", 2, "Instruction Pieces", 3, "Storyboarding", 3,
    "Digital Painting", 2, "Graphic Design", 2, "Type Design", 1, "Cooking", 3,
    "Gardening & Plant Cultivation", 2, "Tabletop Game Design", 2,
    "Puzzle & Crossword Construction", 2, "Curating", 2,
    "Art Direction", 2, "Nonfiction & Journalism", 3))

P("G01_rates_many_things_at_three", "G", "Rates a great many things, almost all at 3",
  "The most engaged person in the panel. Rates a long list, almost all at 3, because 3 is what 'tried it, it was fine' means to her. A handful are higher. Her list is a record of curiosity rather than of expertise.",
  R("Playing an Instrument", 10, "Painting", 7, "Photography", 7, "Cooking", 7, "Drawing", 7, "Fiction Writing", 7, "Singing", 7, "Printmaking", 4, "Calligraphy", 4, "Illustration", 4, "Video Editing", 4, "Poetry", 4, "Nonfiction & Journalism", 4, "Baking & Pastry", 4, "Gardening & Plant Cultivation", 4, "Woodworking", 4, "Ceramics & Pottery", 4, "Knitting & Crochet", 4, "Sewing & Tailoring", 4, "Dance", 4, "Acting", 4, "Stand-Up Comedy", 4, "Architecture", 4, "Interior Design", 4, "Graphic Design", 4, "Music Production", 4, "Blacksmithing", 2, "Jewelry Making", 2, "Glassblowing", 2, "Weaving", 2, "Macrame", 2, "Embroidery", 2, "Quilting", 2, "Leatherworking", 2, "Lapidary & Gem Cutting", 2, "Papercraft", 2, "Origami", 2, "Bookbinding", 2, "Mosaic", 2, "Land Art", 2, "Type Design", 2, "Fashion Design", 2, "UI & UX Design", 2, "Motion Graphics", 2, "Video Game Design", 2, "Choreography", 2, "Directing Theater", 2, "Playwriting & Screenwriting", 2, "Improv Theater", 2, "Puppetry", 2, "Shadow Theater", 2))

# ---------------------------------------------------------------------------
# Self-check, so this module cannot be wrong silently.
#
# Roughly thirty invented names came out of writing these profiles from memory
# across three rounds -- "Whittling", "Lino Printing", "Mural Art", "Chess",
# "Watercolor Painting", "Running", "Swimming", "Yoga", "Manga", "Metalworking",
# "Natural History" and more. They all sound exactly like catalogue items and
# none of them exist. The catalogue also has NO item for running, cycling,
# swimming, yoga, board games, reading, travel or climbing, which archetypes.py
# already documented in its docstring.
#
# So the check lives here rather than in a separate step that can be forgotten.
# If a name is not in the catalogue, importing this module raises.
import os as _os
import re as _re

_SRC = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                     "..", "..", "src", "data", "art-forms.js")
_NAMES = set()
with open(_SRC, encoding="utf-8") as _f:
    for _m in _re.findall(r'"name":\s*"((?:[^"\\]|\\.)*)"', _f.read()):
        _NAMES.add(_m.replace('\\"', '"').replace("\\\\", "\\"))
_MISSING = sorted({n for p in PROFILES for n, _v in p["ratings"] if n not in _NAMES})
if _MISSING:
    raise SystemExit(
        "panel_profiles.py contains %d form names that are not in the catalogue:\n  %s\n"
        "Look them up in src/data/art-forms.js. Do not guess them."
        % (len(_MISSING), "\n  ".join(_MISSING)))
