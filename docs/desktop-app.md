# Desktop app for architects - architecture (draft 1, 2026-10-28)

Goal: an architect opens the DWG they already have, confirms what the app recognised, and gets the same checks this
repository runs today (openings, seats, clearances, routes, privacy, daylight, safety, robustness...) on a clickable plan,
plus a PDF report, a DXF/DWG with the issues on their own layer, and an optional AI pre-mortem.
Users: architects working in AutoCAD with DWG files (user answer, 2026-10-28), mostly on Windows.
Scope: **internal tool** for now (user answer, 2026-10-28); a commercial product may follow, so no choice here may block
it (no GPL dependencies in the shipped app, DWG conversion kept as an external tool).

Status: proposal. Nothing here is built yet; section 9 lists what must be proven first.

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

## 2. Overview

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

## 3. Data model

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

## 4. Recognition pipeline

| Step | Input | Method | Output shown to the user |
|---|---|---|---|
| Units and scale | `$INSUNITS`, dimensions | declared units; cross-check against DIMENSION measurements; ask when undeclared or inconsistent | "1 unit = 1 mm, confirmed by 14 dimensions" |
| Layer classification | layer names, entity types per layer, block names | studio profile first; then heuristics (names like MURI/WALL/A-WALL, PORTE/DOOR, FINESTRE/WINDOW, ARREDI/FURN, hatches); optional AI suggestion from names and counts only (no geometry leaves the machine) | mapping table to confirm |
| Walls | lines, polylines, hatches on wall layers | pair parallel segments at typical thickness (8-50 cm), or take closed polylines/hatches; union into wall polygons; gaps at openings | walls highlighted; unpaired segments flagged |
| Openings | block inserts on door/window layers, arcs | door = insert with an arc: hinge = arc centre, width = radius, swing = arc side; windows = inserts or gaps in external walls; heights from block attributes or profile defaults | each opening with its swing drawn |
| Rooms | wall polygons + openings closed at the jambs | polygonise the free space; name from TEXT/MTEXT inside; kind from the name (BAGNO, WC, CAMERA, CUCINA...) | room list with areas |
| Furniture | block inserts on furniture layers | block name -> type via profile and a built-in dictionary (letto, armadio, divano, tavolo, sedia, wc, lavabo, doccia...); footprint = block extents in local axes; front side = block's local -Y (configurable per block) | unrecognised blocks listed for one-click typing |

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

Parity harness: run old and new engines on `evals/fixtures/*` and `projects/*`, compare result rows by
(category, element, status) and measures within 1 cm; any difference is a failing test. CI runs it headless.

## 6. User interface (first version)

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

## 7. Packaging and distribution

- Windows first (AutoCAD users), macOS second. Internal tool: installers shared inside the studio, code signing optional
  (users may have to confirm the SmartScreen / Gatekeeper warning once); signing and the Tauri updater come with a
  wider release.
- Sidecar: PyInstaller one-folder build of the Python package; expected size tens of MB (ezdxf, Shapely, numpy,
  a PDF library), to be measured in the spike.
- ODA File Converter: installed by each user from the ODA website (free download), detected at its default install
  path or set in settings; without it the app accepts DXF only and tells the user how to save DXF from AutoCAD.
  Before any commercial release: re-check ODA terms or join ODA for the Drawings SDK.
- No telemetry by default; project files stay local; AI calls only when the user starts them.

## 8. Repository layout (proposed)

```
app/
  core/            Python package: geometry, checks, rules (RULES from docs/design-rules.md), report
  importer/        DXF reading and recognition
  semantics/       furniture library (YAML: type -> footprint defaults, front side, uses)
  sidecar/         stdio JSON server, PyInstaller spec
  desktop/         Tauri project (src-tauri/, ui/)
  tests/           parity harness, recognition tests on sample drawings (anonymised)
```

Stays in this repository so the core, the rules and the evals evolve together; CI gets a parity job and a sidecar build.

## 9. Plan and go/no-go

| Phase | Content | Exit criterion |
|---|---|---|
| 0. Spike (about 2 weeks) | (a) recognition prototype on 3-5 real studio DWGs; (b) port routes, clearances, openings to 2.5D | (a) walls, doors with swing, rooms recognised for >= 80% of elements after units are confirmed, measured per drawing; (b) same verdicts as today on `apartment-100sqm` and `evals/fixtures` for those checks |
| 1. Core at parity | every check ported, parity harness in CI | 100% parity on fixtures and projects; engine recall 10/10 |
| 2. Importer + semantics | mapping UI data, studio profile, furniture library for living, kitchen, bedroom, bathroom | a second drawing from the same studio needs <= 5 manual fixes |
| 3. Desktop MVP | Tauri shell, viewer, results, PDF, annotated DXF | an architect runs a real job end to end without help |
| 4. AI | mapping assistant, pre-mortem | pre-mortem recall measured on the review fixtures (as `prompt-evals`) |
| 5. Pilot | 2-3 architects, real jobs, feedback into lessons/FMEA | issues found by the app that the architect agrees with; false alarms per job |

### Progress (2026-10-28)

**Phase 1, core at parity: done.** `app/tools/export_model.py` (headless FreeCAD) writes every project and fixture as a
neutral model with the FreeCAD results as reference, plus 100 mutants (`MUTANTS=1`: each piece of furniture of
`apartment-100sqm` shifted by +-20 cm). `app/core/interiors_core` ports every check of `verify()` (Shapely only);
`app/tests/parity.py` compares row by row. Result: 104 models, 10444 rows, 124 NON-COMPLIANT, parity on all of them;
core 3-5 s for all 104 models. CI runs it. The port found two bugs in the FreeCAD engine, fixed there:
- comfort targets compared without tolerance (110 cm against 110 depended on float rounding);
- `common()` with a compound of touching solids (bookcase, chairs) returns nothing: collisions with those pieces were
  invisible (lesson L21). Found only by the mutants: on clean layouts both engines agreed.

**Phase 2, importer: first slice, on synthetic drawings only.** `app/importer/recognise.py` reads DXF (DWG through ODA),
classifies layers (Italian and English names, studio profile override), rebuilds walls (closed outlines with even-odd,
hatches, loose lines), hinged doors (hinge, width, both leaf directions from block arc + open-leaf line), sliding doors,
windows (with H/DAVANZALE attributes when present), furniture blocks, rooms (free space with every opening closed;
names from texts) and lists what it could not read. `app/importer/to_model.py` turns that into a neutral model: heights
from defaults per furniture type (block-name keywords), wall below sills and above heads, sliding-door parking side,
entrance, the uses from the semantics library below, one destination for each room left without one; every default
goes to `assumptions`. Rooms close every opening with a rectangle as thick as the wall beside it (the convex hull it
replaced cut a bathroom corner diagonally, IoU 0.94). Measured on `app/tests/make_sample_dxf.py` drawings (two styles:
Italian layers with polylines and blocks; English layers with loose lines and no units): every element recognised
(64/64, 24/24, 18/18), walls and rooms IoU 1.000; the open-plan japandi variant 58/60 (living and kitchen are one
space with two names).

**Phase 2, furniture semantics: first version.** `app/semantics/library.py` maps block names to a type and a height band
(`FURNITURE`, Italian and English keywords; hung items such as wall units and mirrors get their band, so they collide
with walls and leaves but are never floor obstacles) and types to uses (`USES`), generated from the plan:
- front side: seating faces its coffee table or the room's TV, chairs face their table, every other piece turns its
  back to the wall it stands against; failing that the deepest free floor, logged as a guess in `assumptions`;
- seats (chair -> nearest table or island, edge and direction from the table outline), access zones (wardrobes,
  cabinets, base units, appliances; a run of touching units shares one front and the zone stops at the corner unit;
  light pieces such as nightstands are moved aside, a bed is not), kitchen aisles (island in front of base units
  90/110 cm, of tall units 80/90), bed sides (destination and 60/70 cm clearance beyond the head zone), destinations in
  front of wardrobes, sanitary fittings, sofas (middle half of the seat) and armchairs (any free side), inside the
  shower tray, splash zones on the sides of a tray or bath not closed by a wall or a screen, electrical items,
  `no_view` of beds and WCs from the entrance, bedrooms private;
- destinations are free cells of the route grid as the grid sees them (square inflation), not free points in general;
- overlaps a plan draws on purpose are listed as type pairs (`STACKS`: chair under its table, TV on its unit, hob in the
  worktop, screen on the tray); every other furniture/furniture overlap is a collision again (lesson L22).
Measured (synthetic drawings, two styles): clean apartment and japandi variant 0 NON-COMPLIANT; planted fixture 8 of 9
defects found (A1-A4, A6-A9; A5 needs window leaves on the plan); judgement fixture: B5 (bed visible from the entrance)
found, because the library declares `no_view` where the FreeCAD project did not, plus the bed's west side blocked by the
open bedroom door. On the 100 shifted-furniture mutants, against the FreeCAD verdict: 57 of 61 defective mutants
caught (the 4 missed: window leaf vs wall units and hood, not drawn on a plan; a desk-chair destination the library does
not generate; a hung mirror over a bidet, heights unknown), 2 of 39 clean mutants flagged, both by the washing machine's
access zone, which the FreeCAD project never declared (blocked by a WC and by a towel warmer).
`app/tests/import_e2e.py` asserts every expected row (cat/elem) and nothing else; `app/tests/import_mutants.py` the
mutant rates. Both run in CI.
Caveat: the sample drawings follow conventions written by the same author as the recogniser and the library; they prove
the pipeline, not robustness. Block rotation is not used for the front side yet (the samples bake it into the
geometry); real studio blocks may carry a front convention, a profile setting. Open-plan rooms with two names and no
wall between them (living and kitchen) come out as one room. Real studio DWGs remain the gate of phase 2.

**Phase 2, mapping data and studio profile.** The confirmation UI edits a studio profile (JSON: `units`, `layers`
layer -> category, `blocks` block-name glob -> furniture type, `front` block axis of the furniture front; format in
`app/importer/recognise.py`). `app/importer/mapping.py` lists every layer, block and furniture front with its
candidates, confidence and evidence (profile 1.0; layer or block name 0.8; layer content 0.3-0.6: texts, blocks with
a swing arc, blocks with attributes; fronts: block rotation 0.9, wall behind 0.8, facing the coffee table or TV 0.6,
deepest free floor 0.3), the choices to confirm (< 0.7) and a proposed profile that keeps every automatic choice.
Undeclared units are read from the door widths (median swing radius 60-130 cm). With a profile `front`, the front of
every furniture block comes from its rotation and mirroring; the checks no longer guess it.
Measured on a third synthetic studio (`make_sample_dxf.py --style codes`: layers 0-M30, 0-INF-P...; centimetres,
undeclared; furniture blocks named by catalogue codes, AR01, SE03..., drawn rotated): without a profile 0/64 elements
(no wall layer), 4 of 5 layers found from their content, units found from the doors; the profile written once on the
first drawing has 28 entries (1 layer, the front convention, 26 code prefixes); with it the first drawing and the other
two drawings of the studio are recognised 100% with the same verdicts as the readable styles, with 0 further fixes
(exit criterion: <= 5). Fronts read from the rotation 28/28; inferred from the plan alone 25/28: the three misses are
an armchair facing the sofa rather than the coffee table, a free-standing wardrobe (logged as a guess) and the sofa of
the judgement fixture, which turns its back to the TV (B1): with fronts from the drawing, B1 becomes measurable (a
"seating facing away from the TV" check is not written yet: it belongs in `lib/interiors.py` first).
The same caveat holds: one author wrote the samples, the profile and the recogniser; 28 profile entries is the cost on
a studio that names nothing, and real DWGs will say how many entries real studios need.

**Phase 3, desktop shell: first version (2026-10-28).** `app/sidecar/server.py` serves the importer, the semantics and
the checks as JSON lines over stdio (`--http` for UI work in a browser): plan scene, mapping with confidence, assumptions,
results each with its place on the plan (shapes, points, room). `app/desktop/` is the Tauri v2 shell: it starts the
sidecar on the first request, keeps it, restarts it once when it died; the TypeScript UI opens a DXF/DWG, draws the plan
(walls, rooms, openings with their sweep, furniture with its front, access and splash zones, destinations), lists the
results by severity and zooms to the element of the clicked one, and edits the studio profile (units, layers, block
families typed once as `AR*`, front convention), saved for the next drawing. Checked: the window starts and talks to
the sidecar (`npm run tauri dev`); the full mapping flow on the codes studio in a browser against the HTTP sidecar
(1 layer, 26 families, front convention -> 0 NON-COMPLIANT, as the readable drawing); `app/tests/sidecar_smoke.py`
(every NON-COMPLIANT or NOT VERIFIABLE result with a place has one) and `cargo test --lib` (dead sidecar restarted).
Found on the way: windows were assigned to the first room within 40 cm (a bathroom window went to the closet next
door, depending on the room order); now to the room they face most.
First real-world-like DWG: `projects/apartment-100sqm/output/Apartment_Plan.dwg`, the 2D plan this repository delivers
to AutoCAD. It is fully exploded (636 LINEs, door swings as loose ARCs, furniture as lines and circles, no blocks): walls
are found (11.3 m2), but no doors, windows, furniture or rooms. The app now says so instead of failing.

Packaging (2026-10-29): `.github/workflows/package.yml` builds the Windows installer (PyInstaller sidecar, 27 MB on
macOS, smoke-tested on a room drawn on the spot, bundled by Tauri as `externalBin`, NSIS, per-user, unsigned). The
same build was run locally on macOS: the app bundle (30.6 MB) starts with no `uv` or Python on the PATH and uses the
bundled sidecar; the first request takes about 4 s (the one-file sidecar unpacks itself), the next ones are immediate.
The Windows job runs on every push to main; tag `v0.1.0` published the installer as a GitHub pre-release. The first
UX pass added the drawing itself under the recognised plan, a diagnosis of what was found and what to do (3D model, no
walls, no rooms, exploded doors or furniture), and layer highlighting from the mapping table. A layer used by entities
but missing from the layer table was ignored; now it is classified.

UX pass 2, help and onboarding (2026-10-29): a welcome screen with the three steps (open, check the mapping, read the
results) and a **Try the example** button, which opens the small flat with planted mistakes bundled with the sidecar
(`demo` method, `app/sidecar/samples/demo-flat.dxf`, also inside the PyInstaller exe via `--add-data`); a help drawer
(`?`, F1) with the guide, how a plan should be drawn, the confidence scale, the legend and the controls; a glossary of
every check category (what it measures and its rule, from `docs/design-rules.md`) reached from the `?` of each result
row, and the selected row shows the explanation and the measuring method; a plan legend and a Fit button (F) next to
the layer boxes; drag and drop of a DXF/DWG onto the window; the Mapping tab opens with the number of choices to
confirm. Checked in WebKit (light and dark) with Playwright against the HTTP sidecar, and the packaged sidecar
(PyInstaller, macOS) passes `sidecar_smoke.py`, demo included.

Next: recognition of exploded drawings (doors from a loose arc and leaf line on a door layer, windows and furniture as
connected outlines, furniture typed by the user in the UI), measured on that DWG; the UI in Italian; the "seating facing
away from the TV" check (engine first, then core).

If the spike's recognition score is far below 80%, the fallback is a "trace over" mode: the architect draws walls and
openings quickly over the imported DWG as an underlay, which is slower but always works.

## 10. Risks

| Risk | Effect | Mitigation |
|---|---|---|
| Drawings too heterogeneous for recognition | long confirmation step, users give up | studio profiles; spike on real files first; trace-over fallback |
| AutoCAD Architecture (AEC objects) - unlikely, users draw in plain AutoCAD | walls/doors unreadable in DXF | importer counts proxy entities and warns; exporting to plain AutoCAD (EXPORTTOAUTOCAD) produces readable geometry |
| Furniture front side ambiguous | wrong access zones and seats | block convention in the profile; one-click flip in the UI; front shown on the plan |
| Missing heights in a 2D plan | sill, door height, furniture height wrong | profile defaults, shown as assumptions in the report (like the brief's assumption log) |
| ODA licensing | cannot ship DWG conversion in a product | internal tool: each user installs the free converter; not bundled; check ODA terms before any commercial release |
| Port loses recall | app misses defects the repo catches | parity harness in CI (D7) |
| Confidential client plans | trust | local-only processing; AI opt-in; AI mapping sends names only |

## 11. Open questions for the user

1. ~~Plain AutoCAD or AutoCAD Architecture?~~ Most likely plain AutoCAD (2026-10-28): walls and doors are lines, arcs
   and blocks; to be confirmed on the sample files (the importer reports proxy entities anyway).
2. 3-5 real DWGs from the architects, anonymised if needed, plus their layer standard if one exists.
3. Windows only, or macOS too from the first release?
4. ~~Internal tool or product?~~ Internal tool for now (2026-10-28); product decision later.
5. Language of the UI and reports: Italian first?
