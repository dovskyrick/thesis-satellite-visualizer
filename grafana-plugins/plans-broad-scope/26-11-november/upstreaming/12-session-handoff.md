# 12 — Session handoff (read this first in a new chat)

Last updated 2026-11-17. Read `README.md` (working agreement) next, then `02-…` (roadmap).

## Repos and branches

| Repo | Role | Branch that matters |
| --- | --- | --- |
| `dovskyrick/grafana-satellite-visualizer` (thesis fork, may be renamed) | Planning docs only | `upstreaming` (from `main`; ignore `dev` and the naive Claude branch) |
| `dovskyrick/satellite-visualizer` | GitHub fork of Lucas's repo | `feat/body-axes` (PR 1); `main` mirrors Lucas, never commit to it |
| `open-space-collective/satellite-visualizer` | Lucas's official plugin | Target of PRs only |
| `dovskyrick/cv-ricardo-santos` | CV; Lucas contact notes on branch `claude/main` | — |

If a repo was renamed on GitHub, the old URL redirects. Attach it with `add_repo` under the new name.

## Current state

- PR 1 (body axes) is implemented, commit `ae4a246`. 18/18 tests pass; lint, typecheck, prettier and build are clean.
- Human test **passed** on 2026-11-17, with no bugs and axes at constant screen size across zoom (`11-…`).
- **Waiting on Ricardo:** posting the issue (`10-…`), then opening the PR.
- Attitude test data for visual checks: `mockup-digital-twin/attitude-test-data/` (3 profiles, self-checked).
- Issue log started: `13-…` (base layer reset on option change, priority 2/10).
- Not yet started: PR 1b (adapter refactor, `06-…`).

## Decisions already made (don't re-ask)

- One feature per PR, conventional commits, squash-merged upstream, branch per PR, delete after merge.
- Unit tests only from Claude; Ricardo does visual testing; no new E2E tests.
- Axes are light grey (`Color.LIGHTGRAY`) with X/Y/Z labels, off by default, length in pixels (default 100).
- Trust Lucas's ECI→ECEF code; keep ECI as the default; an ECEF option comes later in the adapter PR.
- Keep Lucas's `X_A_B` naming (right to left, OSTk house style).
- Archived: uncertainty ellipsoids, source reliability, digital twin and scenarios.

## Technical gotchas

- The fork's April docs `53`, `54`, `61` (ICRF claim) are wrong. Cesium orientation is ECEF (`05-…`).
- Fork code has `console.log`, `any`, `localStorage`, and a 3 000-line component. Re-implement, never copy.
- Jest: Cesium's `Transforms.preloadIcrfFixed` tries to download data, so mock it as in
  `src/components/__tests__/SatelliteVisualizer.bodyAxes.test.tsx`.
- Lucas's existing test already prints an `act(...)` warning, and the build prints 3 bundle-size warnings. Both are pre-existing, not ours.
- Use public Cesium APIs (`camera.getPixelSize`), not internals like `sseDenominator`.
- Upstream is on Grafana 12 / Cesium 1.140, while the fork was on 10 / 1.112.

## Open questions for Lucas

1. Does the glTF model frame match the body frame in his data? (The Duck doesn't line up with the axes.)
2. Settings that only appear when the data supports them, via `showIf(options, data)` (`06-…`).
3. Sensor definition format: a panel-option editor instead of `meta.custom`.
4. Is the attitude quaternion active or passive in OSTk convention? The plugin code uses it as body→ECI
   (`R(q)·v_B = v_ECI`). The attitude test data follows that. Confirm it matches OSTk's `q_B_GCRF`.

## Next actions for Claude

After PR 1 merges: sync the fork's `main`, delete `feat/body-axes`, and update the refactor
ledger in `02-…`. Then branch `refactor/data-adapters` for PR 1b: extract parsing into
`legacyEightColumn` with zero behaviour change, add the ECI/ECEF tests from `07-…`, and
replace the `!` on `computeFixedToIcrfMatrix`.
