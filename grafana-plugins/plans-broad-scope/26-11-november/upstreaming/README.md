# Upstreaming: fork → Lucas Brémond's official plugin

Working notes for moving features from this fork into
[open-space-collective/satellite-visualizer](https://github.com/open-space-collective/satellite-visualizer),
one feature per pull request. This branch (`upstreaming`) only holds planning markdowns.

## Files

| File | Purpose |
| --- | --- |
| `01-gap-analysis.md` | How the fork and upstream differ today |
| `02-feature-roadmap.md` | Every feature split into PR-sized pieces, ordered, with difficulty |
| `03-pr1-plan.md` | Detailed plan for the first PR |
| `04-pr-quality-checklist.md` | What "clean for delivery" means for each PR |
| `05-eci-ecef-investigation.md` | Why the fork's quaternion frame differs from Lucas's |
| `06-data-adapter-interfaces.md` | Data interfaces (adapters): verdict and timeline |
| `07-eci-ecef-maths-and-policy.md` | Is ECI→ECEF maths risky? Where conversion should live |
| `08-best-practices-primer.md` | General engineering, testing, TS and React practices, applied here |
| `09-open-space-collective-practices.md` | House practices of Lucas's organisation |
| `10-pr1-issue-draft.md` | Issue text to open before the body-axes PR |
| `11-pr1-human-test.md` | Ricardo's manual test checklist for body axes |

## Two sides, two standards

**Here (fork):** messy is fine. Discussion, dead ends, rough notes.

**Upstream (Lucas):** one feature per PR, small diff, tests, README section,
conventional-commit messages (`feat:`, `fix:`, `test:`), lint + typecheck + tests green.

## Working agreement (2026-11-11)

- **Claude writes and runs unit tests only** (Jest: pure functions, plus components with Resium faked).
  It does not write new E2E/Playwright tests or run Grafana for visual checks.
- **Ricardo does the user testing**: runs Grafana, looks at the result, decides if it's right.
  Each PR gets a short human-test checklist here (e.g. `11-…`).
- Lucas's existing CI (including its E2E smoke test) still runs on every PR; we just don't extend it.
- Why: AI-generated E2E suites are slow and brittle and can bottleneck development. Unit tests
  plus a human eye cover correctness at MVP speed.
- Planning lives here (thesis repo, `upstreaming` branch); Lucas's repo only gets clean feature code.

## Workflow per feature

Read fork code → write a port plan here → re-implement cleanly on a fresh
branch of upstream `main` (never copy the 3 000-line fork component whole) →
add tests → open PR from a GitHub fork of upstream → address Lucas's review →
log what was learned back here.
