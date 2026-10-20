# The director's plan (schema v1, 2026-10-17) — read by `scripts/research/director_render.py`

A plan is one JSON file per pair, frozen as a tracked input (the model id, the temperature, the
sha256 of the prompt that produced it, the date). The renderer reads it and renders every concept
it can place; a concept whose anchors do not resolve is reported "unplaced", never rendered.
Coordinates: boxes `[x0, y0, x1, y1]` and points `[x, y]` in the CANVAS of the layer source
(`benchmarks/runs/2026-09-28/layers_v3/<photo>/layers.json`, the tool's centred cover crop of each
photo; the renderer re-crops A when the plan asks for an anchored crop). Time: `window` is
`[t0, t1]` in clip fractions, 0 = the first frame (always A exactly), 1 = the last (always B).

```
{
 "pair": "mismatch_5", "planner": {"model": "...", "temperature": 0, "prompt_sha256": "...", "date": "...", "brief": "blind | owner notes of <date>"},
 "reading": {"a": "one sentence", "b": "one sentence"}, "relation": "themed | unrelated | aligned",
 "concepts": [{
   "id": "c1", "rank": 1, "idea": "one sentence, what the viewer sees",
   "container": {"in": "B", "kind": "disc | quad | rect | none", "spec": {...}, "rim": "soft | matte | glass"},
   "anchors": [{"a": {...}, "b": {...}, "how": "one sentence"}],
   "pullback": {"ease": "smootherstep", "parallax": {"kind": "depth | off", "gain": 0.3}},
   "transforms": [{"name": "...", "a": {...}, "b": {...}, "by": "...", "window": [0.1, 0.8], "mix": "luma | edge | noise | none", "params": {...}, "note": "..."}],
   "end_effect": {"kind": "luma_reveal | edge_reveal", "window": [0.78, 1.0]},
   "helper": null,
   "knobs": [{"name": "...", "range": [lo, hi], "default": 0.0, "what": "one sentence"}],
   "risk": "F1 double exposure | F2 decoration | F3 invention: where this concept can fail"
 }]
}
```

Container kinds (in B): `disc` {"center": [x, y] or {"bright_disc": box}, "radius": px}: A's anchor
disc lands on it, the rim is `soft` (A's surround keyed by its luma). `quad` {"points": 4 × [x, y],
clockwise from the top left} or `rect` {"box"}: A's whole frame maps onto it by a homography
(quad) or a similarity (rect), the rim `matte` (B's front elements composite over A) or `glass`
(matte plus B's own glass content blended over A at `params.reflect`, default 0.18). `none`: no
nesting, the camera is the identity (then only the transforms act).

Anchor kinds. In A: `circle_fit` {"box", "min_L": 120} (the renderer fits a circle to the limb of
the bright blob in the box, so a luminary partly behind an object keeps its true centre and
radius), `element` {"ids": [...]}, `box`, `point`, `rows` {"from", "to"} (a horizontal band of the
canvas, for a bridge or a horizon). In B: `bright_disc` {"box", "frac": 0.8}, `element`, `box`,
`point`, `line` {"ids": [...]} or {"points": [[x, y], [x, y]]} (a thin straight element, fitted by
its principal axis), `dark_band` {"box"} (the darkest connected band inside the box).
The renderer derives the camera from the container and the first anchor: one similarity
(anchor centre on anchor centre; the scale from `params.end_scale` or from the two radii) or one
homography (the quad). The camera pulls back from "A fills the frame" to "B fills the frame" under
the ease; `parallax: depth` modulates each source's zoom per pixel by the depth model's disparity
(near moves more than far, `gain` 0–1), `off` is a flat zoom.

Transforms (`by`): `recede` (a disc layer of A contracts radially about its centre to
`params.end_radius` px of B while its limb softens over `params.soften`; for a luminary that
"becomes distant"), `line_to` (a band of A rotates about the first anchor, thins to `params.width`
px and stretches along its axis into a line of B), `morph_to` (optimal transport of A's mass
inside the a-mask onto B's mass inside the b-mask; the b-pixels are revealed inside the moving
matte over the `mix` order; `params.map: "box"` adds the box-to-box affine first), `move_to` (the
rigid version: A's box translates and scales onto B's box, then `mix`), `colour` (Lab statistics
of the a-mask move toward the b-mask over the window), `hold` (the layer keeps its own matte and
rides the camera; no transformation). Masses are luma for bright things and 1 − luma for dark
things (`params.mass: "bright" | "dark"`, default by the a-mask's mean luma).

End effect: inside the container, over its window, B replaces what remains of A in the order of
A's brightness (`luma_reveal`, bright first) or from the rim inward (`edge_reveal`).

Rules the renderer enforces: frame 0 is A and the last frame is B, byte-exact; every pixel comes
from A or B (A re-coloured where a `colour` transform says so); nothing is generated unless
`helper` names a model, a prompt and a region (not built in this round); the renderer is offline.

## Additions of round 9 (2026-10-17 evening, from the owner's grades on the director's page)

- End effect `b_luma_reveal` {"window", "params": {"band": 0.4}}: inside the container, B replaces
  what remains of A in the order of B's own brightness (the brightest leaves, lights or stars first,
  the dark background last) over a wide band, so the pane's content turns into B's content where B
  is bright and keeps A's darkest parts longest.
- A soft rim's sky (`container.params.sky`): {"stars": true, "star_window": [0.1, 0.9],
  "key_window": [0.2, 0.85], "key_band": 0.3}: B's bright points (its stars, by a top-hat of its
  luminance) come through A's sky in B's brightness order over `star_window` while A's sky background
  gives way to B's background dark-first over `key_window` with the wide `key_band` (a slow luma
  crossfade, not an iris); the colour path should lead it (`colour` with an early window).
- Anchor and transform a-kind `dark_line` {"rows": [y0, y1], "thickness": 7}: the darkest thin
  horizontal line inside the row range (a wire, a cable), a band of `thickness` rows around it
  carrying its dark pixels only; use it with `line_to`.
- Transform `exit` {"params": {"direction": "left | right | up | down", "fade": 0.3}}: a layer leaves
  the frame in that direction over its window and fades over the last `fade` of it (a tree that
  "goes away").
- `pullback.parallax.gain_A`: the depth gain inside A (default = `gain`); a larger value makes A's
  near layers (a crowd) move against its far ones (a wall) during the pull-back.
- `morph_to` `params.rotate`: true turns the layer from its own axis to the target's axis (the axis
  map) even when `map` is "box"; `params.ot_weight` 0–1 scales the optimal-transport residual.
- Story rule (owner, 2026-10-17): at most three transforms per concept, each a beat he can name; no
  shuffle of layers.

## Additions of round 10 (2026-10-17 night, from the owner's grades on round 9: `TRANSITIONS.md §13.15`)

- Soft mattes. Every layer whose `a` (or `b`) is an `element` kind composites with the matting
  model's alpha (`benchmarks/runs/2026-10-17/mattes/<photo>/el_<id>.png`, written by
  `scripts/research/matte_source.py`), not the hard element mask; where no matte file exists the
  renderer falls back to the hard mask and prints `INFO matte: no soft matte for <photo> element <id>`
  (also listed in `info.json` under `matte_fallbacks`). B's front layer uses the same mattes. A
  `dark_line` layer's alpha is the wire's own darkness (how much darker than the rows beside it),
  and a `line_to` from a `dark_line` has no end taper unless `params.end_taper` says so.
- The plate under A's layers (`params.plate`, default true; the knob `plate=false` turns it off for
  the whole render). A is filled under every lifted layer's footprint (`cv2.inpaint`, Telea, at
  1280 px or less; a fill, not a generation), so a layer that moves away uncovers A's own surround
  instead of a hard-cut silhouette of B; `info.json` reports `plate_A_share`. A layer with
  `plate: false` keeps the hole (B shows through where it was).
- `recede` params: `limb_flatten` defaults to 1.0 (off; it drew a paler inner disc); the disc is
  the fitted circle plus the sun's connected bright blob (`blob_L` 110, `blob_reach` 1.35 radii; an
  oblate sun's left and right limbs lay outside the circle and stayed in the base as bright
  crescents in round 9); the alpha falls over a smooth ramp from `rim_in` (default 0.55) to
  `rim_out` (1.0) of the radius once the recede has started; `mix_window` (default [0.55, 0.95])
  and `mix_ramp` (default 0.5) set when and how widely the disc's colour mixes into the core's glow,
  limb first, centre last (an early mix at the limb drew a second, darker disc in the drafts of
  2026-10-18, so the default mix is late); the other layers' silhouettes across the disc (the deck's
  chord) are filled from the disc's own pixels and blended in over the first `fill_in` (0.3) of the
  recede.
- `pullback.parallax.a_elements` (list of A element ids; knob `parallax_A_elements`): the depth
  parallax inside A acts on those elements only; the rest of A (a sky) stays at the reference
  disparity, so no sky pixel is remapped.
- `container.spec.front_ids` (list of B element ids; knob `front_ids`): elements forced into B's
  front layer whatever their depth (the ceiling that "should have been in foreground").
- Transform `by: "keyframe_chain"` {"a": an element or `all`, "b": an element or null (= the whole
  of B), "params": {"keyframes": [paths relative to the repo], "frame": "canvas" | "A", "times":
  [t_1, ..., t_{n-1}] (optional; the chain's progress at which each keyframe is reached, evenly
  spaced by default), "guide": true}}: generated keyframes inside the layer's matte. The chain
  A → k_1 → … → k_n → B is rendered by the tool's own morph between consecutive pictures
  (`transitions.morph_frame`: a box similarity A-matte → B-matte as the guide of the first segment,
  DIS flow with consistency weights, forward splats, a linear mix), inside a matte that travels
  with the content from A's soft matte to B's. `frame: "canvas"` means the keyframe is the pair's
  canvas in B's layout (the café: the man already at B's place); `frame: "A"` means the keyframe
  is in A's own geometry (the view through the pane). The keyframes are helpers under the owner's
  2026-09-29 conditions (realistic, at least half of the objects original and consistent, no new
  objects); the page shows them beside the clip and says they are generated. `info.json` reports
  the chain's segments (median displacement, mean consistency inside the matte).

## Additions of round 11 (2026-10-18, from the owner's grades on round 10: `TRANSITIONS.md §13.18`)

- A `keyframe_chain` runs linear in its window and mixes linearly inside each segment (`params.ease`:
  "linear" by default for a chain, "smootherstep" for every other kind); round 10 eased twice and
  packed the pane's crowd dissolve into 0.24 s of a 0.75 s segment. Its `times` therefore map to
  clip time by the window alone.
- `keyframe_chain` with `"depth": "front"` composites after the end effect, like a morph layer that
  leaves the container: the base can become B behind the man while he stays, then he moves over B
  (no vacated footprint, nothing shows "through a cut"). After the rigid lead the chain's matte is
  the moved matte joined with B's matte and dilated by `params.matte_grow` (0.03 of the width), so
  a keyframe's wider shoulders or a turned head are never cut by the matte's edge; the frames the
  chain shows inside that matte are the keyframes themselves.
- `params.face_guide` (default true when the chain is not the whole frame): before the flow of each
  segment between keyframes the renderer aligns the two faces by a similarity from the face box of
  one to the face box of the other (OpenCV's bundled frontal-face Haar cascade, the largest face
  inside the matte); `params.damp` defaults to 0.5 with a face guide (the flow halved where it is
  unreliable) and 1.0 without. `info.json` lists the face boxes per segment under `chain.faces`.
- Under a soft rim (a disc container) what remains of A's sky is keyed inside a radial window
  around the sun that shrinks with the pull-back (`container.params.sky.shape`: "radial", the
  default; "frame" is the round-9 border feather): the window's radius runs from the far corner of
  A's frame to `sky.radial_end` (1.6) sun radii, its edge `sky.radial_width` (0.35) of the radius.
  No rectangle of A's sky remains ("preserving blurred square shape").
- `recede`: `soften` defaults to 0 (the rim ramp is the sun's only radius; a growing blur was a
  second one), the plate under the sun blends in over half the radius (its circle was a third), and
  the ring the recede vacates no longer shows B (a fourth); A's glow around the sun is re-coloured
  toward the galaxy around the core by a `colour` transform, which is a lead and not one of the
  three beats.
- B's front: one layer per front element in depth order, each with its own matte and its own depth
  move (knob `front_per_element=false` restores the single layer); the owner's frame of round 10
  showed B's men cut by a blurred band where the shared alpha met a neighbour.
- The chain's lead moves the layer by its FACE when both A's layer and the first keyframe show one (a
  similarity from the five landmarks, its rotation dropped; `lead_guide: "faces"` in `info.json`),
  else by the matte boxes; the box guide had left A's man's face 95 px right of k1's at 960 px.
- The radial sky window runs in clip time, not the camera's ease: fully open at 0, at the nearest
  frame edge of A by `sky.radial_near_at` (0.25), at `radial_end` sun radii by `radial_end_at`
  (0.9). Before 0.25 A's corners fade out radially; after it no rectangle can show.
- `recede`: `limb_flatten` defaults to 0.55 with a smooth weight (the limb levelled toward the
  disc's inner colour from the rim's start), so the rim ramp does not read as a second ring.
- The face model: `benchmarks/runs/2026-10-18/face/face_detection_yunet_2023mar.onnx` (YuNet,
  OpenCV's `FaceDetectorYN`; fetched once on 2026-10-18, sha256 in `FACE_MANIFEST.json` beside it,
  read offline); without the file the chain runs without a face guide and prints an INFO line.
- The chain's lead segment eases in and out (a rigid move at constant speed "stops dead", the
  skeptic's first pass on round 11); the keyframe segments stay linear.
- B's plate under its front is filled by the pull-push pyramid (knob `plate_fill=telea` restores
  cv2.inpaint): Telea's fill of a body was a flesh-coloured smear that showed below the pane before
  the man's layer arrived. The operator's `parallax_push` (default 2.5) sets how far B's front
  starts beyond the frame; 1.5 brings it in sooner.

## Additions of round 12 (2026-10-20, from the owner's grades on round 11 and the retrospective `research/2026-10-20/retrospective.md`: the rules that hold for any pair)

- The motion model (rule 2, "all happen with weird pauses and in very linear way"): a concept with `"motion": {"kind":
  "continuous", "edge": 0.35, "overlap": 0.1}` renders every beat's progress as a smooth trapezoid in its window
  (the velocity ramps up by a smoothstep over `edge` of the window, holds, ramps down over the last `edge`; `edge`
  0.5 is one smooth hump, a small `edge` is near linear; `params.edge` per transform overrides), with no second
  ease anywhere (a keyframe chain's lead no longer eases on its own). Consecutive beats overlap: a later beat whose
  window starts after the earlier beat has run 1 − `overlap` of its window is moved earlier to that point, and the
  renderer prints `INFO motion: <name> starts at … to overlap <name>` and lists it in `info.json` under
  `motion.adjusted` (`overlap` 0 turns the rule off). The plan's last beat should end at 1.0 and the clip should
  carry a camera or a beat at every moment: the renderer measures the motion profile of the decoded clip
  (`motion_px`: the mean DIS flow magnitude between consecutive frames in frame px; `motion_median_px`;
  `motion_pauses`: frames between 10 % and 90 % of the clip under a fifth of the median; `motion_jumps`: frames
  where the motion changes by more than half the median). Without a `motion` key a plan renders as in round 11
  (knob `motion=continuous` turns the model on for an old plan, `motion=legacy` off).
- The rate of a beat (rule 11, "whole sun to rapidly shrink"): `params.rate` "fast_in" (most of the change early)
  or "fast_out" (late) on any transform; `recede` also takes `params.profile` "geometric" (the disc shrinks at a
  constant relative rate, which reads as accelerating into the target) instead of "linear".
- The reveal policy (rule 1, "should never clip to underlaying next/last frame in advance (unless it was specific
  director intention"): with `"reveal": {"guard": true, "ramp": 0.08, "band": 0.01}` (the default when `motion` is
  present; knob `guard=false`) B's target of every transform that has a `b` (its matte grown by `band` of the width)
  cannot show before the transform has delivered it: not through a hole, not by the end effect, not by the key; A's
  base (its plate under a lifted layer) shows there instead until the beat arrives (`params.arrive`: the chain's
  progress at which the lead lands by default, or the end of a transform's `mix_window`), over `ramp` of the beat.
  A transform with `"reveal_ahead": true` in its params is the director's intention and opts out (`recede` does by
  default: its vacated ring shows B's glow, because a fill of a luminary's footprint is a dark ring, T46). `info.json`
  lists the guarded targets (`guard`) with their B shares and `guard_share_max`; the measure `b_inside` is, every
  third frame, the share of A's covered region where B shows through, and `b_inside_first` the first frame above 1 %.
- Shape alignment of a luminary (rule 4, "do not align (perfectly ) neither by the centers nor by shapes"): `recede`
  with `params.end_shape: "b_blob"` ends on B's bright blob around the b anchor (the connected region above
  `blob_frac` 0.6 of the local maximum within `blob_search` 3 radii): the disc moves to the blob's centroid and
  takes its two axes and its angle, so the sun lands on the core by centre and shape, and the mix then dissolves it
  into that blob. `info.json` reports `end_blob` (centre, axes, angle, offset from the plan's anchor). A larger
  `blob_frac` picks the denser, smaller core.
- A keyframe chain's `params.times: "arc"`: the knots are placed by arc length (each segment's share of the window is
  its median displacement, with a floor of `arc_floor` 0.2 of the largest for a segment without motion), so the
  visual speed is the same through every segment; explicit times still work.
- Rule 5's measure ("hard edges", "concentric bands"): `residual_edges` is, every third frame, the share of the
  frame's Canny edges that lie within 3 px of no edge of A or of B seen through the camera; `residual_edge_max` its
  maximum. A ring or a band the photos do not have raises it.
- Knobs on the command line for all of the above: `motion=continuous`, `guard=false`, `name.edge=0.2`,
  `name.rate=fast_in`, `name.profile=geometric`, `name.end_shape=b_blob`, `name.blob_frac=0.7`, `name.times="arc"`,
  `name.reveal_ahead=true`, `name.arrive=0.5`.
- Later in round 12 (after the first drafts): (a) a layer whose footprint uncovers a guarded target (an `exit`,
  `move_to` or `morph_to` over 20 % or more of the target) may not finish before the guard releases; the renderer
  moves its window's end to the guard's arrival in clip time, prints `INFO guard: <name> ends at …` and lists it
  under `motion.held` (the café's tree over B's man: a pale fill for the gap otherwise); (b) under the motion model
  the radial sky window follows a receding luminary: the scheduled radius is scaled by the disc's current shrink
  (`sky.follow_power`, 1.0) and never tighter than `sky.follow` (2.0) current radii, so the photo's own dark halo at
  the limb (T46) is keyed out as the sun shrinks instead of standing as a ring around a small sun; (c) a `rect`
  container of the frame's own size (a translation) uses the corner-interpolating camera (the zoom camera has no
  fixed point for a translation: mismatch_1's blind plan cut 46 levels at frame 1).
