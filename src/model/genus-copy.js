// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Teo Monroy

/* THE WORDS OF THE READING. Everything the Herbarium says about a person that is prose rather than logic: the sixteen
genus descriptions, the "approach to chance" paragraphs, the tribe names and their field notes (thrives on, wilts when,
shares ground with), the fewer-than-enough-ratings variants, and the glossary.
   Pure data, loaded before model/classification.js, which picks from these tables and does the arithmetic.
   To change what a genus SAYS, edit here. To change who GETS a genus, edit classification.js.
   See docs/model.md. */

// The 16 core types: Breadth x Process x Sociability x Form, keyed "BPSF" as 0/1 digits
// (0 = low pole, 1 = high pole). Each is one real plant/organism genus chosen to echo the
// combination, and a paragraph describing that combination.
const GENUS_TABLE = {
  "0000": {
    name: "Selaginella",
    text: "You work with a small set of things, mostly alone, by feel rather than by plan, and you take the material as it is instead of reading extra meaning into it. Skill comes from repetition and adjustment on the spot: you try it, see what happened, and change the next attempt. The catch is that this is hard to explain from outside. There is no plan or statement to point to, only the results.",
  },
  "0001": {
    name: "Cuscuta",
    text: "Your best work often begins from something already there \u2014 an existing structure, a piece someone else made, a piece of writing, a piece of music \u2014 and you keep working it, alone and without a plan, until it says something it was not built to say. You stay with a small set of these sources rather than roaming, and by the time you are done the original can be hard to recognize. A side effect worth knowing: because the starting point is often borrowed, it can be hard to point at what is yours in the result. Often the answer is the bending itself.",
  },
  "0010": {
    name: "Rafflesia",
    text: "You keep a small, plainly-done set of things in reserve and bring them out when someone is there to see them. Nothing is planned; it happens on contact with the room, and it is direct rather than layered. The long gaps between appearances are not a lull, they are how you make sure each one is worth watching. Others may call that inconsistent; selective is closer. With nobody around there is little pull to do the thing at all, so putting even a small audience or a partner in place is what gets you moving.",
  },
  "0011": {
    name: "Mimosa",
    text: "You work best when something is reading you back. You use a small, familiar set of things and adjust them as you go, and the result is never quite the same twice, which is much of the appeal. People often find your company restorative, and this is much of why: you are watching, timing and meeting the room where it is. Played entirely on your own terms, the same work is still good, but it loses something you cannot quite name, and you may find yourself arranging for a witness sooner or later.",
  },
  "0100": {
    name: "Lithops",
    text: "You go deep on a small handful of things, alone, following a plan only you know, and you take the material fairly literally rather than looking for extra meaning in it. Being overlooked costs you very little: quiet, steady, mostly invisible progress is the job, not a consolation prize. You are usually more intense about the work than you look. Because none of it is performed, people who do not already know you often underestimate how much has gone into it, and you may need to say so out loud, since nobody will infer it.",
  },
  "0101": {
    name: "Pteris",
    text: "You return to the same handful of forms again and again, alone, with real patience and a plan behind each attempt, and you never read them the same way twice. Someone else would call this mastering a fixed thing; you would call it reopening a question. It is why the same old material keeps producing something new in your hands. The cost is that you rarely converge: with no settled reading to measure against, it can be hard for you, or anyone watching, to say when a piece is finished. A deadline set from outside works well here.",
  },
  "0110": {
    name: "Drosera",
    text: "You plan carefully and work the material fairly literally, but a piece is not complete until it happens in front of someone. An audience, a collaborator or a live moment is not decoration on top of the work; it is the step the planning was building toward. The flip side is that rehearsal and private drafts can feel unfinished however good they get, so put the audience on the calendar early instead of waiting until the work feels ready.",
  },
  "0111": {
    name: "Helianthus",
    text: "Real discipline goes into one or two practices, and everything you make faces outward: toward a group, an audience or a tradition you are in conversation with, which you read loosely enough to bend toward your own angle. Like a field of sunflowers you all lean toward the light, no two at quite the same angle. Cut off from that audience or tradition, the work can lose its point for you. Keeping at least one live connection is what keeps the discipline pointed at something.",
  },
  "1000": {
    name: "Physarum",
    text: "You cover a wide range, alone, with no plan going in, taking things mostly at face value. The method resembles the slime mold you are named for: spread out, find the shortest route to something workable, keep what is useful and move on. That is not scatter, it is efficiency across a large territory. Depth and range pull against each other in you, and which one wins depends on what the problem is. A written list of what you have tried tends to make the range visible.",
  },
  "1001": {
    name: "Lemna",
    text: "You take things up alone, with no fixed method, playing loosely with the form each time instead of settling on one version of it. Range is the point: each new form adds ground rather than being a stage on the way to something more polished. Like the duckweed you are named for, you spread across a whole surface at once. From outside it can look as if no single attempt gets your full attention, when you are choosing range over depth. If you ever want depth, pick one attempt and keep it out of the rotation.",
  },
  "1010": {
    name: "Armillaria",
    text: "Your range of practices is wide, but the thread connecting them is people rather than a method. You move between groups, projects and collaborators, and the network does as much of the work as anything you make inside it, much as a honey fungus is one organism spread across a whole forest floor. In the moment you are direct and improvised rather than mapped out. Take away the collaborators, the scene or the exchange and it gets harder to locate what you are trying to do, because for you the connections are close to the substance of the work, not support for it.",
  },
  "1011": {
    name: "Taraxacum",
    text: "You go wherever there is something to do, and you make almost any room, project or group feel like somewhere you already belonged. No format throws you: hand you an unfamiliar setup and within minutes you have bent your loose approach to fit it. The trade-off is follow-through. Nothing in how you work pulls you back once the novelty is spent, so what stays finished is usually what someone or something expects you to return to: a deadline, a person, a standing commitment.",
  },
  "1100": {
    name: "Lycopodium",
    text: "You run a wide range of practices in parallel, alone, each with real method and a hands-on, fairly literal style. You are not choosing a specialty; you are building competence slowly on many fronts, for long enough that the range itself becomes the specialty. Mid-process, from outside, this can look unfocused or undecided, because the payoff shows only in hindsight and over longer stretches than most people judge by. Keeping a visible record of progress helps other people, and sometimes you, see the pattern earlier.",
  },
  "1101": {
    name: "Bambusa",
    text: "You build out a wide set of practices with discipline, alone, following one consistent internal logic that carries from one thing to the next. New material gets read loosely enough to be bent into that same underlying structure, so the throughline is the method itself more than whatever it is applied to at the moment. Bamboo is a fair comparison: many stalks, one root system. Collaborators may find it hard to tell whether you care about the thing in front of you or the system it is an instance of, and telling them which is the quickest fix.",
  },
  "1110": {
    name: "Passiflora",
    text: "Careful, deliberate growth across many practices and many collaborators at once: ambitious in scope, sociable in how you work, and direct about what each piece is for, even with several running in parallel. With that much in flight and that many people involved, something is always getting less attention than it deserves; the useful habit is to choose what that something is instead of leaving it to chance.",
  },
  "1111": {
    name: "Ficus",
    text: "You think in systems, and you build them from whatever is nearby. Given enough time, almost anything you touch, a hobby, a side project, someone else's half-finished idea, starts to look like a component of something larger you are constructing, usually without your deciding to expand. This is not scattered ambition; it is one long operation with many moving parts. Your system tends to absorb things more than it showcases them, so people sometimes struggle to tell where the original ends and your structure begins, which is either exactly the point or a fair question, depending on who is asking.",
  },
};

// Approach to chance: b3 (controlled/repeatable <-> chance-driven/emergent). `label` is what the
// page shows; `word` is only the key plant.js uses to style the plant's leaves and is
// never displayed.
const REGIME_LEVELS = {
  // These two are separate axes and the copy used to blur them. a1 is planned/improvised - whether
  // you arrive with a plan. b3 is controlled/chance-driven - whether a given piece ends up the same
  // way twice. They correlate at only r = +0.20 across a drawn population, and half the population
  // reads as improvised AND controlled at once, which is not a contradiction but was being written
  // as one: the genus paragraph said "no plan going in" and the regime said "you aim at the same
  // outcome on purpose" three lines later, both flatly. So `ordered` is now written about
  // repeatability once the piece is under way, which is what b3 actually measures, and it never
  // claims the plan existed first.
  ordered: {
    word: "ordinata",
    label: "Steers toward control",
    text: "Once a piece is under way you want it to land where you intended: the same brief produces the same result, and one you can repeat is worth more to you than one you got lucky with. Where the piece goes can be an accident; how it comes out is not. That is the distinction you actually work by: being able to do it again is the asset, and the happy surprise is the accident.",
  },
  adaptive: {
    word: "flexilis",
    label: "Moves between control and chance",
    text: "Some jobs get a plan and others get left alone to see what happens, and you pick per job rather than by habit. That reads less like a compromise than a judgment call: you size up what the work wants and give it that.",
  },
  emergent: {
    word: "aleatoria",
    label: "Leaves room for chance",
    text: "Accidents and unplanned turns are not corrected out of your process; they are often where the best part of the result comes from. Working this loosely is harder than it looks.",
  },
};

// Plain words shown on the page for each lean, and a longer gloss.
const TRIBE_PLAIN = {
  Reed: "sound",
  Vine: "language",
  Petal: "the visual",
  Tendril: "movement",
  Nectar: "food and scent",
  Trellis: "space",
  Root: "nature",
};

// The same leans as botanical epithets (invariant Latin adjectives), shown after "cf." in the name line. The plain
// words above are what the text beneath spells out, so the Latin is never left unexplained.
const TRIBE_EPITHET = {
  Reed: "sonans",
  Vine: "eloquens",
  Petal: "versicolor",
  Tendril: "mobilis",
  Nectar: "fragrans",
  Trellis: "spatialis",
  Root: "sylvestris",
};

const TRIBE_GLOSS = {
  Reed: "sound and pattern \u2014 rhythm, tone, the shape of something heard",
  Vine: "language and sequence \u2014 events read as a story with a shape",
  Petal: "the visual \u2014 composition, color, how things sit in a frame",
  Tendril: "the body in motion \u2014 thinking through doing, not before it",
  Nectar: "taste and scent \u2014 the sensory payoff of a thing, not just its use",
  Trellis: "space and structure \u2014 how a room or layout shapes what happens in it",
  Root: "living systems \u2014 growth and change tracked over seasons, not sessions",
};

// ---- Tribe layer: fun, identifiable extras that sit on top of the core genus paragraphs ----
//
// WRITING THE "thrives" / "wilts" PAIR. This took two passes and the first one was
// wrong, so the rule is written down here rather than left to judgement:
//
//   the WILT must not be the THRIVE's absence, its negation, or a harder instance
//   of it. It must name a strain a reader would not predict from the thrive row.
//
// Test it by reading the two rows as one sentence. "Thrives on quick cycles and
// lots of small wins" + "wilts when a piece needs weeks of careful finishing"
// says tempo twice and tells the reader nothing the first row did not. So does
// "thrives on an audience" against "wilts without one", or "room to spread" against
// "told to close it down". Nine of the sixteen were mirrors on the first pass and
// eleven on the second; five were right to begin with.
//
// The fix is always to move the wilt onto an axis the thrive never mentions: the
// Surface Spreaders no longer wilt on slowness, they wilt on being the one still
// holding a project nobody else wants, which is upkeep rather than tempo.
//
// SECOND RULE, learned the same way. These rows render as a bare label/value pair
// with nothing between them, so a pronoun has to resolve inside its own row. "You
// are the one still holding it a year later" had no antecedent anywhere - the
// thrive row above it says "a steady supply of new things to try", which names
// nothing you can hold. That is the same defect as the "Some pieces get a plan /
// It reads less like a compromise" pair fixed at the very start of this work, and
// it came straight back the moment these lines were rewritten. Name the thing.
//
// THIRD RULE, and the one that actually explains the last complaint. A row is a
// CONDITION, not a story beat. "You are the one STILL holding a project nobody
// else wants" is not just vague, it leans on a history the reader was never given:
// still assumes you put it down and came back, and a project assumes one. Same for
// "the project HAS OUTGROWN your memory of why you STARTED it", "say yes BEFORE
// you know whether you want it", "the one that mattered is the one you DROPPED".
// None of those things were ever shown to the reader. Each row has to be true on
// its own, now, naming everything it refers to.
// THIRD RULE, learned the same way. Two of the wide genera made claims about how MUCH the reader
// makes - "making a lot, quickly, is the point", "a dozen half-started projects", "the finished pile
// is bigger than it looks". A rating list records what and how well, never how much anyone made,
// so a person who rated twenty things and kept none of them past a 3 was told they were prolific
// and had a pile. The sentences are not deleted, because for someone with a real practice they are
// true and they are the good part. They are gated on keptEnough (5+ forms at 3 or above), and the
// thin version says the thing that IS supported: the ratings show a wide field of things tried and
// not many kept, which is a different and more useful thing to be told.
const GENUS_VOLUME = {
  "1001": {
    thinMore:
      "You have tried a lot of things and few have gone past a first try. That is a pattern, not a failure: the list is wide and mostly shallow so far, which leaves room to find the one worth the hours.",
    thinThrives: "a short list and the freedom to add to it",
    thinWilts: "you are asked which of these is the real one",
    thinGets:
      "Physarum, who gets through ten things at once and keeps what works; Taraxacum, for finding whatever water is nearest; Lycopodium, for the slow version where the range becomes the thing",
  },
  "1000": {
    thinMore:
      "You try a wide range of things and do not stay long with most of them. Not scatter, exactly \u2014 more that you have not yet found the one that holds your attention, and the ratings say the range is real while the depth is not there yet.",
    thinThrives: "a new problem with no commitment attached",
    thinWilts: "being asked to commit to one of these before you are ready",
    thinGets:
      "Lemna, who also ranges widely; Taraxacum, who turns up wherever there is something to do; Cuscuta, for a route neither of you has taken before",
  },
};

const GENUS_EXTRA = {
  "0000": {
    tribe: "The Quiet Hands",
    more: "You learn by doing and you are not much for announcing it. People see the result before they hear anything about the process, and if asked how you did it, the honest answer is usually that you kept adjusting until it worked. You tend to get better in unseen stretches, and the improvement shows up all at once.",
    thrives: "one clear brief and long quiet stretches",
    wilts: "you are asked to explain a plan you never made",
    gets: "Pteris, who works alone too but reopens finished work; Helianthus, for a night when both of you have to be seen; Physarum, for a problem that needs no plan from either of you",
  },
  // Cuscuta's wilt used to be "you have to explain where the work came from to people who care about
  // provenance", which is the thrive's own condition failing: you cannot push against a source if you
  // also have to account for where it came from. A wilt has to be a different situation, not the
  // thrive withheld. Rewritten as being asked to work inside someone else's structure on their terms,
  // which is a real cost of this way of working and is not the same thing as having no source.
  "0001": {
    tribe: "The Remixers",
    more: "Where other people's finished things are, you see a frame to climb. You tend to be the one with a shelf of other people's ideas half-rebuilt, and an eye for what a piece was secretly reaching for. Starting from nothing is rarely the hard part, because you so often start from something.",
    thrives: "a strong source to push against",
    wilts: "being asked to work inside someone else's structure, on their brief and to their rules",
    gets: "Pteris, for reopening the same old questions from a different angle; Armillaria, who gives your rebuilds somewhere to attach; Lithops, who will never ask you to explain the method",
  },
  "0010": {
    tribe: "The Rare Appearance",
    more: "You are the one people wait for. You turn up, do the thing plainly and well, and vanish again, which builds a reputation you did not plan and cannot always keep up. Whoever follows you tends to be loyal and slightly baffled, and you like it that way more than you admit.",
    thrives: "an audience with a date on it",
    wilts: "you are asked to show your working",
    gets: "Mimosa, who draws work out of a room of one; Drosera, for the date that turns a rarity into an event; Ficus, if what you make has to outlast the evening",
  },
  "0011": {
    tribe: "The Room-Readers",
    more: "You make a room livelier: you feel the mood before anyone else and shift the whole performance a few degrees to match. You are probably better on the night than in rehearsal, and may have stopped apologizing for that. What is easy to miss is that this is a reading skill before it is a performing one, and it does not switch off when you are alone.",
    thrives: "a live audience or a partner",
    wilts: "the piece leaves no room to adjust as you go",
    gets: "Rafflesia, who needs an audience as much as you do; Helianthus, for a stage with the sun on it; Drosera, who holds the plan steady while you read the room",
  },
  "0100": {
    tribe: "The Stone Garden",
    more: "From outside you look like nothing much, and most of the work happens on the inside. You are the friend who has been quietly getting good at the same craft for years, and the reveal is always more impressive than anyone guessed. You do not need it to be noticed; it helps that it eventually is.",
    thrives: "a private routine and one fixed craft",
    wilts: "you are asked to teach what you do",
    gets: "Selaginella, who leaves your progress unremarked; Bambusa, for a system neither of you has to explain; Lycopodium, grinding quietly on several fronts beside you",
  },
  "0101": {
    tribe: "The Perpetual Second Draft",
    more: "You reopen things other people consider closed. Your desk holds several works that are finished in the sense that you stopped and none in the sense that you are satisfied. This is the price of always seeing one more reading, and also the reason your old material never goes stale.",
    thrives: "old material and an outside deadline",
    wilts: "you are asked to defend one fixed reading of a piece",
    gets: "Cuscuta, for reviving old material; Selaginella, for the long quiet stretch a revision needs; Drosera, for a deadline neither of you set yourself",
  },
  "0110": {
    tribe: "The Sticky Planners",
    more: "You plan in private and land in public. Your preparation is thorough, and the fact that you rise to the occasion is what surprises people who only saw the spreadsheet. Collaborators seek you out because you are the one who actually read the brief, and probably annotated it.",
    thrives: "a date, a stage and a plan",
    wilts: "other people keep changing a plan you have already settled",
    gets: "Helianthus, who also turns outward when the work is ready; Physarum, for the part of the plan that keeps not working; Lycopodium, for the slow accumulation behind the deadline",
  },
  "0111": {
    tribe: "The Sun-Followers",
    more: "You are disciplined and public-facing, the kind of person who turns a craft into a community. You are usually the one explaining the thing to newcomers, and you are better at it because you argue with it yourself. You collect mentors, rivals and students, and the boundary between them is soft.",
    thrives: "a scene, a tradition or a regular audience",
    wilts: "you have to explain yourself to people already inside the tradition",
    gets: "Drosera, who keeps the dates you need; Armillaria, for the network that holds after everyone goes home; Taraxacum, who lands anywhere and makes the room bigger",
  },
  "1000": {
    tribe: "The Path-Finders",
    more: "You try everything once and keep what worked. To people who like a tidy answer that looks like drift; to anyone who has watched you solve something new in an afternoon it looks like a knack with no job title. You are the person friends call when the problem has no manual.",
    thrives: "new problems with low commitment",
    wilts: "you are asked what you are good at, and there is no single answer",
    gets: "Lemna, who also ranges widely; Cuscuta, for a route neither of you has taken before; Selaginella, for a long quiet stretch",
  },
  "1001": {
    tribe: "The Surface Spreaders",
    more: "You start easily and in many directions, each attempt with a good reason of its own. Being unafraid of starting is most of what trying new things takes, and you do it on your own terms, without waiting for a plan or for company.",
    thrives: "quick cycles and lots of small wins",
    wilts: "every attempt has to be presentable before the next one can start",
    gets: "Physarum, who gets through ten things at once and keeps what works; Drosera, for turning one of your attempts into a plan with a date on it; Taraxacum, for finding whatever water is nearest",
  },
  "1010": {
    tribe: "The Underground Network",
    more: "You are often the reason a scene exists. You may never be the name on the poster, but ask anyone in the room who introduced them to everyone else. Projects come and go; the web is the work, and it is worth more than any single thing that passed through it.",
    thrives: "collectives, festivals and open-door projects",
    wilts: "everyone already knows everyone and there is nobody left to introduce",
    gets: "Taraxacum, who turns up and connects two groups who had not met; Passiflora, for a crew big enough to need you; Lycopodium, for the patient work the network feeds on",
  },
  "1011": {
    tribe: "The Drifters Who Always Belong",
    more: "You seed yourself into every room and bloom there. You are the one asked to just help out because you will make it work, and you do, and it is fun, and three weeks later you are somewhere else with a new group who swear you have always been there.",
    thrives: "new rooms and new people",
    wilts: "nobody is expecting anything back from you",
    gets: "Armillaria, who keeps the network you seeded; Helianthus, who will find you a stage when the drift settles; Mimosa, who reads the room you have just walked into",
  },
  "1100": {
    tribe: "The Slow Accumulators",
    more: "You never announce a specialty and one day discover you have one anyway. You collect skills the way other people collect apps, the range is invisible for years, and then a project comes along that needs all of it and you turn out to be qualified.",
    thrives: "steady practice on several fronts",
    wilts: "everything you have is useful only to you, and you are the only one who knows that",
    gets: "Bambusa, who builds a system out of the same separate skills; Lithops, for a private routine that compounds quietly; Drosera, for turning the accumulation into something with a date",
  },
  "1101": {
    tribe: "The Root System",
    more: "You have one method and many faces. The work looks unrelated at a glance and is obviously one person's on a second look. Others describe you as a very consistent person doing surprisingly different things, and they are right on both counts.",
    thrives: "a personal framework you can keep extending",
    wilts: "you are asked to use your method on something it was not built for",
    gets: "Lycopodium, for the long slow build; Ficus, when your framework has to become a place other people stand; Pteris, for the version of it that is allowed to change",
  },
  "1110": {
    tribe: "The Ambitious Ensemble",
    more: "You organize complicated, beautiful things with lots of people and remember everyone's job. You tend to be the lead, the producer, the one people ring. The flowers are the showy part; the plant is a well-run machine, and you are the one who knows where every wire goes.",
    thrives: "big projects with a crew",
    wilts: "more than one thing is in flight and there is no time for the one that matters",
    gets: "Ficus, for an empire to run rather than a job to finish; Armillaria, for the network that outlives the crew; Mimosa, for reading the room when a big project turns tense",
  },
  "1111": {
    tribe: "The Banyan Builders",
    more: "Your projects grow aerial roots and become forests. You are the person with the system, the wiki, the web of linked ideas, and a private suspicion that everything can be joined up. It usually can, which is the most annoying part for everyone else.",
    thrives: "one ever-growing project with room to spread",
    wilts: "someone else controls one of the parts you depend on",
    gets: "Passiflora, for building at a scale you cannot hold alone; Armillaria, for the network running underneath what you assemble; Physarum, for reorganizing at speed without a plan",
  },
};

const REGIME_EXTRA = {
  ordered:
    "The repeat performance is a point of pride: the recipe that works every time, the take you can redo on demand. A surprise in the result feels like a leak. The risk is tuning a piece until it is safe and a little sleepy, so schedule one deliberately loose attempt.",
  adaptive:
    "You read the job before choosing a method, which suits an unpredictable brief. The risk is never quite committing to either approach, so decide early which way a given piece should go and hold to it.",
  emergent:
    "The accident is a collaborator. Happy mistakes are raw material, and you can tell in seconds which ones to keep. The risk is that people who need repeatability, clients and schedulers especially, find you hard to plan around.",
};

const TRIBE_READ = {
  Reed: "Sound-minded people hear structure before they see it: rhythm, repetition, how a room changes when something is played in it. You tend to describe things by how they would sound and to notice something is off before you can say why.",
  // These read as DISPOSITION - "everything you do has a beginning, a middle and an argument", "you
  // rarely trust a thing until it looks right". A lean is now gated on real evidence (a lift above
  // the catalog baseline, on at least two forms rated 3+), so the person is known to lean that way,
  // but the evidence is a handful of forms and these sentences describe a whole way of thinking.
  // So each has a THIN form for when the evidence is real but small, and the thin forms say what the
  // ratings actually show: which of your rated things lean this way, rather than what you are like.
  Vine: "Language people tend to narrate. Much of what you do has a beginning, a middle and an argument, and even visual work can arrive with a title and a story.",
  Petal:
    "Visual people judge with the eye first: composition, color, what sits next to what. You tend to notice a badly spaced sign before you notice what it says, and to trust a thing more once it looks right.",
  Tendril: "Movement people think by doing. You understand something once your body has been through it.",
  Nectar:
    "Sensory people treat taste and smell as serious information. You are drawn to what can be cooked, worn or consumed, and suspect anything that ignores the senses of being only half finished.",
  Trellis:
    "Space people notice what rooms do to people. Layout, light, where a doorway leads: you would rather change the arrangement than the thing arranged, and a badly planned space tends to bother you.",
  Root: "Nature people work in seasons, not sessions. You like things that grow, decay and return, and you are patient with slow processes.",
};

// Thin forms of the same seven, used when the lean is real but rests on two or three forms. They
// describe the ratings instead of the person, which is the honest thing to do at that evidence
// level. Keyed by the same internal tribe names the plant code uses.
const TRIBE_READ_THIN = {
  Reed: "Sound stands out a little in your list. It is not a way of working yet, just a tilt: among the things you rated 3 or higher, the ones that live in rhythm and tone make up a larger share than they do across the catalog.",
  Vine: "Language stands out a little in your list. It is not a way of working yet, just a tilt: among the things you rated 3 or higher, the ones that are really about sequence and narrative make up a larger share than they do across the catalog.",
  Petal:
    "The visual stands out a little in your list. It is not a way of working yet, just a tilt: among the things you rated 3 or higher, the ones you would judge with your eye make up a larger share than they do across the catalog.",
  Tendril:
    "Movement stands out a little in your list. It is not a way of working yet, just a tilt: among the things you rated 3 or higher, the ones that are really about the body in motion make up a larger share than they do across the catalog.",
  Nectar:
    "Taste and scent stand out a little in your list. It is not a way of working yet, just a tilt: among the things you rated 3 or higher, the ones with a sensory payoff make up a larger share than they do across the catalog.",
  Trellis:
    "Space and structure stand out a little in your list. It is not a way of working yet, just a tilt: among the things you rated 3 or higher, the ones about rooms, layout and structure make up a larger share than they do across the catalog.",
  Root: "Nature stands out a little in your list. It is not a way of working yet, just a tilt: among the things you rated 3 or higher, the ones about growing and natural systems make up a larger share than they do across the catalog.",
};

// Closes the lean paragraph. It deliberately does NOT name the field again: the headline has
// already glossed it and the TRIBE_READ sentences have already described it, so a third
// "your pull toward sound and pattern" was saying the same thing three times in one paragraph.
const REGIME_TIE = {
  ordered: "Steered by control, what you make here tends toward craft, refined until it is repeatable.",
  adaptive: "Flexible about method, here you can expect to move between planning and improvising.",
  emergent: "Open to chance, here unplanned results have the best chance of becoming a recognizable style.",
};

const GLOSSARY = [
  [
    "Herbarium",
    "The second tab, where your profile is kept.",
    "A collection of pressed, dried and labeled plant specimens, used as a reference library.",
  ],
  [
    "Holotype",
    "Your profile page and the flower at its top: the one specimen your taste is named from.",
    "The single specimen a species name is officially attached to. Every later find is compared against it.",
  ],
  [
    "Plate",
    "The framed picture of your plant, styled like a page from a botanical book.",
    "A full-page illustration in a scientific book, traditionally engraved or lithographed.",
  ],
  [
    "Flower",
    "The flower drawn for every art form and for you. Longer petals mean stronger traits.",
    "The flower of a plant, or a plant in flower.",
  ],
  [
    "Genus",
    "Your core type, one of 16. Each is named after a real organism whose way of living echoes how you work. Fourteen are plants; Armillaria is a fungus and Physarum a slime mold.",
    "A group of closely related species, and the first word of a two-part Latin name, as in Helianthus annuus.",
  ],
  [
    "Tribe",
    "The nickname for your kind of practitioner, such as The Room-Readers.",
    "A rank below subfamily and above genus that groups related genera.",
  ],
  [
    "Growth habit",
    "The section describing how you tend to work, told as a plant.",
    "A plant's characteristic form and manner of growing: climbing, creeping, upright or spreading.",
  ],
  [
    "var. (variety)",
    "Your approach to chance: ordinata steers toward control, flexilis moves between, aleatoria leaves room for chance.",
    "A rank below species for a natural variant that differs in some trait but is not a separate species.",
  ],
  [
    "cf. (compare)",
    "The one or two fields your ratings clearly favor, written as Latin adjectives and spelled out in plain words.",
    "Short for the Latin confer, compare. Written in a name when an identification is provisional and the specimen resembles a named group.",
  ],
  [
    "Epithet",
    "The Latin word after var. or cf.: sonans (sound and pattern), eloquens (language and sequence), versicolor (the visual), mobilis (the body in motion), fragrans (taste and scent), spatialis (space and structure), sylvestris (nature).",
    "The descriptive second part of a species name, such as alba (white) or officinalis (used in medicine).",
  ],
  [
    "indeterminata",
    "What you see while it is too early to tell.",
    "Undetermined: a specimen not yet identified to a variety or species.",
  ],
  [
    "Taxonomy",
    "The naming logic behind your profile: genus first, then variety, then compare.",
    "The science of naming and classifying living things in nested ranks.",
  ],
];

const GENUS_BIO = {
  Selaginella: "Spikemoss. Some species curl up dry and revive when watered.",
  Cuscuta: "Dodder. A leafless parasitic vine that grows on a host plant.",
  Rafflesia: "The corpse lily. Enormous, rare, short-lived, and famously foul-smelling.",
  Mimosa: "The sensitive plant. Folds its leaves when touched.",
  Lithops: "Living stones. Succulents camouflaged as pebbles.",
  Pteris: "Brake ferns. Fiddleheads unfurl into fronds again every season.",
  Drosera: "Sundews. Carnivorous plants with sticky, glistening leaves.",
  Helianthus: "Sunflowers. Young heads turn to follow the sun.",
  Physarum: "A slime mold with no brain that can solve mazes.",
  Lemna: "Duckweed. Tiny floating plants that can cover a whole pond.",
  Armillaria: "Honey fungus. One organism can span a forest floor.",
  Taraxacum: "Dandelions. Weeds that settle almost anywhere.",
  Lycopodium: "Clubmosses. Slow, ancient plants that spread by spores.",
  Bambusa: "Bamboo. Many stalks joined by one root system.",
  Passiflora: "Passionflowers. Elaborate climbers with showy blooms.",
  Ficus: "Figs, including banyans, whose aerial roots grow into forests.",
};
