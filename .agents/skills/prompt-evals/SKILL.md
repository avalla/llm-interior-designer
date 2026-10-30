---
name: prompt-evals
description: Measures the quality of the engine and of the review prompts on fixtures with planted defects, before and after changing a skill, a doc or a check. Use for "run the evals", "did this prompt change help", "regression test".
---

# Prompt evals

Fixtures live in `evals/fixtures/<case>/` (`project.py` + `expected.json` with the planted defects). Fixture A holds defects
`verify()` must catch; fixture B holds defects only a review can catch; fixture C holds the programme, privacy, appliance
and acceptance defects of lessons L23-L29. Recall per case is the score; compare it before and after every change to
`.agents/skills/`, `docs/` or `lib/interiors.py`, and commit the `evals/history.md` row together with the change.

## Steps

1. **Engine eval.** In FreeCAD: `exec(open("/Users/andrea/dev/tmp/freecad/evals/run_engine.py").read(), {})`.
   Expect full recall and an empty "Unexpected NON-COMPLIANT" table; anything else is a regression or a fixture defect
   (a fixture must fail only for its planted defects).

2. **Evidence.** For each fixture: run it (`PARAMS={"quiet": True}`), `interiors.export()`, then
   `tools/export.sh evals/fixtures/<case>`, so `output/<Name>_Plan.png` and `output/verification_report.md` exist.

3. **Blind reviews.** For each fixture start a **fresh** reviewer (subagent or new session) that has not seen
   `expected.json` and reads only the fixture's `project.py`, plan PNG and report. Instruction:
   "Follow `.agents/skills/review-layout/SKILL.md` on `evals/fixtures/<case>/`. Do not open `expected.json` or anything in
   `evals/results/`. Write all findings to `evals/results/<case>-review.md`, one finding per paragraph."

4. **Score.** `python3 evals/score_review.py <case>` for each fixture; results in `evals/results/<case>-score.md`.
   Read the missed defects: for each, decide whether the prompt lacks a leading word or a step (fix the skill or
   `docs/patterns.md`) or the keyword list in `expected.json` is too narrow (fix the fixture, never to inflate a score).

5. **Record.** Append a row to `evals/history.md`: date, change under test, engine recall, review recall per case.
   A change that lowers any recall is reverted or reworked. The row lands in the same commit as the change: a change
   without its row is incomplete.

6. **New rule, new planted defect.** A lesson that yields a check also yields a fixture defect that the check must
   catch (counter-test, L04): add it to the fixture whose envelope can host it, or to a new fixture.

Adding a fixture: a new folder with `project.py` and `expected.json`; every defect has an `engine` list (checks that must
fail, empty for judgement defects) and `keywords` (groups that must all appear in one finding).
