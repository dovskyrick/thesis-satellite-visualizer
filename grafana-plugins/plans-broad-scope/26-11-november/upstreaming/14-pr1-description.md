# 14 — PR 1 description (paste into GitHub)

Paste the block below into the PR description box. The issue is open-space-collective/satellite-visualizer#15.

---

**Title:** `feat: add optional body axes overlay`

**Body:**

Closes #15

## What

An optional overlay of the satellite body frame axes (X, Y, Z), drawn from the existing
orientation data. It is off by default, so existing dashboards are unchanged, and the data
format is unchanged.

- New options: `Show body axes` (default off) and `Body axes length` in pixels (default 100,
  only shown when enabled). The length is in pixels so the axes keep their on-screen size when
  zooming, like `modelMinimumPixelSize`.
- Axes are light grey with X/Y/Z labels. They follow the existing `q_B_ECEF` orientation, so they match the model.
- README: one line under setup.

## Testing

- **Unit tests (Jest), 12 new tests:** axis maths (identity, 90° rotation, orthogonality and length
  for any orientation), pixel-to-metre conversion, rendering (one labelled arrow per axis, nothing
  outside the data time range, listener cleanup, no crash before the viewer is ready), and the panel option
  (hidden by default, shown with the configured length when enabled). Resium is mocked as in the existing test.
- `lint`, `typecheck` and `test:ci` pass, and the existing smoke test is unchanged.
- **Manual check in Grafana:** with the provisioned TestData dashboard, plus synthetic trajectories with
  known attitudes: nadir-pointing LVLH, inertially fixed (identity quaternion), and pointing at a ground
  location. All three pointed as expected, which also exercises the existing ECI → ECEF conversion. The axes
  kept their screen size across zoom, worked in Point and Model mode, and disappeared outside the data range.

## Not included / open questions

- **No new E2E test.** Whether the axes point the right way is hard to assert in Playwright, so I
  relied on unit tests plus a manual check. Happy to add one if you'd prefer.

Feedback welcome. I'm happy to change naming, defaults or scope.

---

## Notes (2026-11-17)

Ricardo removed the model-frame and quaternion-convention questions before submitting. In his
view the Duck *is* oriented consistently with the attitude. Its centre of mass is just offset from the entity
origin, and Point mode shows the axes centred correctly. These can go back to Lucas later if needed.
