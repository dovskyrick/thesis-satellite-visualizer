# Attitude test data (for body axes and future rotation work)

Fictional data in Lucas Brémond's 8-column format, with attitudes whose correct look is
known in advance. Use it to check by eye that the plugin turns quaternions the right way.
The maths lives in `MATHS.md`. This file covers what to do and what to look for.

**Status:** all three profiles were manually tested and validated in Lucas's plugin (2026-11-17).

## What it is

A pure-Python script (no installs) writes three CSVs and one Grafana dashboard. A and C
use the same orbit: circular, 500 km, 97.4° inclination, one full orbit (~95 min) at 10 s
steps, centred on an ascending pass over Lisbon. B uses a 10° orbit (see below). The
format is `time,longitude,latitude,altitude,q_B_ECI_X,Y,Z,S`, exactly what Lucas's plugin reads.

## How to generate

From this folder run `python3 generate_attitude_csv.py`. Output lands in `output/`:
`A-lvlh-nadir.csv`, `B-inertial-equatorial.csv`, `C-lisbon-track.csv` and `attitude-test-dashboard.json`.
The options are `--start` (UTC ISO time, default `2026-01-15T12:00:00Z`), `--step` (seconds)
and `--out`. Running it again with the same options gives identical files, so they are safe to commit.

## How to load it in Grafana

Start Lucas's plugin as in `11-pr1-human-test.md`. In Grafana go to Dashboards → New →
Import, then upload `output/attitude-test-dashboard.json`. You get three panels side by side:
Point mode, body axes on, timeline and animation visible, and Lisbon as a yellow location.
Alternatively, paste any CSV into a TestData panel's "CSV content" query.

## Profile A: LVLH nadir pointing

Body Z always points at Earth's centre, X points along the direction of flight (follows the
grey trajectory line), and Y points across the track, opposite the orbit normal. **Look for:**
Z straight down into the globe at every moment and X tangent to the track. Played back, the
axes turn once per orbit together with the satellite, like a plane flying level.

## Profile B: inertial (identity quaternion)

The quaternion is `0,0,0,1`, so the body axes are the ECI axes, fixed in space. B flies its own
near-equatorial orbit (10° inclination, crossing the equator below Lisbon), which makes this easy to see.
**Look for:** Z always lies flat, pointing north, parallel to Earth's axis (80–100° from local up).
X and Y turn once per orbit around Z on screen, because the tracking camera follows the satellite.

## Profile C: Lisbon tracking

Body Z points from the satellite to Lisbon, and X is kept as close as possible to the direction
of flight. **Look for:** during the pass (mid timeline) Z hits the yellow Lisbon marker, then
sweeps fast overhead, by up to ~0.9° per second. Away from the pass Z points through the
Earth towards Lisbon. That is correct here, since a real spacecraft would stop at the horizon.

## How correctness is guaranteed

On every run the script re-reads its own rounded CSV values the way the plugin would. It
rebuilds the position and the axes and measures the Z error. It stops with an error above 0.01°.
The latest run gave a worst error of 0.00001°. Its ECI/ECEF model matches astropy within 9″
(`verify_against_astropy.py`, optional, needs `pip install astropy`).

## If something looks wrong

If every profile is wrong in the same way, suspect the plugin's frame or quaternion handling.
If only B is wrong, suspect the ECI → ECEF conversion. If axes point opposite to what's
expected, suspect a conjugate or active/passive mix-up (`07-…`). A 360° spin between two
samples means a sign flip. Note the profile, time and the axis that is off, and report it.

## Why not reuse the twin's `orbit-math.ts`

That propagator fakes ECI → ECEF by subtracting Earth's rotation since the start time,
which isn't anchored to real sidereal time. Its "ECI" is therefore off by an arbitrary angle,
fine for scenarios but useless for checking attitude. The same ideas (circular Keplerian
orbit, 500 km LEO) were reused, but with a real frame model, so the result can be trusted.
