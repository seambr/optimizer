from __future__ import annotations
from laser import get_bex_index, set_bex_index
from results import PointData
# from beamsquare import get_beam_centroid


FULL_ROTATION = 300_000
WINDOW_DIVIDER = 4
DISTANCE = 5190




sample = PointData.from_csv("./data/sample_point_data.csv")

print(sample.get_total_divergence(DISTANCE))


current_motor_index = get_bex_index()
