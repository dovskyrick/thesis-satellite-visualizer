# 14 — PR 1 description (paste into GitHub)

Paste the block below into the PR description box. Replace `#<n>` with the issue number from `10-…`.

---

**Title:** `feat: add optional body axes overlay`

**Body:**

Closes #<n>

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
- **Manual check in Grafana:** with the provisioned TestData dashboard, plus synthetic data with known
  attitudes (nadir-pointing LVLH, and pointing at a ground location). The axes pointed as expected,
  kept their screen size across zoom, worked in Point and Model mode, and disappeared outside the data range.

## Not included / open questions

- **No new E2E test.** Whether the axes point the right way is hard to assert in Playwright, so I
  relied on unit tests plus a manual check. Happy to add one if you'd prefer.
- **Model frame:** the sample Duck glTF doesn't line up with the body axes. I assume its model frame
  differs from the body frame. Is that expected for the assets you use?
- **Quaternion convention:** the code uses `q_B_ECI` as body → ECI (`v_ECI = R(q) v_B`). I matched
  that. Could you confirm this is the OSTk convention?

Feedback welcome. I'm happy to change naming, defaults or scope.
