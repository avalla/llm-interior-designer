# Desktop app for architects - architecture and status

Goal: an architect opens the DWG they already have, confirms what the app recognised, and gets the same checks this
repository runs today (openings, seats, clearances, routes, privacy, daylight, safety, robustness...) on a clickable plan,
plus a PDF report, a DXF/DWG with the issues on their own layer, and an optional AI pre-mortem.
Users: architects working in AutoCAD with DWG files (user answer, 2026-10-28), mostly on Windows.
Scope: **internal tool** for now (user answer, 2026-10-28); a commercial product may follow, so no choice here may block
it (no GPL dependencies in the shipped app, DWG conversion kept as an external tool).

## Current implementation (reviewed 2026-10-29)

| Component | State | Evidence / remaining limit |
|---|---|---|
| 2.5D core | Implemented; FreeCAD parity harness exists | `app/tests/parity.py`; current passing status requires a fresh run |
| DXF/DWG recognition and semantics | Implemented for supported drawing conventions | `app/tests/import_e2e.py`, `app/tests/import_mutants.py`; real studio drawings remain a validation gate |
| Studio profile, viewer, results, help | Implemented | `app/sidecar/server.py`, `app/desktop/`; UI build and sidecar smoke test |
| Packaging | Build workflow and internal pre-release recorded | `.github/workflows/package.yml`; see dated history for platform-specific tests |
| Exported PDF / annotated DXF report | Planned | Current desktop results are on screen |
| Versioned project persistence, re-imported per-element overrides, full brief UI | Target design | Studio profile reuse exists; it does not implement the entire project lifecycle below |
| AI features | Planned, optional | No current AI data transfer workflow |
| Exploded furniture/door recognition | Planned | Unsupported elements are diagnosed; own exported plan is not fully recognised |

The sections below retain the architectural decisions and target design. Features marked planned are not present
product capabilities. The [user guide coverage matrix](interior-check.md#coverage-and-required-inputs) describes the
actual import path. [Implementation history](desktop-app-history.md) preserves dated measurements separately; consult
[eval history](../evals/history.md) for validation failures as well as passes.

This source audit includes local programme/privacy engine updates still under validation. It does not establish
that the published installer contains those updates; check the release's source revision before relying on them.

## 1. Decisions

| # | Decision | Why | Rejected alternative |
|---|---|---|---|
| D1 | Port the engine to a **2.5D core** in pure Python (Shapely polygons + z intervals), no FreeCAD at runtime | every shape the checks use is a vertical prism (boxes, cylinders, door sweeps, walls); prism intersection = plan intersection x height overlap. Drops a ~1 GB dependency, runs in milliseconds, handles rotated furniture (today's engine assumes axis-aligned boxes in several places) | bundling FreeCAD headless: works, but heavy, slow to start, hard to sign and update on Windows |
| D2 | **DXF is the internal input format**; DWG is converted on the user's machine | `ezdxf` reads DXF fully; AutoCAD users can save DXF natively (SAVEAS / DXFOUT), and ODA File Converter, if installed, converts DWG silently (already used by `tools/read_plan.py`, also via `ezdxf.addons.odafc`) | writing a DWG reader; bundling ODA File Converter (its licence must be checked before any redistribution); LibreDWG (GPL-3, uneven support for recent DWG versions) |
| D3 | **Recognition is assisted, never silent**: the app proposes walls, openings, rooms and furniture, the architect confirms or fixes them, and fixes are saved | real drawings use studio-specific layers and blocks; a wrong guess passed silently would make every check meaningless (same reason the repo reports NOT VERIFIABLE instead of guessing) | fully automatic recognition (fails on the first unconventional drawing) |
| D4 | **Studio profile**: layer -> category and block name -> furniture type mappings, saved once per studio and reused | a studio draws the same way on every job; the second project should need almost no confirmation | asking the same mapping on every file |
| D5 | **Furniture semantics library**: each furniture type generates its uses (seat, access zone, leaf sweep, destination, clearances, no-view...) from its footprint and front side | the checks only see registered uses (AGENTS.md); architects draw blocks, not uses. This library is where the repo's know-how (design-rules, lessons, patterns) becomes product | asking the architect to register uses by hand |
| D6 | Shell: **Tauri v2 + TypeScript UI + Python sidecar** (engine, ezdxf, Shapely) packaged with PyInstaller, JSON messages over stdio | small installer, native window on Windows and macOS, web UI for the plan viewer; the engine stays in Python where the existing code and evals are | Electron (heavier, otherwise fine as fallback); PySide6 (one language, weaker UI tooling for an interactive plan viewer) |
| D7 | **Parity before features**: the 2.5D core must give the same verdicts as `lib/interiors.py` on `evals/fixtures` and on every project in `projects/` | the evals are the only proof that the port did not lose recall | rewriting checks from the docs |
| D8 | AI features are **optional and opt-in per project** (Claude API, key in the OS keychain); without them the app is complete | client plans are confidential; the deterministic checks must never depend on a model | AI in the main loop (recognition or verdicts) |

## 2. Target overview (includes planned output and AI modules)

```
            DWG ──(ODA File Converter, if installed)──┐
            DXF (AutoCAD SAVEAS) ─────────────────────┤
                                                      v
 ┌──────────────────────────── Python sidecar ─────────────────────────────┐
 │ import/      DXF reader: units, layers, blocks (exploded with transforms),│
 │              xrefs/paper space reported, proxies (AEC objects) reported   │
 │ recognise/   walls, openings, rooms, furniture  ->  candidates + confidence│
 │ model/       Project = source DXF + profile + overrides + brief           │
 │ semantics/   furniture type -> uses (seat, access zone, sweep, ...)        │
 │ core/        2.5D geometry + checks (port of lib/interiors.py verify())   │
 │ output/      report (PDF/Markdown), annotated DXF (+ DWG via ODA), JSON   │
 │ ai/          layer-mapping assistant, pre-mortem (optional)               │
 └───────────────▲──────────────────────────────────────────┬──────────────┘
                 │ JSON over stdio (request/response + progress events)    │
 ┌───────────────┴──────────────────── Tauri shell ─────────┴──────────────┐
 │ UI (TypeScript): import wizard, mapping table, SVG plan viewer with      │
 │ layers and selection, results list linked to the plan, brief and        │
 │ requirements, report preview, settings (profile, ODA path, API key)     │
 └──────────────────────────────────────────────────────────────────────────┘
```

The FreeCAD workflow in this repository stays as it is (agent-driven design, 3D, STEP). Once the core is at parity,
`lib/interiors.py` can delegate its checks to it, so both tools share one set of rules.

## 3. Target project data model (persistence and re-import planned)

```
Project (folder or .zip, versioned JSON)
  source:      path + hash of the DXF/DWG, import date, units and scale confirmed by the user
  profile:     studio profile id (layer and block mappings, defaults: door height, sill heights, room height)
  elements:    recognised elements, each with a stable key = DXF handle (or block insert handle)
     Wall      polygon, thickness, height
     Opening   kind (hinged door, sliding door, window, French window), host wall, width, height, sill,
               hinge side and swing (from the arc in the door block), leaf geometry
     Room      polygon, name (from the text inside), kind (habitable, bathroom, ...), private flag
     Furniture type (from the semantics library), oriented rectangle or polygon, height, front side
  overrides:   user corrections keyed by handle (type, front side, height, "ignore") - survive a re-import
  brief:       requirements R01... with links to checks (same model as requirement() today)
  results:     check results (same fields as today: category, element, measure, threshold, status, severity, method)
```

Re-import: when the architect saves a new version of the DWG, the app re-runs recognition and re-applies overrides by
handle; elements whose handle disappeared are listed for review instead of being dropped silently.

## 4. Recognition design and current limitations

| Step | Input | Method | Output shown to the user |
|---|---|---|---|
| Units and scale | `$INSUNITS`, dimensions | declared units; cross-check against DIMENSION measurements; ask when undeclared or inconsistent | "1 unit = 1 mm, confirmed by 14 dimensions" |
| Layer classification | layer names, entity types per layer, block names | studio profile first; then heuristics (names like MURI/WALL/A-WALL, PORTE/DOOR, FINESTRE/WINDOW, ARREDI/FURN, hatches); optional AI suggestion from names and counts only (no geometry leaves the machine) | mapping table to confirm |
| Walls | lines, polylines, hatches on wall layers | pair parallel segments at typical thickness (8-50 cm), or take closed polylines/hatches; union into wall polygons; gaps at openings | walls highlighted; unpaired segments flagged |
| Openings | block inserts on door/window layers, arcs | door = insert with an arc: hinge = arc centre, width = radius, swing = arc side; windows = inserts or gaps in external walls; heights from block attributes or profile defaults | each opening with its swing drawn |
| Rooms | wall polygons + openings closed at the jambs | polygonise the free space; name from TEXT/MTEXT inside; kind from the name (BAGNO, WC, CAMERA, CUCINA...) | room list with areas |
| Furniture | block inserts on furniture layers | block name -> type via profile and a built-in dictionary (letto, armadio, divano, tavolo, sedia, wc, lavabo, doccia...); footprint = block extents in local axes; front side = block's local -Y (configurable per block) | unrecognised blocks listed for one-click typing |

This table includes target behaviour: dimension cross-checks and recognition beyond supported blocks must not be
assumed from it. Current input support is in the user guide.

Known hard cases to measure in the spike (section 9): AutoCAD Architecture walls and doors (AEC objects appear as proxy
entities and are not readable as geometry), dynamic blocks, nested blocks and xrefs, plans drawn in paper space,
furniture drawn as loose lines instead of blocks, walls drawn as single lines.

## 5. Engine core (port of `lib/interiors.py`)

Every current check maps onto 2.5D geometry:

| Check | Today (FreeCAD) | 2.5D core |
|---|---|---|
| Openings, handles, reveals, geometry | 3D `common()` volumes | polygon intersection area x z-overlap |
| Seats, access zones | box in front of the edge, first obstacle | same, as polygons; works for rotated furniture |
| Clearances | `distToShape` | Shapely `distance` between footprints whose z ranges overlap |
| Routes, privacy | 5 cm grid BFS (already 2D) | same algorithm; grid from polygons |
| Sightlines (no_view) | segment vs walls and leaves | Shapely line intersection |
| Light and air, TV rule, ergonomics, assembly, safety, robustness, requirements | arithmetic on recorded values | unchanged |

Shapes that are not vertical prisms (the plant's sphere, sloped ceilings) are approximated by their bounding prism; the
report says so in the method column.

Parity harness: run old and new engines on fixtures, projects and shifted-furniture mutants. Compare ordered
(category, element) rows, status, severity and measure text. Numeric differences may be one unit of the last printed
digit; collision volumes allow 5 cm3 or 0.1%, whichever is larger. `app/tests/parity.py` also compares runtime rule
dictionaries. CI runs it headless. This proves agreement on supplied models, not complete import semantics or correct
real-world design.

## 6. Target user workflow (brief, export and AI steps planned)

1. **Open**: drop a DWG/DXF; the app converts, reads units, shows the extents.
2. **Confirm**: mapping table (layers, unrecognised blocks) next to the plan; every candidate coloured by confidence.
3. **Brief**: occupants, requirements (R01...), private rooms, defaults (room height, door height).
4. **Results**: plan with issues drawn on it (leaf sweeps, seat zones, routes); list grouped by room and severity;
   clicking a row zooms to the element and shows measure, threshold, rule source and the lesson/pattern behind it.
5. **Deliver**: PDF report with the NOT VERIFIABLE list; DXF (and DWG if ODA is present) with the issues on a layer
   `VERIFICA` so the architect sees them in AutoCAD over their own drawing.
6. **Pre-mortem (optional)**: sends brief, plan image and results to the model; stories come back structured
   (room, scenario, severity, element ids) and are triaged by the architect as in `reviews/premortem-*.md`.

The app reviews and reports; it does not move furniture. Proposing variants (as `tools/explore.py` does) is a later
feature.

## 7. Packaging and distribution decisions

- Windows first (AutoCAD users), macOS second. Internal tool: installers shared inside the studio, code signing optional
  (users may have to confirm the SmartScreen / Gatekeeper warning once); signing and the Tauri updater come with a
  wider release.
- Sidecar: PyInstaller build of the Python package (current package is one-file; initial proposal was one-folder).
  Platform-specific size and startup observations are in the implementation history; PDF output remains planned.
- ODA File Converter: installed by each user from the ODA website (free download), detected at its default install
  path or set in settings; without it the app accepts DXF only and tells the user how to save DXF from AutoCAD.
  Before any commercial release: re-check ODA terms or join ODA for the Drawings SDK.
- No telemetry by default; project files stay local; AI calls only when the user starts them.

## 8. Repository boundaries (output/AI remain planned)

```
app/
  core/            Python package: geometry, checks, rules (RULES from docs/design-rules.md), report
  importer/        DXF reading and recognition
  semantics/       Python library.py: furniture types, height defaults, front side, uses
  sidecar/         stdio JSON server, PyInstaller spec
  desktop/         Tauri project (src-tauri/, ui/)
  tests/           parity harness, recognition tests on sample drawings (anonymised)
```

Stays in this repository so the core, rules and evals evolve together. CI has parity and import tests;
the packaging workflow builds the sidecar and desktop installer.

## 9. Roadmap and acceptance criteria

| Phase | Content | Exit criterion |
|---|---|---|
| 0. Spike (about 2 weeks) | (a) recognition prototype on 3-5 real studio DWGs; (b) port routes, clearances, openings to 2.5D | (a) walls, doors with swing, rooms recognised for >= 80% of elements after units are confirmed, measured per drawing; (b) same verdicts as today on `apartment-100sqm` and `evals/fixtures` for those checks |
| 1. Core at parity | every check ported, parity harness in CI | 100% parity on fixtures and projects; all expected engine checks detected, no unexpected failures |
| 2. Importer + semantics | mapping UI data, studio profile, furniture library for living, kitchen, bedroom, bathroom | a second drawing from the same studio needs <= 5 manual fixes |
| 3. Desktop MVP | Tauri shell, viewer, results, PDF, annotated DXF | an architect runs a real job end to end without help |
| 4. AI | mapping assistant, pre-mortem | pre-mortem recall measured on the review fixtures (as `prompt-evals`) |
| 5. Pilot | 2-3 architects, real jobs, feedback into lessons/FMEA | issues found by the app that the architect agrees with; false alarms per job |

Historical implementation measurements and packaging notes are in [desktop-app-history.md](desktop-app-history.md).

## 10. Risks

| Risk | Effect | Mitigation |
|---|---|---|
| Drawings too heterogeneous for recognition | long confirmation step, users give up | studio profiles; spike on real files first; trace-over fallback |
| AutoCAD Architecture (AEC objects) - unlikely, users draw in plain AutoCAD | walls/doors unreadable in DXF | importer counts proxy entities and warns; exporting to plain AutoCAD (EXPORTTOAUTOCAD) produces readable geometry |
| Furniture front side ambiguous | wrong access zones and seats | block convention in the profile and front shown on plan; per-element flip remains a proposed mitigation |
| Missing heights in a 2D plan | sill, door height, furniture height wrong | profile defaults, shown as assumptions in the report (like the brief's assumption log) |
| ODA licensing | cannot ship DWG conversion in a product | internal tool: each user installs the free converter; not bundled; check ODA terms before any commercial release |
| Port loses recall | app misses defects the repo catches | parity harness in CI (D7) |
| Confidential client plans | trust | local-only processing; AI opt-in; AI mapping sends names only |

## 11. Product decisions and validation inputs still needed

1. ~~Plain AutoCAD or AutoCAD Architecture?~~ Most likely plain AutoCAD (2026-10-28): walls and doors are lines, arcs
   and blocks; to be confirmed on the sample files (the importer reports proxy entities anyway).
2. 3-5 real DWGs from the architects, anonymised if needed, plus their layer standard if one exists.
3. Windows only, or macOS too from the first release?
4. ~~Internal tool or product?~~ Internal tool for now (2026-10-28); product decision later.
5. Language of the UI and reports: Italian first?
