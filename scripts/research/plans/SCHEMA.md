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
