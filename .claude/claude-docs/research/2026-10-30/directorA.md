<!-- Provenance: written by an Opus 5.5 subagent (director track A) of the Claude Code session of 2026-10-30 (the Halloween loops; DECISIONS 2026-10-30); copied verbatim from benchmarks/runs/2026-10-30/halloween/agents/directorA.md (sha256 ee2b1cb76f1b5a6c) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). Director track A on group-teleport, evgen-thug, zeke-back, zeke-bite, talk: one alternative plan each, drafted at 640 px. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy except where TRANSITIONS.md §13.24 says so. -->

# directorA: five Halloween loops, one alternative each (2026-10-30)

Both defects the main thread named are addressed. In zeke-back c2 the red-glasses man no longer doubles while
the ghoul fades in; the cost is a vertical edge through the ghoul's hat at x 0.445. zeke-bite c2 has no
in-betweens, so no frame shows two pairs of glasses. Every number below comes from a draft-640 `measure.json`. These numbers are not comparable to the full-size
numbers on the page. Paths are relative to `benchmarks/runs/2026-10-30/halloween/agents/directorA/`.

## zeke-back
- c1 verdict: the creep lands. The fade-in (frames 12–21) shows two red-glasses men, because he moved between
  k0 and k1 and c1 dissolves the whole matte. The blink-out has the same defect.
- Alternative c2 (`plans/zeke-back_c2.json` → `zeke-back_c2/`): same gag, same holds and RIFE creep legs.
  The fade-in is `teleport` with `mode: fade` (n 10, smooth, span 1.0, `in_box` [0.36,0.145,0.445,0.29]).
  The blink-out is `teleport` with `mode: fade` (n 5, linear, span 1.0, `out_box` [0.29,0.145,0.445,0.29]).
  Everything outside the boxes moves by RIFE. Breath 0.015.
- Measure: 79 frames, 3.16 s, 46.8 % generated, step mean 1.892 / max 7.367 (frame 16), seam step 6.013
  (c1 at full size: 9.007), dexp max 0.0731, faces on keys [2, 3].
  Try 1 (`zeke-back_c2_try1/`) used boxes ending at x 0.50. Each box edge then sliced the man's
  head: his k0 half-face stayed pinned inside the box while RIFE moved the rest of him. Frames 14–18 showed a
  vertical cut through his face and a second lens. Try 2 stops both boxes at 0.445, left of his k0 hair.
- What to look at: frames 14–19 and 74–78. The man now stays one person. The cost is a vertical edge through
  the ghoul's hat and right cheek at x 0.445: the part left of it fades in, and the part right of it arrives
  by RIFE at full opacity (visible on frames 16 and 18). Of the two defects, I judged this one smaller.
  Inside the boxes the wall is pinned to k0, which has reflections on the glass that k1 and k4 lack; on
  frames 12 and 74 at 2× I saw no rectangle at 640 px. Check it again at full size.
- Hand-read values (k1 and k4 on 0.02-line grids, ±0.01 ≈ ±12 px on 1186 px; k0 on a 0.05-line grid, ±0.02 ≈ ±24 px):
  - k1 ghoul: hat x 0.37–0.505, y from 0.155; hands y 0.255–0.28.
  - k4 ghoul: hat x 0.30–0.475, face to 0.50.
  - k0 man's head: x 0.445–0.595, y 0.134–0.25.

## zeke-bite
- c1 verdict: the bite and the whip read. RIFE's in-betweens of a roughly 90° head turn draw two pairs of
  glasses (c1 frames 17 and 28–29). Fewer in-betweens would still put one frame near t 0.5.
- Alternative c2 (`plans/zeke-bite_c2.json` → `zeke-bite_c2/`): a hard cut into his real motion-blur still
  and a hard cut back. Owner rule: "a real motion-blur still … use it as a fast beat". Timeline: the bite
  held 20 frames, cut to the whip held 7 (the vampire is gone), cut back to the bite. Breath 0.02.
- Measure: 27 frames, 1.08 s, 0 generated, step max 45.1 at the cut (frame 19), seam step 44.7 (a declared
  cut), faces on keys [1, 2].
- What to look at: whether two cuts read as a double take or as a flicker. The wall behind can jump at both
  cuts, because k1 was registered by ECC (correlation 0.56). The loop is 1.08 s, near the 1 s floor; k0's hold
  can grow to 30 frames if it feels rushed.

## group-teleport
- c1 verdict: the gag lands. c1's `out_box` starts at x 0.845, but her body starts at 0.795–0.80, so her left
  side goes by RIFE. Her squeeze-out and squeeze-in overlap in time (span 0.55).
- Alternative c2 (`plans/group-teleport_c2.json` → `group-teleport_c2/`): she squeezes out completely, the
  group stands 2–3 frames without her (frames 17–18), then she opens on the left. span 0.45, linear, n 12 per
  leg, holds 12 on the right and 18 on the left. `out_box` is [0.795,0.13,0.945,0.84] and the left box is
  [0.135,0.14,0.25,0.80]; the return leg swaps the two boxes. Breath 0.015.
- Measure: 54 frames, 2.16 s, 44.4 % generated, step mean 2.545 / max 6.014 (frame 12), seam step 4.744,
  dexp max 0.0589, faces on keys [10, 11].
  Try 1 (`group-teleport_c2_try1/`) used a left box ending at x 0.295. The leopard-mask man beside
  her was squeezed with her, so frames 21–22 showed two leopard masks. Try 2 ends the box at 0.25.
- What to look at: frames 12–25. Three defects remain, and c1 has all of them:
  - The squeezed layer brightens the whole matte inside the box, so a pale rectangle shows around her at
    frames 12–15 and 21–23.
  - Her elbow at x 0.25–0.29 arrives by RIFE.
  - Frames 19–21 show a faint second pair of boots by the leopard-mask man's feet.
- Hand-read values (k0 and k1 grids, 0.05 lines, 1870 px wide, read to a quarter cell, ±0.02 ≈ ±37 px):
  - Woman in k0: x 0.795–0.94, y 0.14–0.83.
  - Woman in k1: x 0.14–0.29 (0.24 at her head), y 0.15–0.80.
  - Leopard-mask man in k1: x 0.22–0.34.
  - Top-hat man's right edge in k0: about 0.82 at y 0.45–0.80, so 0.02 of him sits inside the right box.

## evgen-thug
- c1 verdict: the gun is the punchline, but it arrives 1.8 s in (frame 46 of 63) and is held 18 frames. The
  set-up takes longer than the joke. The cut back to the pumpkin reads as a reset.
- Alternative c3 (`plans/evgen-thug_c3.json` → `evgen-thug_c3/`; c2 already exists in `scripts/`): the same
  stills with a faster set-up: k0 ×10 · →k1 rife n2 accel · k1 ×2 · →k2 rife n2 decel · k2 ×3 · →k3 rife n4
  smooth · k3 ×7 · cut k4 ×2 · cut k5 ×24 · cut k0. The gun is on screen from frame 32 of 56.
- Measure: 56 frames, 2.24 s, 14.3 % generated, step max 51.5 at the k4→k5 cut (frames 31→32), seam step 49.5 (a
  declared cut), dexp max 0.1226.
- What to look at: frame 14 (RIFE from the blur still to k2, t about 0.5) shows a faint doubled head over the
  pumpkin. The two unregistered stills still jump the wall at the cuts; I left that as a beat.

## talk
- c1 verdict: the poke reads. In the in-betweens near t 0.5 the wand fades to a partial stick (c1 frames
  13–15).
- Alternative c2 (`plans/talk_c2.json` → `talk_c2/`): poke, poke. The rest pose is held 10 frames. Then come
  two jabs of 3 snap in-betweens each, with a 3-frame hold on the poke, 3 in-betweens back and a 2-frame
  recoil. The second poke is held 10, then an 8-frame smooth settle. No breath, so the comparison with c1's 2 %
  push-in is clean.
- Measure: 42 frames, 1.68 s, 40.5 % generated, step mean 0.991 / max 4.947 (frame 22), seam step 1.418,
  dexp max 0.0623.
- What to look at: frames 17 and 22, the middle in-between of each return and jab, where the wand is half
  gone. A snap ease hides it for one frame at 25 fps, and the defect is the same as c1's. The second jab
  should read as a second jab, not as a stutter.

## Gaps
- All five drafts are 640 px. I checked the defects on decoded mp4 crops at 1.0–3.5×, not at full size.
- zeke-back c2 trades the doubled man for a vertical edge through the ghoul's hat. Neither `teleport` mode can
  remove both, because inside a box the frame stays pinned to one still. A per-pixel matte (ghoul only, man
  excluded) would remove both and needs a change to `scripts/`, which I did not make.
- Fewer in-betweens do not fix the wand (talk) or the glasses (zeke-bite): any frame near t 0.5 of a large
  rotation shows the RIFE defect. zeke-bite c2 avoids it with cuts; talk c2 keeps it.
- I did not grade the loops as a viewer would (gif timing, whether a joke is funny); the owner grades.
- evgen-thug c3 changes only the timing, not the idea. Its pick depends on whether c1's slow set-up was the
  problem.

## Confidence
- High: zeke-bite c2 has no ghost (0 generated frames).
- High: the second leopard mask in group-teleport try 1 was caused by the box, and try 2 removes it.
- Medium: zeke-back c2 reads better than c1. The hat edge is visible at 640 px.
- Low: whether the two-cut double take (zeke-bite) and the double poke (talk) are funny.
