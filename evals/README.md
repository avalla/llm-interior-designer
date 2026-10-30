# Evals

Regression tests for the engine and for the prompts (skills, docs), on fixtures with planted defects.
Procedure: skill `prompt-evals` (`.agents/skills/prompt-evals/SKILL.md`).

| Path | Content |
|---|---|
| `fixtures/<case>/project.py` | a small flat built with `lib/interiors.py`, with planted defects (no comment reveals them) |
| `fixtures/<case>/expected.json` | the planted defects: `engine` = checks that must fail, `keywords` = what a review must say |
| `run_engine.py` | engine eval, run inside FreeCAD; writes `results/engine.md` |
| `score_review.py` | scores a blind review (`results/<case>-review.md`) against `expected.json` |
| `history.md` | one row per eval run: change under test and recalls (committed) |
| `results/` | generated, excluded from git |

| Fixture | Purpose |
|---|---|
| `a-planted-checks` | defects `verify()` must catch: engine regression, plus review recall on measurable defects |
| `b-judgement` | defects only a review can catch: measures the quality of `review-layout` and `pre-mortem` (B6, B7: the toy envelope's own layout defects, caught by the engine since 2026-10-29) |
| `c-programme-privacy` | defects of lessons L23-L29: WC and bed in view from the entrance and the seats, dishwasher zone against an island, under-furnished and empty rooms, oversized laundry, a bedroom below the minimum area, a stale client acceptance |
