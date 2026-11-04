<!-- Provenance: written by an Opus 5.5 subagent (the comp builder, a static HTML mockup of the studio's main screen) of the Claude Code session of 2026-11-04 (the studio design; DECISIONS 2026-11-04 second line); copied verbatim from benchmarks/runs/2026-11-04/studio/agents/comp_build.md (sha256 221d67d8e01e048e) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). What the comp under benchmarks/runs/2026-11-04/studio/comp/ shows, its files, the contrast numbers, and three changes proposed for DESIGN.md. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

# Studio comp build: the angel loop's render stage at 2560 × 1440

<!-- reader: the owner and the parent session (cold); shape: report; written 2026-11-04 by the comp-build agent -->

## Summary

The comp is built and screenshotted: `benchmarks/runs/2026-11-04/studio/comp/index.html` and `comp.png` (2560 × 1440 px, checked with `sips`). It is one static HTML file with system fonts, no network references (0 matches for "http") and every image under `comp/img/`. Every text colour used passes 4.5:1 on its ground. Four deviations from the brief are listed below; the largest is that viewer B shows the registered still k1 instead of frame 49.

## What the screen shows

- **Rail, 240 px.** Three jobs: angel (selected, 2 px amber edge, chip "5 candidates, unjudged after a fix: 0"), seasons (loop, round 4, "ungraded") and mismatch_3 (director plan, round 13). Running tasks: idle. Five models with "ready" chips; RIFE v4.26 reads "ready, offline". The box: reachable, no hold, 34 GB free, queue empty.
- **Stage strip.** Ten tiles, each with a 96 px thumbnail from real job files. Registration shows k1 with the three lock windows from `prep.json` drawn in info blue. Render is selected with the amber outline and a violet "generated" tag. Grades is an empty grey tile with the chip "none yet".
- **Render panel.** The comparator mode buttons (wipe, A/B, onion, difference; fit, 1:1, 2×), then A (frame 0) | frame 25 (violet outline) | B (k1), at 540 px display height. A frame 25 table on the right uses values from `frames.json` and `measure.json`.
- **Shared frame axis.** The scrubber at f 25 is drawn focused (amber ring), with the readout "f 25 · t 0.947 · generated (RIFE)". Three SVG plots share one x from f 0 to f 49:
  - the 49 values of `steps`, with the 0.3 px stall bar dashed and "max 4.09 px at f 43" labelled;
  - ring top dy in px;
  - the generated bands at f 14–25 and f 38–49, plus the skeptic's markers: teeth fade at f 19 and f 43, hair lock at f 44–46.
  
  An amber line at f 25 runs through all three. The x positions follow the range input's thumb travel (16 px thumb), so the line sits under the thumb.
- **Frame strip.** Every 5th frame as a 96 px tile, placed at its own x on the axis. Generated frames have violet outlines; f 25 also has an amber ring.
- **Inspector, 320 px.** Knobs: draft/full set to full, fps 25, crf 14. The four changed plan keys in bold. Provenance, the measures that gate, the copyable command, and the "render full" (primary) and "rerun from here" buttons.

## Files

All under `benchmarks/runs/2026-11-04/studio/comp/`:

| File | What it is |
|---|---|
| `index.html` | the comp |
| `comp.png` | the headless Chrome screenshot |
| `img/f00.jpg`, `img/f25.jpg`, `img/f49.jpg` | viewer frames, 640 px tall |
| `img/k1.jpg` | the registered still, 640 px tall |
| `img/t00.jpg` … `img/t45.jpg` | frame strip tiles, 192 px tall |
| `img/s_*.jpg` | the stage thumbnails |

The generator (`gen_comp.py` + `tpl.html`) is in the session scratchpad, outside the repo.

## Contrast (WCAG ratio, computed from the DESIGN.md hex values)

| Text | on ground #141618 | on panel #1c1f22 | on panel-raised #24282c |
|---|---|---|---|
| text #e8e8e6 | 14.78 | 13.49 | 12.10 |
| text-muted #9aa1a8 | 6.94 | 6.34 | 5.68 |
| text-faint #6c737a | 3.78 | 3.45 | 3.09 |
| amber #e0a65a | 8.44 | 7.70 | 6.91 |
| ok #5cc48a | 8.39 | 7.66 | 6.87 |
| failed #e5655a | 5.48 | 5.00 | **4.48** |
| info / photo-a #6aa9f0 | 7.38 | 6.74 | 6.04 |
| generated #b48ef0 | 6.97 | 6.36 | 5.70 |
| photo-b #f0a06a | 8.59 | 7.84 | 7.03 |

amber-ink on amber: 8.64. amber-ink on amber-deep: 6.30.

The comp uses no text in text-faint. Failed-colour text appears only on the panel (5.00), never on a raised chip, where it would be 4.48.

## What I did not do, and the deviations

- **Viewer B.** B shows the registered still k1, not frame 49. Frame 49 is RIFE at t 0.947 on the k1 → k0 leg, so it looks almost like A. All three frames were still extracted; `img/f49.jpg` is there if the owner wants it.
- **Ring top dy.** The series is illustrative, not measured, as the brief asked: 0.3 px at rest, rising to 4.0 px at f 24–26 along a Gaussian.
- **Plan sha256.** The inspector shows `eba6f703…`, the value `measure.json` recorded. The plan file's sha256 today begins `aef637f0`, so the plan changed after the render or the two hashes cover different bytes. UNVERIFIED which.
- **Script md5.** `79a04007…` is the md5 of the working tree's `loop_seq.py`. That file has uncommitted changes in git status, and the render never recorded a script md5.
- **Missing wall times.** Plan, measures, skeptic, page and grades show "—", because no source gives their wall times.
- **Focus ring.** It is drawn with an `.is-focused` class. A static screenshot cannot show a real `:focus-visible`.
- **Other states.** Hover states are in the CSS but not shown. The browser surfaces (selection, caret, scrollbar) are themed but invisible in a screenshot.
- **Screenshots.** Two were taken, as the brief allows. The second still shows tight captions under the viewer frames (8 px gaps).

## Three changes for DESIGN.md

1. **Strip height.** DESIGN.md sets the stage strip at 112 px, but a tile holding a 96 px thumbnail, a name, a detail line, a wall time and a chip needs about 160 px. Set the strip to 168 px, or the thumbnail to 64 px.
2. **text-faint.** It is 3.78:1 on ground and 3.09:1 on panel-raised, yet DESIGN.md assigns it to placeholder text, which needs 4.5:1. Raise it to #8a9198 (4.65:1 on panel-raised, 5.69:1 on ground), or restrict it to disabled text only.
3. **Selected and generated together.** DESIGN.md does not say how a frame that is both selected and generated is marked. The comp uses a violet outline inside the frame and an amber ring outside it. Write that rule down. Also note that failed-colour text on panel-raised is 4.48:1, so a failed chip needs lighter text: #e8706a measures 4.92:1 there.
