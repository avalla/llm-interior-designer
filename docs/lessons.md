# Lessons learned

One lesson per defect found by the user or by a counter-test. The `Lnn` id is stable: never renumber, never reuse.
Format: what happened, the rule it yields, where it is applied (automatic check or skill step). Add a lesson whenever the
user finds a defect the checks had missed.

**L01 - Collision is not use.** A wardrobe leaf in a 50 cm niche hit nothing, but there was no room to stand in front and
take things out. Rule: every storage unit has a 70 cm access zone. Applied: `access_zone()`.

**L02 - Handles and reveals.** Doors hinged 5 cm from the wall: no room for the jamb, handle against the wall at 90 degrees.
Rule: reveal >= 10 cm and handle checked. Applied: `hinged()` + Handles/Reveals checks.

**L03 - Sitting is not passing.** A round table in a corner with 18-33 cm behind the chairs. Rule: measure from the surface
edge, 75 cm to stand up, 90 to walk behind a seated person. Applied: `chair()` / `seat()`.

**L04 - Counter-test.** A check that has never failed is not proven. Rule: every new check is tested by reintroducing the
defect it must find. Applied: `furnishing` skill, Counter-test step.

**L05 - Legibility.** A white leaf on a white wall and a sliding door drawn as a thin line read as "missing door".
Rule: leaves in a colour different from the wall, sliding doors with a track in 3D and a symbol (thick leaf + arrow) on the
plan. Applied: `hinged()`, `sliding()`, `tools/annotate_plan.py`.

**L06 - Continuous routes.** A floor lamp left 25 cm next to the sofa: sofa and armchair unreachable, with no collision at all.
Rule: every use zone must be reachable from the entrance with a continuous 60 cm; a reading light sits next to its seat.
Applied: `destination()` + Routes check.

**L07 - Check at the right height.** Hood in front of the kitchen window and tap under the leaf: everything clear on the plan.
Rule: window leaves are checked in 3D above the sill. Applied: `hinged(z0=sill)` for windows.

**L08 - AutoCAD formats.** AutoCAD for Mac and LT cannot import STEP. Rule: always deliver the 3D mesh DWG as well.
Applied: `export-autocad` skill.

**L09 - Review without changes.** When the user asks for an analysis, the answer is analysis with measures only; changes start
on confirmation. Applied: `review-layout` skill.

**L10 - Plan section per solid.** Cutting a composite piece at half height showed only the chair legs. Rule: on the plan every
solid is cut at half its own height. Applied: `interiors.export()`.

**L11 - Thresholds and rounding.** Access zones drawn 5 mm short of 70 cm came out NON-COMPLIANT. Rule: draw check zones at the
full threshold, not at the limit. Applied: `furnishing` skill.

**L12 - Name filters.** Excluding objects whose name starts with "Floor" from the plan also dropped the floor lamp.
Rule: technical objects excluded by name use an unambiguous prefix (`Slab`, `Tiles_`, `_Track`); after a rename, compare
the plan entity counts with the previous export. Applied: `interiors.export()`.

