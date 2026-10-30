# Eval fixture C: two-bedroom flat 10.3 x 8.8 m with a central hall. Used by evals/run_engine.py and by review evals.
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "lib"))
import interiors  # noqa: E402
importlib.reload(interiors)
from interiors import *  # noqa: E402,F403

PARAMS = globals().get("PARAMS", {})
new_project("Fixture_C", HERE, interior=(0.30, 0.30, 10.60, 9.10), height=2.70)
c = COL
FA = RULES["armored_frame"]
FR = RULES["frame"]

window("Window_Living", 0.15, 5.00, 8.00, 0.90, 2.30, "Living", axis="y", mullion=True)
window("Window_Bedroom_1", 10.75, 2.20, 4.20, 0.90, 2.30, "Bedroom 1", axis="y")
window("Window_Bedroom_2", 10.75, 5.50, 8.50, 0.90, 2.30, "Bedroom 2", axis="y", mullion=True)

opening("Door_Entrance", 5.05, 9.05, 6.10, 9.45, 2.20, 0.90, 2.10, "armored")
hinged("Door_Entrance", 5.125, 9.10, (1, 0), (0, -1), 0.90, color=c["DARK"], frame=FA)
opening("Door_Bathroom", 5.15, 1.55, 6.05, 1.75, 2.15, 0.80, 2.10)
jambs("Door_Bathroom", 5.15, 1.60, 6.05, 1.70, 2.15, FR)
hinged("Door_Bathroom", 5.20, 1.60, (1, 0), (0, -1), 0.80)
opening("Door_Bedroom_1", 6.05, 3.70, 6.25, 4.60, 2.15, 0.80, 2.10)
jambs("Door_Bedroom_1", 6.10, 3.70, 6.20, 4.60, 2.15, FR)
hinged("Door_Bedroom_1", 6.20, 4.55, (0, -1), (1, 0), 0.80)
opening("Door_Bedroom_2", 6.05, 4.90, 6.25, 5.80, 2.15, 0.80, 2.10)
jambs("Door_Bedroom_2", 6.10, 4.90, 6.20, 5.80, 2.15, FR)
hinged("Door_Bedroom_2", 6.20, 4.95, (0, 1), (1, 0), 0.80)
opening("Door_Laundry", 4.85, 1.85, 5.05, 2.75, 2.15, 0.80, 2.10)
jambs("Door_Laundry", 4.90, 1.85, 5.00, 2.75, 2.15, FR)
hinged("Door_Laundry", 4.90, 1.90, (0, 1), (-1, 0), 0.80)
opening("Door_Store", 4.85, 3.45, 5.05, 4.35, 2.15, 0.80, 2.10)
jambs("Door_Store", 4.90, 3.45, 5.00, 4.35, 2.15, FR)
hinged("Door_Store", 4.90, 3.50, (0, 1), (-1, 0), 0.80)

wall("Wall_South", 0, 0, 10.9, 0.3)
wall("Wall_North", 0, 9.1, 10.9, 9.4)
wall("Wall_West", 0, 0.3, 0.3, 9.1)
wall("Wall_East", 10.6, 0.3, 10.9, 9.1)
wall("Part_West_Hall", 4.90, 0.30, 5.00, 4.55)
wall("Part_Laundry_Store", 0.30, 3.15, 4.90, 3.25)
wall("Part_Store_Living", 0.30, 4.45, 4.90, 4.55)
wall("Part_Bath_N", 5.00, 1.60, 10.60, 1.70)
wall("Part_Hall_East", 6.10, 1.70, 6.20, 9.10)
wall("Part_Bed1_Bed2", 6.20, 4.70, 10.60, 4.80)
box("Slab", 0, 0, -0.2, 10.9, 9.4, 0, c["FLOOR"], "Structure", check=False)

room("Laundry", [(0.30, 0.30, 4.90, 3.15)], (2.6, 1.7), kind="laundry")
room("Store", [(0.30, 3.25, 4.90, 4.45)], (2.6, 3.85), kind="store")
room("Living", [(0.30, 4.55, 4.90, 9.10)], (2.6, 6.0), kind="living")
room("Hall", [(5.00, 1.70, 6.10, 9.10)], (5.55, 7.2), kind="corridor")
room("Bathroom", [(5.00, 0.30, 10.60, 1.60)], (8.0, 0.95), kind="bathroom")
room("Bedroom 1", [(6.20, 1.70, 10.60, 4.70)], (8.4, 2.2), kind="bedroom")
room("Bedroom 2", [(6.20, 4.80, 10.60, 9.10)], (8.4, 8.5), kind="bedroom")
private_room("Bedroom 1")
private_room("Bedroom 2")

g = "Kitchen"
box("Plinth", 0.30, 8.55, 0, 4.90, 9.10, 0.10, c["BLACK"], g, item="Base_Units")
box("Base_Units", 0.30, 8.50, 0.10, 4.90, 9.10, 0.86, c["WHITE"], g, item="Base_Units")
box("Worktop", 0.30, 8.45, 0.86, 4.90, 9.10, 0.90, c["BLACK"], g, item="Base_Units")
box("Sink", 3.20, 8.60, 0.90, 4.00, 9.00, 0.91, c["STEEL"], g, check=False)
appliance_zone("Kitchen: dishwasher", 2.00, 8.50, 2.60, 9.10, "-y", ("Base_Units",), "dishwasher")
box("Island_Base", 1.00, 6.60, 0, 2.20, 7.30, 0.90, c["WHITE"], g, item="Island")
box("Island_Top", 0.95, 6.55, 0.90, 2.25, 7.30, 0.94, c["OAK"], g, item="Island")
clearance("Kitchen aisle", "Island_Top", "Base_Units", kind="aisle")

g = "Living"
box("Sofa_Seat", 0.80, 4.80, 0.01, 2.80, 5.50, 0.42, c["GREY"], g, item="Sofa")
box("Sofa_Back", 0.80, 4.60, 0.01, 2.80, 4.80, 0.80, c["GREY"], g, item="Sofa")
viewpoint("sofa", 1.80, 5.20, seated=True)
cyl("Table", 3.60, 6.30, 0, 0.45, 0.75, c["OAK"], g)
chair("Chair_W", 3.60 - 0.75, 6.30, -1, 0, g, "Table", 0.45)
chair("Chair_E", 3.60 + 0.75, 6.30, 1, 0, g, "Table", 0.45)
chair("Chair_N", 3.60, 6.30 + 0.75, 0, 1, g, "Table", 0.45)
chair("Chair_S", 3.60, 6.30 - 0.75, 0, -1, g, "Table", 0.45)

g = "Bedroom_1"
box("Bed_1_Headboard", 7.60, 4.60, 0.01, 9.20, 4.70, 1.05, c["GREY"], g, item="Bed_1")
box("Bed_1_Frame", 7.60, 2.60, 0.05, 9.20, 4.60, 0.55, c["WHITE"], g, item="Bed_1")
box("Wardrobe_1", 6.30, 1.80, 0, 6.85, 3.40, 2.30, c["WHITE"], g)
access_zone("Bedroom 1: wardrobe", 6.86, 1.80, 7.56, 3.40, ("Wardrobe_1",), depth=0.70)

g = "Bedroom_2"
box("Bed_2", 9.70, 5.50, 0.01, 10.60, 7.50, 0.55, c["WHITE"], g)

g = "Bathroom"
box("WC", 5.40, 0.30, 0.25, 5.95, 0.66, 0.43, c["WHITE"], g)
box("Washbasin", 7.00, 0.30, 0.55, 7.60, 0.75, 0.85, c["OAK"], g)
box("Shower_Tray", 9.30, 0.30, 0.004, 10.60, 1.20, 0.03, c["WHITE"], g)
box("Shower_Glass", 9.30, 1.19, 0.03, 10.60, 1.20, 2.00, c["GLASS"], g, tr=60)
wet_zone("Shower open side (west)", 8.70, 0.30, 9.30, 1.20)

g = "Laundry"
box("Washer", 0.40, 0.40, 0, 1.00, 1.00, 0.85, c["WHITE"], g)
box("Utility_Sink", 1.20, 0.40, 0, 1.80, 1.00, 0.90, c["WHITE"], g)
box("Laundry_Shelves", 0.30, 1.50, 0, 0.70, 3.00, 2.00, c["OAK"], g)
electrical("Washer")

entrance(5.55, 8.60)
intimate("WC", "Bed_1_Frame", "Bed_2")
destination("Living: sofa", 1.80, 5.90)
destination("Kitchen: sink", 3.50, 7.90)
destination("Bedroom 1: bed west side", 7.22, 3.00)
destination("Bedroom 2: bed side", 9.30, 6.50)
destination("Bathroom: WC", 5.70, 1.10)
destination("Bathroom: washbasin", 7.30, 1.15)
destination("Bathroom: shower", 8.90, 0.80)
destination("Laundry: washer", 1.10, 1.45)
destination("Store", 3.00, 3.85)

requirement("R01", "Dining for four", ("Seats/Chair_*",), ("Table",))
requirement("R02", "Warm contemporary style", manual=True)
requirement("R03", "Bedroom 1 private and screened", manual="reviews/review-01.md")
accepted("Seats/Chair_Nowhere*", "client", "2026-10-29", "a chair that was removed in the previous version")

dimensions([0, 0.3, 4.9, 5.0, 6.1, 6.2, 10.6, 10.9], True, -0.6)
dimensions([0, 10.9], True, -1.0)
dimensions([0, 0.3, 1.6, 1.7, 4.7, 4.8, 9.1, 9.4], False, 11.5)

verify(write_report=PARAMS.get("report", True), quiet=PARAMS.get("quiet", False))
