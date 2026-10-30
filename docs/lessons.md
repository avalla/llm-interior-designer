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

**L22 - Do not switch a check off to silence a drawing convention.** The 2D import skipped every furniture/furniture
collision because a plan draws chairs under the table; on the shifted-furniture mutants that hid 12 real collisions
(armchair into the floor lamp, hung items into walls). Rule: list the overlaps that are drawn on purpose (type pairs,
`STACKS`) and keep checking the rest; give hung items their height band instead of dropping them. Same family: a
generated destination must sit on the route grid as the grid sees obstacles (square inflation), or the check reports
the point, not the layout. Applied: `app/semantics/library.py`, `geometry()` in `app/core/interiors_core/checks.py`.

**L23 - A living room is not a corridor.** In a semi-basement the bathroom and a bedroom opened onto the family room:
every night trip to the WC (8.2 m) and every visit to that bedroom crossed the room where a guest sleeps on the sofa
bed. The pre-mortem flagged it and the designer accepted it as a compromise; the user rejected it. Rule: bedrooms and
the shared bathroom open onto circulation (hall, corridor, stair hall), never through a living, dining or family room;
when the plan offers no corridor, carve one (1.00 m) before accepting the compromise, and state what it costs.
Applied: `docs/method.md` par. 5, FMEA F22, `Privacy: entered from` check (room kinds) in `lib/interiors.py`,
fixtures A, B and C.

**L24 - Size service rooms on their contents, not on the leftover.** A blind room that could not host a habitable room
became a 31 m2 laundry while the family room next to it had 15.6 m2: the whole leftover went to a function that needs
6-8 m2. Rule: size laundry, storage and plant rooms on what they hold; give the rest to the rooms that need it (or
declare it as storage on its own), and compare service and habitable areas before closing the layout. Applied:
`docs/method.md` par. 5, `docs/design-rules.md` (minimum areas), FMEA F23, `Programme: area` check (`service_area`),
fixture C.

**L25 - Look from where people sit and arrive, not only from the front door.** The WC was visible from the sofa through
the open bathroom door, and from a stair arrival: `verify()` passed because `no_view` was declared only from the entrance
of each floor (layout review). Rule: declare `no_view` for WC and beds also from the main seats (sofa, table) and from
every stair arrival. Applied: `intimate()` + `viewpoint()` in `lib/interiors.py` (every `seat()` and the entrance are
viewpoints by themselves), `AGENTS.md` conventions, FMEA F10, fixture C.

**L26 - Zero problems is a gate, not the finish.** Three floors reached `TOTAL PROBLEMS: 0` with rooms furnished only with
what a check needs (bed, wardrobe, sofa, TV, fixtures) and nothing of what the occupants need: an empty 3.3 m2 store, an
empty 11.5 m2 stair hall, 27 m2 of empty floor in the laundry, half of the living room bare, no desk, no chest of
drawers, no coat storage, a 3.1 m kitchen without wall units or pantry. The checks only see what is modelled, so a room
with little in it passes everything. Rule: before furniture goes in, write the room's programme row (functions from
brief par. 2-4: sleep, store N m, study, sit N, cook, eat N, dry, clean) and give every function an object; a room with
no object, or only with check-driven objects, is a defect to report; floor occupancy has a lower bound to look at as
well as the 40% upper bound. Applied: `furnishing` skill steps 2 and 4, method par. 4 and 7, FMEA F24, `occupancy_min`
and `Programme: contents` checks, fixture C.

**L27 - Count the beds, the seats and the metres, and never bend the brief to the model.** The brief said two children in
the semi-basement; the model gave them one double and one single bed, and the brief's "Sleep" row was then rewritten to
match the model. Storage: 1.35 m of 45 cm wardrobe against 2.0 m of hanging asked; no linen, suitcase or coat storage
anywhere. Rule: the brief holds a table occupant -> bed -> room, seats (living and dining) against occupants plus guests,
and storage provided against required; each row is a `requirement()` linked to the objects that satisfy it; the brief
is changed only with the user, and the change is logged. Applied: `project-onboarding` and `furnishing` skills, FMEA F13,
F25.

**L28 - A verdict may not rest on what is not drawn.** The pre-mortem triage closed stories with an under-stair closet
that exists in neither the model nor the brief, with "pull-out rails", a "folding chair" and "specify sliding doors",
and marked 16 of 37 stories "founded but accepted"; the user rejected the first one they read. Rule: a fix that is an
object gets modelled before the verdict; a fix that is a specification becomes a `not_verifiable()` or a plan label;
"founded but accepted" is a proposal to the user, who decides, never a verdict the designer gives on their behalf.
Applied: `pre-mortem` skill step 3, FMEA F26, `accepted()` and the ACCEPTED status in `lib/interiors.py` (a stale
acceptance is reported), `requirement(manual="reviews/...")` resolved at verification, fixture C.

**L29 - An appliance zone is the open door plus the person.** Dishwasher, oven and fridge zones were drawn 70 cm deep
from the closed unit's face; a 0.96 m aisle to an island passed every check while a dishwasher door down (60 cm) left
36 cm to stand in (two reviewers found it: Codex review 09, pre-mortem S29). Rule: for drop-down and pull-out doors
(dishwasher, oven, drawers) the `access_zone` depth is the door's projection plus 70 cm, measured from the unit's face
(dishwasher 1.30, oven 1.20); for hinged doors (fridge, cabinets) the leaf is a `hinged()` and the zone stays 70 cm.
Correction status (2026-10-29): `appliance_zone()` now includes the projection plus the person, and
`projects/apartment-100sqm/project.py` uses it for the dishwasher and oven. The headless baseline run on that date
reports zero blocking/significant failures for that example. The Japandi variant was also migrated to the helper in
concurrent layout work, but its complete re-verification is separate. Remaining coverage gap: imported-plan semantics
still generate generic 70 cm appliance zones. That path is not covered by the example correction. Later the same day
the helper caught two more: the oven zone against the island in `apartment-100sqm` (island shortened and moved, table
5 cm east) and the dishwasher in the 1.20 m galley of `apartment-100sqm-japandi` (peninsula moved 15 cm south,
dishwasher next to the sink in the north run); both re-verified at zero.
Applied: `appliance_zone(kind=)` with the projections in `RULES` (`appliance_door`), `docs/design-rules.md` DR25/DR40,
FMEA F18, `furnishing` skill step 2, fixture C (C3).
