# Base project: interiors in FreeCAD through MCP

Reusable base for designing and checking furnishing layouts (apartments, villas, single rooms) in FreeCAD, driven by the
`freecad` MCP server, with delivery for AutoCAD. Every result is a **preliminary proposal**, never a construction document.

## Prerequisites for every session

- FreeCAD open, **MCP Addon** workbench, **Start RPC Server** clicked. Check with `get_rpc_status`; if it does not answer,
  ask the user to start it (one click in the GUI).
- `/Applications/ODAFileConverter.app` for DWG <-> DXF, `uv` for the ezdxf scripts.

## Layout

| Path | Role |
|---|---|
| `lib/interiors.py` | engine: primitives, doors/windows/sliding doors, use registration, `verify()`, `export()` |
| `projects/<name>/project.py` | the project, in phases; rerun after every change |
| `projects/<name>/brief.md` | brief, data sources, assumption log |
| `projects/<name>/input/` | client starting files (plans, PDFs, photos, data sheets): excluded from git |
| `projects/<name>/output/` | FCStd, 2D/3D DWG, STEP, PNG, `verification_report.md`: generated, excluded from git |
| `projects/_template/project.py` | skeleton for a new project |
| `projects/apartment-100sqm/` | complete example to copy patterns from |
| `tools/` | `read_plan.py` (incoming DWG/DXF), `explore.py` (variants), `export.sh`, `annotate_plan.py`, `export_3d_dwg.py` |
| `docs/method.md` | the method: priorities, phases, per-room checks, scenarios, antipatterns, delivery format |
| `docs/design-rules.md` | single source of thresholds (minimum / comfort / source) |
| `docs/brief-template.md` | brief to fill in during onboarding |
| `docs/lessons.md` | lessons learned `Lnn`, to reread before designing and to extend afterwards |
| `docs/patterns.md` | pattern language `Pnn` (Alexander + project patterns), used as leading words |
| `docs/fmea.md` | failure modes with severity/occurrence/detection: what to check first, what to automate next |
| `docs/interior-check.md` | the desktop app for its users: what it reads, recognises, checks and does not do |
| `docs/desktop-app.md` | architecture and progress of the desktop app for architects (DWG import, 2.5D engine core, Tauri) |
| `app/` | desktop app work: `core/interiors_core` (checks without FreeCAD, parity-tested), `importer/` (DXF/DWG recognition), `semantics/` (furniture type -> uses), `tools/export_model.py`, `tests/` |
| `evals/` | fixtures with planted defects, engine eval and review scoring (`prompt-evals` skill) |
| `archive/` | previous (Italian) versions, read-only |

## Commands

- Model + checks, in FreeCAD via `execute_code`:
  `P = ".../projects/<name>/project.py"; exec(open(P).read(), {"__file__": P, "__name__": "__main__"})`.
  Prints the NON-COMPLIANT items and ends with `TOTAL PROBLEMS: N`; details go to `output/verification_report.md`.
- Export: `import interiors; interiors.export()` in FreeCAD, then `tools/export.sh projects/<name>`, which ends with `round-trip OK`.
- Starting plan: `uv run --with ezdxf python tools/read_plan.py <file.dwg|dxf>`.
- Variants: set `PROJECT` and `GRID`, then `exec(open(".../tools/explore.py").read(), {"PROJECT": PROJECT, "GRID": GRID})`
  in FreeCAD; ranking in `output/variants.md`.
- Engine eval: `exec(open(".../evals/run_engine.py").read(), {})` in FreeCAD; review scoring: `python3 evals/score_review.py <case>`.
- CI (`.github/workflows/ci.yml`) runs `ci/check_repo.py`, `ci/test_score_review.py`, ruff and the headless engine run
  (`ci/engine_ci.py`); run them locally before pushing (commands in README, Continuous integration).

## Conventions

- The model lives in the script: changes are made in `project.py`, never by hand in the `.FCStd`.
- Metres, origin at the outer SW corner, y points north; `interior` = inner face of the perimeter walls.
- `window()` and `opening()` before the `wall()` calls they cross; openings already include subframes and jambs.
- Every piece of furniture with a use registers that use (`chair`, `access_zone`, `destination`, `clearance`, `tv`,
  `height_match`): without registration the checks cannot see it. Parts of the same piece share `item=`.
- Plan texts (dimensions, labels) live in the project; room areas and sliding-door symbols are computed.
- Technical objects excluded from the plan by name use unambiguous prefixes (`Slab`, `Tiles_`, `_Track`) (L12).
- Every brief requirement has an id (`R01`...) and a `requirement()` linked to the checks that prove it, or `manual=True`.
- Bedrooms are `private_room()`; WC and beds get a `no_view()` from the entrance.
- Values worth comparing (table, sofa, bed positions) are read from `PARAMS`, so `tools/explore.py` can vary them.
- Changes to skills, docs or checks are followed by the `prompt-evals` skill: no recall may drop (`evals/history.md`).
- A new check goes into `lib/interiors.py`, with its threshold in `RULES` and in `docs/design-rules.md`, and is proven with a
  counter-test (lesson L04).

## Skills (`.agents/skills/`, Agent Skills standard; `.claude/skills` links to the same folder)

- `project-onboarding`: start a new project, from the initial questions to the survey and the baseline review.
- `furnishing`: lay out and furnish in phases until the checks are at zero.
- `review-layout`: judge a plan (model, DWG, photo, sketch, reported issues) with measures and statuses, without changing it.
- `export-autocad`: deliver 2D/3D DWG, STEP and report.
- `pre-mortem`: independent adversarial review by a fresh reviewer, before delivery.
- `prompt-evals`: measure engine and review prompts on the eval fixtures, before and after a change.
