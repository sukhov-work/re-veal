---
reader: the owner and the next session, cold
shape: report
date: 2026-11-17
---
# Wall pairs: the independent check of the aligned stills and videos

Provenance. An Opus 5.5 subagent at xhigh effort wrote this as two returns on 2026-11-17. The harness
refused its report file, so the main thread saved the returns here: the verdict and tables of the
second return (on the set that shipped) in full, the first return (on the superseded first set) as
its summary. The subagent read no file of the main thread's method. Its scripts, number files and
crops are under `benchmarks/runs/2026-11-17/wall/skeptic/` (gitignored). The main thread
re-verified only what "Main thread's use" says at the end.

## Summary

Verdict: ship the corrected after-frame set. Its wall residual is lower in both pairs, it bends
nothing, and no region is worse beyond the measure's 0.4 px noise floor.

Actions asked of the owner:
- decide whether pair 1b/2b's pipe needs a pipe-only fix (it sits 3.5 to 3.9 px low in AFTER);
- decide whether the completed ground inside pair 1/2's 4:5 window is acceptable.

Open questions: the cause of both pipe offsets; playback of the native videos on phones.

## Glossary

- Pair a is `1.jpg` → `2.jpg`; pair b is `1b.jpg` → `2b.jpg`.
- The first set: AFTER warped onto BEFORE's frame (superseded the same day by the owner's word).
- The after-frame set: BEFORE warped onto AFTER's full 3024×4032 frame. U is the uncorrected render
  (the homography alone); C is the corrected render (the homography plus a smooth field of at most
  2.1 px in BEFORE's px).
- Seam step: the vertical jump seen where the slider's seam crosses a level joint. Plus means lower
  (step) or further right (dx) in AFTER. All values are px of AFTER's frame unless marked.
- A site: a point on a relief line (a joint, a crack, an edge) picked in BEFORE with the line's normal.
  A trusted site: a dark line matched to a dark line with normalised cross-correlation of 0.6 or
  more, both half-strips agreeing within 1 px.
- A star marks a cell with fewer than 30 vertical-joint sites, where dx is unreliable.

## The method (the subagent's own)

1. Sites from a Hessian line detector on BEFORE's luminance, one per 16×16 px block, inside the wall
   face and 24 px clear of hand-drawn masks (the chair, the birdhouse, the vines, the scaffold, the lights).
2. The signed luminance derivative across each line, averaged over a 33 px strip along it.
3. A cross-correlation search of ±16 px in AFTER, a parabola at the peak, both polarities kept.
4. Per cell of a 3×3 grid: the median seam step and the median dx.

Controls. A shift of 0.5 px injected into AFTER came back within 0.13 px per cell. A shift of
+0.7 px and a rotation of 0.05° came back within 0.02 to 0.09 px on the after-frame set. A shift
beyond the search range made half the sites drop out; it gave no confident wrong value. The first
version matched an unsigned derivative and read +6 to +19 px in black paint: it had locked onto a
light line under each joint. The signed version replaced it.

## Per cell, uncorrected → corrected (seam step, then dx)

| Cell | Pair a step | Pair a dx | Pair b step | Pair b dx |
|---|---|---|---|---|
| (0,0) top left | +0.05 → −0.15 | +0.75 → +0.79 * | −2.52 → −0.19 | −2.08 → −1.72 |
| (0,1) | +0.09 → +0.28 | +0.29 → +0.29 | +0.92 → +0.14 | −0.55 → −0.11 |
| (0,2) top right | +0.58 → +0.15 | −0.18 → −0.15 | +0.68 → +0.10 | +0.29 → +0.29 * |
| (1,0) | −0.22 → 0.00 | −0.95 → −0.82 * | −0.68 → +0.01 | +2.94 → +1.48 * |
| (1,1) centre | +0.33 → +0.42 | −0.81 → −0.37 * | +2.44 → +0.71 | −1.63 → −0.49 |
| (1,2) | +0.51 → +0.19 | +0.03 → +0.25 * | +1.39 → +0.22 | −0.14 → +0.39 |
| (2,0) bottom left | −0.59 → −0.50 | +0.58 → +0.45 * | −0.23 → +0.35 | no reading |
| (2,1) | −0.14 → −0.18 | +1.37 → +1.16 | +0.33 → −0.20 | −1.25 → −0.34 * |
| (2,2) bottom right | −0.65 → −0.30 | +1.03 → +1.18 | −1.71 → −0.90 | +2.20 → +2.10 (IQR 3.5) |
| Whole face, median / p90 of the absolute step | 0.65 / 1.82 → 0.44 / 1.34 | | 1.07 / 3.25 → 0.44 / 1.66 | |
| Whole face, median / p90 of the absolute dx | | 0.82 / 2.63 → 0.64 / 2.24 | | 1.46 / 4.11 → 0.94 / 3.76 |

Sites trusted in both renders: 1,825 (pair a), 1,138 (pair b).

## Spots singled out

- Pair b's left edge, 120 px blocks: −4.00 → −0.92, −3.01 → −0.22, −2.49 → −0.27. The joint steps in
  the uncorrected crop and runs continuous in the corrected one.
- Pair b's centre blocks: +3.77 → +1.71, +3.14 → +1.35, +3.07 → +1.23, +2.27 → +0.57. The mural's
  edges hide the joints there; not confirmed by eye.
- Pair b's pipe, by sixth of its length, corrected: +0.07, +1.75, +3.45, +3.93, +3.16 (the last on 6
  sites). Both edges move together: a shift. About 3 px seen at 5×.
- Pair a's pipe: the centre within −1.40 to +1.26 px by sixth. AFTER's pipe looks 1.6 to 3.6 px
  thicker; at x 1700–1810 the top edge is 2 to 3 px higher and the bottom edge 1 to 2 px lower.
- The unpainted cap course, pair b's left third: relief −5.34 → −3.38, plain intensity matching
  −2.43 → −0.75. The other thirds sit within ±0.9 px in both renders. Pair a: −1.2 to −2.0 → −0.3 to −1.6.
- Two 200 px blocks are worse in the corrected render by 0.5 px or more. Pair a at (900, 3100)
  goes from 0.22 to 0.72 px. Pair b at (100, 1900) goes from 1.97 to 2.53 px. Against them, 16 and
  28 blocks improve.

## Bending

None visible. Dense optical flow between the two `before_aligned.png` files matches a brute-force
shift search within 0.1 px at 6 spot checks. Over any 384 px run a straight joint bends by at most
0.26 px (pair a) or 0.19 px (pair b). The field changes by at most 0.65 px per 100 px. Its largest
displacement is 1.26 px (pair a) and 3.23 px (pair b), in AFTER's px.

## The corrected set, other checks

- `after.png` is pixel-identical to a Display P3 → sRGB conversion of the source photo with the EXIF
  orientation applied once: the full 3024×4032 frame, 0 differing pixels.
- Both text blocks and the handle are inside the real-pixel rectangle and inside the 4:5 window in
  both pairs. Pair a's margins are read from crops to about ±10 px. The text starts about 20 px
  inside the rectangle's left edge. The last English line ends about 90 px above its bottom. The
  handle is about 130 px from the right edge. Pair b has at least 170 px everywhere. Pair a's English lines
  are half hidden by the chair and the table in the source photo itself.
- The coverage mask is honest: no completed pixel is marked real, checked against BEFORE's footprint
  recovered independently.
- The completed zones looked fake in the render the subagent saw: flat grey noise against the real
  ground, a straight seam with a tone step of 2.5 to 7 levels, visible at 1080×1350. Pair a's 4:5
  video held 16.2 % completed pixels; pair b's 4:5 and both native videos held none.
- The four videos: 150 frames, 30 fps, 5 s. First frame 44.0 to 45.9 dB from BEFORE, last frame
  41.6 to 44.7 dB from AFTER, mean bias at most 0.27 levels. AFTER is left of the seam in 150 of 150
  frames; the seam moves one way; no black frame; both 4:5 files are exactly 1080×1350.
- Not checked on devices: the native files exceeded common hardware decoder limits (pair b's at
  H.264 level 6.0).

## The first return, on the superseded first set (summary)

| Item | Verdict |
|---|---|
| Wall alignment | FAIL at three places: pair a's pipe top edge; pair b's left edge (−1.7 to −3 px) and centre (about +2 px), in BEFORE's px |
| AFTER's geometry | PASS: one homography of its source, fit residual 0.27 px RMS, no local bending |
| Frame hygiene | PASS: sizes equal, no invalid border pixel, tagged sRGB; 5 to 10 % of source pixels lie outside sRGB and were clipped |
| Videos | PASS; the colour primaries and the transfer were untagged |
| Slider page | PASS by reasoning; a swipe starting on a picture could not scroll the page on a phone |

The second return corrects two pipe readings of the first. Pair b's readings (−0.5 / −1.0 / +1.45)
are replaced by the edge tracker's 3.5 to 3.9 px. Pair a's "−3.4 px top-edge step" is a pipe that
looks thicker, with its centre within ±1.4 px.

## Gaps (the subagent's)

- No measurement at the hole: the birdhouse covers it in both AFTER photos.
- dx is unreliable in the starred cells.
- In black paint the same-polarity reading is used; the flipped reading differs by 6 to 15 px. The
  wall-to-ground line and the cracks support the choice; none proves it.
- The pipe offsets are measured; their cause is not.
- Pair b's top-right corner (under a vine) and bottom-left corner (under the scaffold) are unmeasured.
- No browser, no device playback, no cold read of the summary.

## Main thread's use (2026-11-17)

- The corrected render ships. Before the subagent's A/B, the main thread tested the correction on
  the subagent's first-set sites (`benchmarks/runs/2026-11-17/wall/probe5.py`). Pair b's cell
  medians fell from 1.00 to 0.39 px RMS and its left edge from −1.48 to −0.07 px.
- After this report the ground completion was rebuilt: a per-column colour, noise in three bands
  with the real ground's spread, a 32 px cross-fade. The videos were re-encoded with the bt709
  tags. A full-frame native wipe was added per pair (2606×3474, H.264 level 5.2). The real-pixel
  rectangle became a second file (level 5.1 for pair a, 5.2 for pair b). Both 4:5 files are level 4.0.
  The subagent did not see that render. The completed ground is graded by the main thread's eye only.
- The pipes are left as measured. The likely cause is parallax (the pipe stands off the wall); it
  is not determined. A warp that moved the pipe would bend the wall beside it.
