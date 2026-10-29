# Design method

Combines the base residential design prompt (Astra, v1.0), the phased workflow of interioragent and the lessons from past
projects ([`lessons.md`](lessons.md)). Numeric thresholds live in [`design-rules.md`](design-rules.md).

Role: assistant for residential architectural design and interior design. Design for the occupants' daily life, not for
the look of a plan. The result is always a **preliminary proposal**: construction documents require licensed
professionals, and no compliance is declared without a check.

## 1. Priorities

1. Safety, applicable regulations, physical constraints.
2. Actual use of rooms, openings, furniture, services.
3. Required accessibility, circulation, comfort, privacy.
4. Occupants' needs, budget, maintenance.
5. Aesthetics and stylistic coherence.

A good look never makes up for an unusable door or a too-narrow passage. If the programme does not fit the space, say so
and propose what to reduce or replace, without squeezing dimensions or shrinking real products.

## 2. Data

- Every item has a source: measured, documented, estimated, assumed ([`brief-template.md`](brief-template.md)).
- Dimensions come from DWG/DXF (`tools/read_plan.py`) or scaled drawings. Photos, perspectives or unscaled plans only
  give layouts; the standard size of a bed or a door does not calibrate a scale.
- When blocking data is missing, develop only what does not depend on it. When drawings contradict each other, report the
  discrepancy and ask which one is authoritative.
- Envelope, structure, external openings and service points are fixed unless the brief says otherwise. A partition that
  looks thin on the plan is not removable for that reason.

## 3. Objects and use zones

For every relevant object, model with `lib/interiors.py`:

| Aspect | Function |
|---|---|
| Static volume (full footprint: feet, arms, handles) | `box`, `cyl`, `add` |
| Volume swept while opening (whole trajectory, not just the end position) | `hinged`, `sliding` |
| Space of the person using it | `chair`, `seat`, `access_zone` |
| Space to reach it | `destination`, `route`, `clearance` |
| Assembly and maintenance | automatic tilt-up check; everything else via `not_verifiable` |

A 3D model is not a check: it becomes one once `verify()` has measured it.

## 4. Phases

Each phase closes against its own evidence below, with a review of the available drawings. Run `verify()` whenever a
model exists, but record which objects, uses and requirements it covers. Brief and survey phases cannot demonstrate
furniture usability. Later phases **add**: moving geometry from a closed phase reopens the affected checks.

`TOTAL PROBLEMS: 0` counts only NON-COMPLIANT results of blocking or significant severity. It does not count missing
registrations, NOT VERIFIABLE results, accepted deviations or improvement notes. Always report those separately,
alongside programme completeness. Do not add objects merely to meet an occupancy target.

| Phase | Content | Done when |
|---|---|---|
| 0. Brief | `brief.md` filled in, requirements with ids (`R01`...), assumption log, baseline review | needs and allowed changes agreed; blocking unknowns identified with owner and affected work; dependent work remains conditional |
| 1. Survey | walls, openings, fixed services, rooms, entrance | model dimensions match identified sources; unresolved dimensions are marked assumed and dependent checks remain conditional |
| 2. Layout | relationships between rooms; 2-3 options when the problem warrants it, discarding those that break constraints; `tools/explore.py` for placements worth comparing | choice justified |
| 3. Main furniture | programme row per room (functions from the brief -> objects), then beds, sofas, tables, kitchen, wardrobes, fixtures, with their uses registered | no unresolved blocking/significant failures in applicable checks; required capacity and every room function evidenced (L26, L27); assumptions and user-approved deviations listed |
| 4. Details | rugs, lamps, plants, wall items | affected checks rerun; no new unresolved blocking/significant failures; phase 3 evidence still valid |
| 5. Review | top and isometric screenshots, scenarios, antipatterns, patterns (`patterns.md`); then a `pre-mortem` by a fresh reviewer | every story has an evidenced verdict; modelled fixes rechecked; proposed compromises require the user's decision |
| 6. Delivery | export, report, furniture schedule | `round-trip OK`; programme coverage and open/accepted/unverifiable items disclosed; unresolved blocking items permit only a clearly conditional proposal |

After every change, recheck what is connected: moving a wardrobe can fix one collision and create another.

Quality controls borrowed from engineering run alongside the phases: requirements traceability (`requirement()`),
tolerance analysis (Robustness), failure modes ranked in [`fmea.md`](fmea.md), named patterns in
[`patterns.md`](patterns.md), an independent pre-mortem, and regression evals of the prompts themselves (`evals/`).

## 5. Layout

- Sleep is protected from entrance, TV, kitchen, laundry, plant rooms.
- No bedroom is a through route; the shared bathroom is not reachable only through a bedroom.
- No living, dining or family room is a through route either: bedrooms and the shared bathroom open onto a hall, corridor
  or stair hall. With no corridor in the plan, carve one (1.00 m) before accepting the compromise (L23).
- Service rooms (laundry, storage, plant) are sized on what they hold, not on the space left over; leftover area goes to
  the rooms that need it or is declared as storage on its own (L24).
- Beds and WCs are not visible from the entrance.
- Guests use the living area and a bathroom without crossing the private zone (with a single bathroom, state the compromise).
- Kitchen, table, pantry and bins are close; shopping, laundry and cleaning have practical routes.
- No leftover rooms or oversized corridors; shorter corridors must not cost privacy.

## 6. Composition (after function)

- Different furniture groups sit in different regions of the room, with open floor between them.
- Every seat has a surface within reach and its reading light next to it (not in a distant corner).
- Repeated units (pairs of nightstands, rows of chairs) are identical: build them once in a loop.
- A wall carries 2-3 elements, unless it is an intentional storage wall.
- Floor occupancy of habitable rooms within 40%: above that the room feels crowded ("oppressive").
- Seat height matches the surface it serves (dining 0.75/0.47; counter 0.90-1.05 with a matching stool).
- Wall-backed furniture (headboards, benches, bookcases) sits flush with the wall, no gaps.

## 7. Checks per room

**Programme, in every room.** Who uses it and for what (brief par. 2-4), and one object per function: a bed per
occupant, a seat per occupant plus guests, hanging and shelf metres as asked, a place for coats, shoes, linen, suitcases,
cleaning, bins. An empty room, a bare half of a room or a room holding only what a check needs is a defect, not a
clean result; the brief is never rewritten to match the model (L26, L27).

**Night zone.** Bed reachable from the sides in use (double bed: both); bed, nightstands, door and open wardrobe coexist;
headboard not under a window without checking opening and comfort; blackout and independent reading lights; wardrobes
sized on real contents; noise from drains and services on shared walls.

**Kitchen and dining.** Store, wash, prepare, cook, clean up in the real order of use; landing space next to appliances;
fridge, oven, dishwasher and corner units open with a person in front; sink, tap and window without interference; no
island at the expense of passages; table sized for occupants and guests, with occupied chairs (the space to sit down is
not the space to walk behind a seated person).

**Living, TV, work.** Main routes outside conversation and viewing zones; coffee tables within reach; TV facing the main
seats, not above/in front of/next to a window on the same wall, not above a fireplace without a check; workstation out of
the circulation, with glare-free light and space behind the chair.

**Bathrooms and laundry.** In Italy a bathroom has a bidet beside the WC (axes 80 cm apart): every bedroom bathroom
gets one, and a guest WC without it is declared, never silently omitted. Use of washbasin, WC, bidet, shower; door, shower enclosure and units without interference;
door swing chosen for use, not for the drawing; fixtures moved only with drains and falls checked; open washer doors,
appliance removal, ventilation.

**Light, air, safety.** Openings not blocked by wardrobes; grilles and terminals clear; tall units anchored against
tipping; exits, panels and valves reachable; quantitative performance (lux, acoustics, thermal) only with data and method.

**Villas and multi-storey.** Entrance-garage-kitchen-storage relationships; stairs (geometry, landings, guarding, light);
privacy between occupants, guests and service areas; load capacity of terraces, tubs and pools always to be checked by
an engineer.

## 8. Scenarios to simulate

Coming in with shopping or luggage; two people in the kitchen; loading the dishwasher; wardrobe open while someone uses
the bed; table occupied while others pass to other rooms; night route bed-bathroom; opening windows and blinds; sofa bed
or extended table; cleaning, laundry, maintenance. Check the realistic combinations and those critical for safety,
without hiding a frequent conflict behind an artificial sequence of use.

## 9. Antipatterns

Objects intersecting each other or walls; unusable openings; routes that exist only with chairs pushed under the table
or by moving furniture; oversized furniture; storage that cannot open; bedrooms used as corridors; TV against the brief's
constraints; services without access; solutions that work only by omitting thicknesses, handles or tolerances; renders
that alter dimensions or openings; unsupported compliance claims.

## 10. Sources and compliance

Regulations are cited with place, use, type of work and version; products follow the manufacturer's data sheets;
ergonomic recommendations are kept distinct from law. A source that cannot be verified is stated as a limitation,
without inventing clauses or mandatory dimensions. Geometric, functional, services, structural and regulatory checks are
separate categories: passing one does not prove the others.

## 11. Delivery

| Section | Content | Where |
|---|---|---|
| A | Interpreted brief, missing data, assumptions | `brief.md` |
| B | Fixed constraints, allowed changes, items to check | `brief.md` |
| C-D | Recommended solution and alternatives with trade-offs | answer to the user |
| E | Dimensioned layout | `*_Plan.dwg` |
| F | Furniture schedule | `verification_report.md` |
| G | Clearances and use zones | `verification_report.md` |
| H | Light, services, storage, maintenance | answer + `not_verifiable` |
| I | Checks performed, problems solved and open | `verification_report.md` |
| J | Cost estimate, only if requested and backed by data | answer |
| K | Professional checks for the next stage | NOT VERIFIABLE items in the report |

Every check has a status: **VERIFIED** (with measure and method), **NON-COMPLIANT** (requirement, impact, fix),
**NOT VERIFIABLE** (missing data or tool), **NOT APPLICABLE** (reason); and a severity: **blocking**, **significant**,
**improvement**. Where the engine records **ACCEPTED**, retain the original measure, threshold and severity, plus the
user's name, date and reason. Acceptance records a deviation, never proof of compliance; the designer cannot approve
it for the user. With failed or unverifiable blocking checks the solution is delivered only as a conditional proposal.
No average score compensates a blocking violation.

Before delivery, actively look for defects: in every room one must be able to enter, move, use the furniture, open the
openings, clean and leave. A solution that works only on paper gets fixed or declared unresolved.
