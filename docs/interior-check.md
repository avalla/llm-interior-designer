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

Thresholds are those of `docs/design-rules.md`, the same as the FreeCAD engine of this repository (the app's core is
tested for parity with it).

| Check | What it measures | Rule |
|---|---|---|
| Openings | a door or sliding leaf hitting furniture, a wall or another door while it opens | sweep 0-90° (or slide fully) with no contact |
| Handles | handle clear of walls and furniture with the door at 90° | ≥ 7 cm |
| Reveals | door frame too close to the perpendicular wall | ≥ 10 cm |
| Seats | room behind a chair, from the table edge to the first obstacle | 75 cm to stand up, 90 cm to walk behind |
| Clearances | kitchen aisle, island to tall units, bed sides, main passages | 90 (comfort 110), 80/90, 60/70, 80/90 cm |
| Access zones | free floor in front of wardrobes, cabinets, appliances | 70 cm |
| Routes | every destination (sofa, bed sides, WC, wardrobes...) reachable from the entrance | continuous 60 cm path, open doors as obstacles |
| Privacy | shared rooms reached only through a bedroom; WC and bed seen from the entrance | route with private rooms blocked; sightline with doors open |
| Light and air | daylight in habitable rooms, window or ventilation in bathrooms | glazing ≥ 1/8 of the floor (indicative) |
| Brief constraints | TV above, in front of or next to a window on the same wall | ≥ 1 m, 1.5 m better |
| Safety | electrical items in the splash zone of a shower or bath | none within 60 cm of an open side |
| Robustness | a measure that passes by less than the placement tolerance | ≥ 4 cm margin over the minimum |
| Geometry | furniture inside a wall or inside another piece | no unintended overlap |
| Assembly | a tall unit that cannot be tilted up in the room | diagonal ≤ room height − 2 cm |
| Ergonomics | height between a surface and its seat | 25-32 cm |

Each result has a **status**: *non-compliant*, *verified*, *not verifiable* (the plan does not say enough, for example
a bathroom without a window), and a **severity**: *blocking* (must be fixed), *significant* (should be fixed),
*below comfort* (works, but tight). Each shows the measure, the threshold and the room.

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
- No heights from the drawing: sills, door and furniture heights are defaults (see *Assumptions*).
- Window leaves are not modelled, so a window leaf hitting furniture is not found.
- No report export (PDF or annotated DXF) yet: the results are on screen.
- No building services, structure, acoustics or local code compliance.
- AutoCAD Architecture (AEC) objects are not read, only counted on the *Assumptions* tab (EXPORTTOAUTOCAD in
  AutoCAD turns them into plain geometry); plain AutoCAD drawings are read.
- The interface is in English; the app is not code-signed (Windows asks once: More info -> Run anyway).
