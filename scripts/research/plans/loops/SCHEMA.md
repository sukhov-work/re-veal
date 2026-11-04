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
the md5s), `plan.json` (the plan as rendered).

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
