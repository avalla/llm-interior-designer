# Brief - Apartment 100 m2

Demonstration project developed in conversation: no real survey. Every dimension is `assumed` unless stated otherwise.

## Scope

| Item | Value | Source |
|---|---|---|
| Building type | single-floor apartment, 12.5 x 8.0 m gross (100 m2) | assumed |
| Type of work | new internal layout + furnishing | assumed |
| Allowed changes | partitions and internal doors free; envelope and windows fixed | assumed |
| Starting files | none | - |
| Clear height | 2.70 m | assumed |
| Orientation | glazing to the south (y = 0), entrance and services to the north | assumed |

## Requirements (ids traced in project.py and in the verification report)

| Id | Requirement | Priority | Source |
|---|---|---|---|
| R01 | Bathroom, kitchen, bedroom, wardrobe, hall | essential | initial request |
| R02 | Doors open without hitting fixtures or furniture | essential | initial request |
| R03 | Entrance open to the living area | essential | user review |
| R04 | Night zone closed by a door | essential | user review |
| R05 | Rooms that do not feel oppressive | essential | initial request |
| R06 | Modern style | essential | initial request |
| R07 | TV not above, in front of or next to a window on the same wall | essential | base design prompt |
| R08 | Daylight in habitable rooms | essential | regulations (indicative) |

## Assumption log and open points

| # | Assumption or missing data | Impact if wrong | Status |
|---|---|---|---|
| 1 | Living/entrance partition removable and not load-bearing | entrance layout to be redone | to confirm (structural engineer) |
| 2 | Soil stacks compatible with bathroom and kitchen on the north side | fixtures to be moved | to confirm (services engineer) |
| 3 | 4.60 m window rough opening: lintel feasible | smaller window | to confirm (structural engineer) |
| 4 | Occupants: 2 adults, no mobility needs | accessibility dimensions | to confirm |
| 5 | Furniture footprints are indicative | collisions with real products | replace with product data sheets |
| 6 | Lounge layout: sofa and armchair reachable only along the glazing (pre-mortem S12-S14) | lounge awkward to use and clean | open: Q01 (variants A-C in `output/variants.md`) |
| 7 | Single bathroom inside the night zone; second WC? (S17) | guests cross the night zone | open: Q02 |
| 8 | Laundry drying space (S23) | drying rack in the living area | open: Q03 |
| 9 | Desk orientation, work from home (S26) | glare, posture | open: Q04 |
| 10 | Bin position in the kitchen (S08) | waste in the way | open: Q05 |

## Questions for the client

Each answer becomes a requirement (`Rnn`) or closes an assumption above; the options are those that fit the current plan,
with what each one costs. Measures come from the model (`project.py`, report of 2026-10-28) unless marked "estimated".

| Id | Question | Options and impact | Default if unanswered |
|---|---|---|---|
| Q01 | How do you use the lounge: mostly TV, mostly conversation and reading, or both? Do you want to keep the armchair? | L0 (current): L sofa, armchair 12 cm from the glass, sofa reached only along the glazing (12.1 m route). A: straight sofa, armchair by the window facing north (80 cm from the glass), 64 degrees off the TV. B: chaise towards the window, armchair facing the sofa from the north-west; glazing strip free for 1.00 m, armchair not a TV seat. C: as B with a straight sofa 20 cm nearer the TV (3.29 m), 1.65 m passage behind the sofa. | B |
| Q02 | Do guests stay overnight or visit often? Would you give up part of the walk-in closet or the night-hall end for a second WC? | The only space without moving the bathroom is the night-hall end east of the bathroom door (x 9.10-11.75, about 2.9 m2, S18), soil connection to be checked (assumption 2); a WC with a 60 cm basin needs about 0.9 x 1.5 m plus its door (estimated). Cost: utility cupboard and part of the closet; still inside the night zone, so it solves the morning queue, not the guest crossing the night zone. A WC by the entrance would mean moving the entrance wardrobe and a new soil connection (services engineer). | single bathroom, compromise stated in the report |
| Q03 | Where do you dry laundry today? Would you accept a washer-dryer? | (a) washer-dryer in place of the washing machine: no rack needed; (b) ceiling pulley airer over the bathroom's free floor (about 1.15 x 1.85 m, S23) with mechanical extraction; (c) folding rack stored in the utility cupboard and opened in the bedroom or night hall (1.10 m wide hall: blocks it while open). | (a) |
| Q04 | Does anyone work from home, how many hours a week, with one or two screens? | Today the desk faces the west partition with the French window behind the user (reflections, S26). Move the desk to the south wall west of the French window (x 6.60-8.00, estimated): window at 90 degrees on the left, no glare, to be verified in the model; or work at the dining table (no dedicated place). | desk moved to the south wall |
| Q05 | How many waste fractions does your municipality collect (e.g. 3-4 with organic)? | Pull-out sorting bin under the sink (x 1.90-2.70), which needs the same 70 cm open zone in the 95 cm aisle as the dishwasher (to be modelled as an access zone); a fourth fraction needs a second 30-40 cm pull-out or a cupboard by the entrance. | 3-compartment pull-out under the sink |
