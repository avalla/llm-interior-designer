# Design rules

Human-readable catalogue of design defaults. Runtime values are mirrored in `lib/interiors.py` and
`app/core/interiors_core/rules.py`; update all three together. `app/tests/parity.py` checks the two runtime dictionaries,
not this document. Stable `DRnn` ids must not be renumbered or reused.

Implementation snapshot: this audit includes local engine work under validation on 2026-10-29. The occupancy lower
bound, programme screening, grouped viewpoints, `appliance_zone()` and rule-dictionary parity guard belong to that
work; this documentation-only change does not ship them. Check the source revision before relying on those controls.

## Applicability and evidence

- **Reference**: an indicative regulatory reference; establish jurisdiction, use, work type and current applicability
  for each project. This catalogue is not a legal compliance assessment.
- **Ergonomic**: a use/clearance default, checked against occupants and actual products.
- **Physical**: geometric operability, such as a moving leaf remaining clear of obstacles.
- **Installation**: a construction/product assumption, replaced by the chosen manufacturer's data.
- **Heuristic**: a project preference or screening rule. Compare flags with the brief and evidence; they do not prove
  a universal prohibition or a need for more furniture.
- **Professional**: evidence outside the geometric engine is required.

“Automatic” means the scripted engine can check registered geometry/uses, not that every imported drawing supplies
them; see the [coverage matrix](interior-check.md#coverage-and-required-inputs). Report status, severity and method
separately. A comfort target may be guidance only; not every minimum is a statutory requirement. Record proposed
deviations in the brief with impact, evidence and the user's decision. Statutory requirements cannot be waived through
a project acceptance.

Source labels retain historical provenance: “Astra par.” is the project's base prompt, not a regulation; “common
ergonomics” and “installation practice” are currently uncited defaults. For real specifications, replace them with a
traceable edition/page or product sheet. Lnn references are in [lessons](lessons.md), Pnn in [patterns](patterns.md).
The 40% target comes from [interioragent](https://github.com/KunalMGupta/interioragent); it is a heuristic, not a proven
universal comfort limit. DM 5/7/1975 references have not been revalidated for current local applicability in this revision.

## Doors and windows

| Id | Nature | Rule | Minimum | Comfort | Source | Check |
|---|---|---|---|---|---|---|
| DR01 | Installation | Rough opening, internal door | net + 5 cm per side, h 215 | - | subframe installation practice | automatic (opening generated) |
| DR02 | Installation | Rough opening, armored door | net + 7.5 cm per side, h 220 | - | installation practice | automatic |
| DR03 | Installation | Reveal on the hinge side | 10 cm | 15 cm | jamb + handle | automatic |
| DR04 | Installation | Handle with leaf at 90 degrees | 7 cm clear from the wall | - | common handle projection | automatic |
| DR05 | Physical | Leaf / sliding door trajectory | clear of furniture, fixtures, other leaves | - | Astra par. 7 | automatic (3D) |
| DR06 | Heuristic | Door in a corridor < 1.20 m | prefer a sliding door | - | project experience | manual |
| DR07 | Installation | Rough opening, window | frame + 5 cm per side | - | subframe | automatic |
| DR08 | Physical | Inward window leaf | clear above the sill (taps, hoods, wall units) | - | lesson L07 | automatic (3D) |
| DR09 | Reference | Daylight ratio, habitable rooms | 1/8 of the floor | - | DM 5/7/1975 (indicative) | automatic |
| DR10 | Reference | Bathroom | opening window or mechanical ventilation | - | DM 5/7/1975 (indicative) | automatic / NOT VERIFIABLE |
| DR11 | Professional | Opening > 2.5 m in an external wall | lintel by a structural engineer | - | - | NOT VERIFIABLE |

## Furniture, seats, clearances

| Id | Nature | Rule | Minimum | Comfort | Source | Check |
|---|---|---|---|---|---|---|
| DR12 | Ergonomic | Surface edge (table, island, desk) -> obstacle behind the seat | 75 cm (stand up) | 90 cm (walk behind a seated person) | common ergonomics | automatic |
| DR13 | Ergonomic | Surface - seat height | 25-32 cm | - | common ergonomics | automatic |
| DR14 | Ergonomic | Route from the entrance to every use zone | continuous 60 cm width | - | Astra par. 21 | automatic (5 cm grid) |
| DR15 | Ergonomic | Main passage | 80 cm | 90 cm | common ergonomics | automatic (per object pair) |
| DR16 | Ergonomic | Kitchen aisle island/base units | 90 cm | 110 cm | common ergonomics | automatic |
| DR17 | Ergonomic | Double bed sides | 60 cm | 70 cm | common ergonomics | automatic |
| DR18 | Ergonomic | Access zone in front of wardrobes and cabinets | 70 cm clear | 90 cm | common ergonomics | automatic |
| DR19 | Heuristic | Corner between two L-shaped wardrobes | open walk-in or corner unit, no hinged leaves in the corner | - | lesson L01 | manual |
| DR20 | Ergonomic | Hall / corridor | 100 cm | 110 cm | common ergonomics | automatic |
| DR21 | Heuristic | Floor occupancy, habitable rooms | below 10% prompts programme review | <= 40% | L26; interioragent (VLM target 0.4) | automatic: below 10% NON-COMPLIANT/significant; above 40% VERIFIED/improvement |
| DR22 | Heuristic | TV relative to windows | not above/in front of/next to one on the same wall (>= 1 m) | side wall >= 1.5 m | Astra par. 11 | automatic |
| DR23 | Installation | Assembly of tall units | diagonal (height x depth) <= room height - 2 cm | - | assembly practice | automatic |
| DR24 | Installation | Placement tolerance | every measure >= minimum + 2 x 2 cm | - | survey and installation tolerances (Astra par. 15) | automatic (Robustness) |
| DR25 | Ergonomic | Appliance doors (fridge, oven, dishwasher) | 70 cm clear with the door open: drop-down and pull-out doors -> zone depth = door projection + 70 (dishwasher 60 + 70 = 130, oven 50 + 70 = 120); hinged doors -> `hinged()` leaf + 70 cm zone (L29) | 90 cm beyond the door | common ergonomics | automatic (access zones, depth declared) |
| DR26 | Ergonomic | Hob landing | 40 cm each side | 55 cm | common ergonomics | manual (F21) |
| DR27 | Ergonomic | WC / bidet axes | 80 cm between axes, 40 cm from axis to wall | - | common ergonomics | manual |
| DR28 | Ergonomic | Shower or bath open side | 60 cm splash zone free of electrical items | - | electrical safety practice (check local code) | automatic (Safety) |
| DR29 | Heuristic | Shared destinations | reachable without crossing a private room | - | Astra par. 6, pattern P02 | automatic (Privacy) |
| DR30 | Heuristic | WC and bed from entrance, main seats and stair arrivals | not visible with doors open | - | Astra par. 6; L25 | automatic for declared `no_view`, or `intimate` objects and `viewpoint` observers; seating registrations add observers |

## Room programme and areas

| Id | Nature | Room | Requirement / screening target |
|---|---|---|---|
| DR31 | Reference | Double bedroom | 14 m2 |
| DR32 | Reference | Single bedroom | 9 m2 |
| DR33 | Reference | Living room | 14 m2 |
| DR34 | Reference | Walk-in closet, hall, utility cupboard | non-habitable: no window required |
| DR35 | Heuristic | Laundry room | size from contents; planning range 4-8 m2 (L24). Engine reference 6 m2 x factor 2: above 12 m2 is NON-COMPLIANT/significant, pending programme review |
| DR36 | Heuristic | Night corridor / hall | 1.00 m wide (comfort 1.10): bedrooms and the shared bathroom open onto it, not onto a living room (L23) |

## Additional implemented controls and parameters

| Id | Nature | Rule / parameter | Runtime behaviour and limit |
|---|---|---|---|
| DR37 | Heuristic | Non-habitable room contents | At least one registered object by centre point, except corridors; empty rooms are NON-COMPLIANT/significant. Object count does not prove usefulness or capacity (L26) |
| DR38 | Heuristic | Observer eye height | Standing 1.60 m, seated 1.15 m; defaults for declared viewpoints, not occupant-specific measurements |
| DR39 | Heuristic | Privacy circulation | Bedrooms and bathrooms: preceding room on a sampled entrance route must not be living/dining/kitchen; failure is significant. Review alternate routes and bathroom scope manually (L23) |
| DR40 | Installation | Appliance door projection | Default dishwasher 0.60 m, oven/drawer 0.50 m; `appliance_zone()` adds the 0.70 m person zone. Actual product projection takes precedence (L29) |

Geometry uses a 5 cm route grid and a 1000 mm3 intersection-volume tolerance (`tol`). These are numerical method
parameters, not placement allowances or proof of accessibility. Placement robustness uses 2 cm per element (4 cm
combined). Minimum-area failures are currently significant; daylight failures are blocking. Other severities depend
on the check and are available in the report. Numeric screening does not replace the required/provided tables in the
[brief](brief-template.md).
