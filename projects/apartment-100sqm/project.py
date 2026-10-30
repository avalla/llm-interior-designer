# Apartment ~100 m2 (12.5 x 8.0 m gross). Brief and assumptions: brief.md.
# Run in FreeCAD through MCP:
#   P = "/Users/andrea/dev/tmp/freecad/projects/apartment-100sqm/project.py"
#   exec(open(P).read(), {"__file__": P, "__name__": "__main__"})
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "lib"))
import interiors  # noqa: E402
importlib.reload(interiors)
from interiors import *  # noqa: E402,F403

# PARAMS: values varied by tools/explore.py (variant exploration); defaults = chosen design
PARAMS = globals().get("PARAMS", {})
new_project("Apartment", HERE, interior=(0.30, 0.30, 12.20, 7.70), height=2.70)
c = COL
FA = RULES["armored_frame"]
FR = RULES["frame"]

# ======================= PHASE 1 - ENVELOPE, OPENINGS, WALLS =======================
window("Window_Living", 0.15, 1.00, 5.50, 0, 2.40, "Living area", mullion=True)        # lift-and-slide
window("French_Window_Bedroom", 0.15, 8.20, 10.60, 0, 2.40, "Bedroom", mullion=True)   # sliding
window("Window_Kitchen", 7.85, 1.40, 3.20, 1.20, 2.20, "Living area", mullion=True)    # 2 inward leaves
window("Window_Bathroom", 7.85, 9.55, 10.15, 1.60, 2.20, "Bathroom")                   # 1 inward leaf
hinged("Window_Kitchen_Leaf_L", 1.45, 7.70, (1, 0), (0, -1), 0.825, z0=1.23, hgt=2.15, leaf=False, kind="Window", handle=False)
hinged("Window_Kitchen_Leaf_R", 3.15, 7.70, (-1, 0), (0, -1), 0.825, z0=1.23, hgt=2.15, leaf=False, kind="Window", handle=False)
hinged("Window_Bathroom_Leaf", 9.60, 7.70, (1, 0), (0, -1), 0.50, z0=1.63, hgt=2.15, leaf=False, kind="Window", handle=False)

opening("Door_Entrance", 6.75, 7.65, 7.80, 8.05, 2.20, 0.90, 2.10, "armored, 7.5 cm subframe")
jambs("Door_Entrance", 6.75, 7.70, 7.80, 8.00, 2.20, FA)
hinged("Door_Entrance", 7.725, 7.70, (-1, 0), (0, -1), 0.90, color=c["DARK"], frame=FA)

opening("Door_Bedroom", 6.70, 3.50, 7.60, 3.70, 2.15, 0.80, 2.10)
jambs("Door_Bedroom", 6.70, 3.55, 7.60, 3.65, 2.15, FR)
hinged("Door_Bedroom", 6.75, 3.55, (1, 0), (0, -1), 0.80)

opening("Door_Bathroom", 8.20, 4.70, 9.10, 4.90, 2.15, 0.80, 2.10)
jambs("Door_Bathroom", 8.20, 4.75, 9.10, 4.85, 2.15, FR)
hinged("Door_Bathroom", 8.25, 4.85, (1, 0), (0, 1), 0.80)

opening("Door_Night_Zone", 6.40, 3.75, 6.60, 4.65, 2.15, 0.90, 2.10, "surface-mounted sliding")
sliding("Door_Night_Zone", (6.40, 3.70, 0.01, 6.44, 4.70, 2.15), (6.40, 2.70, 0.01, 6.44, 3.70, 2.15))
opening("Door_Closet", 10.50, 4.70, 11.20, 4.90, 2.15, 0.70, 2.10, "surface-mounted sliding")
sliding("Door_Closet", (10.45, 4.69, 0.01, 11.25, 4.73, 2.15), (9.65, 4.69, 0.01, 10.45, 4.73, 2.15))

wall("Wall_South", 0, 0, 12.5, 0.3)
wall("Wall_North", 0, 7.7, 12.5, 8.0)
wall("Wall_West", 0, 0.3, 0.3, 7.7)
wall("Wall_East", 12.2, 0.3, 12.5, 7.7)
wall("Partition_Living", 6.45, 0.3, 6.55, 4.75)
wall("Partition_Bedroom", 6.55, 3.55, 12.2, 3.65)
wall("Partition_Hall_North", 6.45, 4.75, 12.2, 4.85)
wall("Partition_Entrance_Bathroom", 7.95, 4.85, 8.05, 7.7)
wall("Partition_Bathroom_Closet", 10.25, 4.85, 10.35, 7.7)
box("Slab", 0, 0, -0.20, 12.5, 8.0, 0, c["FLOOR"], "Structure", check=False)
box("Tiles_Bathroom", 8.05, 4.85, 0, 10.25, 7.7, 0.004, c["TILE"], "Structure", check=False)

room("Living area", [(0.30, 0.30, 6.45, 4.85), (0.30, 4.85, 7.95, 7.70)], (2.90, 4.45), kind="living")
room("Bedroom", [(6.55, 0.30, 12.20, 3.55)], (8.70, 2.60), kind="bedroom")
room("Bathroom", [(8.05, 4.85, 10.25, 7.70)], (9.20, 6.25), kind="bathroom", lines=["BATH"])
room("Walk-in closet", [(10.35, 4.85, 12.20, 7.70)], (10.77, 6.25), kind="store", lines=["WALK-IN", "CLOSET"])
room("Night hall", [(6.55, 3.65, 12.20, 4.75)], (9.30, 4.30), kind="corridor")

# ======================= PHASE 2 - MAIN FURNITURE =======================
g = "Living"
box("TV_Unit", 0.30, 1.40, 0.15, 0.75, 3.40, 0.55, c["OAK"], g)
box("TV_65", 0.31, 1.75, 0.95, 0.36, 3.05, 1.70, c["BLACK"], g)
# lounge layout (pre-mortem S12-S14), compared with tools/explore.py: L0 = L sofa with the chaise to the north,
# armchair against the glazing; A = straight sofa, armchair by the window facing north; B = chaise to the window,
# armchair closing the circle from the north-west; C = straight sofa 20 cm nearer the TV, armchair from the north-west
LIV = PARAMS.get("living", "L0")
SX = {"L0": 3.40, "A": 3.40, "B": 3.40, "C": 3.20}[LIV]           # sofa seat front (sofa faces west, towards the TV)
SY0, SY1 = (1.00, 3.80) if LIV == "L0" else (1.30, 3.50)        # sofa ends, arms included
box("Sofa_Seat", SX, SY0 + 0.20, 0.01, SX + 0.90, SY1 - 0.20, 0.42, c["GREY"], g, item="Sofa")
box("Sofa_Back", SX + 0.90, SY0, 0.01, SX + 1.10, SY1, 0.80, c["GREY"], g, item="Sofa")
box("Sofa_Arm_S", SX if LIV != "B" else 2.60, SY0, 0.01, SX + 0.90, SY0 + 0.20, 0.60, c["GREY"], g, item="Sofa")
box("Sofa_Arm_N", SX, SY1 - 0.20, 0.01, SX + 0.90, SY1, 0.60, c["GREY"], g, item="Sofa")
if LIV == "L0":
    box("Sofa_Chaise", 2.60, 3.00, 0.01, 3.40, 3.80, 0.42, c["GREY"], g, item="Sofa")
elif LIV == "B":
    box("Sofa_Chaise", 2.60, 1.50, 0.01, 3.40, 2.10, 0.42, c["GREY"], g, item="Sofa")
box("Sofa_Cushions", SX + 0.70, SY0 + 0.25, 0.42, SX + 0.90, SY1 - 0.25, 0.72, c["SAGE"], g, item="Sofa")
CT = {"L0": (1.90, 1.80, 2.60, 2.60), "A": (2.40, 1.85, 3.00, 2.95), "B": (2.40, 2.40, 3.00, 3.40),
      "C": (2.20, 2.20, 2.80, 3.30)}[LIV]                         # coffee table top
box("Coffee_Table_Base", CT[0] + 0.10, CT[1] + 0.10, 0.01, CT[2] - 0.10, CT[3] - 0.10, 0.33, c["BLACK"], g, item="Coffee_Table")
box("Coffee_Table_Top", CT[0], CT[1], 0.33, CT[2], CT[3], 0.38, c["OAK"], g, item="Coffee_Table")
if LIV in ("L0", "A"):                                            # armchair facing north (back to the glazing)
    AX, AY = {"L0": (1.30, 0.42), "A": (1.60, 1.10)}[LIV]
    box("Armchair_Seat", AX, AY + 0.18, 0.01, AX + 0.80, AY + 0.83, 0.42, c["TERRA"], g, item="Armchair")
    box("Armchair_Back", AX, AY, 0.01, AX + 0.80, AY + 0.18, 0.82, c["TERRA"], g, item="Armchair")
else:                                                             # armchair facing east, towards the sofa
    AX, AY = {"B": (1.30, 3.10), "C": (1.10, 3.10)}[LIV]
    box("Armchair_Seat", AX + 0.18, AY, 0.01, AX + 0.80, AY + 0.80, 0.42, c["TERRA"], g, item="Armchair")
    box("Armchair_Back", AX, AY, 0.01, AX + 0.18, AY + 0.80, 0.82, c["TERRA"], g, item="Armchair")
shelf = [B(5.95, 0.60, 0, 6.45, 2.60, 0.03)]
for z in (0.40, 0.80, 1.20, 1.60, 1.97):
    shelf.append(B(5.95, 0.60, z, 6.45, 2.60, z + 0.03))
shelf += [B(5.95, 0.60, 0, 6.45, 0.63, 2.0), B(5.95, 2.57, 0, 6.45, 2.60, 2.0), B(5.95, 1.585, 0, 6.45, 1.615, 2.0)]
add("Bookcase", Part.makeCompound(shelf), c["OAK"], g)
tv("TV_65")

g = "Dining"
TX, TY, TR = PARAMS.get("table_x", 5.40), PARAMS.get("table_y", 6.10), 0.55   # 5.40: 80 cm from the island (L29 move)
cyl("Table_Base", TX, TY, 0, 0.28, 0.03, c["BLACK"], g, item="Table")
cyl("Table_Leg", TX, TY, 0.03, 0.06, 0.69, c["BLACK"], g, item="Table")
cyl("Table_Top", TX, TY, 0.72, TR, 0.03, c["OAK"], g, item="Table")
# 3 fixed chairs: an east chair would sit on the entrance -> night zone route (pre-mortem S03); a 4th is a folding chair
for i, (dx, dy) in [(1, (-1, 0)), (3, (0, -1)), (4, (0, 1))]:   # 1=west 3=south 4=north
    chair("Chair_%d" % i, TX + dx * 0.75, TY + dy * 0.75, dx, dy, g, "Table", TR)
height_match("Table / chairs", 0.75, 0.47)

g = "Kitchen"
# tall column stops at the worktop line; the base run turns the corner with a carousel unit (pre-mortem S11)
box("Tall_Units_Fridge_Oven", 0.30, 5.00, 0, 0.90, 7.05, 2.30, c["WHITE"], g)
box("Plinth", 0.30, 7.15, 0, 4.50, 7.70, 0.10, c["BLACK"], g, item="Base_Units")
box("Base_Units", 0.30, 7.10, 0.10, 4.50, 7.70, 0.86, c["WHITE"], g, item="Base_Units")
box("Worktop", 0.30, 7.05, 0.86, 4.50, 7.70, 0.90, c["BLACK"], g, item="Base_Units")
# appliance doors with a person in front (pre-mortem S07, S08): hinged fridge door = leaf + 70 cm; drop-down oven and
# dishwasher doors = door projection + 70 cm (L29), so the island starts east of the oven zone and the dishwasher sits
# west of the sink, out of the island's shadow
hinged("Fridge_Door", 0.90, 6.40, (0, -1), (1, 0), 0.60, hgt=1.85, leaf=False, kind="Appliance door", handle=False,
       own="Tall_Units_Fridge_Oven")
access_zone("Kitchen: in front of fridge", 0.91, 5.80, 1.61, 6.40, ("Tall_Units_Fridge_Oven",), depth=0.70)
appliance_zone("Kitchen: oven", 0.30, 5.05, 0.90, 5.75, "+x", ("Tall_Units_Fridge_Oven",), "oven")
appliance_zone("Kitchen: dishwasher", 0.90, 7.10, 1.50, 7.70, "-y", ("Base_Units",), "dishwasher")
box("Island_Base", 2.20, 5.40, 0, 4.00, 6.10, 0.90, c["WHITE"], g, item="Island")
box("Island_Top", 2.15, 5.05, 0.90, 4.05, 6.10, 0.94, c["OAK"], g, item="Island")   # 190 long, 4 cm east of the oven zone
for i, x in enumerate((2.55, 3.10, 3.65)):
    n = "Stool_%d" % (i + 1)
    cyl(n + "_Seat", x, 4.85, 0.62, 0.19, 0.05, c["BLACK"], g, item=n)
    cyl(n + "_Leg", x, 4.85, 0, 0.03, 0.62, c["BLACK"], g, item=n)
    seat(n, (n, "Island"), (x, 5.05), (0, -1), 0.19)
height_match("Island / stools", 0.94, 0.67)

g = "Entrance"
box("Entrance_Wardrobe", 6.95, 4.85, 0, 7.95, 5.30, 2.40, c["WHITE"], g)
hinged("Entrance_Wardrobe_Leaf_1", 6.95, 5.30, (1, 0), (0, 1), 0.50, hgt=2.40, leaf=False, kind="Wardrobe leaf", handle=False, own="Entrance_Wardrobe")
hinged("Entrance_Wardrobe_Leaf_2", 7.95, 5.30, (-1, 0), (0, 1), 0.50, hgt=2.40, leaf=False, kind="Wardrobe leaf", handle=False, own="Entrance_Wardrobe")
access_zone("Entrance: in front of wardrobe", 6.96, 5.305, 7.92, 6.01, ("Entrance_Wardrobe",))

g = "Night_Hall"
box("Utility_Cupboard", 11.75, 3.65, 0, 12.20, 4.75, 2.40, c["WHITE"], g)
# sliding fronts: a 90 cm hinged leaf swept the 1.10 m hall and blocked the closet door (S19, P17)

g = "Bedroom"
box("Bed_Headboard", 12.08, 0.95, 0.01, 12.20, 2.95, 1.10, c["GREY"], g, item="Bed")
box("Bed_Frame", 10.00, 1.00, 0.05, 12.08, 2.90, 0.35, c["OAK"], g, item="Bed")
box("Bed_Mattress", 10.05, 1.05, 0.35, 12.05, 2.85, 0.60, c["WHITE"], g, item="Bed")
box("Bed_Duvet", 10.05, 1.05, 0.60, 11.50, 2.85, 0.65, c["SAGE"], g, item="Bed")
box("Bed_Pillow_1", 11.60, 1.15, 0.60, 12.00, 1.85, 0.72, c["WHITE"], g, item="Bed")
box("Bed_Pillow_2", 11.60, 2.05, 0.60, 12.00, 2.75, 0.72, c["WHITE"], g, item="Bed")
for i, (y0, y1) in enumerate([(0.45, 0.90), (2.95, 3.40)]):
    box("Nightstand_%d" % (i + 1), 11.70, y0, 0.01, 12.15, y1, 0.45, c["OAK"], g)
    cyl("Bedside_Lamp_%d" % (i + 1), 11.92, (y0 + y1) / 2, 0.45, 0.10, 0.30, c["WHITE"], g)
box("Desk_Top", 6.55, 0.80, 0.72, 7.15, 2.20, 0.75, c["OAK"], g, item="Desk")
box("Desk_Leg_1", 7.08, 0.82, 0, 7.13, 0.87, 0.72, c["BLACK"], g, item="Desk")
box("Desk_Leg_2", 7.08, 2.13, 0, 7.13, 2.18, 0.72, c["BLACK"], g, item="Desk")
box("Desk_Chair_Seat", 7.25, 1.27, 0.43, 7.67, 1.69, 0.47, c["BLACK"], g, item="Desk_Chair")
box("Desk_Chair_Back", 7.64, 1.27, 0.47, 7.67, 1.69, 0.85, c["BLACK"], g, item="Desk_Chair")
box("Desk_Chair_Leg", 7.42, 1.44, 0, 7.50, 1.52, 0.43, c["BLACK"], g, item="Desk_Chair")
seat("Desk_Chair", ("Desk_Chair", "Desk"), (7.15, 1.48), (1, 0), 0.21)
height_match("Desk / chair", 0.75, 0.47)

g = "Bathroom"
box("Vanity_Unit", 8.05, 5.80, 0.55, 8.55, 6.60, 0.85, c["OAK"], g, item="Washbasin")
box("Washbasin", 8.10, 5.90, 0.85, 8.50, 6.50, 0.97, c["WHITE"], g, item="Washbasin")
cyl("Washbasin_Tap", 8.12, 6.20, 0.97, 0.015, 0.20, c["STEEL"], g, item="Washbasin")
box("WC_Wall_Hung", 9.70, 5.97, 0.25, 10.25, 6.33, 0.40, c["WHITE"], g, item="WC")
box("WC_Lid", 9.72, 5.99, 0.40, 10.20, 6.31, 0.43, c["WHITE"], g, item="WC")
box("Bidet_Wall_Hung", 9.70, 5.15, 0.25, 10.25, 5.51, 0.40, c["WHITE"], g)   # 82 cm between axes (S22)
box("Shower_Tray", 8.05, 6.70, 0.004, 9.45, 7.70, 0.03, c["WHITE"], g)
box("Shower_Glass", 8.05, 6.70, 0.03, 8.75, 6.71, 2.00, c["GLASS"], g, tr=60)
box("Shower_Glass_East", 9.44, 6.71, 0.03, 9.45, 7.70, 2.00, c["GLASS"], g, tr=60)   # closes the side towards the machine (S20)
box("Washing_Machine", 9.65, 7.10, 0, 10.25, 7.70, 0.85, c["WHITE"], g)

g = "Walk_in_Closet"


def open_wardrobe(name, x0, y0, x1, y1, along, posts, rails, shelves_bay, drawer_bay):
    """Open 60 cm deep unit (along='y': front towards -x; 'x': front towards -y)."""
    p = []
    for q in posts:
        p.append(B(q - 0.01, y0, 0, q + 0.01, y1, 2.40) if along == "x" else B(x0, q - 0.01, 0, x1, q + 0.01, 2.40))
    p += [B(x0, y0, 2.38, x1, y1, 2.40), B(x0, y0, 2.00, x1, y1, 2.02)]
    for i in range(len(posts) - 1):
        a0, a1 = posts[i] + 0.01, posts[i + 1] - 0.01
        seg = (lambda z0, z1: B(x0, a0, z0, x1, a1, z1)) if along == "y" else (lambda z0, z1: B(a0, y0, z0, a1, y1, z1))
        if i in shelves_bay:
            p += [seg(z, z + 0.02) for z in (0.40, 0.75, 1.10, 1.45)]
        if i in drawer_bay:
            p += [seg(0.0, 0.70), seg(1.25, 1.27)]
    add(name, Part.makeCompound(p), c["WHITE"], g)
    for i in rails:
        a0, a1 = posts[i] + 0.01, posts[i + 1] - 0.01
        if along == "y":
            r = Part.makeCylinder(0.012 * S, (a1 - a0) * S, V((x0 + x1) / 2 * S, a0 * S, 1.85 * S), V(0, 1, 0))
        else:
            r = Part.makeCylinder(0.012 * S, (a1 - a0) * S, V(a0 * S, (y0 + y1) / 2 * S, 1.85 * S), V(1, 0, 0))
        add("%s_Rail_%d" % (name, i + 1), r, c["STEEL"], g, item=name)


open_wardrobe("Closet_Unit_East", 11.60, 4.85, 12.20, 7.70, "y", [4.86, 5.80, 6.75, 7.69], [0, 1], [2], [0])
open_wardrobe("Closet_Unit_North", 10.35, 7.10, 11.60, 7.70, "x", [10.36, 10.98, 11.59], [1], [0], [])
access_zone("Closet: in front of east unit", 10.89, 4.86, 11.595, 7.09, ("Closet_Unit_East",))
access_zone("Closet: in front of north unit", 10.38, 6.39, 11.59, 7.095, ("Closet_Unit_North",))

# ======================= PHASE 3 - DETAILS, LIGHTING, DECOR =======================
RUG = {"L0": (1.20, 0.80, 4.00, 3.60), "A": (1.40, 1.40, 3.80, 3.40), "B": (1.40, 1.50, 3.80, 3.60),
       "C": (1.20, 1.60, 3.60, 3.60)}[LIV]
box("Rug", RUG[0], RUG[1], 0, RUG[2], RUG[3], 0.01, c["RUG"], "Living", check=False)
# reading lights (P14, P15): one at the armchair; L0 had none at the sofa (S13)
# in L0 the armchair lamp's previous position closed the access to the sofa (25 cm), lesson L06
LAMPS = {"L0": [("Floor_Lamp", 1.05, 0.70)],
         "A": [("Floor_Lamp", 1.35, 1.35), ("Floor_Lamp_Sofa", 4.70, 1.45)],
         "B": [("Floor_Lamp", 1.10, 3.60), ("Floor_Lamp_Sofa", 4.70, 3.35)],
         "C": [("Floor_Lamp", 0.90, 3.60), ("Floor_Lamp_Sofa", 4.50, 1.45)]}[LIV]
for n, lx, ly in LAMPS:
    cyl(n + "_Base", lx, ly, 0, 0.15, 0.03, c["BLACK"], "Living", item=n)
    cyl(n + "_Stem", lx, ly, 0.03, 0.015, 1.50, c["BLACK"], "Living", item=n)
    cyl(n + "_Shade", lx, ly, 1.50, 0.20, 0.25, c["WHITE"], "Living", item=n)
cyl("Plant_Pot", 0.65, 4.30, 0, 0.20, 0.45, c["TERRA"], "Living", item="Plant")   # moved off the night-door track (S15)
add("Plant_Foliage", Part.makeSphere(0.35 * S, V(0.65 * S, 4.30 * S, 0.95 * S)), c["GREEN"], "Living", item="Plant")
cyl("Pendant_Table", TX, TY, 1.75, 0.25, 0.18, c["BLACK"], "Dining", item="Pendant_Table")
cyl("Pendant_Table_Cord", TX, TY, 1.93, 0.005, 2.70 - 1.93, c["BLACK"], "Dining", item="Pendant_Table")
for i, x in enumerate((2.70, 3.50)):
    cyl("Pendant_Island_%d" % (i + 1), x, 5.60, 1.70, 0.12, 0.18, c["BLACK"], "Kitchen", item="Pendant_Island_%d" % i)
    cyl("Pendant_Island_%d_Cord" % (i + 1), x, 5.60, 1.88, 0.005, 2.70 - 1.88, c["BLACK"], "Kitchen", item="Pendant_Island_%d" % i)
box("Hob", 3.35, 7.15, 0.90, 3.95, 7.65, 0.905, (0.05, 0.05, 0.05), "Kitchen")
box("Sink", 1.90, 7.20, 0.90, 2.70, 7.60, 0.91, c["STEEL"], "Kitchen")
cyl("Tap", 2.30, 7.63, 0.91, 0.02, 0.20, c["STEEL"], "Kitchen")       # top 1.11 < sill 1.20
box("Wall_Units_East", 3.25, 7.35, 1.50, 4.50, 7.70, 2.30, c["WHITE"], "Kitchen")   # hob landing 55 cm (S09)
box("Integrated_Hood", 3.35, 7.35, 1.40, 3.95, 7.70, 1.50, c["STEEL"], "Kitchen")
box("Entrance_Mirror", 7.93, 5.85, 1.00, 7.95, 6.65, 2.00, c["GLASS"], "Entrance", tr=30)
box("Entrance_Console", 7.65, 6.05, 0.75, 7.95, 6.70, 0.80, c["OAK"], "Entrance")   # landing surface, P03 (S02)
box("Entrance_Mat", 6.90, 6.90, 0, 7.65, 7.40, 0.01, c["DARK"], "Entrance", check=False)
box("Bedroom_Rug", 9.30, 0.60, 0, 11.60, 3.30, 0.01, c["RUG"], "Bedroom", check=False)
box("Bathroom_Mirror", 8.05, 5.85, 1.10, 8.07, 6.55, 1.90, c["GLASS"], "Bathroom", tr=30)
cyl("Shower_Head", 8.45, 7.45, 2.05, 0.12, 0.02, c["STEEL"], "Bathroom", item="Shower_Head")
box("Shower_Arm", 8.43, 7.45, 2.07, 8.47, 7.70, 2.10, c["STEEL"], "Bathroom", item="Shower_Head")
box("Towel_Warmer", 10.20, 6.45, 0.50, 10.25, 6.95, 1.50, c["STEEL"], "Bathroom")
box("Closet_Mirror", 10.35, 5.20, 0.30, 10.37, 6.00, 2.00, c["GLASS"], "Walk_in_Closet", tr=30)

# ======================= USES, ROUTES, CLEARANCES =======================
entrance(7.10, 7.25)
# where a person steps into the seat: L0 in front of the seat (80 cm leg zone); A-C at the sofa's open north end,
# because a 40 cm coffee-table gap is a leg zone, not a route
destination("Living: sofa (in front of seat)" if LIV == "L0" else "Living: sofa (open end)",
            *{"L0": (3.00, 2.00), "A": (3.85, 3.85), "B": (3.85, 3.85), "C": (3.65, 3.85)}[LIV])
destination("Living: armchair", *{"L0": (2.70, 1.10), "A": (1.80, 2.45), "B": (2.70, 3.95), "C": (2.50, 3.95)}[LIV])
destination("Living: table east side", 6.75, 6.10)
destination("Kitchen: sink", 2.30, 6.60)
destination("Kitchen: fridge/oven tall units", 1.30, 6.00)
destination("Entrance: wardrobe", 7.45, 5.70)
destination("Bedroom: bed south side", 11.00, 0.65)
destination("Bedroom: bed north side", 11.00, 3.22)
destination("Bedroom: desk", 8.00, 1.48)
destination("Bathroom: washbasin", 8.90, 6.20)
destination("Bathroom: WC", 9.30, 6.15)
destination("Bathroom: shower", 9.00, 7.20)
destination("Closet: in front of units", 11.10, 6.00)
destination("Night hall: utility cupboard", 11.30, 4.20)
route("Night route bed -> WC", "Bedroom: bed north side", "Bathroom: WC")
electrical("Washing_Machine", "Towel_Warmer")
wet_zone("Shower open side (south)", 8.75, 6.10, 9.44, 6.70)
private_room("Bedroom")
intimate("WC_Wall_Hung", "Bed_Frame")              # screened from the entrance, the table, the stools and the sofa (L25)
viewpoint("sofa", SX + 0.45, (SY0 + SY1) / 2, seated=True)

clearance("Entrance -> night zone: table / entrance wardrobe", "Table_Top", "Entrance_Wardrobe", kind="passage")
clearance("Entrance -> night zone: south chair / partition", "Chair_3", "Partition_Living", kind="passage")
clearance("Kitchen: island / base units", "Island_Top", "Worktop", kind="aisle")
clearance("Kitchen: island / tall units", "Island_Top", "Tall_Units_Fridge_Oven", kind="passage")
clearance("Night hall: width", "Partition_Bedroom", "Partition_Hall_North", kind="corridor")
clearance("Bedroom: bed south side", "Bed_Frame", "Wall_South", kind="bed_side")
clearance("Bedroom: bed north side", "Bed_Frame", "Partition_Bedroom", kind="bed_side")
clearance("Closet: in front of east unit", "Closet_Unit_East", "Partition_Bathroom_Closet", 0.90, 1.00)

not_verifiable("Living window 4.60 m rough opening", "lintel to be sized by a structural engineer")
not_verifiable("Bathroom and closet ventilation", "mechanical extraction to be designed (pre-mortem S21, S25)")
not_verifiable("Bedroom acoustics", "10 cm partition next to the dining area; specify an acoustic partition (S16)")

# ======================= REQUIREMENTS (ids as in brief.md) =======================
requirement("R01", "Bathroom, kitchen, bedroom, wardrobe, hall", ("Routes/Bathroom*", "Routes/Kitchen*", "Routes/Bedroom*", "Routes/Closet*"),
            ("WC_Wall_Hung", "Base_Units", "Bed_Frame", "Closet_Unit_East", "Partition_Hall_North"))
requirement("R02", "Doors open without hitting fixtures or furniture", ("Openings/*", "Handles/*", "Reveals/*"))
requirement("R03", "Entrance open to the living area", satisfied_by=("Door_Entrance_Leaf",), manual=True)
requirement("R04", "Night zone closed by a door", ("Openings/Door_Night_Zone*", "Privacy/*"), ("Door_Night_Zone_Leaf",))
requirement("R05", "Rooms that do not feel oppressive", ("Light and air/*occupancy",))
requirement("R06", "Modern style", manual=True)
requirement("R07", "TV not next to a window on the same wall", ("Brief constraints/TV*",), ("TV_65",))
requirement("R08", "Daylight in habitable rooms", ("Light and air/Living area", "Light and air/Bedroom"))

# ======================= PLAN ANNOTATIONS =======================
dimensions([0, 0.95, 5.55, 8.15, 10.65, 12.5], True, -0.5)
dimensions([0, 0.3, 6.45, 6.55, 12.2, 12.5], True, -0.9)
dimensions([0, 12.5], True, -1.3)
dimensions([0, 0.3, 1.35, 3.25, 6.75, 7.80, 9.50, 10.20, 12.2, 12.5], True, 8.6)
dimensions([0, 0.3, 7.7, 8.0], False, -0.6)
dimensions([0, 8.0], False, -1.0)
dimensions([0, 0.3, 3.55, 3.65, 4.75, 4.85, 7.7, 8.0], False, 13.1)
for t, x, y in [
    ("D 90x210 armored - opening 105x220", 7.275, 8.25), ("D 90x210 sliding, frosted glass", 5.70, 4.20),
    ("D 80x210 - opening 90x215", 7.40, 2.55), ("D 80x210", 8.65, 4.56), ("D 70x210 sliding", 10.85, 4.42),
    ("UC", 11.975, 4.20), ("W 180x100 sill h120 - tilt-and-turn", 2.30, 8.25), ("W 60x60 h160", 9.85, 8.25),
    ("FW 450x240 sliding", 3.25, -0.25), ("FW 240x240 sliding", 9.40, -0.25),
]:
    label(t, x, y)
note("Wall openings enlarged by 5 cm per side for subframes/jambs (7.5 cm armored door)  -  "
     "D = door, W = window, FW = French window, UC = utility cupboard  -  4.60 m opening: lintel to be sized by a structural engineer")

verify(write_report=PARAMS.get("report", True), quiet=PARAMS.get("quiet", False))
