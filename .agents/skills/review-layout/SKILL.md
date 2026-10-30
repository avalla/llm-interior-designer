---
name: review-layout
description: Critical review of a plan or furnishing (FreeCAD model, DWG/DXF, screenshot, photo or user sketch) with measures, statuses and severities, also as baseline review of a starting state. Use for "check", "verify", "what do you think", reported issues to assess.
---

# Review layout

A review **measures and judges**; the project stays unchanged until the user confirms the changes (L09), then move to the
`furnishing` skill. References: [`docs/method.md`](../../../docs/method.md) (per-room checks, scenarios, antipatterns),
[`docs/patterns.md`](../../../docs/patterns.md) (pattern ids), [`docs/fmea.md`](../../../docs/fmea.md) (known failure modes),
[`docs/design-rules.md`](../../../docs/design-rules.md).

## Steps

1. **Source.** Identify what you are looking at. DWG/DXF: `tools/read_plan.py`. Image or sketch: dimensions from the scale of
   the visible dimension lines, declared as `estimated`. If a `project.py` exists, list the differences from it (walls
   removed, furniture moved, new elements). Done when every visible difference is listed.

2. **User's reported issues.** For each one: measure, threshold, verdict (founded / partly / unfounded). A founded issue that
   `verify()` did not find is a gap in the checks: say so openly and propose the check that closes it.

3. **Known failure modes first.** Go through `docs/fmea.md` from the highest RPN down and check each failure mode in every
   room where it can occur. These are the defects that keep coming back.

4. **Full pass.** Apply to every room the checks in section 7 of `method.md`, the patterns in `patterns.md`, the scenarios in
   section 8 and the antipatterns in section 9. Read every object for its use: open it, sit on it, stand in front of it,
   walk past it, see it from the entrance and from every seat; measure the route to each lounge seat against the
   straight distance (F20). Check that every brief requirement is visibly satisfied. Take measures from the
   model in FreeCAD with read-only code (`distToShape`, `common`, bounding boxes) or by rerunning `verify()` on the
   unchanged project. Done when every room has been walked through and every requirement has a status.

5. **Proposals.** For each problem: a concrete fix with coordinates, effects on other rooms (one fix can solve or create
   others: link them), trade-offs. Separate what the drawing solves from what needs a professional.

## Format

One finding per paragraph: room and element, what goes wrong, measure and threshold, status (VERIFIED / NON-COMPLIANT /
NOT VERIFIABLE / NOT APPLICABLE), severity (blocking / significant / improvement), pattern or FMEA id when one applies
(e.g. "P12 Bed alcove", "F05"), proposal. Tables when there are several measures of the same kind. End with a two-line
summary and the questions that block applying the changes.
