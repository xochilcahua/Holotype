# Audit checks

Run these checks from the repository root using the Python executable reported by
`tests/env_check.py`. Scripts marked (writes) save results in `out/audit/`.

| script | what it answers |
|---|---|
| `check.py` | checks catalogue structure, hierarchy links, parent labels and participation data |
| `orphan_ratings.py` | checks that ratings for missing forms are preserved |
| `live_search.py` | checks catalogue search terms through the app |
| `verify_search.py` | the same, under the matcher's rules |
| `calibrate.py` | the distance model scored against declared near and far pairs (a pass rate; read the pairs, not just the rate) |
| `probe_ten.py` (writes) | put a 10 on each form; what the app calls close and far |
| `probe_extremes.py` (writes) | checks connected forms, isolated forms and expected distance orderings |
| `probe_decompose.py` | reports each axis group's contribution to a distance |
| `probe_catalogue.py` (writes) | the shape of the catalogue: categories, cross-category neighbours, isolates, closest pairs |
| `probe_novelty.py` (writes) | novelty invariants, scenarios, growth curve, score ceiling |
| `probe_genus_text.py` (writes) | every genus paragraph next to the bits that select it |
| `probe_breadth.py` | the breadth bit separates spread from focus at equal rating counts |
| `probe_sessions.py` | what the app says about each saved session in $HOLOTYPE_SESSIONS |
| `probe_population.py` | an independent population probe (different generator from `population.py`) |
| `loadapp.py` | shared app loader |
| `audit_all_tools.py` | run everything and classify PASS / FAIL / SILENT (SILENT = exited 0 and printed nothing) |

Longer checks (`run_tests.py`, `population_check.py`) are in the parent folder.
