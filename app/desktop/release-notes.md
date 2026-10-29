Test build for architects: open a DXF or DWG plan and check the furnishing (passages and 60 cm routes, door and
leaf swings, space behind chairs, zones in front of wardrobes and appliances, bed sides, bathroom privacy, TV and
windows). Everything stays on the computer.

**Install (Windows):** download `Interior Check_*_x64-setup.exe` below and run it (no administrator rights). The build
is not signed yet: if Windows shows "Windows protected your PC", click "More info", then "Run anyway". The first
analysis takes a few seconds longer.

**Plans:** DXF works as is; DWG needs the free [ODA File Converter](https://www.opendesign.com/guestfiles/oda_file_converter)
(or save the plan as DXF from AutoCAD). Today the app reads walls as closed outlines or hatches, and doors, windows
and furniture as **blocks**; plans drawn with loose lines and arcs are shown with a note but not checked yet.

**Use:** Open plan -> what was recognised appears above the drawing; Results lists the issues (click one to see it on
the plan); Mapping fixes layer roles and furniture types, and Save profile keeps them for the studio's next plans.

Architecture, measures and limits: `docs/desktop-app.md`.
