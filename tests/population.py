# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""
A generative model of plausible Holotype users, for checking whether the app's output
distribution is plausible - not just whether each individual profile reads well.

The hand-written archetypes in archetypes.py say "this person is like this". This module
says "here is the shape of the whole population, and here are N people drawn from it", so
that questions like "does Cuscuta get 30% of people, and is that right?" get answered with
a distribution rather than an opinion.

SOURCES. Participation rates come from the NEA Survey of Public Participation in the Arts
2022 (12-month, US adults):
    any art creation/performance      52%   (ages 18-34: 66%; 65+: 33%)
    social or artistic dancing        22%
    singing (informally)              20%
    taking photographs                13%
    sewing / crocheting / needlework  12%
    playing an instrument             11%
    creative writing                   7%
    acting / performing                6%
    pottery / ceramics                 4%
The survey does not cover cooking, gardening or sport at all, and the app's catalog reaches
well below the survey's "arts" frame (phone snapshots, amateur dance, sport). So these
rates are used as *relative weights* for the families the survey does cover, not as an
attempt at a census. The weights are deliberately coarse and are declared in FAMILY_WEIGHTS
rather than hidden.

REAL-LIFE ACTIVITIES ARE MAPPED ONTO CATALOG ITEMS, never invented. The catalog has one item
for "Playing an Instrument", so guitar, piano, drums and ukulele all collapse into it. It has
no item for running, cycling, swimming, yoga, board games, reading or playing video games,
so those parts of a person's life cannot be rated at all - see archetypes.py for what that
means. Names here are checked against the live catalog by the test runner, which fails loudly
on a name that does not exist.

HOW A PERSON IS DRAWN. Three steps.
  1. Draw a family (weighted by participation) and then a type within it. A type is a
     coherent cluster - "singer", "maker", "dancer" - with its own house style.
  2. Give the person a depth and a breadth, drawn independently. depth sets the ceiling of
     their ratings, breadth sets how many forms they bother to rate.
  3. Emit ratings for that person's forms from a bottom-heavy distribution, because most of
     what anyone does is a little, and only a thin tail is done well.

TWO DELIBERATE MODELLING CHOICES, both of which are the point:
  - Ratings are NOT independent. A "singer" is far more likely to also rate instrument
    playing and songwriting, and very unlikely to rate blacksmithing. A "performer" skews
    collaborative, a "maker" skews solo. That correlation is what makes the interesting
    profiles, and it is what the d1 axis is actually reading.
  - A large share of users are near-zero on art. The app's most common real user is someone
    who rates two or three things at 1-3 and would rather not be here. Those are modelled
    explicitly rather than left as a token edge case.

The sampler is seeded, so the same seed always produces the same people.
"""

import random

# --- participation weights per family -----------------------------------------------------------
# Relative likelihood that an adult engages with this family in a given year. "none" is kept
# large on purpose: the survey says roughly half of adults made no art in the past year, and
# the app's catalog reaches lower-commitment activity than the survey's frame, so the honest
# share of people who arrive with almost nothing to rate is high.
FAMILY_WEIGHTS = {
    "none":     0.30,
    "photo":    0.145,   # NEA photography 13%, plus phone-only users the survey undercounts
    "music_v":  0.135,   # NEA singing 20% + instrument 11%, overlapping
    "dance":    0.115,   # NEA social/artistic dancing 22% - the most common art activity there is
    "visual":   0.085,
    "making":   0.075,   # NEA sewing/crochet 12%, ceramics 4%
    "writing":  0.055,   # NEA creative writing 7%
    "food":     0.045,   # not in the NEA frame at all, but real and frequent in this app
    "land":     0.035,
}

# --- what each type actually rates, and how it sits on the solo/collaborative axis ---------------
# core:  always rated. reach: the pool it samples its other forms from.
# solo_bias: >0 skews solo, <0 skews collaborative. This is the parameter that matters most for
#            the d1 axis, so it is first-class rather than emerging from the ratings.
# ceiling: the highest rating a deeply-engaged member of this type tends to give.
TYPES = {
    "none": dict(core=[], reach=[], solo_bias=0.0, ceiling=3),

    "phone_photographer": dict(
        core=["Photography"],
        reach=["Drawing", "Short-Form Video & Social Content Creation", "Digital Painting",
               "Collage", "Color Grading", "Motion Graphics"],
        solo_bias=+0.20, ceiling=6),

    "hobby_dancer": dict(
        core=["Dance"],
        reach=["Flamenco", "Noh", "Butoh", "Ta'ziyeh",
               "Choreography", "Flash Mob Choreography", "Tai Chi & Qigong"],
        solo_bias=-0.30, ceiling=7),

    "singer": dict(
        core=["Singing"],
        reach=["Playing an Instrument", "Songwriting", "Music Composition", "Musical Improvisation",
               "Music Production", "Music Arranging & Orchestration", "Mixing & Mastering",
               "Scat Singing", "Beatboxing", "Opera"],
        # CORRECTED during d1 validation. This was +0.10, which asserted that singers work
        # alone. Almost nobody sings alone: a band, a choir, a karaoke room. The app was right
        # and this model was wrong.
        solo_bias=-0.20, ceiling=8),

    "instrumentalist": dict(
        core=["Playing an Instrument"],
        reach=["Music Composition", "Music Production", "Musical Improvisation", "DJing",
               "Live Coding Music", "Songwriting", "Circuit Bending", "Mixing & Mastering",
               "Analog Record Cutting (Lathe & Wax Cylinder)"],
        # CORRECTED during d1 validation: +0.15 asserted instrumentalists work alone, but a
        # band or an orchestra is the ordinary destination for anyone good at this. Genuinely
        # mixed rather than solo, so this is now neutral.
        solo_bias=0.0, ceiling=8),

    "maker": dict(
        core=["Woodworking", "Ceramics & Pottery"],
        reach=["Metal Casting", "Blacksmithing", "Leatherworking", "Jewelry Making",
               "Glassblowing", "Stained & Fused Glass", "Bookbinding", "Papercraft",
               "Creative Electronics & PCB Design", "Instrument Making (Lutherie)",
               "Digital Fabrication (3D Printing, Laser Cutting & CNC)"],
        solo_bias=+0.35, ceiling=8),

    "sewer": dict(
        core=["Sewing & Tailoring", "Knitting & Crochet"],
        reach=["Embroidery", "Quilting", "Macrame", "Weaving", "Felting", "Rug Hooking & Tufting",
               "Beadwork", "Clothing Customization & Upcycling", "Spinning (Fiber)", "Basket Weaving"],
        solo_bias=+0.20, ceiling=7),

    "visual_artist": dict(
        core=["Drawing", "Painting"],
        reach=["Illustration", "Printmaking", "Calligraphy", "Comics", "Concept Art",
               "Mandala Art", "Botanical & Scientific Illustration", "Encaustic (Wax) Painting",
               "Caricature", "Chalk & Pavement Art"],
        solo_bias=+0.20, ceiling=8),

    "digital_artist": dict(
        core=["Digital Painting"],
        reach=["3D Modeling & Rendering", "Visual Effects Compositing", "Generative Art",
               "Motion Graphics", "UI & UX Design", "Pixel Art", "AI & Machine Learning Art",
               "Data Visualization & Infographic Design", "3D Character Animation"],
        # CORRECTED during d1 validation: +0.25 understated this. 3D modelling, digital painting
        # and VFX are desk work done by one person, coordinating only at the end.
        solo_bias=+0.35, ceiling=9),

    "writer": dict(
        core=["Fiction Writing", "Poetry"],
        reach=["Playwriting & Screenwriting", "Copywriting", "Letter Writing", "Nonfiction & Journalism",
               "Worldbuilding & Lore Design", "Comedy & Humor Writing", "Puzzle & Crossword Construction",
               "Speechwriting", "Ciphers & Hidden Messages", "Invented Languages"],
        solo_bias=+0.30, ceiling=8),

    "filmmaker": dict(
        core=["Video Editing"],
        reach=["Independent Filmmaking", "Cinematography", "Directing Film & TV", "Photography",
               "Sound Design", "Motion Graphics", "Documentary Filmmaking", "Color Grading",
               "Production & Set Design", "Foley Sound Effects"],
        solo_bias=-0.10, ceiling=8),

    "performer": dict(
        core=["Acting", "Directing Theater"],
        reach=["Improv Theater", "Stand-Up Comedy", "Voice Acting", "Spoken Word & Rap",
               "Clowning", "Mime", "Stage Magic", "Musical Theater", "Costume Design",
               "Puppetry", "Cardistry & Card Flourishes", "Juggling"],
        solo_bias=-0.45, ceiling=9),

    "food": dict(
        core=["Cooking"],
        reach=["Baking & Pastry", "Cake Decorating & Sugar Art", "Chocolate Making & Confectionery",
               "Fermentation & Pickling", "Coffee Roasting", "Brewing, Wine & Spirits",
               "Charcuterie & Butchery", "Cheese Making", "Mixology (Cocktail Craft)", "Floral Design"],
        solo_bias=+0.10, ceiling=8),

    "land": dict(
        core=["Gardening & Plant Cultivation"],
        reach=["Bonsai", "Topiary", "Espalier", "Terrarium & Vivarium Design", "Aquascaping",
               "Floral Design", "Ikebana", "Beekeeping", "Karesansui (Japanese Dry Gardens)",
               "Dry Stone Walling", "Landscape Design"],
        solo_bias=+0.25, ceiling=7),

    "sport": dict(
        core=["Martial Arts Forms (Kata, Taolu & Poomsae)"],
        reach=["Striking Arts (Karate, Taekwondo, Muay Thai & Boxing)",
               "Grappling Arts (Judo, Jiu-Jitsu & Wrestling)", "Fencing & HEMA", "Capoeira",
               "Archery (Target & Kyudo)", "Parkour & Freerunning", "Tai Chi & Qigong",
               "Figure Skating & Ice Dance", "Artistic Gymnastics", "Acrobatics & Tumbling",
               "Surfing", "Skateboarding"],
        solo_bias=+0.05, ceiling=8),
}

# which types a family can resolve to
FAMILY_TYPES = {
    "none": ["none"],
    "photo": ["phone_photographer"],
    "music_v": ["singer", "instrumentalist"],
    "dance": ["hobby_dancer"],
    "visual": ["visual_artist", "digital_artist"],
    "making": ["maker", "sewer"],
    "writing": ["writer"],
    "food": ["food"],
    "land": ["land"],
    "sport": ["sport"],
}

# --- depth and breadth distributions ------------------------------------------------------------
# Most people who rate anything at all are casual. Serious commitment is a real minority,
# and this matters: if the population is modelled as mostly deep, the app's z-scores will
# look far more decisive than a real population is, and the calibration will be tuned to a
# population that does not exist.
DEPTH_WEIGHTS = [(1, 0.55), (2, 0.33), (3, 0.12)]   # 1 casual, 2 hobbyist, 3 serious
BREADTH_WEIGHTS = [(2, 0.20), (3, 0.25), (5, 0.27), (8, 0.19), (12, 0.09)]

# The same distribution for people who have already opened the app. This is not the general
# population: anyone who loads a 306-item art-form rating sheet is self-selected, and they
# rate more things, and they rate them higher. Calibrating against the general population
# would understate both breadth and depth, so both are available and both get used.
ENGAGED_DEPTH_WEIGHTS = [(1, 0.18), (2, 0.42), (3, 0.40)]
ENGAGED_BREADTH_WEIGHTS = [(4, 0.14), (6, 0.24), (9, 0.28), (13, 0.21), (18, 0.13)]


def _pick_weighted(rng, pairs):
    r = rng.random()
    acc = 0.0
    for value, w in pairs:
        acc += w
        if r <= acc:
            return value
    return pairs[-1][0]


def _rating(rng, ceiling, is_core):
    """Turn 'how deep is this person' into an actual 1-10 self-rating.

    Self-rating is bottom-heavy: most things a person rates are a 2 or 3 and only a thin tail
    is done well. A flat uniform here would make almost everyone look like a specialist.
    """
    if is_core:
        v = rng.triangular(ceiling * 0.40, ceiling, ceiling * 0.80)
    else:
        v = rng.triangular(1, max(2.0, ceiling * 0.50), ceiling * 0.20)
    return max(1, min(10, int(round(v))))


def draw_person(rng, engaged=False):
    """Return one plausible person as a dict. engaged=True models someone who has already
    opened the app, which selects for more ratings and higher ones."""
    fam = rng.choices(list(FAMILY_WEIGHTS), weights=list(FAMILY_WEIGHTS.values()))[0]
    typ = rng.choice(FAMILY_TYPES[fam])
    spec = TYPES[typ]

    depth = _pick_weighted(rng, ENGAGED_DEPTH_WEIGHTS if engaged else DEPTH_WEIGHTS)
    breadth = _pick_weighted(rng, ENGAGED_BREADTH_WEIGHTS if engaged else BREADTH_WEIGHTS)
    ceiling = spec["ceiling"] + (depth - 2)          # serious members of a type rate higher
    if engaged:
        ceiling += 1                                # engaged users also self-report higher

    pool = list(dict.fromkeys(spec["core"] + spec["reach"]))
    core = list(spec["core"])
    n_extra = max(0, min(len(spec["reach"]), breadth - len(core)))
    forms = core + rng.sample(spec["reach"], n_extra) if spec["reach"] else list(core)

    ratings = {f: _rating(rng, ceiling, f in core) for f in forms}
    return dict(type=typ, family=fam, depth=depth, breadth=breadth, engaged=engaged,
                solo_bias=spec["solo_bias"], ratings=ratings)


def sample(n, seed=0, engaged=False):
    """n people drawn from the model. Seeded, so the same seed gives the same people."""
    rng = random.Random(seed)
    return [draw_person(rng, engaged) for _ in range(n)]


if __name__ == "__main__":
    import collections, sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    people = sample(n, seed=int(sys.argv[2]) if len(sys.argv) > 2 else 0)
    c = collections.Counter(p["type"] for p in people)
    print(f"{len(people)} people drawn (seed {sys.argv[2] if len(sys.argv) > 2 else 0})")
    for k, v in c.most_common():
        print("  %-22s %4d  %5.1f%%" % (k, v, v / len(people) * 100))
    nr = [len(p["ratings"]) for p in people]
    print("  mean forms rated: %.1f   (median %d)" % (sum(nr) / len(nr), sorted(nr)[len(nr) // 2]))
