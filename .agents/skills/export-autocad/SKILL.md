---
name: export-autocad
description: Exports a project for AutoCAD (2D plan DWG with dimensions and layers, 3D DWG, STEP) with the verification report. Use for "send me the files", DWG, DXF, STEP, AutoCAD.
---

# Export AutoCAD

## Steps

1. **Project at zero problems.** Run `projects/<name>/project.py` in FreeCAD; it must end with `TOTAL PROBLEMS: 0`.
   With open problems, fix them (`furnishing` skill) or ask whether the user wants a conditional proposal anyway.

2. **Annotations.** If walls or openings changed, update the `dimensions()` chains and the door/window `label()` calls in
   `project.py`, using the rough openings from the report. Room areas, title block and sliding-door symbols update by
   themselves.

3. **Export.** In FreeCAD: `import interiors; interiors.export()`. Then `tools/export.sh projects/<name>`: it must end with
   `round-trip OK`.

4. **Preview.** Open `output/<Name>_Plan.png` (generated from the re-read DWG): texts overlapping dimensions or furniture,
   unreadable dimensions, recognisable doors and sliding doors, visible windows. Fix positions in `project.py` and repeat
   from step 3. Done when the preview is clean.

## Delivery

| File in `projects/<name>/output/` | Use |
|---|---|
| `<Name>_Plan.dwg` | 2D plan, AutoCAD 2018+, layers WALLS/WINDOWS/DOORS/SWINGS/FURNITURE/DIMENSIONS/TEXT |
| `<Name>_3D.dwg` | 3D meshes: opens with Open everywhere, including AutoCAD LT and Mac (L08) |
| `<Name>_3D.step` | 3D solids: `IMPORT` command, AutoCAD for Windows only |
| `<Name>_Plan.png` | preview |
| `verification_report.md` | checks with statuses and severities, rooms, rough openings, furniture schedule |

State what was verified (round trip with entity counts) and what was not (opening in real AutoCAD, if unavailable), and
list the NOT VERIFIABLE items with the professional who closes them.
