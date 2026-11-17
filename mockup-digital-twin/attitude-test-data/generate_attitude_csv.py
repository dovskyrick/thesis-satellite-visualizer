#!/usr/bin/env python3
"""Generate visually testable attitude data in Lucas Brémond's 8-column CSV format.

Columns: time, longitude, latitude, altitude, q_B_ECI_X, q_B_ECI_Y, q_B_ECI_Z, q_B_ECI_S
(time in Unix ms, geodetic WGS-84 degrees and metres, body->ECI quaternion, scalar last).

Profiles (see MATHS.md):
  A  lvlh-nadir     Z to Earth's centre, X along track, Y = -orbit normal
  B  inertial       identity: body axes = ECI axes (Z parallel to Earth's spin axis), 10 deg orbit
  C  lisbon-track   Z points at Lisbon, X as close to the velocity as possible

Pure Python standard library. Usage:
  python3 generate_attitude_csv.py [--start 2026-01-15T12:00:00Z] [--step 10] [--out output]
"""

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

# --- Constants --------------------------------------------------------------------------------- #

MU_KM3_S2 = 398600.4418
WGS84_A_M = 6378137.0
WGS84_F = 1 / 298.257223563
WGS84_E2 = WGS84_F * (2 - WGS84_F)
ALTITUDE_KM = 500.0
INCLINATION_DEG = 97.4
EQUATORIAL_INCLINATION_DEG = 10.0
LISBON = {"name": "Lisbon", "latitude": 38.7223, "longitude": -9.1393, "altitude": 0.0}
ARCSEC = math.pi / (180 * 3600)
CHECK_TOLERANCE_DEG = 0.01
HEADER = "time,longitude,latitude,altitude,q_B_ECI_X,q_B_ECI_Y,q_B_ECI_Z,q_B_ECI_S"

# --- Small vector / matrix helpers (3-vectors as tuples, matrices as row tuples) ------------- #


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def scale(a, k):
    return tuple(x * k for x in a)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    return math.sqrt(dot(a, a))


def unit(a):
    return scale(a, 1 / norm(a))


def mat_vec(m, v):
    return tuple(dot(row, v) for row in m)


def mat_mul(a, b):
    cols = list(zip(*b))
    return tuple(tuple(dot(row, col) for col in cols) for row in a)


def transpose(m):
    return tuple(zip(*m))


def angle_deg(a, b):
    c = max(-1.0, min(1.0, dot(unit(a), unit(b))))
    return math.degrees(math.acos(c))


def r2(a):
    c, s = math.cos(a), math.sin(a)
    return ((c, 0, -s), (0, 1, 0), (s, 0, c))


def r3(a):
    c, s = math.cos(a), math.sin(a)
    return ((c, s, 0), (-s, c, 0), (0, 0, 1))


# --- Frames (MATHS.md section 2-3) ------------------------------------------------------------ #


def julian_centuries(t_ms):
    return (t_ms / 86_400_000 + 2_440_587.5 - 2_451_545.0) / 36_525


def eci_to_ecef(t_ms):
    """C(t) = R3(GMST) * P, ECI (J2000/ICRF) -> ECEF. Nutation and polar motion omitted."""
    T = julian_centuries(t_ms)
    zeta = (2306.2181 * T + 0.30188 * T**2 + 0.017998 * T**3) * ARCSEC
    z = (2306.2181 * T + 1.09468 * T**2 + 0.018203 * T**3) * ARCSEC
    theta = (2004.3109 * T - 0.42665 * T**2 - 0.041833 * T**3) * ARCSEC
    precession = mat_mul(r3(-z), mat_mul(r2(theta), r3(-zeta)))
    gmst_s = 67310.54841 + (876600 * 3600 + 8640184.812866) * T + 0.093104 * T**2 - 6.2e-6 * T**3
    gmst = math.radians((gmst_s % 86400) / 240)
    return mat_mul(r3(gmst), precession)


def geodetic_to_ecef(lon_deg, lat_deg, alt_m):
    """Same as Cesium's Cartesian3.fromDegrees on WGS-84."""
    lon, lat = math.radians(lon_deg), math.radians(lat_deg)
    n = WGS84_A_M / math.sqrt(1 - WGS84_E2 * math.sin(lat) ** 2)
    return (
        (n + alt_m) * math.cos(lat) * math.cos(lon),
        (n + alt_m) * math.cos(lat) * math.sin(lon),
        (n * (1 - WGS84_E2) + alt_m) * math.sin(lat),
    )


def ecef_to_geodetic(r):
    x, y, z = r
    lon = math.atan2(y, x)
    p = math.hypot(x, y)
    lat = math.atan2(z, p * (1 - WGS84_E2))
    for _ in range(5):
        n = WGS84_A_M / math.sqrt(1 - WGS84_E2 * math.sin(lat) ** 2)
        alt = p / math.cos(lat) - n
        lat = math.atan2(z, p * (1 - WGS84_E2 * n / (n + alt)))
    n = WGS84_A_M / math.sqrt(1 - WGS84_E2 * math.sin(lat) ** 2)
    alt = p / math.cos(lat) - n
    return math.degrees(lon), math.degrees(lat), alt


# --- Quaternions (MATHS.md section 6) --------------------------------------------------------- #


def matrix_to_quaternion(m):
    """Shepperd's method, scalar last (x, y, z, s), Cesium's Quaternion.fromRotationMatrix convention."""
    (m00, m01, m02), (m10, m11, m12), (m20, m21, m22) = m
    trace = m00 + m11 + m22
    if trace >= max(m00, m11, m22):
        s = 2 * math.sqrt(1 + trace)
        q = ((m21 - m12) / s, (m02 - m20) / s, (m10 - m01) / s, s / 4)
    elif m00 >= m11 and m00 >= m22:
        s = 2 * math.sqrt(1 + m00 - m11 - m22)
        q = (s / 4, (m01 + m10) / s, (m02 + m20) / s, (m21 - m12) / s)
    elif m11 >= m22:
        s = 2 * math.sqrt(1 + m11 - m00 - m22)
        q = ((m01 + m10) / s, s / 4, (m12 + m21) / s, (m02 - m20) / s)
    else:
        s = 2 * math.sqrt(1 + m22 - m00 - m11)
        q = ((m02 + m20) / s, (m12 + m21) / s, s / 4, (m10 - m01) / s)
    k = 1 / math.sqrt(sum(c * c for c in q))
    return tuple(c * k for c in q)


def quaternion_to_matrix(q):
    x, y, z, w = q
    k = 1 / (x * x + y * y + z * z + w * w)
    x, y, z, w = (c * math.sqrt(k) for c in (x, y, z, w))
    return (
        (1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
        (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
        (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)),
    )


def axes_to_quaternion(x_axis, y_axis, z_axis):
    """Body axes written in ECI become the columns of R_B->ECI."""
    return matrix_to_quaternion(transpose((x_axis, y_axis, z_axis)))


# --- Orbit (MATHS.md section 4) --------------------------------------------------------------- #


def make_orbit(t_mid_ms, inclination_deg=INCLINATION_DEG, lon_deg=LISBON["longitude"], lat_deg=LISBON["latitude"]):
    """Circular orbit whose ascending pass is right above (lon, lat) (geocentric) at t_mid. Default: Lisbon."""
    a_km = WGS84_A_M / 1000 + ALTITUDE_KM
    n = math.sqrt(MU_KM3_S2 / a_km**3)  # rad/s
    inc = math.radians(inclination_deg)
    s_ecef = unit(geodetic_to_ecef(lon_deg, lat_deg, 0.0))
    s_eci = mat_vec(transpose(eci_to_ecef(t_mid_ms)), s_ecef)
    dec, ra = math.asin(s_eci[2]), math.atan2(s_eci[1], s_eci[0])
    u0 = math.asin(math.sin(dec) / math.sin(inc))
    raan = ra - math.atan2(math.cos(inc) * math.sin(u0), math.cos(u0))
    p_hat = (math.cos(raan), math.sin(raan), 0.0)
    q_hat = (-math.cos(inc) * math.sin(raan), math.cos(inc) * math.cos(raan), math.sin(inc))

    def state(t_ms):
        u = u0 + n * (t_ms - t_mid_ms) / 1000
        r = scale(add(scale(p_hat, math.cos(u)), scale(q_hat, math.sin(u))), a_km * 1000)
        v_hat = add(scale(p_hat, -math.sin(u)), scale(q_hat, math.cos(u)))
        return r, v_hat, cross(p_hat, q_hat)

    period_s = 2 * math.pi / n
    return state, period_s


# --- Attitude profiles (MATHS.md section 5) --------------------------------------------------- #


def lisbon_eci(t_ms):
    g_ecef = geodetic_to_ecef(LISBON["longitude"], LISBON["latitude"], LISBON["altitude"])
    return mat_vec(transpose(eci_to_ecef(t_ms)), g_ecef)


def attitude_lvlh_nadir(t_ms, r, v_hat, h_hat):
    z = scale(unit(r), -1)
    y = scale(h_hat, -1)
    return axes_to_quaternion(cross(y, z), y, z)


def attitude_inertial(t_ms, r, v_hat, h_hat):
    return (0.0, 0.0, 0.0, 1.0)


def attitude_lisbon_track(t_ms, r, v_hat, h_hat):
    z = unit(sub(lisbon_eci(t_ms), r))
    x_raw = sub(v_hat, scale(z, dot(v_hat, z)))
    if norm(x_raw) < 1e-6:
        x_raw = sub(h_hat, scale(z, dot(h_hat, z)))
    x = unit(x_raw)
    return axes_to_quaternion(x, cross(z, x), z)


def expected_z_lvlh(t_ms, r_eci):
    return scale(r_eci, -1)


def expected_z_inertial(t_ms, r_eci):
    return (0.0, 0.0, 1.0)


def expected_z_lisbon(t_ms, r_eci):
    return sub(lisbon_eci(t_ms), r_eci)


PROFILES = [
    ("A-lvlh-nadir", "A. LVLH nadir pointing", attitude_lvlh_nadir, expected_z_lvlh),
    ("B-inertial-equatorial", "B. Inertial (identity), 10° orbit", attitude_inertial, expected_z_inertial),
    ("C-lisbon-track", "C. Lisbon tracking", attitude_lisbon_track, expected_z_lisbon),
]

# --- Generation, self-check, output ----------------------------------------------------------- #


def generate_rows(t_start_ms, step_s, state, period_s, attitude):
    rows, previous = [], None
    count = int(period_s // step_s) + 1
    for i in range(count):
        t_ms = t_start_ms + round(i * step_s * 1000)
        r, v_hat, h_hat = state(t_ms)
        lon, lat, alt = ecef_to_geodetic(mat_vec(eci_to_ecef(t_ms), r))
        q = attitude(t_ms, r, v_hat, h_hat)
        if previous is not None and dot(q, previous) < 0:
            q = tuple(-c for c in q)
        previous = q
        rows.append(f"{t_ms},{lon:.6f},{lat:.6f},{alt:.1f}," + ",".join(f"{c:.7f}" for c in q))
    return rows


def self_check(rows, expected_z):
    """Rebuild everything from the rounded CSV text, as the plugin would, and measure the error."""
    worst = 0.0
    for row in rows:
        t, lon, lat, alt, *q = (float(c) for c in row.split(","))
        r_eci = mat_vec(transpose(eci_to_ecef(t)), geodetic_to_ecef(lon, lat, alt))
        z_body_eci = tuple(col[2] for col in quaternion_to_matrix(q))
        worst = max(worst, angle_deg(z_body_eci, expected_z(t, r_eci)))
    if worst > CHECK_TOLERANCE_DEG:
        raise SystemExit(f"Self-check failed: worst Z error {worst:.5f} deg > {CHECK_TOLERANCE_DEG} deg")
    return worst


def make_dashboard(csv_by_profile, t_start_ms, t_end_ms):
    def iso(ms):
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    datasource = {"type": "grafana-testdata-datasource", "uid": "P53465F745837BCFD"}
    panels = []
    for index, (slug, title, _, _) in enumerate(PROFILES):
        panels.append({
            "datasource": datasource,
            "gridPos": {"h": 16, "w": 8, "x": 8 * index, "y": 0},
            "id": index + 1,
            "title": title,
            "type": "lucasbremond-satellitevisualizer-panel",
            "targets": [{"datasource": datasource, "refId": "A", "scenarioId": "csv_content",
                         "csvContent": csv_by_profile[slug]}],
            "options": {
                "assetMode": "Point", "coordinatesType": "Geodetic", "pointColor": "red", "pointSize": 12,
                "showBodyAxes": True, "bodyAxesLength": 100,
                "trajectoryShow": True, "trajectoryColor": "gray", "trajectoryWidth": 1, "trajectoryDashLength": 16,
                "locations": [LISBON], "locationPointColor": "yellow", "locationPointSize": 10,
                "showAnimation": True, "showTimeline": True, "showBaseLayerPicker": True,
                "subscribeToDataHoverEvent": True, "showCredits": False,
            },
        })
    return {
        "title": "Attitude Test Profiles (body axes)",
        "uid": "attitude-test-profiles",
        "editable": True, "graphTooltip": 1, "schemaVersion": 42, "timezone": "utc",
        "time": {"from": iso(t_start_ms), "to": iso(t_end_ms)},
        "panels": panels,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--start", default="2026-01-15T12:00:00Z", help="UTC start, ISO 8601")
    parser.add_argument("--step", type=float, default=10.0, help="sample step in seconds")
    parser.add_argument("--out", default=str(Path(__file__).parent / "output"), help="output folder")
    args = parser.parse_args()

    t_start_ms = int(datetime.fromisoformat(args.start.replace("Z", "+00:00")).timestamp() * 1000)
    # Pass happens half an orbit after the start. A and C fly over Lisbon (97.4 deg). B crosses the
    # equator below Lisbon on a 10 deg orbit, so its inertial Z stays flat, pointing north (MATHS.md 4).
    _, period_s = make_orbit(t_start_ms)
    t_mid_ms = t_start_ms + int(period_s * 500)
    orbits = {
        "lisbon": make_orbit(t_mid_ms),
        "equatorial": make_orbit(t_mid_ms, EQUATORIAL_INCLINATION_DEG, LISBON["longitude"], 0.0),
    }

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    csv_by_profile, t_end_ms = {}, t_start_ms
    for slug, title, attitude, expected_z in PROFILES:
        state, period_s = orbits["equatorial" if slug.startswith("B") else "lisbon"]
        rows = generate_rows(t_start_ms, args.step, state, period_s, attitude)
        worst = self_check(rows, expected_z)
        csv_text = HEADER + "\n" + "\n".join(rows) + "\n"
        (out / f"{slug}.csv").write_text(csv_text)
        csv_by_profile[slug] = csv_text
        t_end_ms = int(rows[-1].split(",")[0])
        print(f"{slug:16s} {len(rows)} rows, self-check worst Z error {worst:.6f} deg")

    dashboard = make_dashboard(csv_by_profile, t_start_ms, t_end_ms)
    (out / "attitude-test-dashboard.json").write_text(json.dumps(dashboard, indent=2) + "\n")
    print(f"Wrote CSVs and attitude-test-dashboard.json to {out}")


if __name__ == "__main__":
    main()
