"""Default thresholds for models built outside FreeCAD (imported plans). Same values as RULES in lib/interiors.py,
whose source is docs/design-rules.md; app/tests/parity.py fails if the two drift apart."""
RULES = dict(
    frame=0.05, armored_frame=0.075, reveal=0.10, handle=0.07, seat_min=0.75, seat_comfort=0.90, access=0.70,
    person_radius=0.30, daylight=1 / 8, occupancy=0.40, tv_window=1.0, seat_height=(0.25, 0.32), assembly_margin=0.02,
    tol=1000.0, placement=0.02,
)
