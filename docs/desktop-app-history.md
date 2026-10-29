# Desktop app implementation history

Dated observations from 2026-10-28 and 2026-10-29, retained as historical evidence. Later entries may supersede earlier
limitations. These measurements are not a current CI result. See [architecture and status](desktop-app.md) and
[eval history](../evals/history.md) for the current validation record.

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
