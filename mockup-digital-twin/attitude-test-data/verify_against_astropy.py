#!/usr/bin/env python3
"""Optional: compare the generator's light ECI->ECEF model with astropy (GCRS -> ITRS).

Needs `pip install astropy`. Not required to generate data; it only backs the accuracy claim in MATHS.md.
"""

import warnings

import numpy as np
from astropy import units as u
from astropy.coordinates import GCRS, ITRS, CartesianRepresentation
from astropy.time import Time
from astropy.utils import iers

from generate_attitude_csv import angle_deg, eci_to_ecef, mat_vec

iers.conf.auto_download = False  # like Cesium without EOP data: UT1 = UTC, no polar motion
warnings.simplefilter("ignore")

worst = 0.0
for iso in ["2026-01-15T12:00:00", "2026-06-01T00:00:00", "2030-12-31T18:00:00"]:
    t = Time(iso, scale="utc")
    t_ms = (t.unix * 1000)
    for axis in np.eye(3):
        gcrs = GCRS(CartesianRepresentation(*(axis * 7000) * u.km), obstime=t)
        itrs = gcrs.transform_to(ITRS(obstime=t)).cartesian.xyz.to_value(u.km)
        ours = mat_vec(eci_to_ecef(t_ms), tuple(axis * 7000))
        worst = max(worst, angle_deg(tuple(itrs), ours))
print(f"Worst axis difference vs astropy: {worst * 3600:.1f} arcsec ({worst:.5f} deg)")
