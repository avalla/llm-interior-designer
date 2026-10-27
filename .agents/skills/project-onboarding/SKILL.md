---
name: project-onboarding
description: Starts a new furnishing or interior layout project: collects starting files, type of work, occupants, furnishing style and constraints, fills in the brief with traceable requirements, surveys the plan into the model and reviews the starting state. Use for "new project", "start from this plan", "furnish this home".
---

# Project onboarding

Goal: a `projects/<name>/` with a filled-in `brief.md` (requirements with ids), a `project.py` at **PHASE = 1** (envelope
surveyed, requirements registered) and a baseline review, ready for the `furnishing` skill.
Reference method: [`docs/method.md`](../../../docs/method.md), sections 1-2.

## Steps

1. **Starting files.** Ask for the available files: DWG/DXF, scaled PDF, photos, survey, data sheets of furniture to keep.
   Copy them into `projects/<short-name>/input/` (excluded from git: client data). For DWG/DXF run
   `uv run --with ezdxf python tools/read_plan.py <file>` and note units, extents, dimensions and off-square segments.
   For unscaled PDFs/photos state that dimensions will be `estimated` and ask for at least one known dimension.
   Done when you know which dimensions are `measured`/`documented` and which are not.

2. **Blocking questions.** Ask together (with the harness question tool if there is one, e.g. `AskUserQuestion` in Claude
   Code, otherwise in a single message; at most 4 per round) the questions that change the solution, in this order,
   skipping those already answered by the files:
   1. **Type of work**: furnishing only / internal reorganisation / renovation / new build; what can be touched
      (partitions, doors, windows, services).
   2. **Furnishing style**: modern, Scandinavian, japandi, industrial, contemporary classic, mid-century, other; desired
      feel (e.g. "not oppressive"); visual references.
   3. **Occupants**: how many, age, mobility needs, pets, regular guests, working from home.
   4. **Programme**: essential and desirable rooms.
   Done when the four items have an answer or an explicit assumption.

3. **Detail questions.** Collect the rest of the brief, proposing a default for each item so the user confirms instead of
   writing: clear heights and beams; orientation and views; fixed services (soil stacks, electrical panel, boiler,
   radiators/split units); floor, lift and car size (furniture delivery); cooking habits and seats at the table with
   guests; storage (metres of hanging clothes, shoes, suitcases); laundry; blackout and TV in the bedroom; furniture to
   keep and chosen products with dimensions; forbidden elements (e.g. TV next to windows); budget and timing; deliverable
   formats and AutoCAD version (Windows / Mac / LT).
   Done when every row of [`docs/brief-template.md`](../../../docs/brief-template.md) has a value, a confirmed default
   or "to confirm".

4. **Project folder and requirements.** Create `projects/<short-name>/`, copy `projects/_template/project.py` and
   `docs/brief-template.md` as `brief.md`. Fill in the brief with sources and the assumption log, and turn every
   programme item, constraint and forbidden element into a requirement with a stable id (`R01`, `R02`, ...).
   Done when every requirement has an id, a priority and a source.

5. **Survey (PHASE 1).** In `project.py`: `new_project()` with `interior` and height, then windows, doors, walls, rooms,
   `entrance()`, `private_room()` for bedrooms, `no_view()` from the entrance towards WC and beds, furniture to keep, and one
   `requirement()` per brief requirement, linked to the checks that prove it (or `manual=True`). Run it in FreeCAD, look
   at the top screenshot and compare: every source dimension matches the model (same extents, same openings).
   Differences go into the assumption log. Done when `verify()` runs and the dimensions match.

6. **Baseline review.** Run the `review-layout` skill on the surveyed starting state (envelope, fixed services, furniture
   to keep), before any design. Look for constraints the brief did not mention: dark rooms, doors that clash, services in
   the way, kept furniture that does not fit, requirements already impossible in this envelope. Every finding goes into
   the brief: as a new requirement, an open point in the assumption log, or a question for the user.
   Done when every baseline finding is filed in the brief.

7. **Hand-over.** Summarise for the user: what is measured and what is assumed, the baseline findings, the open questions
   that still block, and the proposed next step (`furnishing` skill, possibly with 2-3 layout options).
