# FMEA - failure modes of a furnished layout

Failure Mode and Effects Analysis, as used in manufacturing: for every failure mode, **S** severity (1 cosmetic - 5 unusable
or unsafe), **O** occurrence in past projects and fixtures (1 rare - 5 every project), **D** detection (1 caught by
`verify()` every time - 5 found only by the occupant). **RPN** = S x O x D: the higher, the sooner it needs a better control.
Update after every project using observed defects and test evidence. A new automatic check does not by itself lower
D to 1: confirm that relevant inputs and use registrations exist, a counter-test catches the defect and the workflow
under review actually invokes it. Core parity alone does not prove coverage of imported drawings.

Scores below are the current review priorities, not calibrated probabilities. Retain severity as an independent
priority: a low RPN never excuses a blocking safety failure. Controls apply to the scripted FreeCAD workflow unless
stated otherwise; see the [app coverage matrix](interior-check.md#coverage-and-required-inputs) for import limitations.
Control status includes the local 2026-10-29 engine work under validation, as identified in
[design rules](design-rules.md); it does not certify inclusion in the published installer.

| Id | Element | Failure mode | Effect | S | O | D | RPN | Current control | Action |
|---|---|---|---|---|---|---|---|---|---|
| F01 | Hinged door | leaf hits fixture or furniture | door cannot open | 5 | 4 | 1 | 20 | `Openings` | - |
| F02 | Hinged door | hinge too close to a wall | no jamb, handle hits the wall | 3 | 4 | 1 | 12 | `Handles`, `Reveals` | - |
| F03 | Hinged door | open leaf parks in the room | circulation cut while the door is open | 4 | 2 | 1 | 8 | `Routes` with open leaves | pattern P16 |
| F04 | Window | inward leaf hits tap, hood, wall unit | window cannot open | 3 | 2 | 1 | 6 | `Openings` at sill height | - |
| F05 | Window | wardrobe or tall unit in front of it | lost daylight, unusable window | 3 | 2 | 4 | 24 | review (P08) | candidate check: tall furniture inside the window's daylight zone |
| F06 | Table | chairs against wall or island | cannot stand up | 4 | 3 | 1 | 12 | `Seats` | - |
| F07 | Storage | no space in front of doors/drawers | storage unusable | 4 | 3 | 1 | 12 | `Access zones` | - |
| F08 | Route | small object closes a passage | furniture unreachable | 4 | 2 | 1 | 8 | `Routes` | - |
| F09 | Layout | bathroom reachable only through a bedroom | no privacy for guests | 4 | 2 | 1 | 8 | `Privacy` | - |
| F10 | Layout | WC or bed visible from the entrance, a main seat or a stair arrival | no privacy | 3 | 3 | 3 | 27 | `no_view` when declared | declare `no_view` for WC and bed from the entrance, the main seats and every stair arrival (L25) |
| F11 | Sofa / TV | seats turned away from the TV | living area unusable for watching | 3 | 1 | 4 | 12 | review (P11) | candidate check: TV inside the seats' front cone |
| F12 | Bed | headboard under a window | draught, light, window unusable | 3 | 2 | 4 | 24 | review (P12) | candidate check: headboard within 0.3 m of a window |
| F13 | Programme | required function missing (no dining table, no wardrobe, a bed short of the occupants) | brief not met | 4 | 2 | 4 | 32 | `requirement()` traceability, occupant -> bed table in the brief (L27) | link every brief requirement to the objects that satisfy it; candidate check: `occupants()` against beds and seats |
| F14 | Measures | exactly at the minimum | fails on site with real tolerances | 3 | 3 | 1 | 9 | `Robustness` | - |
| F15 | Tall units | cannot be tilted up in the room | cannot be assembled | 3 | 1 | 1 | 3 | `Assembly` | - |
| F16 | Drawings | door or window not legible on the plan | misread as missing | 2 | 2 | 3 | 12 | `export-autocad` preview | - |
| F17 | Data | dimensions from an unscaled source used as measured | whole layout wrong on site | 5 | 2 | 3 | 30 | brief sources, onboarding step 1 | keep `measured/estimated` tags in the brief |
| F18 | Appliance | fridge, oven, dishwasher door not modelled, or its zone measured from the closed face | kitchen blocked with an appliance open; island aisles that pass on paper | 4 | 3 | 3 | 36 | `hinged` for hinged doors; `appliance_zone()` used by both apartment variants (L17, L29) | baseline example checked; finish Japandi re-verification; migrate imported appliance semantics and prove that path with an open-door counter-test |
| F19 | Bathroom | electrical appliance next to an open shower side | electrical safety | 5 | 1 | 1 | 5 | Safety: `wet_zone` + `electrical` (L18) | - |
| F20 | Layout | lounge seats reachable only along the glazing | lounge awkward to use and clean | 3 | 2 | 3 | 18 | review (P11), `destination` routes measure length | candidate check: route length / straight distance ratio |
| F21 | Kitchen | short landing next to the hob or no bin position | hot pans carried over the route | 3 | 2 | 4 | 24 | review | candidate check: landing >= 40 cm each side of the hob |
| F22 | Layout | bedroom or shared bathroom reached only through a living / family room | the living room becomes a corridor, night trips cross it | 4 | 2 | 4 | 32 | `Privacy: entered from` implemented using the preceding room on the entrance route; review (L23) | validate alternative routes, room kinds and shared versus private bathrooms; review the full layout, not just the sampled route |
| F23 | Layout | service room sized on the leftover, not on its contents | habitable rooms cramped next to an oversized laundry or store | 2 | 1 | 4 | 8 | `Programme`: laundry above 2 x 6 m2 flagged significant; contents review (L24) | validate against the actual laundry programme; this heuristic does not establish a universal maximum area |
| F24 | Programme | room empty, or furnished only with the objects a check needs | dead rooms, no storage, no secondary seats; checks pass | 4 | 3 | 4 | 48 | programme row per room (L26); under-10% habitable occupancy and empty non-habitable rooms (except corridors) now flagged | prove required functions and capacity; occupancy and object count cannot establish programme completeness |
| F25 | Programme | storage, seats or kitchen content below the brief (hanging metres, coat place, pantry, bins, hood) | coats on chairs, winter clothes on another floor, no worktop | 3 | 3 | 4 | 36 | provided-vs-required table in the brief (L27) | candidate check: `storage()` declarations summed against the brief |
| F26 | Process | review verdict resting on an unmodelled element or on a brief rewritten to fit the model | defect accepted on paper, found by the occupant | 4 | 3 | 5 | 60 | pre-mortem step 3, brief change log (L28, L27) | - |

Highest RPN first (RPN >= 27): F26 (60), F24 (48), F18/F25 (36), F13/F22 (32), F17 (30), F10 (27).
F05, F11, F12, F13, F20, F21 and F25 remain candidates for new automatic checks. F18 and F22-F24 have partial controls
with the remaining actions above. Detection scores stay conservative until workflow-specific counter-tests justify
lowering them.
Villa 5 self-review (2026-10-29): F24-F26 raised and F13 occurrence and detection raised, after the user found the floors
under-furnished behind reports at zero.
Pre-mortem 2026-10-27 (apartment-100sqm) raised F18-F21 and initially lowered D for F18 and F19 to 1 with new controls.
F18 is now D=3 after L29 exposed incomplete door-projection coverage; the earlier reduction was not sufficient evidence.
Villa 5 (2026-10-29): user review raised F22 and F23 (accepted by the designer, rejected by the user); layout review
raised O and D of F10 (WC visible from the sofa and from a stair arrival, `no_view` declared only from the entrance).
