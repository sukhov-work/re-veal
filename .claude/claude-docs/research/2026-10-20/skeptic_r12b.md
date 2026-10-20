<!-- Provenance: written by an Opus 5.5 subagent (the skeptic, round 12, second pass on the sunset's re-render with `wire_to_streak.reveal_ahead=true`, 2026-10-21 about 02:05) of the Claude Code session of 2026-10-20 (the round-12 session; DECISIONS 2026-10-20), copied verbatim from benchmarks/runs/2026-10-20/agents/skeptic_r12b.md (sha256 35c31518bcd9cd7e) on the owner's standing order of 2026-10-17; folded into `TRANSITIONS.md §13.21`, the page `director_r12/notes.json`. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

<!-- Provenance: written 2026-10-20 by the round-12 skeptic's second pass (claude-opus-5-5), Claude Code session of 2026-10-20. Inputs: the re-rendered mismatch_5 clip (md5 0485681a4918a5a284858589f2707c37), the first-pass frames of fd23da82 still decoded in the session scratchpad (sk12/m5_r12.npy), and round 11 (cc153097). No render was run; no tracked file was edited. Scratch work is in the session scratchpad under sk12b/. -->

# Skeptic r12b: mismatch_5 re-rendered with `wire_to_streak.reveal_ahead=true`

The dark band along the streak is gone, and nothing else in the clip changed. The new clip is
better than the first round-12 render. Against round 11 it is mixed. The sun shrinks faster,
which the owner asked for. The bright ring at 55–59 is still there, and so is a straight
horizontal edge under the truss at 18–33, which the first pass did not name; neither fault is
in round 11. The bridge and the disc centre are the same as in round 11. The clip can go on
the owner's page as round 12's sunset if the page names the ring and the unchanged bridge.

Method: the first pass's method, unchanged. I decoded all 90 frames with cv2 and ran the first
pass's own scripts (`bridge.py`, `sun4.py`, `motion.py`) on round 11, on the first render and
on the new render. The first render's frames were still decoded in the scratchpad, so every
comparison below is frame against frame. It does not rely on the numbers the first pass
wrote down. Where the two renders differ: at frames 0–9, by at most 0.8 levels mean. At
15–48 they differ along the streak's diagonal, plus two small patches under the bridge's left
end (signed difference maps at 15, 27, 39, 48). At 51–89 they differ by 1.6–1.9 levels mean
with ≤ 0.17 % of pixels above 12 levels, which is encoder noise.

| First-pass fault | Now | Measurement (first render → new; round 11) |
|---|---|---|
| Dark band along the streak, 15–48 | gone | Column x 1500, frame 27, y 400–640: minimum 35 with 69 px below 50 → minimum 57 with 0 px below 50; round 11: 57 and 0. In the streak box (x 1300–1800, y 380–640) mean luma relative to round 11 at frame 27: −5.9 → +2.2, pixels more than 20 darker: 13.7 % → 0 %. At frame 39: −3.5 → 0.0 and 6.1 % → 0 %. The pale stretched wire bar along the band is also gone; the wire is a thin line, as in round 11. |
| Bright ring round the shrunk sun, 55–59 | unchanged | Radial profile at frame 57: centre 193 → 190, maximum 207 → 208 at r 15 px (rim minus centre +14 → +18). Round 11: 191 and +1. Frame 55: +10 in both renders; round 11: −1. |
| Bridge's discrete motion, then it vanishes at 50–51 | unchanged | Deck top row at x 500 is the same series in both renders within 1 px. It rises at −5 to −7 px/frame at 28–43, slows to −2 at 45–50, then jumps +22 at 50→51 and +32 at 51→52. |
| Disc centre 13–15 px from the core at the beat's end | unchanged | `sun4.py` distance to B's core: 15, 15, 15, 13 at frames 48, 51, 54, 57 (first render 16, 15, 15, 13; round 11 12, 9, 8, 13). |
| Dark ring in the sky at 18–24 (the photo's own halo) | unchanged | Radial profile round (990, 520) at frame 18 is identical in both renders (minimum 32 at r 260–280); round 11: 30. |

Faults the first pass did not name, present in both round-12 renders and absent in round 11:
- A straight horizontal edge under the truss, about 450 px wide (x 1050–1500). It moves up the
  frame from y 1047 at frame 18 to y 924 at 33, with a 2-px vertical step of +6 to +8 levels.
  Round 11 reads +2 to +3 at the same frames. Below it a dark patch sits under the truss at
  15–33, and the truss has red outlines at 27 (seen in crops).
- A pale concentric disc, about 1.4 times the sun's radius, stays behind the shrinking sun at
  frame 24 (seen by eye). Round 11 shows only a pale crescent on the left side at 24.
I found no fault that the new render added.

| Rule | Grade | Basis |
|---|---|---|
| 1 B before its beat | PASS (declared surround) | Stars and the sky key come through the surround from frame 12. The streak's path now reads as round 11's sky; B's own streak line shows only from 63. |
| 2 continuous motion | FAIL | The deck vanishes over frames 50–52. My `motion_px` recompute matches the first render within 0.5 except at frames 12–16, where the peak falls from 31.5 to 27.0 px/frame (cause UNVERIFIED). |
| 4 shape alignment | FAIL | The disc's centre is 13–15 px from the core at 48–57. |
| 5 no foreign edges | FAIL | The band is gone. The ring (55–59), the horizontal edge under the truss (18–33) and the pale disc (24) remain. |
| 7 declared dissolve | FAIL | The last of the disc still dissolves as a ring, 55–63. |
| 11 rate | PASS | Rate as in the first render: the sun's radius halves at about frame 27 (round 11: 37). |

The measures. `b_inside` is now read after the guard: the code at `director_render.py`
lines 1855–1861 sits below the guard block. It reads 0.364 at frame 15 and 0.547 at 18, against
0.39 and 0.61 in the first render. The difference of 0.03–0.06 is about the size of the
bridge guard's share (`share_B` 0.0396, `guard_share_max` 0.0944). It agrees with what I see:
B's stars and the keyed sky cover most of A's sky by frame 18. I did not compute an independent
value. The line is taken before the front and element layers are drawn, so B under an A layer
drawn later still counts as shown. `residual_edges` peaks at 1.0 % at frame 24, the same as
the first render's 0.9 %, although the band is gone. That means it never measured the band;
it also reads 0 at 54–60 and misses the ring. `motion_jumps` 4 at frames 9, 10, 11 and 15 is
the sky key and the stars; it misses the deck's vanishing at 50–52.

### Confidence

85 % that the band is gone and nothing else changed: the frames were compared directly against
the first render's frames, and the difference maps sit on the streak's path. 80 % on the
unchanged ring, bridge and centre: the same scripts gave the same numbers within 1–4 levels or
1 px. 60 % on the two unnamed faults: the horizontal edge is measured, the pale disc is by eye.

### Gaps

- I did not compute `b_inside` independently, because it needs the renderer's maps.
- The pale disc at frame 24 is seen by eye; I did not measure which frames it spans.
- I did not check that the streak's end shape (frames 80–89) matches B's.
- I watched frames at full size and in crops, not the clip at speed.
