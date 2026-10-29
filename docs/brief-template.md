# Brief - <project name>

Every item carries its **source**: `measured` (survey / dimension in a DWG), `documented` (scaled drawing, product data sheet),
`estimated` (from photos or proportions), `assumed` (default choice to be confirmed). Only `measured` and `documented`
support a dimensional check.

## 1. Scope

| Item | Value | Source |
|---|---|---|
| Location (municipality) | | |
| Building type, floor, lift (car size) | | |
| Type of work: furnishing only / internal reorganisation / renovation / new build | | |
| Allowed changes: partitions, doors, windows, services, facade | | |
| Starting files (DWG/DXF/PDF/photos/survey) and their reliability | | |
| Scale, units, origin, north | | |
| Clear heights, false ceilings, beams, columns, out-of-square walls | | |

## 2. Occupants and use

| Item | Value | Source |
|---|---|---|
| Number, age, relevant body size | | |
| Mobility or sensory needs, future accessibility | | |
| Pets, regular guests (how many, how often, where they sleep) | | |
| Working from home (permanent or occasional desk, video calls) | | |
| Kitchen: how much and how people cook, how many cook together, dishwasher, pantry, recycling | | |
| Meals: everyday seats / seats with guests, extending table | | |
| Sleep: bed side, blackout, reading lights, TV in the bedroom yes/no | | |
| Entertainment: TV (inches), projector, music, games | | |
| Laundry: washer, dryer, drying rack, detergent storage | | |

## 3. Programme

| Requirement id | Room / activity | Essential or desirable | Required quantity / acceptance criterion | Objects providing it | Check or manual evidence | Status |
|---|---|---|---|---|---|---|
| R01 | | | | | | open |

Keep requirement ids stable. Register each as `requirement()` in the project, link the objects with `satisfied_by`
and the relevant checks with `verified_by`, or identify the manual review evidence. An object link alone does not
prove capacity. A missing object or unverified function stays open; do not change the requirement to fit the model.

### Sleeping allocation

| Requirement id | Occupant / guest scenario | Bed object | Room | Required / provided sleeping places | Source | Status |
|---|---|---|---|---|---|---|
| | | | | | | |

### Seating capacity

| Requirement id | Living / dining / work | Everyday required / provided | With guests required / provided | Objects and deployed configuration | Evidence / source | Status |
|---|---|---|---|---|---|---|
| | | | | | | |

Check occupied seats and extended or folding furniture in the configuration used for the claimed capacity.

## 4. Storage

| Requirement id | Category | Required quantity and unit | Provided usable capacity | Objects / room | Evidence / source | Status |
|---|---|---|---|---|---|---|
| | Long / short hanging clothes | | | | | |
| | Linen, shoes, suitcases | | | | | |
| | Cleaning, tools, supplies | | | | | |
| | Coats, pantry, bins | | | | | |

Compare like units (hanging metres, shelf metres, pairs, volumes). External cabinet width alone does not prove usable
hanging capacity; record internal dimensions and the chosen storage arrangement.

## 5. Style and products

| Item | Value |
|---|---|
| Furnishing style (e.g. modern, Scandinavian, japandi, industrial, contemporary classic, mid-century) | |
| Palette, materials, finishes, references (photos, links) | |
| Furniture to keep (with real dimensions) | |
| Products already chosen (with data sheet) | |
| Desired feel (e.g. "not oppressive", cosy, essential) | |

## 6. Constraints

| Item | Value |
|---|---|
| Fixed services: soil stacks, electrical panel, boiler, radiators/split units, existing sockets | |
| Orientation, views, noise, privacy from outside | |
| Explicitly forbidden elements (e.g. TV next to windows) | |
| Budget (furniture / works / services) and timing | |

## 7. Deliverables

| Item | Value |
|---|---|
| Formats: 2D DWG, 3D DWG, STEP, PNG, verification report, furniture schedule | |
| AutoCAD version (Windows / Mac / LT) | |

## Assumption log and open points

| # | Assumption or missing data | Source / evidence | Affected requirements and checks | Impact if wrong | Owner / confirmation needed by | Status (to confirm / confirmed) |
|---|---|---|---|---|---|---|

## Approved changes and compromises

| Date | Requirement / finding id | Previous requirement or measured failure | Proposed change and consequences | Approved by / evidence | Follow-up verification |
|---|---|---|---|---|---|

Only record approval actually received from the user. Proposed compromises remain open until then. An accepted
deviation remains visible with its measure, severity and reason; acceptance does not turn it into a passed check or
override a statutory requirement. Keep failed or unverifiable blocking items explicit in any conditional proposal.
