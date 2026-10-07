# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Ten more panel people, written by Claude to fill gaps in panel_profiles.py.

WHY. The first 50 contain nobody expected to be improvised (P = LOW), only four expected to be
wide (B = HIGH), and nobody who rates 70 or more forms. Without those, the panel cannot test
whether the app can detect improvisers or generalists, or whether readings settle at depth.

HOW TO USE. Import AFTER panel_profiles (it appends to the same PROFILES list):
    import panel_profiles, panel_profiles_extra   # PROFILES now has 60 people

HAND-WRITTEN CORES, SEEDED TAILS. Each person's core ratings (the forms named in the
description) are written by hand. X06 and X07 also carry a long tail of 1-2 ratings ("tried
once") drawn with a fixed seed from forms not already used, so they reach 70+ ratings; the
tail is labelled in the key. Names are validated against the live catalogue at import time.
Written before any app output on these people was seen. Expectations are in expectations.md.
"""
import os, re, random, json
from panel_profiles import P, R, PROFILES

_HERE = os.path.dirname(os.path.abspath(__file__))
_CAT = os.path.join(_HERE, "..", "..", "src", "data", "art-forms.js")


def _catalogue_names():
    src = open(_CAT, encoding="utf-8").read()
    return set(re.findall(r'\bname:\s*"((?:[^"\\]|\\.)*)"', src)) | \
           set(re.findall(r'"name"\s*:\s*"((?:[^"\\]|\\.)*)"', src))


_NAMES = _catalogue_names()


def _tail(used, how_many, seed, high_share=0.0):
    rnd = random.Random(seed)
    pool = sorted(n for n in _NAMES if n not in used)
    picks = rnd.sample(pool, how_many)
    return [(n, 1 if rnd.random() < 0.7 else 2) for n in picks]


P("X01_jazz_improviser", "X", "Improvising jazz musician, plays in a working quartet",
  "Plays a different solo every night and would be bored otherwise. Reads charts but treats "
  "them as a starting point. Gigs four nights a week with the same three people. Scats when "
  "the horn is in the case. Writes a little but mostly to give the band something to play with.",
  R("Musical Improvisation", 10, "Playing an Instrument", 9, "Scat Singing", 6,
    "Music Composition", 4, "Music Arranging & Orchestration", 3, "Songwriting", 3,
    "Singing", 3, "Mixing & Mastering", 2, "Conducting", 1))

P("X02_improv_comedian", "X", "Improv comedian, house team at a small theatre",
  "Performs unscripted scenes with a troupe twice a week and rehearses by playing. Teaches "
  "beginners. Has never written a full script and does not want to.",
  R("Improv Theater", 10, "Acting", 7, "Stand-Up Comedy", 5, "Clowning", 4,
    "Comedy & Humor Writing", 4, "Musical Theater", 2, "Mime", 2, "Commedia dell'Arte", 2))

P("X03_intuitive_painter", "X", "Paints without sketching first, alone, abstract",
  "Starts with colour and finds the picture as it goes. Never plans a composition. Works "
  "alone in a spare room and shows almost nobody. Collage and wax on days the paint is not "
  "working.",
  R("Painting", 9, "Drawing", 7, "Encaustic (Wax) Painting", 5, "Collage", 5,
    "Printmaking", 3, "Mandala Art", 2, "Photography", 2, "Glitch Art", 1))

P("X04_freestyle_rapper", "X", "Freestyle rapper and beatboxer, cyphers and open stages",
  "Makes lines up on the spot, in cyphers with friends and alone in the car. Writes some "
  "things down afterwards. Beatboxes for the group.",
  R("Freestyle & Battle Rap", 9, "Spoken Word & Rap", 8, "Beatboxing", 6, "Songwriting", 5,
    "Poetry", 3, "Music Production", 3, "Improv Theater", 2, "DJing", 2))

P("X05_flow_artist", "X", "Flow artist, fire and juggling, practises alone, performs at festivals",
  "Moves with props and lets the practice decide what happens. Hours alone in a park or a "
  "garage, then a handful of festival sets a summer. Tries every new prop that appears.",
  R("Fire Performance & Flow Arts", 9, "Juggling", 8, "Cardistry & Card Flourishes", 6,
    "Stage Magic", 4, "Aerial Arts", 3, "Acrobatics & Tumbling", 3, "Dance", 3,
    "Clowning", 2))

_core06 = R("Social Practice Art", 8, "Curating", 7, "Flash Mob Choreography", 6,
            "Installation Art", 6, "Audio Walks", 5, "Zine Making", 5, "Guerrilla Art", 5,
            "Mail Art", 4, "Projection Mapping & Light Art", 4, "Performance Art", 4,
            "Graffiti & Street Art", 4, "Oral Storytelling", 4, "Photography", 4,
            "Cooking", 3, "Gardening & Plant Cultivation", 3, "Dance", 3, "Singing", 3,
            "Acting", 3, "Poetry", 3, "Drawing", 3, "Collage", 3, "Puppetry", 3)
P("X06_community_arts_organiser", "X", "Community arts organiser, runs projects with whoever turns up (70+, seeded tail)",
  "Runs neighbourhood arts projects: walks, zines, projection nights, street pieces. Nothing "
  "is made alone and almost nothing is planned past the next meeting. Has dabbled in "
  "everything that has ever come through the door. (Tail of one-off tries drawn with seed 3.)",
  _core06 + _tail({n for n, _ in _core06}, 50, 3))

_core07 = R("Painting", 6, "Drawing", 5, "Ceramics & Pottery", 6, "Knitting & Crochet", 5,
            "Gardening & Plant Cultivation", 6, "Baking & Pastry", 5, "Singing", 5,
            "Photography", 5, "Bookbinding", 4, "Calligraphy", 4, "Quilting", 4, "Weaving", 3,
            "Cooking", 5, "Woodworking", 3, "Mosaic", 3, "Embroidery", 3,
            "Playing an Instrument", 4)
P("X07_retired_teacher_did_a_class_in_everything", "X", "Retired teacher, an evening class in everything (70+, seeded tail)",
  "Has taken a beginners' class in almost every craft going and kept a few. Solitary mostly, "
  "follows what the teacher showed, enjoys all of it a little. (Tail of one-off classes "
  "drawn with seed 5.)",
  _core07 + _tail({n for n, _ in _core07}, 55, 5))

P("X08_makerspace_organiser", "X", "Runs a community makerspace, builds with whoever walks in",
  "Teaches the laser cutter on Mondays, welds with a volunteer on Wednesdays and fixes "
  "whatever is broken. Moves between wood, metal, electronics and fabric every week. Works "
  "with other people nearly all the time.",
  R("Digital Fabrication (3D Printing, Laser Cutting & CNC)", 8, "Creative Electronics & PCB Design", 7,
    "Woodworking", 7, "Metal Casting", 5, "Custom Bicycle & Motorcycle Building", 5,
    "Blacksmithing", 5, "3D Modeling & Rendering", 5, "Kinetic Sculpture & Automata", 5,
    "Leatherworking", 4, "Creative Robotics & Animatronics", 4, "Prop & Armor Making", 4,
    "Sewing & Tailoring", 3, "Brick Art (LEGO & Construction Toys)", 3))

P("X09_serial_dabbler", "X", "Serial dabbler: fifteen different crafts kept at a modest level",
  "Picks something up for a season, gets competent, moves on. Pottery, then weaving, then "
  "leather, then candles. Always alone, always from a book or a video, never improvises.",
  R("Ceramics & Pottery", 5, "Weaving", 5, "Leatherworking", 4, "Candle Making", 4,
    "Soap Making", 4, "Macrame", 4, "Felting", 4, "Bookbinding", 4, "Embroidery", 4,
    "Jewelry Making", 3, "Woodworking", 3, "Papercraft", 3, "Origami", 3, "Quilling", 3,
    "Beadwork", 3, "Resin Art", 2, "Mosaic", 2, "Textile Dyeing", 2, "Basket Weaving", 2,
    "Cooking", 2, "Gardening & Plant Cultivation", 2, "Drawing", 2, "Photography", 1))

P("X10_touring_theatre_maker", "X", "Touring theatre maker who also designs the show",
  "Directs, performs, writes and designs for a four-person touring company. Everything is "
  "made together in a van and a rehearsal room. Interprets, adapts and rewrites constantly.",
  R("Directing Theater", 8, "Acting", 7, "Production & Set Design", 6, "Playwriting & Screenwriting", 5,
    "Costume Design", 5, "Lighting Design", 5, "Puppetry", 5, "Shadow Theater", 4,
    "Sound Design", 4, "Mime", 3, "Clowning", 3, "Pro Wrestling & Stage Combat", 3,
    "Ritual Mask Making", 3, "Oral Storytelling", 3, "Musical Theater", 2, "Singing", 2,
    "Sewing & Tailoring", 2, "Woodworking", 2, "Photography", 1, "Cooking", 1))

# guard: every name must exist in the live catalogue
for _p in PROFILES:
    _bad = [n for n, _ in _p["ratings"] if n not in _NAMES]
    if _bad:
        raise ValueError(f'{_p["key"]}: names not in catalogue: {_bad}')
