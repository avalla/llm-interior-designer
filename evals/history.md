# Eval history

One row per eval run. A change that lowers any recall is reverted or reworked (skill `prompt-evals`).

| Date | Change under test | Engine recall | Unexpected NON-COMPLIANT | Review A recall | Review B recall | Notes |
|---|---|---|---|---|---|---|
| 2026-10-27 | baseline: review-layout with FMEA + pattern pass, requirements, robustness, privacy checks | 10/10 | 0 | 9/9 | 5/5 | scorer moved to whole-word matching after "bed" matched "bedroom" (B2, B5 false hits in the first scoring); A6/A9 keywords narrowed |
| 2026-10-27 | Safety check (wet_zone/electrical), access_zone depth, appliance zones; pre-mortem triage of apartment-100sqm | 10/10 | 0 | - | - | review evals not rerun: prompts unchanged since the baseline row |
| 2026-10-28 | engine: booleans solid by solid (L21), comfort tolerance; app core parity on 104 models incl. 100 mutants | 10/10 | 0 | - | - | prompts unchanged; mutants: 124 NON-COMPLIANT rows, 2 of them missed by the old engine (bookcase compound) |
| 2026-10-28 | app: furniture semantics library for imported plans (uses from block type and front side), plan_2d collisions by allow-list (L22), rooms closed by wall-thick rectangles | 10/10 | 0 | - | - | engine and prompts unchanged; import path: planted 8/9 (A5 needs window leaves), B5 found, mutants 57/61 caught, 2/39 extra (undeclared washing-machine zone) |
| 2026-10-29 | documentation audit baseline on working tree | 10/10 | 5 | 10/11 | 7/7 | Fresh blind A/B reviewers, exported plans round-trip OK. Existing programme/privacy changes produced extra results; Japandi and Villa 5 failed project checks. Expected A/B lists expanded concurrently before scoring (11/7 defects); not directly comparable with the old 9/5 baseline. |
| 2026-10-29 | documentation audit after: brief capacity, rule ids/types, phase gates, coverage, architecture status, FMEA | 23/23 | 2 | 10/11 | 7/7 | Fresh blind A/B reviewers, same supplied plans/reports; no per-case recall drop. Concurrent engine/fixture work added C and changed the denominator; C blind review was not part of this documentation comparison. Working-tree CI still failed (C route extras, Japandi privacy, Villa 5 routes). |
| 2026-10-29 | documentation-only publication isolated on 98b7c7b code | 10/10 | 0 | - | - | Detached worktree with revised docs and committed runtime/fixtures: repository structure, scorer unit test, Ruff, headless engine and apartment example all pass. Local engine/layout changes excluded from this publication. |

Documentation audit scoring note: baseline A9 was described as “Bedroom entrance” with reveal/handle findings, but the
keyword scorer expects `door_bedroom` or “bedroom door”. After the edit, A3 was described as TV 0.21 m from
`Window_Living` on the same wall; whole-word `window` does not match that identifier. Both are substantive findings in
the reviews, but scores above retain the automated misses. Neither expected keywords nor the scorer were changed by
this documentation task. These vocabulary-sensitive misses remain a scorer limitation; 10/11 is not reported as full
recall. Generated reviews and scores remain in ignored `evals/results/`.
