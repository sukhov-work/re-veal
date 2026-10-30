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
