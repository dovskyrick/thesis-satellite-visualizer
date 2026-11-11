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
