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
| `tools/` | `read_plan.py` (incoming DWG/DXF), `export.sh`, `annotate_plan.py`, `export_3d_dwg.py` |
| `docs/method.md` | the method: priorities, phases, per-room checks, scenarios, antipatterns, delivery format |
| `docs/design-rules.md` | single source of thresholds (minimum / comfort / source) |
| `docs/brief-template.md` | brief to fill in during onboarding |
| `docs/lessons.md` | lessons learned `Lnn`, to reread before designing and to extend afterwards |
| `archive/` | previous (Italian) versions, read-only |

## Commands

- Model + checks, in FreeCAD via `execute_code`:
  `P = ".../projects/<name>/project.py"; exec(open(P).read(), {"__file__": P, "__name__": "__main__"})`.
  Prints the NON-COMPLIANT items and ends with `TOTAL PROBLEMS: N`; details go to `output/verification_report.md`.
- Export: `import interiors; interiors.export()` in FreeCAD, then `tools/export.sh projects/<name>`, which ends with `round-trip OK`.
- Starting plan: `uv run --with ezdxf python tools/read_plan.py <file.dwg|dxf>`.

## Conventions

- The model lives in the script: changes are made in `project.py`, never by hand in the `.FCStd`.
- Metres, origin at the outer SW corner, y points north; `interior` = inner face of the perimeter walls.
- `window()` and `opening()` before the `wall()` calls they cross; openings already include subframes and jambs.
- Every piece of furniture with a use registers that use (`chair`, `access_zone`, `destination`, `clearance`, `tv`,
  `height_match`): without registration the checks cannot see it. Parts of the same piece share `item=`.
- Plan texts (dimensions, labels) live in the project; room areas and sliding-door symbols are computed.
- Technical objects excluded from the plan by name use unambiguous prefixes (`Slab`, `Tiles_`, `_Track`) (L12).
- A new check goes into `lib/interiors.py`, with its threshold in `RULES` and in `docs/design-rules.md`, and is proven with a
  counter-test (lesson L04).

## Skills (`.agents/skills/`, Agent Skills standard; `.claude/skills` links to the same folder)

- `project-onboarding`: start a new project, from the initial questions to the survey in the model.
- `furnishing`: lay out and furnish in phases until the checks are at zero.
- `review-layout`: judge a plan (model, DWG, photo, sketch, reported issues) with measures and statuses, without changing it.
- `export-autocad`: deliver 2D/3D DWG, STEP and report.
