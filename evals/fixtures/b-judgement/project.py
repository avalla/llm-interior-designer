# Eval fixture B: one-bedroom flat 8.0 x 6.0 m. Used by review evals.
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "lib"))
import interiors  # noqa: E402
importlib.reload(interiors)
from interiors import *  # noqa: E402,F403

PARAMS = globals().get("PARAMS", {})
new_project("Fixture_B", HERE, interior=(0.30, 0.30, 7.70, 5.70), height=2.70)
c = COL

window("Window_Living", 0.15, 1.00, 3.00, 0, 2.40, "Living", mullion=True)
window("Window_Bedroom", 0.15, 5.50, 6.70, 0.90, 2.20, "Bedroom")
window("Window_Bathroom", 5.85, 6.90, 7.40, 1.60, 2.20, "Bathroom")

opening("Door_Entrance", 0.90, 5.65, 1.95, 6.05, 2.20, 0.90, 2.10)
hinged("Door_Entrance", 1.80, 5.70, (-1, 0), (0, -1), 0.90, color=c["DARK"], frame=RULES["armored_frame"])
opening("Door_Bedroom", 4.35, 2.00, 4.55, 2.90, 2.15, 0.80, 2.10)
hinged("Door_Bedroom", 4.50, 2.05, (0, 1), (1, 0), 0.80)
opening("Door_Bathroom", 4.35, 4.10, 4.55, 5.00, 2.15, 0.80, 2.10)
hinged("Door_Bathroom", 4.50, 4.15, (0, 1), (1, 0), 0.80)

wall("Wall_South", 0, 0, 8.0, 0.3)
wall("Wall_North", 0, 5.7, 8.0, 6.0)
wall("Wall_West", 0, 0.3, 0.3, 5.7)
wall("Wall_East", 7.7, 0.3, 8.0, 5.7)
wall("Partition_Living", 4.40, 0.3, 4.50, 5.7)
wall("Partition_Bathroom", 4.50, 3.40, 7.70, 3.50)
box("Slab", 0, 0, -0.2, 8.0, 6.0, 0, c["FLOOR"], "Structure", check=False)

room("Living", [(0.30, 0.30, 4.40, 5.70)], (2.0, 3.3))
room("Bedroom", [(4.50, 0.30, 7.70, 3.40)], (6.9, 2.9))
room("Bathroom", [(4.50, 3.50, 7.70, 5.70)], (6.0, 4.4), habitable=False, kind="bathroom")
private_room("Bedroom")

g = "Living"
box("TV_Unit", 0.30, 2.40, 0.15, 0.75, 4.00, 0.55, c["OAK"], g)
box("TV", 0.31, 2.60, 0.90, 0.36, 3.80, 1.60, c["BLACK"], g)
tv("TV")
box("Sofa_Seat", 1.60, 2.40, 0.01, 2.50, 4.20, 0.42, c["GREY"], g, item="Sofa")
box("Sofa_Back", 1.40, 2.40, 0.01, 1.60, 4.20, 0.80, c["GREY"], g, item="Sofa")
box("Wardrobe_Living", 1.10, 0.40, 0, 2.70, 1.00, 2.20, c["WHITE"], g)
box("Kitchen_Units", 2.00, 5.10, 0, 4.30, 5.70, 0.90, c["WHITE"], g)

g = "Bedroom"
box("Bed", 5.40, 0.30, 0.01, 7.00, 2.40, 0.60, c["WHITE"], g)
box("Nightstand_1", 4.80, 0.35, 0.01, 5.25, 0.80, 0.45, c["OAK"], g)

g = "Bathroom"
box("Vanity", 5.00, 5.20, 0.55, 5.80, 5.70, 0.85, c["OAK"], g)
box("WC", 7.15, 4.70, 0.25, 7.70, 5.06, 0.43, c["WHITE"], g)

entrance(1.35, 4.60)
destination("Living: sofa", 3.00, 3.30)
destination("Bedroom: bed side", 7.35, 1.50)
destination("Bathroom: WC", 6.80, 4.90)

dimensions([0, 0.3, 4.4, 4.5, 7.7, 8.0], True, -0.6)
dimensions([0, 8.0], True, -1.0)
dimensions([0, 0.3, 3.4, 3.5, 5.7, 6.0], False, 8.6)

verify(write_report=PARAMS.get("report", True), quiet=PARAMS.get("quiet", False))
