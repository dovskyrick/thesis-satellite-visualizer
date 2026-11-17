# 11 — PR 1 human test (body axes)

Branch `feat/body-axes` on `dovskyrick/satellite-visualizer`.

## Setup

Clone your fork, `git checkout feat/body-axes`, `npm install`, `npm run build`, then
`npm run server`. Open http://localhost:3000 (admin/admin).

## Unit tests yourself

`npm run test:ci`: expect 18 passed. Also `npm run lint` and `npm run typecheck`:
both should print no errors.

## Default unchanged

Open the "Satellite Visualizer Test Data" dashboard. No arrows should appear.
Everything should look exactly like before.

## Turn it on

Edit a panel and switch on **Show body axes**. Three light-grey arrows labelled X, Y, Z
should appear on the satellite. **Body axes length** should then appear in the settings.

## Length

Change the length (e.g. 50, 300). The arrows resize. Zoom in and out: the arrows
keep roughly the same screen size, like the model does.

## Motion and time

Play the animation, or hover a time series with shared crosshair. The arrows should
follow the satellite and rotate smoothly. Outside the data time range they disappear.

## Attitude sanity

The axes must look orthogonal and right-handed: X cross Y gives Z. The duck's
shape won't match the axes. That's expected, since the glTF model frame differs (question for Lucas).

## Point mode

Switch **Display mode** to Point. The axes still show and rotate, which shows the
attitude even without a 3D model.

## Report back

Note anything odd: colour, label overlap with the model, default length 100 too
short or long, flicker. I'll adjust before you open the PR.

## Result (2026-11-17): passed

Ricardo ran the manual test on `feat/body-axes` (WSL, `npm run dev` + `docker compose up`,
TestData dashboard). **Successful, no bugs found.** The body axes keep a constant screen size
at every zoom level, which is the intended behaviour (length is set in pixels). Next: post the
issue (`10-…`) and open the PR. For deeper attitude checks, use the profiles in
`mockup-digital-twin/attitude-test-data/` (LVLH nadir, inertial, Lisbon tracking).

## Attitude profiles (2026-11-17)

Ricardo loaded the three CSVs from `mockup-digital-twin/attitude-test-data/`.

- **A (LVLH nadir): passed.** Z points down, X along the track.
- **C (Lisbon tracking): passed.** Z points at the Lisbon marker.
- **B (inertial): looked wrong.** Ricardo expected static axes, and they visibly moved.

**Likely explanation, not a bug:** the data is right. Re-checked numerically, Z stays within 0.15° of
Earth's axis on every row, and that 0.15° is precession since J2000. The plugin uses `tracked={true}`, so the camera
follows the satellite's local frame. Inertial axes then *have* to swing on screen: Z is ~10° from
local up near the north pole, ~90° at the equator and ~170° near the south pole. A and C look calm
because they are tied to the local frame. The B section in the data README now gives the correct
criterion (Z parallel to the globe's polar axis).

**Decision:** the PR 1 manual tests are archived as **successful**. A and C are harder and depend on
the same ECI → ECEF code as B, so they already exercise it. If a retest of B with the new criterion still fails,
treat it as a data or test-design problem, not a plugin bug.

**Update:** Ricardo re-checked B fully zoomed out, and it is almost certainly correct. For an easier
retest, B now flies a 10° near-equatorial orbit (`B-inertial-equatorial.csv`). Z stays flat, pointing north (80–100°
from local up), and X/Y turn around it once per orbit.
