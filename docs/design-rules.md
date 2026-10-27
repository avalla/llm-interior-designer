# Design rules

Single source of the thresholds. `lib/interiors.py` (`RULES` dictionary) mirrors them: when a threshold changes here, update it
there too. Each rule separates the **minimum** (below: NON-COMPLIANT), the **comfort** target (below: improvement note) and
the **source**. Regulatory values are indicative (Italian DM 5/7/1975 as reference): on a real project the local building
code and a licensed professional are authoritative.

## Doors and windows

| Rule | Minimum | Comfort | Source | Check |
|---|---|---|---|---|
| Rough opening, internal door | net + 5 cm per side, h 215 | - | subframe installation practice | automatic (opening generated) |
| Rough opening, armored door | net + 7.5 cm per side, h 220 | - | installation practice | automatic |
| Reveal on the hinge side | 10 cm | 15 cm | jamb + handle | automatic |
| Handle with leaf at 90 degrees | 7 cm clear from the wall | - | common handle projection | automatic |
| Leaf / sliding door trajectory | clear of furniture, fixtures, other leaves | - | Astra par. 7 | automatic (3D) |
| Door in a corridor < 1.20 m | prefer a sliding door | - | project experience | manual |
| Rough opening, window | frame + 5 cm per side | - | subframe | automatic |
| Inward window leaf | clear above the sill (taps, hoods, wall units) | - | lesson L07 | automatic (3D) |
| Daylight ratio, habitable rooms | 1/8 of the floor | - | DM 5/7/1975 (indicative) | automatic |
| Bathroom | opening window or mechanical ventilation | - | DM 5/7/1975 (indicative) | automatic / NOT VERIFIABLE |
| Opening > 2.5 m in an external wall | lintel by a structural engineer | - | - | NOT VERIFIABLE |

## Furniture, seats, clearances

| Rule | Minimum | Comfort | Source | Check |
|---|---|---|---|---|
| Surface edge (table, island, desk) -> obstacle behind the seat | 75 cm (stand up) | 90 cm (walk behind a seated person) | common ergonomics | automatic |
| Surface - seat height | 25-32 cm | - | common ergonomics | automatic |
| Route from the entrance to every use zone | continuous 60 cm width | - | Astra par. 21 | automatic (5 cm grid) |
| Main passage | 80 cm | 90 cm | common ergonomics | automatic (per object pair) |
| Kitchen aisle island/base units | 90 cm | 110 cm | common ergonomics | automatic |
| Double bed sides | 60 cm | 70 cm | common ergonomics | automatic |
| Access zone in front of wardrobes and cabinets | 70 cm clear | 90 cm | common ergonomics | automatic |
| Corner between two L-shaped wardrobes | open walk-in or corner unit, no hinged leaves in the corner | - | lesson L01 | manual |
| Hall / corridor | 100 cm | 110 cm | common ergonomics | automatic |
| Floor occupancy, habitable rooms | - | <= 40% | interioragent (VLM target 0.4) | automatic |
| TV relative to windows | not above/in front of/next to one on the same wall (>= 1 m) | side wall >= 1.5 m | Astra par. 11 | automatic |
| Assembly of tall units | diagonal (height x depth) <= room height - 2 cm | - | assembly practice | automatic |

## Minimum areas (reference DM 5/7/1975, indicative)

| Room | Minimum |
|---|---|
| Double bedroom | 14 m2 |
| Single bedroom | 9 m2 |
| Living room | 14 m2 |
| Walk-in closet, hall, utility cupboard | non-habitable: no window required |
