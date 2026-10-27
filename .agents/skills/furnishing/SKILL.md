---
name: furnishing
description: Lays out and furnishes a project in projects/<name>/project.py in phases, until the checks are at zero. Use for new rooms, moving walls/doors/windows, furnishing, applying fixes from a review.
---

# Furnishing

Before drawing, read [`docs/method.md`](../../../docs/method.md) (phases, per-room checks, composition),
[`docs/lessons.md`](../../../docs/lessons.md) and the project's `brief.md`. Thresholds are in
[`docs/design-rules.md`](../../../docs/design-rules.md); `projects/apartment-100sqm/project.py` is the example to copy patterns
from. Without a `brief.md`, start from the `project-onboarding` skill.

## Steps

1. **Layout.** When the programme warrants it, sketch 2-3 genuinely different options (position of night zone, kitchen,
   bathrooms relative to services and light), discard those that break constraints and choose with reasons. Doors: reveal
   >= 15 cm, sliding doors in narrow corridors and corners. Done when every room has access and habitable rooms have a window.

2. **Main furniture (PHASE = 2).** Beds, sofas, tables, kitchen, wardrobes, fixtures. Register each piece's use right away:
   `chair`/`seat` for whoever sits, `access_zone` in front of storage, `destination` where a person must get to, `clearance`
   for pinch points, `tv`, `height_match`. Draw check zones at the full threshold (L11).
   Done when every piece with a use has its registration.

3. **Verify.** Run the project in FreeCAD. The summary must end with `TOTAL PROBLEMS: 0`. For every NON-COMPLIANT item fix
   the project, not the threshold, and run again; recheck the elements connected to the fix. Improvement notes are fixed
   when cheap, otherwise declared. Done when the report is at zero.

4. **Details (PHASE = 3).** Rugs, lamps, plants, wall items: added without moving anything from phase 2, then verified again
   (a lamp can close a route: L06). Done when verification is back at zero.

5. **Counter-test.** For every new or changed check in `lib/interiors.py`, reintroduce the defect it must find (test objects
   prefixed `TEST_`, then rerun the project to clean up) and show that it is reported.

6. **Visual review.** `Top` and `Isometric` screenshots. Look for what the checks do not measure: groups competing for the
   same region, overloaded walls, seats without a surface or light, doors and windows that read poorly, rooms that look
   crowded. Walk through the scenarios in `docs/method.md` section 8. Done when you have described what you looked at and
   what you fixed.

7. **Export and lessons.** If files are needed, `export-autocad` skill. Every defect found by the user that the checks had
   missed becomes an `Lnn` lesson in `docs/lessons.md` and, when measurable, a new check.

## Report

What changed and why; default choices made; `verify()` outcome with measures (not just "OK"); counter-tests; accepted
improvement notes; NOT VERIFIABLE items with the professional who closes them.
