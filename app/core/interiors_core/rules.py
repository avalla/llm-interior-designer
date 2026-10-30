"""Default thresholds for models built outside FreeCAD (imported plans). Same values as RULES in lib/interiors.py,
whose source is docs/design-rules.md; app/tests/parity.py fails if the two drift apart."""
RULES = dict(
    frame=0.05, armored_frame=0.075, reveal=0.10, handle=0.07, seat_min=0.75, seat_comfort=0.90, access=0.70,
    person_radius=0.30, daylight=1 / 8, occupancy=0.40, tv_window=1.0, seat_height=(0.25, 0.32), assembly_margin=0.02,
    tol=1000.0, placement=0.02,
    occupancy_min=0.10, eye_standing=1.60, eye_seated=1.15,
    clearances=dict(corridor=[1.00, 1.10], passage=[0.80, 0.90], aisle=[0.90, 1.10], bed_side=[0.60, 0.70]),
    appliance_door=dict(dishwasher=0.60, oven=0.50, drawer=0.50),
    min_area=dict(bedroom=14.0, single_bedroom=9.0, living=14.0),
    service_area=dict(laundry=6.0), service_factor=2.0,
)
HABITABLE = ("bedroom", "single_bedroom", "living", "dining", "kitchen")
THROUGH = ("living", "dining", "kitchen")
