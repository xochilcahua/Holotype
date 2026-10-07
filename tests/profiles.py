# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""
Profile definitions for the Holotype test harness.

A profile is a dict:
  key        short unique id
  group      one of GROUPS
  title      short label
  who        the person, in plain words
  basis      why this profile exists (statistics it draws on, or what an edge case is meant to exercise)
  ratings    list of (art form name, rating 1-10[, note about how the real-life activity maps onto the app's item])
             or "ALL" with all_value / all_random_seed to rate the whole catalog
  mapping    how real-life activities were mapped to the app's art-form list (the app has one generic item for
             e.g. "Playing an Instrument", so several instruments collapse into one rating)
  discount   "how far ratings reach" setting (default 0.5, the app's default)
  name       exporter name typed into the app (default: blank)

Names are resolved against the app's own catalog at run time (exact match first, then unique prefix, then unique
substring), so a typo fails loudly instead of silently rating the wrong thing.

RATING SCALE (from the app's own calibration note):
  1 = tried once or twice, or did it as a kid      3 = casual / occasional dabbling
  5 = working hobbyist, comfortable with basics    7 = quite good, serious hobbyist / semi-pro
  10 = professional-level mastery
"""

GROUPS = [
    ("A", "Common hobbyists (built from participation statistics)"),
    ("B", "Working professionals with hobby crossovers"),
    ("C", "Polymaths, starters and dabblers"),
    ("D", "Minimal-engagement and non-artistic people"),
    ("E", "Cultural and regional practices (incl. the newest catalog additions)"),
    ("F", "Edge cases and boundary tests"),
    ("G", "Setting variants: reach, plant seed, exporter name"),
    ("H", "Sport, making and tech-art additions (the 2026 catalog expansion)"),
]

STATS_NOTE = ("NEA Survey of Public Participation in the Arts 2022 (12-month adult participation): 52% created or performed any art; "
              "social/artistic dancing 22%, singing 20%, taking photographs 13%, sewing/crocheting/needlework 12%, playing an instrument 11%; "
              "participation is higher at ages 18-34 (66% / 59%) and with more education. YouGov (3,000 US adults): 66% have learned an "
              "instrument at some point; about half started between ages 6 and 10; ukulele and harmonica are mostly self-taught.")

PROFILES = []
def P(key, group, title, who, basis, ratings, mapping="", discount=0.5, name="", all_value=None, all_random_seed=None):
    PROFILES.append(dict(key=key, group=group, title=title, who=who, basis=basis, ratings=ratings, mapping=mapping,
                         discount=discount, name=name, all_value=all_value, all_random_seed=all_random_seed))

# ============================================================================================ A. common hobbyists
P("A01_singer_multi_instrument", "A", "Singer with several instruments, doodles and watercolors",
  "A singer who also plays guitar (more than a little, not a lot), has some drums or bass, a bit of ukulele; likes to doodle and paint watercolors; has danced but not as an art form; photographs things with a phone and took an analog photography class years ago.",
  "Singing and instrument playing are two of the five most common personal-art activities in the NEA 2022 data (20% and 11%); multi-instrument amateurs are common (YouGov: 66% have learned an instrument, ukulele mostly self-taught).",
  [("Singing", 7), ("Playing an Instrument", 5, "guitar moderate; drums/bass/ukulele minor - all collapse into the one instrument item"),
   ("Drawing", 3, "doodling"), ("Painting", 4, "watercolor"), ("Dance", 2, "has danced, not as an art form"),
   ("Photography", 3, "phone photos + an old analog class, one item")],
  "The app has a single 'Playing an Instrument' item, so guitar/drums/bass/ukulele become one rating. Watercolor maps to Painting; doodling to Drawing.")
P("A02_cgi_artist_music_hobby", "A", "CGI artist with music production as a hobby",
  "A CGI/VFX artist who produces music as a hobby, plays a little MIDI keyboard and no other instrument (once dabbled in guitar and dropped it).",
  "Digital art creation is captured in the NEA 2022 survey ('creating art using a computer or mobile device', 'creative coding and design for software or games' added in 2022).",
  [("3D Modeling & Rendering", 8), ("3D Character Animation", 5), ("Visual Effects Compositing", 5), ("Look Development", 4),
   ("Motion Graphics", 4), ("Music Production", 4), ("Playing an Instrument", 3, "MIDI keyboard; the dropped guitar attempt adds nothing separate"), ("Sound Design", 2)],
  "MIDI keyboard = Playing an Instrument. The abandoned guitar is folded into the same item.")
P("A03_social_dancer_singer", "A", "Weddings-and-karaoke casual",
  "Sings at karaoke, dances at weddings and clubs, takes phone photos; nothing formal.",
  "The two most common activities in NEA 2022: social/artistic dancing (22%) and singing (20%), plus photography (13%).",
  [("Singing", 3, "karaoke"), ("Dance", 3, "social dancing"), ("Photography", 2, "phone")], "")
P("A04_needlecraft_home", "A", "Weekend needlecrafter and home cook",
  "Knits and sews at home, a bit of embroidery, cooks and bakes regularly, takes phone photos.",
  "Sewing/crocheting/needlework is 12% of adults in NEA 2022, more common among women.",
  [("Knitting & Crochet", 5), ("Sewing & Tailoring", 4), ("Embroidery", 2), ("Cooking", 4), ("Baking & Pastry", 4), ("Photography", 2)], "")
P("A05_weekend_woodworker", "A", "Weekend woodworker / DIY",
  "Builds furniture and shelves in the garage, some leather and metal work, a few turned bowls.",
  "Woodwork, metalwork and leatherwork rose between 2017 and 2022 in the NEA data; more common among men (about 12% of White adults).",
  [("Woodworking", 6), ("Furniture Design", 3), ("Wood Turning", 2), ("Leatherworking", 3), ("Blacksmithing", 2), ("Drawing", 1, "sketching a plan")], "")
P("A06_home_cook_baker", "A", "Home cook and baker",
  "Cooks daily, bakes bread and cakes, ferments a bit, makes cocktails and coffee, photographs the food.",
  "Cooking and baking are near-universal hobbies; the app treats them as art forms in the Food, Scent & Plants category.",
  [("Cooking", 7), ("Baking & Pastry", 6), ("Cake Decorating & Sugar Art", 3), ("Fermentation & Pickling", 3), ("Mixology", 3),
   ("Latte Art", 2), ("Brewing, Wine & Spirits", 2), ("Photography", 2, "food photos")], "")
P("A07_hobby_writer", "A", "Hobby writer",
  "Writes stories and some poems, occasionally humour pieces and essays; doodles.",
  "Creative writing is one of the listed NEA 2022 activities and is stable between 2017 and 2022.",
  [("Fiction Writing", 6), ("Poetry", 4), ("Nonfiction & Journalism", 3), ("Comedy & Humor Writing", 2), ("Drawing", 2)], "")
P("A08_gamer_maker", "A", "Gamer who makes things",
  "Makes small games and pixel art, edits videos, dabbles in chiptune and tabletop design.",
  "NEA 2022 added creative coding/game creation as a measured activity; games and video are common entry points for younger adults (66% of 18-24 year olds created or performed art).",
  [("Video Game Design", 4), ("Pixel Art", 4), ("Chiptune & Demoscene Music", 2), ("Short-Form Video & Social Content Creation", 5),
   ("Video Editing", 4), ("Digital Painting", 3), ("Tabletop Game Design", 3)], "")
P("A09_social_media_creator", "A", "Short-form video creator",
  "Posts short videos, edits them, takes photos, some graphic design, writes captions.",
  "Creating art on a computer or mobile device and creating films/videos are both NEA 2022 activities.",
  [("Short-Form Video & Social Content Creation", 7), ("Video Editing", 5), ("Photography", 5), ("Motion Graphics", 3), ("Graphic Design", 3), ("Copywriting", 2)], "")
P("A10_choir_singer", "A", "Choir / church singer",
  "Sings weekly in a choir, plays some piano, has written a couple of songs.",
  "Singing in a group or choir is inside the NEA 2022 'singing' category (20%); 40% of adults who sang, made music, danced or acted did so in a place of worship (2017 report).",
  [("Singing", 7), ("Playing an Instrument", 4, "piano"), ("Songwriting", 2)], "")
P("A11_teen_artist_fandom", "A", "Teen artist, fandom and cosplay",
  "Draws constantly, digital art and comics, writes fan fiction, makes cosplay.",
  "Youngest adults report the highest art participation (66% at 18-24).",
  [("Drawing", 6), ("Digital Painting", 4), ("Comics", 4), ("Illustration", 4), ("Cosplay", 3), ("Fiction Writing", 4, "fan fiction"), ("Pixel Art", 2)], "")
P("A12_retired_painter", "A", "Retired hobby painter",
  "Paints and draws most days, botanical sketches, some photography, gardening, flower arranging, a bit of calligraphy.",
  "Older adults (65+) create or perform art at 45% (NEA 2022), with visual art and gardening-adjacent hobbies common.",
  [("Painting", 6), ("Drawing", 5), ("Botanical & Scientific Illustration", 3), ("Photography", 4), ("Landscape Design", 3), ("Floral Design", 2), ("Calligraphy", 2)], "")
P("A13_garage_band", "A", "Amateur rock-band musician",
  "Plays in a garage band, sings backup, writes songs, records demos at home.",
  "Instrument playing is 11% of adults and higher among men and the college-educated (NEA 2022).",
  [("Playing an Instrument", 7), ("Singing", 4), ("Songwriting", 5), ("Music Production", 3), ("Mixing & Mastering", 2), ("Musical Improvisation", 4)], "")
P("A14_bedroom_producer", "A", "Bedroom electronic producer / DJ",
  "Makes electronic music, mixes at parties, designs sounds, VJs occasionally.",
  "Electronic-music production is a common modern instrument-adjacent hobby; not separately measured by the NEA.",
  [("DJing", 6), ("Music Production", 6), ("Mixing & Mastering", 4), ("Sound Design", 4), ("Playing an Instrument", 2), ("VJing", 2)], "")
P("A15_social_dance_regular", "A", "Regular social dancer",
  "Goes to salsa and swing nights weekly, took some ballroom classes.",
  "Social dancing is the single most common personal-art activity in NEA 2022 (22%).",
  [("Dance", 7), ("Choreography", 1)], "")
P("A16_parent_crafter", "A", "Parent doing crafts with kids",
  "Draws and cuts paper with the children, bakes, sings lullabies and songs, folds origami.",
  "Broad low-intensity making is typical of household creative activity (63% of singing/dancing/acting/music-making happens at home, NEA 2017).",
  [("Drawing", 3), ("Papercraft", 3), ("Origami", 2), ("Collage", 3), ("Baking & Pastry", 4), ("Cake Decorating & Sugar Art", 2), ("Singing", 3, "lullabies"), ("Sculpture", 1, "clay with the kids")], "")

# ============================================================================================ B. professionals
P("B01_graphic_designer", "B", "Graphic designer",
  "Professional graphic designer with side illustration and photography.", "Working professional in a design-adjacent field, with adjacent skills at hobby level.",
  [("Graphic Design", 9), ("Illustration", 6), ("Type Design", 4), ("Photography", 6), ("UI & UX Design", 5), ("Drawing", 6), ("Motion Graphics", 4), ("Art Direction", 5)], "")
P("B02_actor", "B", "Professional actor with improv and voice work",
  "Stage actor who also does improv, voice acting and musical theatre.", "Performance professional.",
  [("Acting", 9), ("Improv Theater", 6), ("Voice Acting", 5), ("Musical Theater", 5), ("Singing", 4), ("Stand-Up Comedy", 2), ("Dance", 3)], "")
P("B03_chef", "B", "Professional chef",
  "Restaurant chef with pastry, fermentation and charcuterie.", "Food professional.",
  [("Cooking", 9), ("Baking & Pastry", 6), ("Fermentation & Pickling", 5), ("Charcuterie & Butchery", 4), ("Sushi Making", 3), ("Cake Decorating & Sugar Art", 3), ("Mixology", 3)], "")
P("B04_architect", "B", "Architect who sketches and builds",
  "Practicing architect, sketches, models, designs interiors and furniture.", "Built-environment professional.",
  [("Architecture", 9), ("Drawing", 6), ("Interior Design", 5), ("Landscape Design", 4), ("3D Modeling & Rendering", 5), ("Furniture Design", 4), ("Miniatures & Dioramas", 3), ("Photography", 4)], "")
P("B05_composer", "B", "Professional composer-musician",
  "Composer and instrumentalist, arranges and conducts, improvises, produces.", "Music professional.",
  [("Music Composition", 9), ("Playing an Instrument", 9), ("Music Arranging & Orchestration", 7), ("Conducting", 4), ("Musical Improvisation", 7), ("Music Production", 5), ("Songwriting", 6)], "")
P("B06_ceramicist", "B", "Studio ceramicist",
  "Full-time potter with some sculpture, drawing and kintsugi.", "Craft professional.",
  [("Ceramics & Pottery", 9), ("Sculpture", 5), ("Jewelry Making", 3), ("Weaving", 2), ("Drawing", 3), ("Kintsugi", 3)], "")
P("B07_filmmaker", "B", "Independent filmmaker",
  "Directs, shoots, edits and grades; writes scripts; some sound.", "Directing/curating professional.",
  [("Independent Filmmaking", 8), ("Video Editing", 8), ("Cinematography", 6), ("Color Grading", 5), ("Directing Film & TV", 6), ("Playwriting & Screenwriting", 5), ("Sound Design", 3), ("Documentary Filmmaking", 4)], "")
P("B08_theatre_technician", "B", "Theatre designer-technician",
  "Lighting and set designer with costume, projection and sound side work.", "Stage-design professional.",
  [("Lighting Design", 8), ("Production & Set Design", 7), ("Costume Design", 5), ("Art Direction", 4), ("Projection Mapping & Light Art", 4), ("Sound Design", 3), ("Directing Theater", 3)], "")
P("B09_game_developer", "B", "Game developer",
  "Professional game developer with 3D, pixel art, tabletop and interactive fiction hobbies.", "Digital professional.",
  [("Video Game Design", 9), ("3D Modeling & Rendering", 6), ("Pixel Art", 4), ("Generative Art", 3), ("Music Composition", 3), ("Interactive Fiction", 3), ("Tabletop Game Design", 5)], "")
P("B10_tattoo_artist", "B", "Tattoo artist",
  "Professional tattooist who draws, illustrates and paints.", "Body-art professional with a strong drawing base.",
  [("Tattooing", 9), ("Drawing", 8), ("Illustration", 7), ("Painting", 5), ("Body Art", 4), ("Graphic Design", 3), ("Calligraphy", 3)], "")

# ============================================================================================ C. polymaths / starters
P("C01_polymath", "C", "Polymath: one deep, several mid, many light",
  "Paints seriously; sculpts, composes, writes, photographs and cooks at a good hobby level; and has dabbled in a long list of other things.",
  "The classic generalist shape requested: depth in one area, mid-level in a few, a little in many.",
  [("Painting", 9), ("Sculpture", 6), ("Music Composition", 5), ("Fiction Writing", 5), ("Photography", 6), ("Cooking", 5),
   ("Woodworking", 2), ("Ceramics & Pottery", 3), ("Poetry", 3), ("Dance", 2), ("Singing", 3), ("Acting", 2), ("Weaving", 1), ("Origami", 2),
   ("Calligraphy", 3), ("Mosaic", 1), ("Graphic Design", 3), ("Landscape Design", 2), ("Baking & Pastry", 3), ("Perfumery", 1), ("Improv Theater", 2), ("Stand-Up Comedy", 1)], "")
P("C02_serial_starter", "C", "Serial starter, never gets pro",
  "Starts new hobbies constantly - guitar, pottery, knitting, brewing, magic, juggling - and none goes past beginner.",
  "The classic 'likes to start things but never gets pro' shape: many items, all at the low end.",
  [("Playing an Instrument", 3, "guitar"), ("Painting", 2), ("Ceramics & Pottery", 2), ("Knitting & Crochet", 2), ("Woodworking", 1), ("Calligraphy", 3), ("Origami", 2),
   ("Podcasting & Audio Storytelling", 2), ("Video Game Design", 1), ("Bonsai", 2), ("Baking & Pastry", 3), ("Brewing, Wine & Spirits", 2), ("Playwriting & Screenwriting", 1),
   ("Poetry", 2), ("Stand-Up Comedy", 1), ("Juggling", 2), ("Stage Magic", 3), ("Improv Theater", 2), ("Photography", 3), ("Leatherworking", 2),
   ("Candle Making", 2), ("Soap Making", 2), ("Embroidery", 2), ("Terrarium & Vivarium Design", 2)], "")
P("C03_uniform_mid", "C", "Even generalist: twenty things, all at 5",
  "Does twenty different things equally, at a comfortable hobby level.", "Uniform mid-level breadth.",
  [(n, 5) for n in ["Drawing", "Singing", "Cooking", "Woodworking", "Acting", "Video Editing", "Poetry", "Photography", "Ceramics & Pottery", "Playing an Instrument",
                    "Graphic Design", "Landscape Design", "Dance", "Baking & Pastry", "Video Game Design", "Sewing & Tailoring", "Improv Theater", "Fiction Writing", "Interior Design", "Sculpture"]], "")
P("C04_t_shaped", "C", "T-shaped professional",
  "One professional specialism (UI/UX) with a shallow layer across a dozen other things.", "Depth in one, thin layer across many.",
  [("UI & UX Design", 9)] + [(n, 2) for n in ["Drawing", "Photography", "Cooking", "Singing", "Video Editing", "Poetry", "Woodworking", "Baking & Pastry", "Graphic Design", "Playing an Instrument", "Dance", "Landscape Design"]], "")
P("C05_two_depths", "C", "Two unrelated depths",
  "Serious cook and serious musician, little else.", "Two deep specialisms in different categories.",
  [("Cooking", 8), ("Baking & Pastry", 7), ("Playing an Instrument", 8), ("Music Composition", 6), ("Singing", 4)], "")
P("C06_phase_hopper", "C", "Hobby-phase hopper",
  "Currently into knitting and baking; earlier phases of woodworking, pottery, painting and guitar are behind them.", "Recent depth plus a trail of past phases.",
  [("Knitting & Crochet", 5), ("Baking & Pastry", 5), ("Woodworking", 3), ("Ceramics & Pottery", 3), ("Painting", 3), ("Playing an Instrument", 3, "old guitar phase")], "")
P("C07_digital_shallow_wide", "C", "Wide and shallow digital native",
  "Tries every new digital format: shorts, pixel art, generative art, podcasts, AI art, motion graphics.", "Wide, shallow, digital-only.",
  [("Short-Form Video & Social Content Creation", 4), ("Pixel Art", 3), ("Generative Art", 2), ("Podcasting & Audio Storytelling", 3), ("Video Game Design", 3),
   ("Digital Painting", 3), ("AI & Machine Learning Art", 4), ("Motion Graphics", 2), ("Glitch Art", 2), ("Net Art", 1)], "")

# ============================================================================================ D. minimal / non-artistic
P("D01_nonartistic_basic", "D", "Non-artistic: phone photos, childhood piano, a doodle",
  "Takes phone photographs, played piano for a couple of years because parents insisted, has doodled; does not enjoy any of it.",
  "The most common shape: 48% of US adults made no art in 2022 (NEA); 66% have learned an instrument at some point (YouGov); a Baylor alumni study found the most common reason for starting piano was the parents' decision (small, non-representative sample).",
  [("Photography", 2), ("Playing an Instrument", 1, "piano as a child"), ("Drawing", 1)], "")
P("D02_nonartistic_school_exposure", "D", "Non-artistic: school-level exposure to the common forms",
  "As D01 plus the usual school and party exposure: karaoke, dancing at weddings, a school play, a poem, a painting class, home cooking.",
  "Wider but very light contact with the most common forms.",
  [("Photography", 2), ("Playing an Instrument", 1), ("Drawing", 1), ("Singing", 1), ("Dance", 1), ("Painting", 1), ("Cooking", 2), ("Poetry", 1), ("Acting", 1)], "")
P("D03_only_cooks", "D", "Only cooks", "Cooks dinner; nothing else.", "Single common activity.", [("Cooking", 4)], "")
P("D04_only_phone_photos", "D", "Only phone photos", "Takes phone photos; nothing else.", "Single most common visual activity.", [("Photography", 2)], "")
P("D05_recorder_and_choir", "D", "Recorder at school and choir once", "Played recorder in primary school and sang in the school choir.", "Childhood-only music exposure.",
  [("Playing an Instrument", 1, "recorder"), ("Singing", 1)], "")
P("D06_active_non_artist", "D", "Sporty non-artist", "Plays sports and did gymnastics at school; dances at parties; tried parkour.", "Movement-based but not art-identified.",
  [("Dance", 2), ("Acrobatics & Tumbling", 2), ("Parkour & Freerunning", 3), ("Artistic Gymnastics", 2)], "")
P("D07_office_doodler", "D", "Office worker: slides, charts, doodles", "Makes slide decks and charts at work, doodles in meetings, takes phone photos.", "Workplace-adjacent design exposure only.",
  [("Drawing", 2), ("Graphic Design", 1), ("Data Visualization & Infographic Design", 3), ("Photography", 3), ("Copywriting", 2)], "")
P("D08_casual_gardener", "D", "Casual gardener", "Keeps a small garden and houseplants, cooks, takes phone photos.", "Plant-adjacent hobby without art self-identification.",
  [("Landscape Design", 3), ("Floral Design", 2), ("Bonsai", 1), ("Terrarium & Vivarium Design", 2), ("Cooking", 3), ("Photography", 2)], "")

# ============================================================================================ E. cultural / regional
P("E01_folklorico_school", "E", "School ballet folklórico dancer",
  "Danced Mexican regional dances for years in school groups; some singing, guitar, and hand-embroidered costumes.", "Regional folk dance is a common youth activity in Mexico and the Mexican diaspora.",
  [("Dance", 6), ("Singing", 3), ("Playing an Instrument", 2), ("Sewing & Tailoring", 2), ("Embroidery", 3)], "")
P("E02_danza_azteca", "E", "Danza azteca / conchera practitioner",
  "Dances in a ceremonial group, plays the huehuetl, teponaztli and conch, makes beadwork and embroidered regalia.", "Living pre-Hispanic-rooted ritual dance (newly added catalog item).",
  [("Mesoamerican Ritual Dance", 8), ("Playing an Instrument", 5), ("Beadwork", 4), ("Embroidery", 3), ("Singing", 3), ("Sewing & Tailoring", 3)], "")
P("E03_voladores", "E", "Danza de los Voladores participant",
  "Performs the flyers' ritual, plays the flute-and-drum role, comfortable with ritual dance and heights.", "Newly added catalog item with rare, specific practice.",
  [("Danza de los Voladores", 8), ("Mesoamerican Ritual Dance", 5), ("Playing an Instrument", 4), ("Acrobatics & Tumbling", 3)], "")
P("E04_capoeirista", "E", "Capoeirista", "Trains capoeira, plays berimbau, sings in the roda, tumbles.", "Movement + music + martial art.",
  [("Capoeira", 8), ("Playing an Instrument", 5), ("Singing", 5), ("Acrobatics & Tumbling", 4), ("Dance", 3)], "")
P("E05_japanese_traditional_arts", "E", "Student of traditional Japanese arts",
  "Studies tea ceremony, ikebana, calligraphy; has watched and studied Noh and Kabuki; folds origami; likes kintsugi.", "Traditional-arts cluster across categories.",
  [("Japanese Tea Ceremony", 5), ("Ikebana", 4), ("Calligraphy", 5), ("Noh", 4), ("Kabuki", 3), ("Origami", 3), ("Karesansui", 1), ("Kintsugi", 3)], "")
P("E06_flamenco", "E", "Flamenco dancer", "Trains flamenco seriously; some palmas and guitar; choreographs a little.", "Newly added catalog item.",
  [("Flamenco", 8), ("Dance", 5), ("Playing an Instrument", 3), ("Singing", 2), ("Choreography", 3)], "")
P("E07_totem_carver", "E", "Woodcarver working in totem/ceremonial styles", "Carves cedar figures and poles, uses chainsaw and hand tools, draws designs first.", "Newly added catalog item alongside existing woodworking.",
  [("Totem Pole & Ceremonial Carving", 6), ("Woodworking", 6), ("Chainsaw Carving", 4), ("Wood Turning", 3), ("Drawing", 4)], "")
P("E08_rhythmic_gymnast", "E", "Former rhythmic gymnast", "Competed in rhythmic gymnastics as a teen, trained ballet, choreographs, some contortion.", "Sport-art hybrid (newly added).",
  [("Rhythmic Gymnastics", 8), ("Dance", 5), ("Choreography", 4), ("Contortion", 3)], "")
P("E09_ex_ballet", "E", "Ex-ballet dancer in an office job", "Trained ballet through school, later contemporary; still dances for fun.", "Long training, no current profession.",
  [("Dance", 6), ("Choreography", 2)], "")
P("E10_hip_hop_head", "E", "Hip-hop culture participant", "Breaks, beatboxes, tags walls, freestyles.", "Hip-hop's four-element cluster spans several categories.",
  [("Dance", 8), ("Beatboxing", 3), ("DJing", 2), ("Graffiti & Street Art", 3), ("Freestyle & Battle Rap", 3)], "")
P("E11_jazz_vocalist", "E", "Jazz vocalist who scats", "Sings jazz, improvises vocally, writes some songs, plays piano a bit.", "Newly added Scat Singing item.",
  [("Scat Singing", 6), ("Singing", 8), ("Musical Improvisation", 6), ("Songwriting", 3), ("Playing an Instrument", 4)], "")
P("E12_classical_indian_dancer", "E", "Classical Indian dancer", "Trains in a classical Indian dance tradition; sings; choreographs; has studied Kathakali.", "Newly added catalog items.",
  [("Dance", 8), ("Kathakali", 3), ("Singing", 3), ("Choreography", 3)], "")
P("E13_taziyeh_performer", "E", "Ta'ziyeh community performer", "Performs in a community Ta'ziyeh during Muharram; acts and chants.", "Rare, specific ritual-theatre practice (newly added).",
  [("Ta'ziyeh", 5), ("Acting", 4), ("Spoken Word & Rap", 1, "chanted recitation")], "")

# ============================================================================================ F. edge cases
P("F00_empty", "F", "No ratings", "Opens the Herbarium tab without rating anything.", "Zero-rating state: what the profile page shows before any input.", [], "")
P("F01_single_low", "F", "One rating, low", "A single tried-once item.", "Minimum input.", [("Photography", 1)], "")
P("F02_single_high", "F", "One rating, high", "A single professional-level item.", "Single maximum rating.", [("Woodworking", 10)], "")
P("F03_two_same_category", "F", "Two ratings, same category", "Drawing and painting at 5.", "Under the 4-rating threshold; one category.", [("Drawing", 5), ("Painting", 5)], "")
P("F04_three_three_categories", "F", "Three ratings, three categories", "Singing, cooking and drawing at 4.", "One below the 4-rating threshold, spread across categories.", [("Singing", 4), ("Cooking", 4), ("Drawing", 4)], "")
P("F05_four_same_category", "F", "Four ratings, all one category", "Four Visual Arts items at 5.", "Exactly at the 4-rating threshold, single category (hhi = 1).",
  [("Drawing", 5), ("Painting", 5), ("Illustration", 5), ("Printmaking", 5)], "")
P("F06_four_four_categories", "F", "Four ratings, four categories", "Singing, cooking, drawing, woodworking at 5.", "Exactly at the 4-rating threshold, spread across categories.",
  [("Singing", 5), ("Cooking", 5), ("Drawing", 5), ("Woodworking", 5)], "")
P("F07_one_category_deep", "F", "Twelve craft items in one category", "Twelve Craft & Sculpture items at mixed levels.", "Single-category depth (hhi = 1) with enough ratings to be past the early threshold.",
  [("Ceramics & Pottery", 8), ("Sculpture", 6), ("Glassblowing", 4), ("Jewelry Making", 5), ("Weaving", 3), ("Woodworking", 6), ("Bookbinding", 4), ("Leatherworking", 3),
   ("Blacksmithing", 3), ("Silversmithing", 4), ("Stone Carving", 5), ("Origami", 2)], "")
P("F08_one_per_category", "F", "One item in each of the 11 categories", "One item per category, all at 5.", "Maximum breadth: equal weight over every category.",
  [("Poetry", 5), ("Painting", 5), ("Ceramics & Pottery", 5), ("Singing", 5), ("Acting", 5), ("Independent Filmmaking", 5), ("Video Game Design", 5), ("Product Design", 5),
   ("Cooking", 5), ("Architecture", 5), ("Zine Making", 5)], "")
P("F09_all_at_1", "F", "Entire catalog rated 1", "Every art form rated 1.", "Full-catalog minimum; also exercises the largest rendering load.", "ALL", all_value=1)
P("F10_all_at_5", "F", "Entire catalog rated 5", "Every art form rated 5.", "Full-catalog midpoint.", "ALL", all_value=5)
P("F11_all_at_10", "F", "Entire catalog rated 10", "Every art form rated 10.", "Full-catalog maximum.", "ALL", all_value=10)
P("F12_all_random", "F", "Entire catalog, random ratings 1-10", "Every art form rated with a seeded random 1-10.", "Full catalog with no structure (seed 20260928).", "ALL", all_random_seed=20260928)
_SAME15 = ["Drawing", "Singing", "Cooking", "Woodworking", "Acting", "Video Editing", "Poetry", "Photography", "Ceramics & Pottery", "Playing an Instrument",
           "Graphic Design", "Landscape Design", "Dance", "Baking & Pastry", "Video Game Design"]
P("F13_same15_at_1", "F", "Same fifteen items, all rated 1", "Fifteen items across categories, each rated 1.", "Rating-level comparison set (1 / 5 / 10 on identical items).", [(n, 1) for n in _SAME15], "")
P("F14_same15_at_5", "F", "Same fifteen items, all rated 5", "The same fifteen items, each rated 5.", "Rating-level comparison set.", [(n, 5) for n in _SAME15], "")
P("F15_same15_at_10", "F", "Same fifteen items, all rated 10", "The same fifteen items, each rated 10.", "Rating-level comparison set.", [(n, 10) for n in _SAME15], "")
P("F16_polarised", "F", "Performance at 9, craft at 1", "Five performance items at 9 and five craft items at 1.", "Strong within-profile contrast in rating level.",
  [("Acting", 9), ("Dance", 9), ("Improv Theater", 9), ("Musical Theater", 9), ("Stand-Up Comedy", 9), ("Woodworking", 1), ("Ceramics & Pottery", 1), ("Sewing & Tailoring", 1), ("Weaving", 1), ("Jewelry Making", 1)], "")
P("F17_precisionist", "F", "Solo, planned, literal craft", "Watchmaking, bookbinding, scientific illustration, calligraphy, silversmithing, architecture, tailoring, marquetry.",
  "Expected to sit at the planned / solo / literal / controlled end of the axes.",
  [("Horology", 7), ("Bookbinding", 6), ("Botanical & Scientific Illustration", 6), ("Calligraphy", 6), ("Silversmithing", 5), ("Architecture", 5), ("Sewing & Tailoring", 5), ("Marquetry", 4)], "")
P("F18_improviser", "F", "Collaborative, improvised, interpretive performance", "Improv, clowning, flash mobs, social practice, commedia, fire, guerrilla art.",
  "Expected to sit at the improvised / collaborative / open / chance-led end of the axes.",
  [("Improv Theater", 8), ("Musical Improvisation", 7), ("Clowning", 6), ("Flash Mob Choreography", 4), ("Social Practice Art", 4), ("Commedia dell'Arte", 4), ("Fire Performance & Flow Arts", 4), ("Guerrilla Art", 3)], "")
P("F19_chance_solo", "F", "Solo chance-driven making", "Glitch art, generative art, marbling, resin, dyeing, blackout poetry, found objects, ceramics.",
  "Chance-led and solo.", [("Glitch Art", 7), ("Generative Art", 6), ("Paper Marbling", 5), ("Resin Art", 5), ("Textile Dyeing", 5), ("Blackout Poetry", 4), ("Found Object Art", 4), ("Ceramics & Pottery", 4)], "")
P("F20_ensemble_precision", "F", "Collaborative, controlled ensemble work", "Conducting, directing, ballroom, artistic swimming, rhythmic gymnastics, arranging, choreography, skating.",
  "Collaborative and controlled.", [("Conducting", 7), ("Directing Theater", 6), ("Dance", 6), ("Artistic Swimming", 6), ("Rhythmic Gymnastics", 5), ("Music Arranging & Orchestration", 5), ("Choreography", 5), ("Figure Skating & Ice Dance", 4)], "")
P("F21_domain_sound", "F", "Domain-pure: sound", "Composition, instrument, sound design, field recording, mixing.", "One of seven single-domain profiles (Sound).",
  [("Music Composition", 6), ("Playing an Instrument", 6), ("Sound Design", 5), ("Field Recording & Sound Maps", 4), ("Mixing & Mastering", 4)], "")
P("F22_domain_language", "F", "Domain-pure: language", "Fiction, poetry, speeches, interactive fiction, translation, invented languages.", "Single-domain profile (Language).",
  [("Fiction Writing", 6), ("Poetry", 5), ("Speechwriting", 4), ("Interactive Fiction", 4), ("Literary Translation", 4), ("Invented Languages", 3)], "")
P("F23_domain_visual", "F", "Domain-pure: the visual", "Painting, photography, graphic design, illustration, grading, collage.", "Single-domain profile (Visual).",
  [("Painting", 6), ("Photography", 5), ("Graphic Design", 5), ("Illustration", 5), ("Color Grading", 4), ("Collage", 4)], "")
P("F24_domain_movement", "F", "Domain-pure: movement", "Dance, parkour, acrobatics, choreography, capoeira, contemporary dance.", "Single-domain profile (Movement).",
  [("Dance", 6), ("Parkour & Freerunning", 5), ("Acrobatics & Tumbling", 5), ("Choreography", 5), ("Capoeira", 4)], "")
P("F25_domain_food_scent", "F", "Domain-pure: food and scent", "Cooking, perfumery, baking, brewing, fermenting, chocolate.", "Single-domain profile (Food and scent).",
  [("Cooking", 6), ("Perfumery", 5), ("Baking & Pastry", 5), ("Brewing, Wine & Spirits", 4), ("Fermentation & Pickling", 4), ("Chocolate Making & Confectionery", 3)], "")
P("F26_domain_space", "F", "Domain-pure: space", "Architecture, interiors, landscape, set design, furniture, installation.", "Single-domain profile (Space).",
  [("Architecture", 6), ("Interior Design", 5), ("Landscape Design", 5), ("Production & Set Design", 4), ("Furniture Design", 4), ("Installation Art", 3)], "")
P("F27_domain_nature", "F", "Domain-pure: nature", "Beekeeping, bonsai, aquascaping, terrariums, espalier, floral design, animal training.", "Single-domain profile (Nature).",
  [("Beekeeping", 5), ("Bonsai", 5), ("Aquascaping", 5), ("Terrarium & Vivarium Design", 4), ("Espalier", 3), ("Floral Design", 4), ("Animal Training & Handling", 3)], "")
P("F28_two_domains", "F", "Two domains together: sound and movement", "Singing, dance, composition, choreography, musical theatre.", "Intended to produce two leans at once.",
  [("Singing", 6), ("Dance", 6), ("Music Composition", 5), ("Choreography", 5), ("Musical Theater", 5)], "")
P("F29_breadth_cutoff_above", "F", "Breadth cutoff: just above 0.4", "Visual 11 / Music 5 / Food 4 (weights 55% / 25% / 20%, concentration 0.405).",
  "Sits just on the focused side of the 0.4 concentration cutoff.", [("Painting", 6), ("Drawing", 5), ("Singing", 5), ("Cooking", 4)], "")
P("F30_breadth_cutoff_below", "F", "Breadth cutoff: just below 0.4", "Visual 10 / Music 5 / Food 5 (50% / 25% / 25%, concentration 0.375).",
  "One rating point away from F29; sits just on the wide side of the cutoff.", [("Painting", 5), ("Drawing", 5), ("Singing", 5), ("Cooking", 5)], "")
P("F31_category_tie", "F", "Two categories tied for the color", "Painting 5 and singing 5.", "Equal category weight: which hue is chosen.", [("Painting", 5), ("Singing", 5)], "")
P("F32_dominant_one_rest_light", "F", "One 10 and fourteen 1s", "Drawing 10 plus fourteen other items at 1.", "One rating carries most of the weight.",
  [("Drawing", 10)] + [(n, 1) for n in _SAME15 if n != "Drawing"], "")
_EIGHT = ["Drawing", "Singing", "Cooking", "Woodworking", "Acting", "Photography", "Ceramics & Pottery", "Poetry"]
P("F33_eight_descending", "F", "Same eight items, ratings 8 down to 1", "Eight items rated 8,7,6,5,4,3,2,1 in this order.", "Rating-assignment comparison (paired with F34).",
  [(n, v) for n, v in zip(_EIGHT, [8, 7, 6, 5, 4, 3, 2, 1])], "")
P("F34_eight_ascending", "F", "Same eight items, ratings reversed", "The same eight items with the ratings reversed (1 up to 8).", "Rating-assignment comparison (paired with F33).",
  [(n, v) for n, v in zip(_EIGHT, [1, 2, 3, 4, 5, 6, 7, 8])], "")
P("F35_new_items_only", "F", "Only the 32 newest catalog items, all 5", "All 32 items added in the latest catalog expansion, each rated 5.", "Exercises only the new entries.",
  [(n, 5) for n in ["Dance", "Flamenco",
                    "Mesoamerican Ritual Dance", "Danza de los Voladores", "Capoeira", "Artistic Swimming", "Artistic Gymnastics", "Rhythmic Gymnastics", "Figure Skating & Ice Dance",
                    "Scat Singing", "Kabuki", "Noh", "Chinese Opera", "Kathakali", "Butoh", "Commedia dell'Arte", "Ta'ziyeh", "Totem Pole & Ceremonial Carving", "Ritual Mask Making", "Sacred & Ritual Sculpture"]], "")
P("F36_all_dance_cluster", "F", "Every dance item at 5", "Nineteen dance items, each rated 5.", "Dense-neighborhood case named in the app's calibration note.",
  [(n, 5) for n in ["Dance", "Choreography", "Flamenco", "Chinese Opera", "Noh", "Kabuki", "Butoh", "Kathakali",
                    "Ta'ziyeh", "Mesoamerican Ritual Dance", "Danza de los Voladores", "Capoeira"]], "")
P("F37_single_rare_item", "F", "One rare item at 9", "Butoh only.", "Single rating on a low-neighbor-count item.", [("Butoh", 9)], "")
P("F38_conflicting_signals", "F", "Opposing poles in one profile", "Precise solitary crafts and loose collaborative improv, each held at 6.", "Contradictory axis signals inside one person.",
  [("Horology", 6), ("Bookbinding", 6), ("Botanical & Scientific Illustration", 6), ("Improv Theater", 6), ("Clowning", 6), ("Flash Mob Choreography", 6)], "")

# ============================================================================================ G. setting variants
_A1 = [r for r in PROFILES if r["key"] == "A01_singer_multi_instrument"][0]
for r in (0.0, 0.25, 0.75, 1.0):
    P(f"G0{int(r*4)+1}_A01_reach_{r}", "G", f"A01 with reach setting {r}", _A1["who"], f"Same ratings as A01; only 'how far ratings reach' changed to {r} (default 0.5).", _A1["ratings"], _A1["mapping"], discount=r)
for i in (2, 3, 4):
    P(f"G0{5+i-2}_A01_seed_{i}", "G", f"A01 with plant seed {i}", _A1["who"], "Same ratings as A01; only the per-person plant seed changed.", _A1["ratings"], _A1["mapping"])
P("G08_name_html", "G", "Exporter name with HTML characters", "A01 ratings; name is <b>O'Brien</b> & Sons.", "Escaping of a typed name in the page title.", _A1["ratings"], "", name="<b>O'Brien</b> & Sons")
P("G09_name_long", "G", "Very long exporter name", "A01 ratings; a 120-character name.", "Layout of a long title.", _A1["ratings"], "", name=("Maximiliano Alejandro de la Cruz-Hernández y Villaseñor " * 2)[:120])
P("G10_name_0_o", "G", "Exporter name '0_o'", "A01 ratings; the name a tester actually used.", "Short name with punctuation.", _A1["ratings"], "", name="0_o")
P("G11_name_unicode", "G", "Exporter name with accents and emoji", "A01 ratings; name Zoë 🌸 Müller-Łukasiewicz.", "Unicode in the title.", _A1["ratings"], "", name="Zoë 🌸 Müller-Łukasiewicz")

# ============================================================================================ H. the 2026 catalog expansion
# Group H exists because the catalog grew from 274 to 306 forms and 11 to 12 categories when Sport &
# Martial Arts was created. Before this group not one of the 32 new forms was rated by any profile, so
# the whole new tier was untested. These rate the new forms in realistic combinations, and the straddlers
# deliberately span the Performance/Sport boundary to pin down how the migration behaves.

P("H01_skateboarder", "H", "Skateboarder, part-time", "Rides a skateboard most days, learned to drop in as a kid, watches a lot of skate video. Does not build boards; buys them.",
  "Skateboarding is one of the 12 new Sport & Martial Arts forms. A single-domain person in a brand new category: checks the hue, the HHI and the solo/collaborative read for a sport usually done alone.",
  [("Skateboarding", 7), ("Drawing", 3, "sketching tricks"), ("Photography", 4, "phone filming at the park"), ("Music Production", 3, "a practice playlist")], "")

P("H02_martial_arts_student", "H", "Karate student, three years", "Trains karate twice a week, has a yellow belt, drills kata alone and sparses with the class. Nothing else creative in particular.",
  "Covers Martial Arts Forms and Striking Arts, the two martial-arts entries added together. A focused, planned, collaborative person: the opposite pole from the Cuscuta-heavy middle of the distribution.",
  [("Martial Arts Forms", 6, "kata and taolu"), ("Striking Arts", 5, "the same karate, scored separately from the forms"), ("Dance", 1, "no dance at all, the only other movement he does")], "Karate appears twice in the catalog (forms vs sparring) and is rated as both, which is how a real person experiences it.")

P("H02b_grappling_and_striking", "H", "BJJ blue belt who also boxes", "Wrestles in BJJ twice a week, took boxing classes for a few years. Very sporty, very physical, no art practice at all.",
  "Grappling plus Striking and no creative category anywhere. The purest Sport & Martial Arts profile: what does the app do when every rating is a sport?",
  [("Grappling Arts", 7), ("Striking Arts", 4), ("Martial Arts Forms", 3), ("Acrobatics & Tumbling", 4, "rollouts and conditioning")], "")

P("H03_fencer", "H", "HEMA fencer", "Practises historical European martial arts from a club, drills longsword and rapier forms, sparses, occasionally does stage combat.",
  "Fencing & HEMA is the entry the catalog-gap review added on the grounds that HEMA reconstructs swordsmanship from treatises. Planned (a form is drilled), collaborative (a partner is required), with a craft crossover via stage combat.",
  [("Fencing & HEMA", 7), ("Stage Combat", 4, "the theatrical side"), ("Martial Arts Forms", 5, "weapon forms"), ("Bladesmithing & Knifemaking", 2, "no forging, but the same materials question")], "")

P("H04_prop_maker", "H", "Costume and prop maker for a theatre company", "Builds props and armour for a small theatre company: wood, foam, resin, some leather. Sews a lot. A making job disguised as a theatre job.",
  "Prop & Armor Making was one of the six 'make the thing behind the performance' gaps filled by the update. Straddles Craft & Sculpture and Performance & Movement, exactly the seam the review worried about.",
  [("Prop & Armor Making", 7), ("Sewing & Tailoring", 6), ("Woodworking", 5), ("Ceramics & Pottery", 3, "moulds and casting"),
   ("Sculpture", 4), ("Set Design", 5), ("Costume Design", 5), ("Stage Combat", 4, "wears what he builds")], "")

P("H05_bike_builder", "H", "Custom bicycle builder", "Builds a handful of steel frames a year in a home workshop: welding, finishing, geometry. Rides the results and restores old tools.",
  "Custom Bicycle & Motorcycle Building plus Transportation & Vehicle Design, the two vehicle entries the review added. Tests the Design category from a maker's side rather than a drawing-board side.",
  [("Custom Bicycle & Motorcycle Building", 8), ("Transportation & Vehicle Design", 5, "frame geometry is design work"),
   ("Blacksmithing", 4, "TIG and brazing at the bench, not forge work"), ("Woodworking", 4), ("Photography", 3, "documents the builds")], "")

P("H06_pcb_hobbyist", "H", "PCB designer for a small studio", "Designs circuit boards and firmware for clients, hand-solders, keeps a bench at home. Learned electronics as a teenager and does not think of it as art.",
  "Creative Electronics & PCB Design, added in the review's tech-arts section. A technical person who would not self-describe as creative: checks the app does not punish low art engagement.",
  [("Creative Electronics & PCB Design", 8), ("Creative Robotics & Animatronics", 5), ("Digital Fabrication", 4, "3D printed enclosures"),
   ("3D Modeling & Rendering", 5, "enclosure CAD"), ("Brick Art (LEGO & Construction Toys)", 3, "older kits and models")], "")

P("H07_gardener", "H", "Serious allotment gardener", "Twenty years of an allotment, seed saving, a small greenhouse, a lot of reading about soil. Cooks from what grows. Draws the layout in a notebook.",
  "Gardening & Plant Cultivation was added as a 'missing basic'. The old catalog had horticulture-adjacent items but no gardening itself, so this profile is largely new behaviour against a new form.",
  [("Gardening & Plant Cultivation", 8), ("Cooking", 7), ("Fermentation & Pickling", 5), ("Drawing", 3, "plot plans"),
   ("Woodworking", 4, "raised beds and a shed"), ("Photography", 4, "the plot through the year")], "")

P("H08_puppet_maker", "H", "Puppet maker who also performs", "Makes rod and hand puppets for children's television and performs a few of them. Sews, carves foam, paints.",
  "Puppet & Doll Making was the review's first 'make the thing' gap. This person both makes and performs, so they straddle Craft and Performance: a clean test of whether the app rewards a maker-performer or splits them in two.",
  [("Puppet & Doll Making", 8), ("Sewing & Tailoring", 6), ("Sculpture", 5, "carving and armature"), ("Painting", 4),
   ("Acting", 5, "performing the puppets"), ("Voice Acting", 4), ("Playwriting & Screenwriting", 3, "scripts for the show")], "")

P("H09_worldbuilder", "H", "Tabletop worldbuilder", "Runs a long campaign, writes the setting's own histories and languages between sessions, makes maps, plays an instrument badly.",
  "Worldbuilding & Lore Design plus Cartography & Map Design, both added by the review. A writing person whose writing is mostly setting-building: checks the Writing & Language lean and the new Design forms.",
  [("Worldbuilding & Lore Design", 8), ("Cartography & Map Design", 6, "the campaign maps"), ("Fiction Writing", 5),
   ("Invented Languages", 5, "conlangs for the setting"), ("Playing an Instrument", 2), ("Drawing", 4, "the maps, by hand")], "")

P("H10_roller_skater", "H", "Roller skater, adult league", "Plays in a local roller league, skates for fitness, goes to the rink weekly. No other art form.",
  "Roller & Inline Skating is one of the 12 new sport forms. A second single-sport profile alongside H01, to check two different new sports do not collapse onto the same result by accident.",
  [("Roller & Inline Skating", 6), ("Skateboarding", 2, "tried it, prefers inline"), ("Acrobatics & Tumbling", 4, "falls and balance work")], "")

P("H11_surfer", "H", "Surfer, occasional", "Surfing for a few years, weekend trips, photographs the water a lot. Reads about boards but does not build them.",
  "Surfing is a new sport form and one of the few where the community values style over score. Paired with H01 as the closest comparison the app has: do two board sports read as the same kind of person?",
  [("Surfing", 6), ("Photography", 5, "always a phone in the water"), ("Astrophotography & Scientific Imaging", 2), ("Drawing", 2), ("Tai Chi & Qigong", 3, "stretching and breath work between sessions")], "")

P("H12_tech_fabricator", "H", "3D printer and laser cutter tinkerer", "Prints replacement parts, laser-cuts boxes, has made a dozen things that did not need making. Comfortable with CAD, weak on fine art.",
  "Digital Fabrication is a new Digital & Interactive form. Tests how the app handles a maker who is technical rather than artistic, alongside H05 and H06.",
  [("Digital Fabrication", 8), ("Creative Electronics & PCB Design", 4, "drives the printer, fixes the board"),
   ("Miniatures & Dioramas", 5), ("Woodworking", 4, "the laser does the cutting"), ("3D Modeling & Rendering", 5, "slicing and parametric CAD")], "")

P("H13_escape_room_designer", "H", "Escape-room designer", "Writes puzzles, props and story for a commercial escape room and runs the games on weekends.",
  "Escape Room & Immersive Experience Design and Mechanical Puzzle & Puzzle Box Making, both added by the review. A puzzle person whose puzzles are physical and installed in a room rather than printed on paper.",
  [("Escape Room & Immersive Experience Design", 8), ("Mechanical Puzzle & Puzzle Box Making", 7),
   ("Puzzle & Crossword Construction", 5), ("Prop & Armor Making", 4, "the room's props"), ("Copywriting", 4, "the narrative spine"),
   ("Creative Electronics & PCB Design", 3, "sensor triggers")], "")

P("H14_astrophotographer", "H", "Astrophotographer with a small scope", "A few years of deep-sky imaging on a small tracker, a lot of processing, prints occasionally.",
  "Astrophotography & Scientific Imaging is a new Visual Arts form and the only new entry in Visual Arts rather than a making or tech category. The only profile that rates it above 2.",
  [("Astrophotography & Scientific Imaging", 7), ("Photography", 6), ("Digital Painting", 3, "processing, sort of"), ("Data Visualization", 4, "stretching and calibration curves")], "")

P("H15_pole_dancer", "H", "Pole and lap dance regular", "Trains pole twice a week, performs at a local night, teaches a little. Body-oriented, in Performance & Movement.",
  "Pole Dance & Pole Sport was one of the less obvious additions the review included. A Performance & Movement person in a form the app previously had nothing for.",
  [("Pole Dance & Pole Sport", 6), ("Dance", 5), ("Acrobatics & Tumbling", 5, "inversions and strength")], "")

# --- straddlers: deliberately span the Performance & Movement -> Sport & Martial Arts migration ---
P("H16_dancer_who_skates", "H", "Straddler: dancer who also roller-skates",
  "A professional contemporary dancer who roller-skates for fun at weekends. Strong in Performance, casual in Sport.",
  "The migration test. This person's two activities now sit in DIFFERENT categories where before the update they sat in one. Checks whether a genuine two-domain person reads as wide, and whether the new category is treated as a real second pole rather than a rounding error.",
  [("Dance", 8), ("Choreography", 6), ("Flamenco", 5), ("Roller & Inline Skating", 3), ("Acrobatics & Tumbling", 4)],
  "The point: roller skating was 'Performance & Movement' before the update and is 'Sport & Martial Arts' now, so this profile's category mix changed without the person changing.")

P("H17_gymnast_who_does_martial_arts", "H", "Straddler: former gymnast now takes martial arts",
  "Rhythmic gymnast until her teens, now does aikido twice a week. Movement-heavy in both, but the two are now different categories.",
  "Second migration straddler, and the one behind the E-group changes. Rhythmic Gymnastics moved to Sport & Martial Arts, so an ex-gymnast with any other movement practice is now automatically two-domain.",
  [("Rhythmic Gymnastics", 7, "as a teenager"), ("Martial Arts Forms", 4), ("Tai Chi & Qigong", 3), ("Dance", 3, "a little as an adult")], "")

P("H18_capoeira_who_fights", "H", "Straddler: capoeira plus a striking art",
  "Capoeira for six years, recently started muay Thai. The profile most affected by the update, pinned here explicitly.",
  "E04_capoeirista is the one real-person profile whose genus changed from Mimosa to Taraxacum when Capoeira moved category. Reproduced with a second sport added, to show the new result is a coherent 'wide' read rather than an accident.",
  [("Capoeira", 8), ("Striking Arts", 4, "muay Thai, new"), ("Martial Arts Forms", 4), ("Playing an Instrument", 5), ("Singing", 5), ("Dance", 3)], "")

# --- boundary probes aimed specifically at the new category structure ---
P("H19_hhi_at_cutoff_with_sport", "H", "HHI probe: one sport plus a little else",
  "Mostly a single new sport with a little elsewhere, tuned to sit just on the focused side of the 0.4 concentration cutoff.",
  "Because the category set changed, the HHI at which a profile reads as 'focused' has moved for anyone touching sport. A deliberate boundary probe at the same 0.4 line the F-group probes, in the new category structure.",
  [("Fencing & HEMA", 6), ("Martial Arts Forms", 5), ("Tai Chi & Qigong", 4, "the only other thing he does"), ("Drawing", 3), ("Cooking", 2)], "")

P("H20_hhi_below_with_sport", "H", "HHI probe: two sports, clearly wide",
  "Two sports and a little making, tuned to sit clearly on the wide side of the cutoff.",
  "The paired control for H19, one notch further from the line, to confirm the cutoff is still where it was and has not been destabilised by the new category.",
  [("Skateboarding", 6), ("Surfing", 5), ("Drawing", 4), ("Photography", 3), ("Cooking", 2), ("Playing an Instrument", 2)], "")

_SPORT18 = ["Fencing & HEMA", "Skateboarding", "Roller & Inline Skating", "BMX Freestyle & Bike Trials", "Motorcycle Stunt Riding & Freestyle Motocross",
            "Martial Arts Forms (Kata, Taolu & Poomsae)", "Tai Chi & Qigong", "Grappling Arts (Judo, Jiu-Jitsu & Wrestling)", "Striking Arts (Karate, Taekwondo, Muay Thai & Boxing)",
            "Archery (Target & Kyudo)", "Freestyle Snowboarding & Skiing", "Surfing", "Capoeira", "Parkour & Freerunning", "Acrobatics & Tumbling",
            "Artistic Gymnastics", "Rhythmic Gymnastics", "Figure Skating & Ice Dance"]
_NEW32 = ["Fencing & HEMA", "Skateboarding", "Roller & Inline Skating", "BMX Freestyle & Bike Trials", "Motorcycle Stunt Riding & Freestyle Motocross",
          "Martial Arts Forms (Kata, Taolu & Poomsae)", "Tai Chi & Qigong", "Grappling Arts (Judo, Jiu-Jitsu & Wrestling)", "Striking Arts (Karate, Taekwondo, Muay Thai & Boxing)",
          "Archery (Target & Kyudo)", "Freestyle Snowboarding & Skiing", "Surfing", "Puppet & Doll Making", "Skateboard & Surfboard Building",
          "Custom Bicycle & Motorcycle Building", "Prop & Armor Making", "Papermaking (Handmade Paper)", "Lapidary & Gem Cutting", "Bladesmithing & Knifemaking",
          "Mechanical Puzzle & Puzzle Box Making", "Transportation & Vehicle Design", "Cartography & Map Design", "Creative Electronics & PCB Design",
          "Digital Fabrication (3D Printing, Laser Cutting & CNC)", "Creative Robotics & Animatronics", "Escape Room & Immersive Experience Design",
          "Astrophotography & Scientific Imaging", "Pole Dance & Pole Sport", "Cardistry & Card Flourishes", "Oral Storytelling",
          "Gardening & Plant Cultivation", "Worldbuilding & Lore Design"]

P("H21_all_new_forms_at_5", "H", "Only the newest 32 additions, all 5", "Every form added in the 2026 expansion, each rated 5.",
  "The F35 test applied to the new tier. F35 rates the previous 32 additions; this rates the current 32, so the dense-neighbourhood and all-same-value behaviour of the newest cluster is exercised on its own.",
  [(n, 5) for n in _NEW32], "")

P("H22_sport_only_all", "H", "Every one of the 18 Sport & Martial Arts forms, all 5",
  "The entire new category rated 5, and nothing else rated at all.",
  "Single-category, single-domain probe in the new category. The closest existing analogues are D03/D04 (only cooks / only phone photos): a one-category person should read as maximally focused, and this checks the new category behaves that way and that a category being merely new does not trip the 0.4 cutoff.",
  [(n, 5) for n in _SPORT18], "")

# seeds used by the G02-G04 style seed variants are set by the runner: seed = "t-" + key, so keys differ -> seeds differ.

# ============================================================================================ evolution traces
# Ratings are added in the listed order; the runner records the result after each addition.
TRACE_PROFILES = ["A01_singer_multi_instrument", "A02_cgi_artist_music_hobby", "C01_polymath", "C02_serial_starter", "E02_danza_azteca"]
