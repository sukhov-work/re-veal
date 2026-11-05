# Loop plans (`scripts/research/loop_seq.py render`), 2026-10-30

A plan is a hand-written JSON (no planner model this round) that lays a loop over the registered stills of one
sequence (`loop_seq.py prep` writes them as `k<i>.png` under `benchmarks/runs/<date>/halloween/in/<seq>/`).

```json
{"seq": "talk", "in": "benchmarks/runs/2026-10-30/halloween/in/talk",
 "title": "one line: what differs from the first candidate (optional)",
 "gag": "one line the owner can read as the idea of the clip",
 "timeline": [
   {"key": 0, "hold": 12},
   {"to": 1, "n": 6, "method": "rife", "ease": "accel"},
   {"key": 1, "hold": 8},
   {"to": 0, "n": 9, "method": "rife", "ease": "smooth"}],
 "effects": [{"kind": "breath", "z": 0.02, "cx": 0.5, "cy": 0.35}],
 "matte": {"thr": 14, "grow": 0.015, "feather": 0.01},
 "crf": 14, "gif_long": 540}
```

Timeline steps, in order; the loop is the concatenation, and the last transition lands on the first step's still
(which is not repeated: the loop's frame 0 is that still's hold).
- `{"key": k, "hold": n}`: still k for n frames at 25 fps, byte-exact pixels.
- `{"to": k, "n": N, "method": m, "ease": e}`: N in-betweens from the current still to still k. Methods:
  - `rife`: RIFE v4.26 in-betweens inside the change matte of the two stills, the plain blend outside. Generated
    content (the page says so; the contact sheet marks the frame with a red `g`).
  - `dissolve`: the plain blend (for content that exists in one still only).
  - `morph`: transitions.py's morph (the DIS flow); optional `preset`, `anchors` ("ax,ay,bx,by;..." canvas px),
    `falloff`, `warp`, `color`.
  - `teleport`: `out_box` (content of the current still absent in the next) and/or `in_box` (content of the next
    still absent in the current), both `[x0, y0, x1, y1]` in canvas FRACTIONS; `mode` "squeeze" (the content
    squeezes to a bright vertical line and re-opens; `span` the share of the segment each half takes, `glow`
    the brightness gain at the line) or "fade" (the content fades in place); the rest of the changed area by RIFE.
  - `cut`: no frames (`n` 0).
  - `rewind`: the frames rendered so far from index `from`, played backward every `stride`-th frame.
- Eases map frame i of N to t: `linear`, `smooth` (smoothstep), `snap` (smoothstep twice), `accel` (t²),
  `decel` (1 − (1 − t)²).

Effects run on the finished frame list: `breath` pushes the frame in about (`cx`, `cy`) (fractions) by
1 + z·sin²(πu) over the loop, frame 0 untouched (so the seam is a still).

`matte`: `thr` the Lab distance above which a pixel counts as changed (on 2 px blurred copies), `grow` the dilation
and `feather` the Gaussian feather, both as fractions of the width.

Outputs per render: `loop.mp4` (libx264, the plan's `crf`, yuv420p), `loop.gif` (the plan's `gif_long` px long
edge, a two-pass palette, 40 ms per frame), `sheet.jpg`, `frames.json` (what each frame is), `measure.json`
(the step series on the decoded mp4, the seam step, faces per frame, the double-exposure share per generated frame,
the md5s; since 2026-11-04 also `script_md5` and `rife_version`), `plan.json` (the plan as rendered), and with
`--frames` the folder `frames/` (see the last section).

## `slices` (2026-11-01, the seasons sequence): diagonal cards that slide into place

`{"to": k, "method": "slices", ...}` cuts the canvas into cells and slides the next still into each cell as a card;
with `"through": [..]` the cells cycle on through the listed stills (a wave) and `n` is computed from the schedule
(the plan's `n` is overwritten in `plan.json`). Nothing is generated: a landed cell is the next still's pixels, the
borders are 1 px soft, the moving content is motion-blurred by temporal sub-samples.
- Geometry: `angle` (degrees of the band lines from the horizontal; 62 crosses the wire of the seasons view at about
  88°), `bands` (count across the canvas) or `widths` (relative), `families` 1 (bands) or 2 (a lattice: a second family
  along the band axis, `width2` px, cells indexed i, j), `mirror` (the bands folded about the centre column: chevrons;
  each band is a left and a right half-cell with mirrored slide directions).
- Slide: `slide` `across` (the card enters from the neighbouring side over the cell's width) or `along` (the whole
  band's content rolls along the band by `travel` × the canvas diagonal over the mirrored canvas (`wrap: true` rolls the canvas round instead; the canvas edge then shows as a hard line inside the band) and locks; `ramp` frames of
  alpha at the start of each band). `dir` ±1 the entry side; `alternate` flips it on odd cells; `lattice_axis`
  `alt` | 1 | 2 (which family's normal the lattice cells slide along; `alt` by parity).
- Schedule: `order` `up` | `down` | `centre` | `edges` | `random` (`seed`) | `diag` | `antidiag` (families 2) gives
  each cell a rank; a cell starts at rank × `stagger` frames and takes `dur` frames under `ease`; `period` frames
  between the cell's successive transitions when `through` is given (default: one transition's span, no overlap);
  `flip_each` (default true) reverses the entry side on every second transition, `reverse_each` the rank order.
- Blur: `samples` sub-frames (at least; raised to one per 2 px of the frame's displacement, at most `samples_max` 48)
  over `shutter` of the frame's motion. `shadow` (0–1) and `shadow_px` darken the uncovered side of a card's leading
  edge (default off).

## `sheets` (2026-11-01, round 2 of the seasons): whole pictures that slide across each other

`{"to": k, "method": "sheets", "n": 90, "sheets": [...]}` with `to` = the current still (the base, the only still held): the
listed stills slide across the base as sheets, back to front, over `n` frames, and leave; nothing is generated.
- A sheet: `{"key": k, "side": "+" | "-", "width": 0.8, "carry": 1.0, "lag": 0, "scale": 0.0}`: a band `width` × the
  canvas extent along the slide normal, bounded by edges at `angle`, home at the canvas centre, entering from its `side`
  and leaving at the other under `ease` (`lag` frames late); its content moves with it by `carry` (1: the picture slides and
  is registered with the base only at home; 0: a wipe over the static still; between: a drift behind the edge); `scale`
  enlarges the content about the centre (a depth cue; it misregisters the sheet by scale × the half-size at the edges).
- The sheets travel the VISIBLE extent: with a plan-level `crop` (the centre fraction of the canvas that is output) a sheet
  enters as a sliver under the slow end of the ease and leaves by the step's end. `valid_feather` px softens a picture's own
  edge inside a carried sheet (default 1).
- Step keys: `angle` (62), `ease` (the code's default is `linear`; the seasons plans set `sine`), `feather` px (1.5), `overlap_alpha` (the front sheet's opacity where it covers
  a back sheet; 0.5 shows both), `shadow` and `shadow_px` (a contact shadow ahead of the front sheet's leading edge onto what lies beneath, faded while the sheet is a sliver; `shadow_from` "all" casts from every sheet's leading edge, which turns the gap between two facing edges into a tube),
  `parallax` (the content's move scaled by 1 + parallax × (2 depth − 1) from `in/<seq>/depth_k<i>.npy`, the depth model's
  map saved by the session; near more than far), `shutter` and `samples_max` (motion blur by sub-samples over the frame's
  edge motion, forward window, one per 2 px).
- `objects` (on the base): `[{"name": ..., "box": [x0, y0, x1, y1], "lead": 8, "linger": 14, "seasons": [1, 2]}]` (the code's defaults are lead 6 and linger 10; the seasons plans set 4 and 14), with
  `object_feather` px: per object a GrabCut matte on the base still from the box, and per season the object Poisson-blended
  into the base once (`cv2.seamlessClone`); the plate fades in `lead` frames before that season's sheet reaches the object's
  centre and out `linger` frames after the sheet leaves it. Static plates: no flicker, no per-frame Poisson cost. Boxes and
  pixel knobs are in prep-canvas px; a draft scales them.
- `motion` (2026-11-01, round 3): `normal` (the sheets move along the edge's normal) or `lateral` (the edge keeps its slant at
  `angle`, the sheet moves along x; `side` "+" enters from the right). `edge_depth` px: the wipe edge bends with the base still's
  depth map (`in/<seq>/depth_k<i>.npy`, blurred 8 px), near pixels reached later than far ones by up to that much; the content
  never moves, so every border stays registered (a depth cue with no misalignment).
- Per sheet (2026-11-01, round 4): `dur` (its own sweep length in frames; default the step's remainder after `lag`) and
  `layer` `[lo, hi]` (the sheet applies only where the base still's depth map lies in that range, 0 far .. 1 near, soft over
  `layer_soft` 0.06: sky about [-1, 0.06], far [0.04, 0.3], mid [0.26, 0.62], near [0.56, 2]), so seasons cross by layer.
  `gen_seasons_bands.py` writes a plan of many narrow lateral bands in a seeded random order from the accepted s6.
- Per sheet (round 4b): `layer_y` `[y0, y1]` (prep-canvas rows; the sky layer stops above the skyline, which the depth map
  cannot separate from the far buildings) and `shadow` (its own contact-shadow strength; 0 for a summer band over summer,
  which would otherwise show only as its shadow). The travel includes the feather's half width, so nothing is left at the end.

## The portrait pair (2026-11-04, the angel loop): far-field registration, whole-frame RIFE, a depth sway, a glow

- `prep --bg-depth T [--min-inliers N] [--ecc-refine]`: the SIFT fit uses only keypoints whose relative depth (the depth model's
  map of each scaled still, 0 far .. 1 near) is below T, so a handheld pair of a subject-filled frame registers on the wall,
  not on the people (on the angel pair the all-keypoint fit, 467 inliers, held the people and let the far field drift 16 px; the
  far fit at T 0.15, 31 inliers, held the wall; neither held the lamp, which had moved between the shots). `--min-inliers` lowers
  the fit's floor (40) for a plain wall. `--ecc-refine` refines the far fit by a masked ECC on the far pixels (measured worse on the
  angel pair; off by default). With `--bg-depth` or `--depth-maps` the prep writes `depth_k<i>.npy` for every registered still.
  `--depth-blend lo,hi|auto` warps near pixels by a second, all-keypoint fit, blended from the far fit to the near fit over the
  reference frame's depth range (the camera's parallax between the shots undone per layer): on the angel pair the depth model
  puts the thin ring inside the transition (0.14–0.16), so no range held it; not usable there.
- `prep --lock-window "x0,y0,x1,y1;..."` (reference-frame px; the windows drawn on the still and looked at first): after the fit,
  each map gains the translation that zeroes the windows' mean offset, measured by template match (sub-pixel). The gag object is
  the anchor (the angel pair: three windows on the ring light, within 2.1 px after the lock); the room's drift is RIFE's.
- `matte: {"all": true}`: a `rife` LEG runs on the whole frame (no change matte, no plain blend outside it); a locked or far-field
  registration leaves the rest of the scene's drift as motion, and RIFE carries it with the pose change. A `through` chain, a
  teleport, a slide and a rise keep the change matte (the key is dropped for them; 2026-11-04).
- A `rife` step's `margin` (t runs over [margin, 1 − margin]: no in-between hugs a still; the code's default is 0, the angel plans set 0.04) and `local`
  (`[{"box": [x0, y0, x1, y1], "ease": "snap", "feather": 0.01}]`, canvas fractions): inside each box the in-between is RIFE at
  the box's own ease of u, blended over a feathered edge (two RIFE calls per frame per box). A mouth that opens crosses its
  half-open state, which RIFE draws as teeth through closed lips, in about 3 frames under `snap` while the lean keeps `sine`.
- Effects on the finished frames (frame 0 always untouched, so the seam is a still):
  - `parallax`: `{"kind": "parallax", "amp": 0.014, "ref_at": [fx, fy] | "ref": d, "dir": [1, 0], "shape": "sin" | "pulse",
    "dir2": [0, -1], "shape2": "pulse", "amp2": 0.5, "sigma": 3}`: one remap per frame in which a pixel at relative depth d
    moves by `amp` × W × (d − ref) × wave(u) along `dir` (`sin`: sin 2πu, a sway; `pulse`: sin² πu, one excursion), plus
    `amp2` × that along `dir2` with `shape2` (an orbit); the plane at depth `ref` (or the depth read at `ref_at` in frame 0's
    map) stays put; the maps `depth_k<i>.npy` are blurred `sigma` px and blended per frame by the in-between's t. With a
    `breath` present the two compose into ONE remap (a plan with `breath` alone keeps the old single-warp path, byte-identical).
  - `glow`: `{"kind": "glow", "box": [x0, y0, x1, y1], "thr": 235, "sigma": [0.012, 0.05], "mix": [0.6, 0.4], "gain": 0.15,
    "shape": "pulse"}`: the frame's pixels above `thr` inside `box` (canvas fractions) are blurred at the `sigma` radii
    (fractions of W), mixed by `mix`, and added back at `gain` × wave(u): a light source breathing (a bloom); luminance only.

## Render flags and the `readers` command (2026-11-04 evening, for the studio)

`--progress` and `--frames` are off by default. Without them a render writes the same mp4, gif and stderr as before
(checked on 2026-11-04 with a2 and s6, whose md5s held with and without the flags).
- `render … --progress` prints `PROGRESS i n phase` lines on stderr, each flushed. The phases come in this order:
  - `frames`: `i` counts the timeline's frames produced so far, and `n` is the planned total: the holds plus every
    step's `n`. A `slices` step replaces its `n` by its schedule's count when it starts, and a `rewind` adds its count
    when it runs. `n` is therefore an estimate: s6 plans 165 and renders 164, because a `sheets` step of `n` 135
    renders 134 frames. A line follows each in-between of a `rife` leg or a `through` chain, and every 10th frame of a
    `sheets`, `slices`, `dissolve`, `morph` or `snap` step. Holds, `cut`, `rewind`, `teleport`, `slide` and `rise`
    print no line of their own; the next line counts their frames.
  - `effects`: a line per 10 frames of each breath, parallax or glow pass; `i` counts the frames of that pass.
  - `encode`: `0 N` before the mp4 is encoded and `N N` after the gif.
  - `measure`: one line after `measure.json` and the `--frames` JPEGs are written; `i` is the number of frames decoded
    from the mp4.
- `render … --frames` writes `OUT/frames/f0000.jpg`, `f0001.jpg`, … at JPEG quality 90: the frames decoded from
  `loop.mp4`, the ones the measures read. Older `f*.jpg` in that folder are removed first. At s6's size the folder
  takes 182 MB for 164 frames.
- `measure.json` always records `script_md5` (the md5 of `loop_seq.py` as run) and `rife_version`: the `model` string
  of `benchmarks/runs/2026-10-21/rife/RIFE_MANIFEST.json` when the render loaded RIFE, null when it did not (a
  `sheets` plan).
- `readers PREP_DIR [--out DIR]` reads what each still of a prep folder holds, before a plan is written. `DIR`
  defaults to `PREP_DIR/readers`. It writes `DIR/readers.json`, `DIR/depth_k<i>.jpg` (each depth map stretched
  min..max to 8-bit grey) and one summary line on stdout: `{"stills": n, "faces": [counts], "lab_above_14": [shares]}`.
  `readers.json` holds `prep` (the folder as given), `stills` and `pairs`:
  - a still: `{"still": "k0.png", "size": [W, H], "faces": [[x, y, w, h, score], …], "depth": "depth_k0.npy",
    "depth_stats": {"min", "max", "mean"}, "mean_level", "clipped_high_px", "clipped_low_px", "laplacian_var"}`. The
    faces come from YuNet through `rife_probe.faces_of`, the call the render's measures use: an integer box and the
    score to 3 places. `depth` names the prep folder's map. When `depth_k<i>.npy` is missing, the depth model computes
    it offline and `readers` saves it into the prep folder as `prep` does, so a later `parallax` finds it. The depth
    statistics are rounded to 3 places and `mean_level`, the grey mean, to 1. The clipped counts are the grey pixels
    above 250 and below 5. `laplacian_var` is the variance of the grey still's Laplacian at full size (OpenCV's 3×3
    aperture, `ksize` 1), to 1 place.
  - a neighbouring pair: `{"a": 0, "b": 1, "lab_above_14", "lab_above_30"}`, the shares of pixels whose Lab distance
    between the two stills exceeds 14 and 30, to 4 places. The distance is the one `change_matte` thresholds: on
    2 px blurred copies, before the matte's opening and closing. The shares depend on the registration: the angel
    pair reads 0.3021 on its locked canvas (`in/angel/`) and 0.1964 on the all-keypoint fit without the ring lock.

## 2026-11-05: windows, probe, measure, variants (for the studio)

Four additions, each off unless named: `prep --windows`, the `probe` command, the `measure` command and
`page --variants`. When none is named, `prep`, `render` and `page` write the same bytes as before. Checked on 2026-11-05:
a2 renders `c302623f293eacd069218fd7518e0967` and s6 `5908af3d5300046579548848679b0cbb` with both scripts, the angel
prep's `k*.png` and `depth_k*.npy` equal the recorded `in/angel/` byte for byte, and the angel page rebuilds to
`72dadc4f5ea4db16152fe0c7062a3f94`. A malformed or missing input to any of the four prints one `FAILED: …` line on
stderr and exits 2.

### `prep --windows "name:x0,y0,x1,y1;…"`

The windows are in frame-0 px before the crop, the px of `--lock-window`; each side is 4 px or more. The windows are
measured and never applied: the stills, the depth maps and every other `prep.json` key stay as they are without the flag.
For every frame i ≥ 1 that is not a cut, and every window, the prep finds frame 0's window content in frame i under
each fit below. The match is `_window_shift`, the lock's own measure: a template match over a ±30 px search, sub-pixel
by a parabola.
- `all`: the SIFT fit on every keypoint, direct to frame 0. Under `--bg-depth` the prep computes it for the windows
  only; a rejected all-keypoint fit gets no entry and a log line.
- `far`: the masked SIFT fit of `--bg-depth`.
- `chain`: the fit through frame i − 1, when the direct fit was rejected.
- `ecc`: the ECC fallback, or the masked refinement of `--ecc-refine`.
- `final`: frame i as the prep writes it (after `--lock-window`, with the written stills' resampling) against frame 0,
  both on the canvas before the crop, so a window at the crop's edge still finds content beyond it.

The first four are read on frame i warped onto frame 0 by the fit (cubic). A fit that made no map has no entry.

`prep.json` gains a top-level `"windows": {"<name>": [x0, y0, x1, y1]}` and, per frame i ≥ 1, `frames[i].windows`:
`{"<name>": {"box": [x0, y0, x1, y1], "box_canvas": [x0, y0, x1, y1] | null, "fits": {"<fit>": {"dx", "dy", "corr",
"edge"}}}}`. `dx` and `dy` are px (positive: right and down), to 2 places. `corr` is the match's peak, −1 to 1, to 3 places.
`edge` is true when the peak lies on the search's border; the offset is then a bound, not a measurement. `box_canvas`
is the window in the px of the written `k<i>.png` (carried by the canvas map, less the crop's origin; null when less
than 4 px of a side stays inside the crop). `OUT/windows.jpg` holds one panel per frame i ≥ 1: frame 0 at a 960 px long
edge with the windows and their names. Each fit draws one arrow from the window's centre, 8 times the offset: `all`
orange, `far` blue, `chain` magenta, `ecc` green, `final` red.

On the angel pair (2026-11-05) the windows reproduce the sheet's registration table (`benchmarks/2026-11-04-angel.md`)
in every cell at its 0.1 px precision. Under the lock, `final` holds the three ring windows within 2.14 px.

### `probe PREP_DIR --out DIR [--long 960] [--pairs "i,j;k,l"]`

The probe compares three in-between methods before a plan is written. It reads the prep folder's `k<i>.png`, scales
them to `--long` (downscale only, sides made even) and takes every adjacent pair, or the listed pairs. Per pair it
makes the in-betweens at t 0.25, 0.5 and 0.75 by three methods:
- `rife`: RIFE v4.26 over the whole frame, as a `matte: {"all": true}` leg renders it. RIFE loads only behind
  `RIFE_MANIFEST.json`, offline. When the manifest is missing, or `rife_probe` refuses a weight, the probe skips the
  RIFE strips with a log line, and `rife_skipped` says why.
- `morph`: transitions.py's DIS morph (`prepare` and `iter_frames`, as `frames_morph` calls them). Its three frames sit
  at 1/4, 1/2 and 3/4 of a five-frame morph, where the morph preset's sine ease puts the warp and the mix at 0.15, 0.5
  and 0.85.
- `dissolve`: the plain blend.

It writes `DIR/probe_<i>_<j>_<method>.jpg` (the three frames side by side, each labelled with its t) and `DIR/crops/`.
The crops are 1:1 at the YuNet face boxes of the pair: a face of still i and the nearest face of still j share one box,
grown by 25 % on every side. Their names are `<i>_<j>_k<i>_face<k>.jpg` and `<i>_<j>_k<j>_face<k>.jpg` for the two
stills, and `<i>_<j>_<method>_t<t>_face<k>.jpg` for the in-betweens.

`probe.json` holds `prep`, `long`, `size` [W, H], `t`, `matte` (the change matte's settings), `rife_version` (the
manifest's model string, or null), `rife_skipped` (null or the reason), `faces_model`, `seconds` and `script_md5`.
Its `pairs` list holds, per pair, `{"a", "b", "matte_share", "faces": [{"box", "a", "b"}], "methods": {"<method>":
{"strip", "flow" (morph only), "frames": [{"t", "dexp", "dexp_frame", "step_a", "step_b", "seconds" (rife only),
"crops"}]}}}`. `dexp` is rule 7's double-exposure share (`rife_probe.dexp_share`: pixels within 20 levels of the two
stills' mean and more than 20 from each) inside the change matte, where the stills differ. `dexp_frame` is the same
share over the whole frame, the value a `matte: {"all": true}` render records in `frames.json`. `step_a` and `step_b`
are the mean absolute differences to still i and still j (0–255).

On the angel pair at 960 px (2026-11-05): RIFE's `dexp` is 0.0223–0.0494 on the unlocked prep, the sheet's 0.022–0.049;
it is 0.0341–0.0611 on the locked prep. Two to three seconds per pair.

### `measure MP4 --out DIR [--frames-json PATH] [--window "name:x0,y0,x1,y1;…"] [--ref 0] [--margin 30]`

`measure` computes the measures of `render` on any mp4, without rendering. `render` calls the same function
(`measures_of`), so on the five angel candidates the 16 measure keys of `measure` equal the render's own `measure.json`.
`DIR/measure.json` holds `mp4`, `frames_json`, `frames` (the decoded count), `fps` (the container's), `canvas`,
`seconds`, then the render's keys in the render's order: `step_mean`, `step_max`, `step_max_at`, `seam_step`, `steps`,
`faces_per_frame`, `faces_keyframes`, `generated_frames`, `generated_share`, `dexp_max`, `rife_seconds_per_frame`, and
`md5_mp4` and `script_md5`. Five of them need the render's `frames.json`, because only the render knows which frame is
a still or generated and what its double-exposure share was: `faces_keyframes`, `generated_frames`, `generated_share`,
`dexp_max` and `rife_seconds_per_frame`. They are null unless `--frames-json` is given, and its row count must equal
the decoded frame count.

With `--window` (px of the clip), `measure` also writes `stability_ref`, `stability_margin`, `stability` and
`stability_max`. `stability` maps each window name to one `[dx, dy, corr]` per decoded frame: where frame `--ref`'s
window content sits in that frame. `stability_max` gives per window `box`, `dx_max` and `dy_max` (the largest absolute
offsets, px) with `dx_max_at` and `dy_max_at` (their frames), `corr_min`, and `edge_frames` (frames whose peak lies on
the search's border). `--margin` (default 30 px) is the search around the window.

On the a2 mp4 (2026-11-05) the ring's top window (393, 371, 553, 441) moves at most 1.18 px sideways and 3.96 px up.
Over a1–a3 the largest are 1.22 and 4.15 px, the sheet's "1.2 and 4.2". Margins 12 and 30 give the same numbers.
The count of sheets moving at once per frame (the seasons s9 reading) is absent: it is a count of the plan's schedule
(the per-sheet displacement `d` in `frames.json`), not of the decoded frames.

### `page --variants a2,a3`

`--variants` lists only the named full renders of each sequence, in the given order; a full render is a folder of
`<root>/<seq>/` that holds `measure.json`. The list applies to every sequence on the page, so pass `--order` with one
sequence when the names belong to one. A name that is not a full render of a sequence, or a name given twice, is a
`FAILED:` exit 2 before anything is written. When the flag is absent, the page lists every full render in name order,
as before.
On a copy of the angel run the page with the recorded title, intro, footer and notes gives md5
72dadc4f5ea4db16152fe0c7062a3f94, the recorded page's, with and without `--variants a1,a2,a3,a4,a5`.
