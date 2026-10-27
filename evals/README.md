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
| `b-judgement` | defects only a review can catch: measures the quality of `review-layout` and `pre-mortem` |
