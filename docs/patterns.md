# Pattern language

Named design patterns used as **leading words** when designing and reviewing: one name recalls a whole problem and its
solution. Numbered `Pnn`, stable ids. Patterns marked APL come from C. Alexander et al., *A Pattern Language* (1977),
with the book's number; the others come from this project's lessons ([`lessons.md`](lessons.md)).

Each pattern: the problem it prevents, the rule, how it is checked (automatic check in `verify()` or review judgement).

| Id | Pattern | Problem | Rule | Check |
|---|---|---|---|---|
| P01 | **Entrance transition** (APL 112) | arriving straight into the room, no threshold | a short transition between front door and living space: change of floor, light, or a screening wardrobe | review |
| P02 | **Intimacy gradient** (APL 127) | private rooms exposed to guests | public -> semi-private -> private in that order from the entrance; bedrooms deepest | `private_room` + review |
| P03 | **Entrance room** (APL 130) | nowhere to drop coats, keys, shoes | storage and a landing surface within two steps of the front door | `access_zone` on the entrance wardrobe |
| P04 | **Indoor sunlight** (APL 128) | living rooms in shade, service rooms in sun | living spaces on the sunny side, services on the shaded side | review (orientation in the brief) |
| P05 | **Sleeping to the east** (APL 138) | bedrooms that are dark in the morning or hot in the evening | bedrooms towards morning light where climate and noise allow; never imposed universally (method par. 5) | review |
| P06 | **Farmhouse kitchen** (APL 139) | cook isolated from the household | kitchen open to the place where people eat and gather, if the brief accepts cooking smells | review |
| P07 | **Sequence of sitting spaces** (APL 142) | one kind of seat everywhere | a range of seats: sofa, reading chair, dining chairs, stools, each in its own place | review |
| P08 | **Light on two sides of every room** (APL 159) | gloomy rooms with glare from a single window | habitable rooms with daylight from two sides where the envelope allows; never block a window with furniture | `Light and air` + review |
| P09 | **Window place** (APL 180) | windows that nobody uses | a seat or a work surface by the main window of a room | review |
| P10 | **Eating atmosphere** (APL 182) | table lost in the room, harsh light | a defined dining place with a pendant light over the table and walls or furniture around it | review |
| P11 | **Sitting circle** (APL 185) | seats facing a wall or turned away from each other | seats facing each other around a centre (table, TV), out of the main route | review; `tv` for the TV |
| P12 | **Bed alcove / bed against a solid wall** (APL 188) | bed exposed, headboard under a window or on the route | headboard against a solid wall, not under a window, not visible from the entrance | review |
| P13 | **Closets between rooms** (APL 198) | thin partitions carrying noise and wasted wall depth | wardrobes as acoustic buffers between bedroom and noisy rooms | review |
| P14 | **Pools of light** (APL 252) | uniform flat lighting | light where activities happen: over the table, by the reading chair, at the desk | review (pendants, lamps registered) |
| P15 | **Reading light with its seat** | lamp in a corner blocking access (L06) | every seat has its surface and light next to it, outside the routes | `destination` routes |
| P16 | **Leaf against the wall** | open door leaf parked in the room cuts the circulation (L15) | hinge on the side of the nearest wall, so the open leaf rests against it | `Routes` (open leaves are obstacles) |
| P17 | **Slide in the narrow** | a hinged door filling a corridor or a corner (L01, L02) | sliding doors in corridors under 1.20 m and in corners | `Openings`, `Handles` |
| P18 | **TV across from the window** | glare and reflections on the screen | TV on a wall perpendicular to or opposite the window, never next to it on the same wall | `Brief constraints` |

When a review finding matches a pattern, cite it by id and name (e.g. "P12 Bed alcove: headboard under the window").
