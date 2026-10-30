---
name: furnishing
description: Lays out and furnishes a project in projects/<name>/project.py in phases, until the checks are at zero. Use for new rooms, moving walls/doors/windows, furnishing, applying fixes from a review.
---

# Furnishing

Before drawing, read [`docs/method.md`](../../../docs/method.md) (phases, per-room checks, composition),
[`docs/patterns.md`](../../../docs/patterns.md), [`docs/lessons.md`](../../../docs/lessons.md) and the project's `brief.md`.
Thresholds are in [`docs/design-rules.md`](../../../docs/design-rules.md); `projects/apartment-100sqm/project.py` is the example
to copy patterns from. Without a `brief.md` with requirement ids, start from the `project-onboarding` skill.

## Steps

1. **Layout.** When the programme warrants it, sketch 2-3 genuinely different options (position of night zone, kitchen,
   bathrooms relative to services and light), discard those that break constraints and choose with reasons. Doors: reveal
   >= 15 cm, hinge on the wall side (P16), sliding doors in narrow corridors and corners (P17). Every `room()` gets its
   `kind` (the minimum areas, the programme and the way into bedrooms are checked on it); bedrooms and the shared
   bathroom open onto a `corridor` room, never onto a living one (L23). Done when every room has access and a kind and
   habitable rooms have a window.

2. **Programme per room, then main furniture (PHASE = 2).** First write, in the brief, one row per room with its functions
   from brief par. 2-4 (who sleeps there and in what bed, metres of hanging and shelves, study, how many sit, cook with
   pantry and bins, eat N everyday / M with guests, dry, clean) and the object that will serve each function; count beds
   against occupants, seats against occupants plus guests, storage provided against required (L27). Then model the
   objects: beds, sofas, tables, the whole kitchen (sink, hob, oven, fridge, dishwasher, landings, wall units or pantry,
   bins, hood), wardrobes with their real capacity, fixtures (WC, bidet, basin, shower or bath: a bathroom without a
   bidet is declared), entrance storage, secondary pieces (chest of drawers, desk, bookcase, sideboard). Appliance zones are the open door
   plus the person: drop-down and pull-out doors get an `appliance_zone(kind="dishwasher"|"oven"|"drawer")`, whose
   depth comes from `RULES`; hinged doors a `hinged()` leaf with a plain `access_zone` (L29). Register each piece's use
   right away: `chair`/`seat` for whoever sits (each seat is also a viewpoint), `access_zone` in front of storage,
   `destination` where a person must get to, `clearance(kind=)` for pinch points, `tv`, `height_match`; WC and beds are
   `intimate()`, every sofa and stair arrival a `viewpoint()` (L25). Draw check zones at the full threshold (L11). Every
   `requirement()` links to the checks that prove it. Done when every function of every room has its object and its
   registration, and no room (service rooms included) is empty without a stated reason (L26: the engine reports empty
   service rooms and habitable rooms under 10% occupancy).

3. **Variants.** For the placements you are least sure of (table, island, sofa, bed), expose them in `PARAMS` and run
   `tools/explore.py` with a small grid. Read `output/variants.md`: the ranking is a filter, the choice and its reason are
   yours. Done when the chosen values are the project defaults and the reason is stated.

4. **Verify.** Run the project in FreeCAD. The summary must end with `TOTAL PROBLEMS: 0`, including Robustness (no measure
   at zero margin) and Requirements (no unlinked requirement). For every NON-COMPLIANT item fix the project, not the
   threshold, and run again; recheck the elements connected to the fix. Improvement notes are fixed when cheap, otherwise
   declared. A NON-COMPLIANT result that cannot be fixed within the brief is proposed to the user, and becomes
   `accepted(pattern, by, date, reason)` in the project only with their answer (L28). Zero is a gate, not the finish (L26): a fix may not remove the function a piece served (a chair taken away
   is a seat lost, to be given back elsewhere), and a room that passes because it is nearly empty has not passed. Done
   when the report is at zero and the programme rows of step 2 are still all served.

5. **Details (PHASE = 3).** Rugs, lamps, plants, wall items: added without moving anything from phase 2, then verified again
   (a lamp can close a route: L06). Done when verification is back at zero.

6. **Counter-test.** For every new or changed check in `lib/interiors.py`, reintroduce the defect it must find (test objects
   prefixed `TEST_`, then rerun the project to clean up) and show that it is reported; then run the `prompt-evals` engine
   eval to confirm no regression.

7. **Visual review and pre-mortem.** `Top` and `Isometric` screenshots: look for what the checks do not measure (patterns
   P01-P14, groups competing for a region, overloaded walls, seats without surface or light, crowded rooms, and the
   opposite: empty rooms, bare walls, half a room with nothing in it, occupancy under 10%). List every room with its
   objects from the furniture schedule and justify each room with fewer than three. Then run the
   `pre-mortem` skill and triage its stories: the designer's own review is not enough (L19). Done when every pre-mortem
   story has a verdict.

8. **Export and lessons.** If files are needed, `export-autocad` skill. Every defect found by the user or the pre-mortem that
   the checks had missed becomes an `Lnn` lesson in `docs/lessons.md`, updates `docs/fmea.md` and, when measurable, a new check.

## Report

What changed and why; default choices made; variants explored and the reason for the choice; `verify()` outcome with
measures (not just "OK"); requirements traceability; counter-tests; pre-mortem verdicts; accepted improvement notes;
NOT VERIFIABLE items with the professional who closes them.
