# Eval history

One row per eval run. A change that lowers any recall is reverted or reworked (skill `prompt-evals`).

| Date | Change under test | Engine recall | Unexpected NON-COMPLIANT | Review A recall | Review B recall | Notes |
|---|---|---|---|---|---|---|
| 2026-10-27 | baseline: review-layout with FMEA + pattern pass, requirements, robustness, privacy checks | 10/10 | 0 | 9/9 | 5/5 | scorer moved to whole-word matching after "bed" matched "bedroom" (B2, B5 false hits in the first scoring); A6/A9 keywords narrowed |
| 2026-10-27 | Safety check (wet_zone/electrical), access_zone depth, appliance zones; pre-mortem triage of apartment-100sqm | 10/10 | 0 | - | - | review evals not rerun: prompts unchanged since the baseline row |
