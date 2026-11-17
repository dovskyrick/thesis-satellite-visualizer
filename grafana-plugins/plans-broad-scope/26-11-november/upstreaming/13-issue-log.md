# 13 — Issue log (upstream plugin)

Small problems found along the way in Lucas's plugin that aren't part of the current PR.
Priority runs from 1 to 10, where 10 is the highest. Log the issue, don't fix it in passing: each fix becomes its own
small PR (or an upstream issue) once its priority justifies it.

| # | Priority | Area | Issue | Status |
| --- | --- | --- | --- | --- |
| 1 | 2/10 | Cesium viewer state | Changing a panel setting resets parts of the Cesium view, e.g. the chosen base layer (Earth map texture) | Logged only |

## 1 — Panel setting changes reset the Cesium view

**Seen:** when any Grafana panel option is changed, some state inside the Cesium window is
reset instead of preserved. The clearest case is the base layer picked in the BaseLayerPicker,
which goes back to the default imagery.

**Expected:** user choices made inside the viewer (base layer and similar) survive option
changes.

**Likely solved in the fork:** Ricardo believes the thesis plugin already handles this. A starting
point to check is `grafana-plugins/3d-orbit-attitude-plugin/src/components/SatelliteVisualizer.tsx`:
the `<Viewer key={viewerKey}>` remount control and the BaseLayerPicker ref-callback that sets
`selectedImagery` (around lines 1539 and 1580–1630). Probable cause upstream: the Resium `Viewer`
is re-created when options change, and a new Viewer starts from the default imagery.

**Plan:** find the fork's mechanism, port it as one small `fix:` PR. Super low priority, so only log it for now.
