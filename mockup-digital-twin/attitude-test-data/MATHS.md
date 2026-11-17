# Attitude test data: maths plan

This is the planning note for `generate_attitude_csv.py`. It fixes the conventions
first and then turns each attitude profile into a few lines of maths. The code
follows this document one to one.

## 1. What Lucas's plugin does with a row

From `src/components/SatelliteVisualizer.tsx` (upstream, `feat/body-axes`):

```
x_ECEF   = Cartesian3.fromDegrees(lon, lat, alt)          // WGS-84 geodetic -> ECEF
q_B_ECI  = Quaternion(x, y, z, s)                          // columns 5..8, scalar last
q_B_ECEF = conj(q_ECI_ECEF) * q_B_ECI                      // q_ECI_ECEF from computeFixedToIcrfMatrix
axis_ECEF = R(q_B_ECEF) * e_body                           // bodyAxes.ts
```

So `R(q_B_ECI)` maps **body coordinates to ECI coordinates**: `v_ECI = R · v_B`.
The columns of `R` are the body X, Y and Z axes written in ECI. That gives us
the recipe: build the three body axes as ECI unit vectors, stack them as columns, and
convert the matrix to a quaternion. This also answers open question 4 in
`12-session-handoff.md` for the plugin: the quaternion is used as body→ECI (active).

## 2. Time

`t` is Unix time in ms (UTC). Julian date `JD = t/86 400 000 + 2 440 587.5`,
centuries `T = (JD − 2 451 545.0)/36 525`. We use UTC for UT1 and TT. The 69 s
TT−UTC offset moves precession by about 10⁻⁶ °. Cesium also assumes UT1 = UTC when no EOP
data is loaded.

## 3. ECI ↔ ECEF (must match Cesium closely)

Cesium's `computeIcrfToFixedMatrix` uses the full IAU 2006 model. We reproduce it to
about 20″ (0.006°) with two classic pieces, no library needed:

- **Precession (IAU 1976)**, angles in arcseconds:
  `ζ = 2306.2181T + 0.30188T² + 0.017998T³`,
  `z = 2306.2181T + 1.09468T² + 0.018203T³`,
  `θ = 2004.3109T − 0.42665T² − 0.041833T³`,
  `P = R3(−z) · R2(θ) · R3(−ζ)` (J2000 → mean of date).
- **Earth rotation (GMST, IAU 1982)**, in seconds:
  `67 310.54841 + (876 600·3600 + 8 640 184.812866)T + 0.093104T² − 6.2·10⁻⁶T³`.

`C(t) = R3(GMST) · P` maps ECI → ECEF and `Cᵀ` maps back. `R2` and `R3` are frame
rotations, e.g. `R3(a) = [[c, s, 0], [−s, c, 0], [0, 0, 1]]`.

We leave out nutation (≤ 20″), frame bias (0.02″) and polar motion (Cesium also leaves it out
without EOP data). `verify_against_astropy.py` checks the remaining gap against
astropy's GCRS → ITRS.

## 4. Orbit

Circular orbit, altitude 500 km, inclination 97.4° (sun-synchronous-like), radius
`a = 6378.137 + 500` km, mean motion `n = √(μ/a³)`, period ≈ 94.6 min.

```
P̂ = ( cosΩ,        sinΩ,       0    )
Q̂ = (−cos i sinΩ,  cos i cosΩ, sin i)
u(t) = u₀ + n (t − t_mid)
r = a (cos u P̂ + sin u Q̂)        v̂ = −sin u P̂ + cos u Q̂        ĥ = P̂ × Q̂
```

**Pass over Lisbon at `t_mid`.** Put Lisbon's geocentric unit vector into ECI at
`t_mid` (`s = Cᵀ s_ECEF`), with declination `δ` and right ascension `α`. An ascending pass
through it needs `sin u₀ = sin δ / sin i` and `Ω = α − atan2(cos i sin u₀, cos u₀)`.

**Profile B orbit.** Same maths with `i = 10°` and target `(lat 0°, lon −9.1393°)`, so `u₀ = 0`.
Its inertial Z then stays 80–100° from local up, flat and pointing north.

**Row output.** `r_ECEF = C(t) r`, then an iterative ECEF → WGS-84 geodetic
conversion (Bowring start, 5 iterations, < 1 mm). This is the exact inverse of `Cartesian3.fromDegrees`, so
the plugin recreates our ECEF point.

## 5. Attitude profiles (columns x, y, z in ECI)

| Profile | Body axes | What the user must see |
| --- | --- | --- |
| **A. LVLH, nadir** | `z = −r̂`, `y = −ĥ`, `x = y × z` (= v̂) | Z points at Earth's centre, X along the track, Y across it |
| **B. Inertial** | `x, y, z = ECI axes` (identity, q = 0,0,0,1) | Z parallel to Earth's spin axis everywhere. The axes don't turn with the orbit |
| **C. Lisbon tracking** | `z = unit(g − r)`, `x = unit(v̂ − (v̂·z) z)`, `y = z × x` | Z points at the Lisbon marker. During the overhead pass it sweeps fast |

`g` is Lisbon (38.7223° N, 9.1393° W, 0 m) in ECEF, rotated to ECI with `Cᵀ(t)`.
In C, `z` can never be parallel to `v̂`: a line tangent to the orbit stays above radius
`a`, and Lisbon sits below it. The code still falls back to `ĥ` below 10⁻⁶.

Note: "nadir" here is geocentric (towards Earth's centre). Geodetic nadir differs by up to
0.19° at mid-latitudes, which you can't see on screen.

## 6. Matrix → quaternion

Shepperd's method (pick the largest of `trace, R₁₁, R₂₂, R₃₃` to avoid dividing by a
small number), scalar last `(x, y, z, s)`, same convention as Cesium's
`Quaternion.fromRotationMatrix`. Then **sign continuity**: if `q_i · q_{i−1} < 0`,
negate `q_i` (same rotation, no 360° spin when interpolating; see `07-…`).

## 7. Self-check (built in, runs on every generation)

For every written row, from the **rounded CSV values**: geodetic → ECEF → ECI, quaternion →
matrix, then recompute the intended axis and measure the angle. The check passes when
A (Z vs nadir), B (Z vs ECI pole) and C (Z vs Lisbon) all stay below 0.01°. The
generator stops with an error if any row fails.

## 8. Sampling

The default step is 10 s over one orbit (≈ 570 rows). Profile C turns at up to ~0.9°/s
overhead, so a 30 s step (Lucas's sample data) would leave ~26° between samples.
At 10 s the interpolation error between samples stays well under a degree.
