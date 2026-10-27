# FMEA - failure modes of a furnished layout

Failure Mode and Effects Analysis, as used in manufacturing: for every failure mode, **S** severity (1 cosmetic - 5 unusable
or unsafe), **O** occurrence in past projects and fixtures (1 rare - 5 every project), **D** detection (1 caught by
`verify()` every time - 5 found only by the occupant). **RPN** = S x O x D: the higher, the sooner it needs a better control.
Update after every project: a defect found by the user raises O and D; a new automatic check lowers D to 1.

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
| F10 | Layout | WC or bed visible from the entrance | no privacy | 3 | 2 | 2 | 12 | `no_view` when declared | declare `no_view` for WC and bed in every project |
| F11 | Sofa / TV | seats turned away from the TV | living area unusable for watching | 3 | 1 | 4 | 12 | review (P11) | candidate check: TV inside the seats' front cone |
| F12 | Bed | headboard under a window | draught, light, window unusable | 3 | 2 | 4 | 24 | review (P12) | candidate check: headboard within 0.3 m of a window |
| F13 | Programme | required function missing (no dining table, no wardrobe) | brief not met | 4 | 1 | 3 | 12 | `requirement()` traceability | link every brief requirement to a check |
| F14 | Measures | exactly at the minimum | fails on site with real tolerances | 3 | 3 | 1 | 9 | `Robustness` | - |
| F15 | Tall units | cannot be tilted up in the room | cannot be assembled | 3 | 1 | 1 | 3 | `Assembly` | - |
| F16 | Drawings | door or window not legible on the plan | misread as missing | 2 | 2 | 3 | 12 | `export-autocad` preview | - |
| F17 | Data | dimensions from an unscaled source used as measured | whole layout wrong on site | 5 | 2 | 3 | 30 | brief sources, onboarding step 1 | keep `measured/estimated` tags in the brief |
| F18 | Appliance | fridge, oven, dishwasher door not modelled | kitchen blocked with an appliance open | 4 | 3 | 1 | 12 | `hinged`/`access_zone` on appliances (L17) | - |
| F19 | Bathroom | electrical appliance next to an open shower side | electrical safety | 5 | 1 | 1 | 5 | Safety: `wet_zone` + `electrical` (L18) | - |
| F20 | Layout | lounge seats reachable only along the glazing | lounge awkward to use and clean | 3 | 2 | 3 | 18 | review (P11), `destination` routes measure length | candidate check: route length / straight distance ratio |
| F21 | Kitchen | short landing next to the hob or no bin position | hot pans carried over the route | 3 | 2 | 4 | 24 | review | candidate check: landing >= 40 cm each side of the hob |

Highest RPN first: F17, F05, F12, F21 are the current priorities; F05, F11, F12, F20 and F21 have a candidate automatic check.
Pre-mortem 2026-10-27 (apartment-100sqm) raised F18-F21 and lowered D for F18 and F19 to 1 with new controls.
