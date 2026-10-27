# Eval fixture A: one-bedroom flat 8.0 x 6.0 m. Used by evals/run_engine.py and by review evals.
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "lib"))
import interiors  # noqa: E402
importlib.reload(interiors)
from interiors import *  # noqa: E402,F403

PARAMS = globals().get("PARAMS", {})
new_project("Fixture_A", HERE, interior=(0.30, 0.30, 7.70, 5.70), height=2.70)
c = COL

window("Window_Living", 0.15, 1.00, 3.00, 0, 2.40, "Living", mullion=True)
window("Window_Kitchen", 5.85, 2.40, 3.60, 1.00, 2.20, "Living", mullion=True)
window("Window_Bedroom", 0.15, 5.30, 6.90, 0, 2.40, "Bedroom", mullion=True)
window("Window_Bathroom", 5.85, 6.90, 7.40, 1.60, 2.20, "Bathroom")
hinged("Window_Kitchen_Leaf_L", 2.45, 5.70, (1, 0), (0, -1), 0.55, z0=1.03, hgt=2.15, leaf=False, kind="Window", handle=False)
hinged("Window_Kitchen_Leaf_R", 3.55, 5.70, (-1, 0), (0, -1), 0.55, z0=1.03, hgt=2.15, leaf=False, kind="Window", handle=False)

opening("Door_Entrance", 0.90, 5.65, 1.95, 6.05, 2.20, 0.90, 2.10)
hinged("Door_Entrance", 0.95, 5.70, (1, 0), (0, -1), 0.90, color=c["DARK"], frame=RULES["armored_frame"])
opening("Door_Bedroom", 4.35, 0.35, 4.55, 1.25, 2.15, 0.80, 2.10)
hinged("Door_Bedroom", 4.50, 0.40, (0, 1), (1, 0), 0.80)
opening("Door_Bathroom", 6.00, 3.35, 6.90, 3.55, 2.15, 0.80, 2.10)
hinged("Door_Bathroom", 6.05, 3.50, (1, 0), (0, 1), 0.80)

wall("Wall_South", 0, 0, 8.0, 0.3)
wall("Wall_North", 0, 5.7, 8.0, 6.0)
wall("Wall_West", 0, 0.3, 0.3, 5.7)
wall("Wall_East", 7.7, 0.3, 8.0, 5.7)
wall("Partition_Living", 4.40, 0.3, 4.50, 5.7)
wall("Partition_Bathroom", 4.50, 3.40, 7.70, 3.50)
box("Slab", 0, 0, -0.2, 8.0, 6.0, 0, c["FLOOR"], "Structure", check=False)

room("Living", [(0.30, 0.30, 4.40, 5.70)], (2.0, 3.3))
room("Bedroom", [(4.50, 0.30, 7.70, 3.40)], (5.6, 2.9))
room("Bathroom", [(4.50, 3.50, 7.70, 5.70)], (5.6, 5.2), habitable=False, kind="bathroom")
private_room("Bedroom")

g = "Living"
box("Shoe_Cabinet", 1.00, 5.30, 0, 1.50, 5.70, 1.00, c["WHITE"], g)
box("TV_A", 3.10, 0.31, 0.90, 4.00, 0.36, 1.50, c["BLACK"], g)
tv("TV_A")
box("Sofa", 0.80, 1.20, 0.01, 3.00, 2.10, 0.80, c["GREY"], g)
cyl("Floor_Lamp", 3.25, 0.75, 0, 0.20, 1.70, c["WHITE"], g)
cyl("Table", 1.28, 2.85, 0, 0.45, 0.75, c["OAK"], g)
chair("Chair_1", 1.28 - 0.75, 2.85, -1, 0, g, "Table", 0.45)
chair("Chair_2", 1.28 + 0.75, 2.85, 1, 0, g, "Table", 0.45)
box("Worktop", 2.00, 5.10, 0, 4.30, 5.70, 0.90, c["WHITE"], g)
cyl("Tap", 2.80, 5.62, 0.90, 0.02, 0.35, c["STEEL"], g)
box("Island", 2.20, 3.60, 0, 3.50, 4.20, 0.92, c["OAK"], g)
clearance("Kitchen aisle", "Island", "Worktop", 0.90, 1.10)

g = "Bedroom"
box("Bed", 5.40, 0.80, 0.01, 7.00, 2.75, 0.60, c["WHITE"], g)
box("Wardrobe", 7.10, 0.30, 0, 7.70, 1.30, 2.30, c["WHITE"], g)
access_zone("Bedroom: wardrobe", 6.39, 0.31, 7.09, 1.29, ("Wardrobe",))

g = "Bathroom"
box("Vanity", 4.50, 4.60, 0.55, 5.00, 5.40, 0.85, c["OAK"], g)
box("WC", 7.15, 4.70, 0.25, 7.70, 5.06, 0.43, c["WHITE"], g)

entrance(1.35, 4.60)
destination("Living: sofa", 1.80, 0.75)
destination("Bedroom: bed side", 5.00, 2.00)
destination("Bathroom: WC", 6.80, 4.90)

dimensions([0, 0.3, 4.4, 4.5, 7.7, 8.0], True, -0.6)
dimensions([0, 8.0], True, -1.0)
dimensions([0, 0.3, 3.4, 3.5, 5.7, 6.0], False, 8.6)

verify(write_report=PARAMS.get("report", True), quiet=PARAMS.get("quiet", False))
