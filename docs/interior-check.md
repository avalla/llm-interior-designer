# Interior Check: what the program does

Interior Check is the desktop app of this repository (Windows installer from the
[releases](https://github.com/avalla/llm-interior-designer/releases), source in `app/`). It opens an architect's
**2D furnishing plan** (DXF, or DWG) and **checks whether the furniture can actually be used**: doors that open,
room to pull out a chair, a way through to every bed side and wardrobe, a bathroom not reached through a bedroom.
It **reviews** the plan: it does not draw, move furniture or change the file. Results are a preliminary check, not a
construction document. Everything runs on the computer; no file leaves it.

Architecture, measures and progress for developers: `docs/desktop-app.md`. Building and running: `app/desktop/README.md`.

## From the drawing to the results

1. **Read the file.** DXF directly; DWG is first converted to DXF by the free ODA File Converter, which the user
   installs (not bundled). Drawing units come from the file (`$INSUNITS`) or, when missing, from the widths of the
   doors (otherwise millimetres are assumed); the app asks to confirm them, and they can be overridden.
2. **Recognise the plan elements**, each with the evidence it came from and a confidence:

   | Element | How it is recognised |
   |---|---|
   | Walls | closed polylines or hatches on a wall layer (layer names such as `MURI`, `WALL`, `PARETI`, `A-WALL`, `TRAMEZZI`) |
   | Doors, sliding doors, windows | **blocks** on door and window layers (`PORTE`, `DOOR`, `FINESTRE`, `WINDOW`, `SERRAMENTI`...): leaf, hinge, swing |
   | Rooms | the spaces closed by walls and openings; named by the texts inside them (`CAMERA`/`BEDROOM` makes a room private, `BAGNO`/`WC` a bathroom) |
   | Furniture | one **block** per piece, on a furniture layer; its type from the block name, Italian or English (`ARMADIO`, `LETTO`, `DIVANO`, `SEDIA`...) |
   | Front of each piece | seating faces its coffee table or the TV, chairs face their table, other pieces turn their back to the wall; otherwise the side with the most free floor (logged as a guess), or a front convention of the studio's blocks |

   Furniture types known today: wardrobe, cabinet, base unit, wall unit, island, bookcase, built-in, tv unit, tv,
   bed, nightstand, sofa, armchair, chair, table, coffee table, appliance, sanitary, wc, shower, shower screen, bath,
   mirror, heater, lamp, table lamp, rug, decor, hung.
3. **Give each piece its uses**, as an architect would: a wardrobe needs free floor in front to open it, a chair needs
   room behind it, a bed needs passable sides, a WC must be reachable and not visible from the entrance, a washing
   machine must stay out of the shower's splash zone. The entrance is the door that opens onto the outside.
4. **Fill in what a 2D plan does not say** with stated defaults (room height 2.70 m, doors 2.10 m, window sill 0.90 m,
   furniture heights by type): they are listed on the *Assumptions* tab.
5. **Run the checks** and place every result on the plan.

## The checks

Thresholds are catalogued in [design-rules.md](design-rules.md). The core is tested against FreeCAD on exported neutral
models. Importing a drawing is a separate path: recognition, defaults and generated uses determine which checks can
actually run. Passing core parity does not prove complete coverage of a DWG or DXF.

| Check | What it measures | Rule |
|---|---|---|
| Openings | a door or sliding leaf hitting furniture, a wall or another door while it opens | sweep 0-90° (or slide fully) with no contact |
| Handles | handle clear of walls and furniture with the door at 90° | ≥ 7 cm |
| Reveals | door frame too close to the perpendicular wall | ≥ 10 cm |
| Seats | room behind a chair, from the table edge to the first obstacle | 75 cm to stand up, 90 cm to walk behind |
| Clearances | kitchen aisle, island to tall units, bed sides, main passages | 90 (comfort 110), 80/90, 60/70, 80/90 cm |
| Access zones | free floor in front of wardrobes, cabinets, appliances | import currently generates 70 cm; appliance door projection is missing, so this does not verify use with the door open (L29) |
| Routes | every destination (sofa, bed sides, WC, wardrobes...) reachable from the entrance | continuous 60 cm path, open doors as obstacles |
| Privacy | shared rooms reached only through a bedroom; WC and bed seen from the entrance (FreeCAD projects also check seats and declared viewpoints, and the way into bedrooms by room kind; the importer declares neither yet) | route with private rooms blocked; sightline with doors open |
| Light and air | daylight in habitable rooms, window or ventilation in bathrooms | glazing ≥ 1/8 of the floor (indicative) |
| Brief constraints | TV above, in front of or next to a window on the same wall | ≥ 1 m, 1.5 m better |
| Safety | electrical items in the splash zone of a shower or bath | none within 60 cm of an open side |
| Robustness | a measure that passes by less than the placement tolerance | ≥ 4 cm margin over the minimum |
| Geometry | furniture inside a wall or inside another piece | no unintended overlap |
| Assembly | a tall unit that cannot be tilted up in the room | diagonal ≤ room height − 2 cm |
| Ergonomics | height between a surface and its seat | 25-32 cm |
| Programme | room area, oversized laundry and empty service rooms | indicative area defaults and screening heuristics; see coverage below |

Each result has a **status**: *non-compliant*, *verified*, *not verifiable* (the plan does not say enough, for example
a bathroom without a window), or *not applicable*. Severity is separate: *blocking*, *significant*, or *improvement*
(including below-comfort advice). The core can also preserve an *accepted* deviation recorded in a model; the import
guide does not imply a UI approval workflow. Each result shows its measure, threshold and room where available.

Zero reported problems is not a completeness certificate. Check recognition, assumptions, missing uses and the
required/provided programme before interpreting the results. A result computed with assumed heights remains
conditional on those heights; the engine does not automatically downgrade every such result to *not verifiable*.

## Coverage and required inputs

“Core” below means a neutral model with the required declarations. “Import” describes the current recognition and
semantics path, not every possible drawing. Named tests are coverage evidence, not a claim that the current checkout
passes them; current outcomes belong in [eval history](../evals/history.md).

Programme screening and grouped viewpoints describe the local engine update under validation on 2026-10-29, not a
capability guaranteed in the published installer. This documentation change ships separately from that engine work.

| Control | Scripted FreeCAD / core | Imported plan | Required inputs and residual limit | Evidence |
|---|---|---|---|---|
| Door/sliding sweeps, handles, reveals | Registered opening geometry | Recognised door blocks | Hinge, swing, dimensions and defaults must be correct | `app/tests/parity.py`, `app/tests/import_e2e.py` |
| Window-leaf collisions | Registered elevated sweep | Not generated | Window blocks/glazing alone do not describe moving leaves | Import fixture misses A5; `app/tests/import_mutants.py` |
| Appliance open-door use | Explicit leaf or projection plus person zone; FreeCAD `appliance_zone()` | Generic 70 cm access only | Door type/projection and occupied use are not generated; manual review required | L29; `app/semantics/library.py` |
| Seats, bed sides, storage access, routes | Explicit uses, destinations and entrance | Uses inferred from type/front and recognised rooms | Missing/incorrect type or front changes coverage; grid routing is not an accessibility assessment | `app/tests/import_e2e.py`, `app/tests/import_mutants.py` |
| Private-room routes and room-entry screening | Registered private rooms, kinds and destinations | Recognised room kinds and generated destinations | Alternate routes, room naming and shared/private bathroom scope still require review | `app/tests/parity.py`; method L23 |
| WC/bed sightlines | Explicit views; declared intimate objects and viewpoints | Entrance views generated | Main-seat and stair-arrival observer coverage is not equivalent to scripted declarations | L25; `app/semantics/library.py` |
| Daylight, ergonomics, assembly, collisions at height | Modelled heights and geometry | Attributes where supported, otherwise defaults | Assumed sill/furniture heights can change verdicts; confirm data | `app/tests/import_e2e.py`; Assumptions tab |
| Programme screening | Areas, laundry reference, object count, occupancy | Runs on recognised rooms and objects | 10% occupancy and 12 m2 laundry flags are heuristics; neither proves programme capacity | `app/core/interiors_core/checks.py`; rules DR21, DR35, DR37 |
| Brief completeness and storage capacity | Explicit requirements plus manual evidence | No complete brief/capacity workflow | Count occupants, beds, seats and usable storage in the brief | [Brief template](brief-template.md), L26-L27 |
| Safety splash zones | Declared wet zones and electrical items | Inferred from recognised types/sides | Type and geometry assumptions; no electrical-code compliance assessment | `app/tests/import_e2e.py`; L18 |

The remaining geometric/comfort checks in the table above use the same core, subject to the same recognition and
default-data limitations. Review a partly recognised drawing as partial evidence, even when its recognised subset passes.

## What the user sees and does

- **Welcome screen**: Open plan, *Try the example* (a small flat with planted mistakes, bundled with the app),
  *How it works*. A plan can also be dragged onto the window.
- **Above the plan**: what was found (m² of walls, rooms, doors, windows, furniture) and, when something is missing,
  why and what to do (a 3D model instead of a plan, no walls, rooms not closed, doors or furniture drawn as loose
  lines).
- **Plan**: the drawing as it is, with the recognised elements over it (walls, rooms, door sweeps, furniture with its
  front, access and splash zones, destinations, entrance); layers can be switched off; Legend; Fit (F).
- **Results**: non-compliant first, by severity. A click zooms to the element and explains the check and how it was
  measured; `?` opens its entry in the help.
- **Mapping**: how the drawing was read, with a confidence for each choice: the role of each layer, the type of each
  block family (catalogue codes such as `AR01`, `AR02` are typed once as `AR*`), the front convention, the units.
  Choices below 0.7 are counted on the tab. After a correction, *Re-analyse*.
- **Studio profile**: *Save profile* keeps the corrections in a JSON file; *Load profile* applies them to the next
  plans of the same studio, which are then read correctly at once.
- **Help** (`?`, F1): the steps, how a plan should be drawn, every check with its rule, the legend, the keys.

## What it does not do (yet)

- Plans drawn with **loose lines and arcs** ("exploded": doors as arcs, furniture as outlines) are shown with a note
  but not checked: doors, windows and furniture must be blocks.
- Heights are incomplete: supported opening attributes (`H`, `DAVANZALE`/`SILL`) are read; missing opening heights and
  furniture heights use defaults (see *Assumptions*).
- Appliance door projection is not added to imported access zones; review door-open use manually (L29).
- Sightlines from all main seats and stair arrivals, required storage capacity and full brief coverage are not
  automatically established by import.
- Window leaves are not modelled, so a window leaf hitting furniture is not found.
- No report export (PDF or annotated DXF) yet: the results are on screen.
- No building services, structure, acoustics or local code compliance.
- AutoCAD Architecture (AEC) objects are not read, only counted on the *Assumptions* tab (EXPORTTOAUTOCAD in
  AutoCAD turns them into plain geometry); plain AutoCAD drawings are read.
- The interface is in English; the app is not code-signed (Windows asks once: More info -> Run anyway).
