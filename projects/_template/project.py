# <PROJECT NAME>. Brief and assumption log: brief.md. Full example: ../apartment-100sqm/project.py
# Run in FreeCAD through MCP:
#   P = "/Users/andrea/dev/tmp/freecad/projects/<folder>/project.py"
#   exec(open(P).read(), {"__file__": P, "__name__": "__main__"})
# PHASE = 1 builds only the envelope (survey), 2 adds the main furniture, 3 details and decor.
# Later phases ADD: they never move geometry from earlier phases.
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "lib"))
import interiors  # noqa: E402
importlib.reload(interiors)
from interiors import *  # noqa: E402,F403

PHASE = 1
new_project("Project", HERE, interior=(0.30, 0.30, 0.30, 0.30), height=2.70)   # inner face of perimeter walls
c = COL

# ======================= PHASE 1 - SURVEY: ENVELOPE, OPENINGS, WALLS, ROOMS =======================
# Required order: window()/opening() BEFORE the wall() calls they cross.
# window("Window_X", yc, x0, x1, sill, head, "Room")
# opening("Door_X", x0, y0, x1, y1, rough_h, net_w, net_h); jambs(...); hinged(...) / sliding(...)
# wall("Wall_X", x0, y0, x1, y1)
# room("Room", [(x0, y0, x1, y1)], (label_x, label_y), kind="bedroom")   # kind from KINDS: bedroom, single_bedroom,
#     living, dining, kitchen, bathroom, corridor, laundry, store, service (minimum areas, programme, privacy checks)
# entrance(x, y); private_room("Bedroom"); intimate("WC", "Bed_Frame") (screened from the entrance, every seat and
#     every viewpoint("sofa", x, y, seated=True) / viewpoint("stair arrival", x, y) you declare)
# requirement("R01", "text from brief.md", ("Category/Element pattern", ...), ("object", ...))
#     or manual=True (review pending) / manual="reviews/<file>.md" (the review that judged it, must cite the id)
# accepted("Category/Element*", by="client name", date="YYYY-MM-DD", reason="..."): only the client accepts a defect
PARAMS = globals().get("PARAMS", {})   # values varied by tools/explore.py, e.g. PARAMS.get("table_x", 5.0)

if PHASE >= 2:
    # ======================= PHASE 2 - MAIN FURNITURE (beds, sofas, tables, kitchen, wardrobes) =======================
    # Register each piece's USE: chair()/seat(), access_zone(), clearance(kind="corridor|passage|aisle|bed_side"),
    # appliance_zone(..., front, own, kind="dishwasher|oven|drawer"), destination(), tv(), height_match()
    pass

if PHASE >= 3:
    # ======================= PHASE 3 - DETAILS, LIGHTING, DECOR =======================
    pass

# ======================= PLAN ANNOTATIONS (before export) =======================
# dimensions([...], True, y_line) / dimensions([...], False, x_line); label("D 80x210", x, y); note("...")

verify(write_report=PARAMS.get("report", True), quiet=PARAMS.get("quiet", False))
