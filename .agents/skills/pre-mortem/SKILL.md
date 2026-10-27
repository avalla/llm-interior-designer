---
name: pre-mortem
description: Independent adversarial review of a finished layout by a reviewer who did not design it - imagines six months of living in it and lists what fails. Use before delivery, or for "stress test", "pre-mortem", "what could go wrong", "second opinion".
---

# Pre-mortem

The designer tends to confirm their own choices. A pre-mortem asks a **fresh reviewer** to assume the project has already
failed and explain why. Run it after `verify()` is at zero and before delivery.

## Steps

1. **Package the evidence.** Run the project and export it (skill `export-autocad`, steps 1-3), so that
   `output/<Name>_Plan.png`, `output/verification_report.md` and `brief.md` are current. These three files are all the
   reviewer gets: no `project.py`, no conversation, no design rationale.

2. **Fresh reviewer.** Start the reviewer in a clean context: a subagent if the harness has one, otherwise a new session.
   Give it exactly this brief, with the paths filled in:

   > You are reviewing an apartment layout you did not design. Files: `<brief.md>`, `<plan.png>`, `<report.md>`.
   > It is six months later and the occupants described in the brief are unhappy. Write the failure stories: for each,
   > the scenario (from `docs/method.md` section 8), the room and element, what goes wrong, the measure you read on the
   > plan or the report, the pattern it breaks (`docs/patterns.md`, cite the id) and a severity (blocking / significant /
   > improvement). Walk every room: enter, move, sit, open every door, window and storage unit, clean, leave.
   > Also list each brief requirement you cannot see satisfied. Do not soften: an empty list needs a reason per room.
   > Write the result to `<project>/reviews/premortem-<date>.md` (versioned: it is part of the design record).

3. **Triage.** For every failure story, as the designer: **founded** (fix it with the `furnishing` skill), **founded but
   accepted** (state the compromise to the user), or **unfounded** (explain with a measure). Write the verdicts next to
   each story in the same file.

4. **Close the loop.** A founded story that `verify()` did not catch becomes a lesson in `docs/lessons.md`, updates the
   FMEA row in `docs/fmea.md` (occurrence and detection) and, when measurable, a new check with a counter-test.
   Done when every story has a verdict and every founded one has an action.
