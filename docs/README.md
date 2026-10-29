# Documentation guide

All layouts and checks in this repository support **preliminary proposals**. A passing geometric check does not
establish programme completeness, regulatory compliance or suitability for construction.

## Reading paths and authority

| Task | Read in order | Authority |
|---|---|---|
| Start a furnishing project | [Brief](brief-template.md), [method](method.md), [rules](design-rules.md) | The user-approved project brief defines needs and permitted changes; the method defines the workflow |
| Design or review a layout | [Method](method.md), [rules](design-rules.md), [FMEA](fmea.md), [patterns](patterns.md), [lessons](lessons.md) | Rules define defaults and applicability; FMEA prioritises review; patterns guide judgement; lessons preserve evidence |
| Use Interior Check | [User guide and coverage](interior-check.md) | Describes what the imported drawing workflow supports and omits |
| Develop the desktop app | [Architecture](desktop-app.md), [build instructions](../app/desktop/README.md) | Current implementation and planned capabilities are labelled separately |
| Change docs or checks | [Prompt evals](../.agents/skills/prompt-evals/SKILL.md), [eval history](../evals/history.md) | Compare engine and blind-review recall; record failures as well as successes |

For a real project, applicable requirements and verified product data take precedence over generic defaults. A
conflict with the brief must be raised and resolved explicitly; the brief is never rewritten to fit a model.

## Keeping documents consistent

- Change a threshold in [design-rules.md](design-rules.md) and both runtime `RULES` dictionaries together. The parity
  test compares the dictionaries, but does not validate the Markdown or the authority of a source.
- Change a capability in the user-guide coverage table as well as the architecture status. A check in the core may
  still lack the inputs needed by the importer.
- Keep lesson and rule identifiers stable. Record correction status and evidence without erasing the original defect.
- Update FMEA control coverage and remaining actions when a fix lands. Do not lower detection risk solely because a
  helper or check exists.
- Record dated implementation measurements in the architecture history. They are evidence for that run, not a claim
  that the current checkout passes. Use current test results for delivery and publication decisions.
