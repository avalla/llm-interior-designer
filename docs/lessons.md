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

**L13 - Broken links are silent.** Requirements R03/R04 pointed to object names that did not exist (`Door_Entrance` instead of
`Door_Entrance_Leaf`): without a check, the trace would have looked complete. Rule: every `requirement()` link is resolved
at verification time; a missing object is blocking. Applied: Requirements check.

**L14 - Measure against others, not yourself.** The robustness margin of a wardrobe leaf was 0 cm from its own wardrobe body.
Rule: a leaf declares its owner (`hinged(..., own=item)`) and margins ignore it. Applied: Robustness check.

**L15 - An open leaf is furniture.** In an eval fixture the entrance leaf, open at 90 degrees, parked in the middle of the room
and cut the only passage. Rule: hinge on the side of the nearest wall so the leaf rests against it (P16); routes treat open
leaves as obstacles. Applied: Routes check, pattern P16.

**L16 - Fixtures fail only for planted defects.** The first eval fixtures failed for unplanned reasons (cramped table and
island, wrong target point), which hid one planted defect. Rule: an eval run must show an empty "Unexpected NON-COMPLIANT"
table before its recall means anything. Applied: `evals/run_engine.py`, skill `prompt-evals`.

**L17 - Unmodelled is unchecked.** The fridge door, the oven and the dishwasher were not in the model, so R02 ("doors open
without hitting anything") passed while the kitchen could not be used with an appliance open (pre-mortem S07, S08).
Rule: every appliance with a door gets a `hinged()` leaf or an `access_zone()` with the person in front.
Applied: `furnishing` skill step 2, example project.

**L18 - Water and power.** A shower with an open side stood 20 cm from the washing machine: no collision, a safety
violation (pre-mortem S20, the only blocking story). Rule: declare `electrical()` items and a `wet_zone()` on every open
side of a shower or bath. Applied: Safety check, counter-test on the old layout.

**L19 - The designer's review is not enough.** After `verify()` at zero and three user reviews, a fresh reviewer still
found 1 blocking and 14 significant stories (pre-mortem 2026-10-27). Rule: the `pre-mortem` skill is mandatory before
delivery, and its founded stories feed lessons, FMEA and checks. Applied: `furnishing` skill step 7.

**L20 - Say what "depth" means.** A 60 cm wide fridge zone was read as 60 cm deep (shorter side). Rule: `access_zone(...,
depth=)` when the zone is narrower than it is deep. Applied: `access_zone()`.

**L21 - A boolean that returns nothing is not "no collision".** FreeCAD's `common()` between a shape and a compound of
touching solids (bookcase, chairs) returns an empty shape: a bookcase pushed 20 cm into a partition and into the open
night-zone sliding door gave 0 cm3 instead of 54000 and 3068. Found by the 2.5D port's parity run on shifted furniture
(`app/tests/parity.py`). Rule: intersect solid by solid; test checks on deliberately broken layouts, not only on clean
ones. Applied: `_common()` / `_vol()` in `lib/interiors.py`; mutants in `app/tools/export_model.py`.
