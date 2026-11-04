<!-- Provenance: written by an Opus 5.5 subagent (the director track) of the Claude Code session of 2026-11-04 (the angel portrait loop; DECISIONS 2026-11-04); copied verbatim from benchmarks/runs/2026-11-04/angel/agents/director.md (sha256 3d56123ea4ada4ad) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). Three lines on what moves (the second still brighter, the ring clipped), two ideas (a resting-breath tempo, drafted at 640 px; a breath pushed in by depth), rendered by the main thread as a4 and a5. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

## Findings: director

### What moves (3 lines)
- People: the left woman's closed smile becomes a toothy smile, the right woman's head tilts, and the lean is up to 14 px (crop `/private/tmp/claude-501/-Users-yevhens-Projects-personal-reveal-1-5-0/f9495174-91eb-4fda-b938-997caac0ae17/scratchpad/dir/halo_crop.jpg`). With `matte: all`, the couch's 5 px camera parallax is motion too. 26.8 % of pixels differ by more than 14 Lab units.
- Light: k1 is brighter than k0. Its ring is clipped (30,680 px above 250 in the ring box; k0 has 0), the wall is +3.7 grey levels and the frame +4.4. The a1 draft's ring-box mean already rises 7.1 % to a peak at frame 29 with no glow; a3's glow lifts that to 9.0 % at frame 27. The largest frame-to-frame jump is 2.6 grey levels, so no flash (`drafts/a1`, `a3/loop.mp4`, decoded).
- The gag needs: the ring held still (prep: within 0.4 px), its brightness continuous through the loop, and no visible stop in the pose.

### Ideas (≤3; mechanism · knobs · risk · rule at risk)
| Idea | Mechanism | Knobs | Risk (what the skeptic crops) | Rule at risk |
|---|---|---|---|---|
| I1 breathing tempo (no new code; drafted) | The a1–a3 loop is 50 frames = 2.0 s, about 30 cycles a minute (`drafts/a2/measure.json`). A resting breath is about 12–20 a minute [INFERRED, general knowledge]. Shorter holds and longer in-betweens, with the settle-back longer than the lean-in. Breath and sway stretch with the loop because both are functions of the loop phase. | holds 8 / 6 (were 14 / 12); lean-in n 30 sine, settle-back n 40 sine; 84 frames = 3.36 s, about 18 a minute | The mouth spends 70 generated frames half-open instead of 24. At 640 px frames 22 and 60 show faint teeth and no doubled lip (crop below); full size is unverified. Generated share rises from 0.48 to 0.83. | "He sets the pace in words." He has not named a pace, so 3.4 s is a proposal (UNVERIFIED as his taste). |
| I2 depth push (one new effect, about 5 lines in `apply_camera`) | Replace the scalar breath scale with a per-pixel one, so the push-in acts like a dolly: near layers grow, the ring's plane does not, the wall recedes. Math: `sc(x) = 1 + z·sin²(πu)·(1 + k·(D(x) − ref))`, with `D` the same blurred, t-blended depth map and `ref` the depth read at the ring (0.182 in the log). Then `mx = cx + (x − cx)/sc`, likewise `my`, in the existing single remap, composed with the parallax. | z 0.010–0.018; k 1.0. `k·(D − ref)` clamped to ±0.6 | Head against ring: Δd 0.19 at about 130 px from the centre gives 0.4 px at z 1.8 %, which is invisible. Laptop against hoodie: Δd 0.7 at about 860 px gives about 11 px of radial stretch along the laptop's top edge, so a smeared edge. Hence the clamp and z ≈ 1 %. These figures are arithmetic, not renders (UNVERIFIED). | "No hard cutouts, no ugly cheap 2D effects", if an edge smears |

I weighed a third idea and dropped it: lock every effect's peak to the smile hold with a trailing `{"key": 0, "hold": 7}`. The peak already lands within 2–4 frames of the k1 hold (frames 26–37): the breath peaks at frame 25 and the measured ring brightness at frame 27–29. The gain is too small to spend a candidate on.

### Draft (which, the command, what the sheet shows, or "none: needs code")
- Which: I1, `benchmarks/runs/2026-11-04/angel/agents/director/angel_d1.json` (a2 with only the timeline, title and gag changed).
- Command: `.venv/bin/python scripts/research/loop_seq.py render benchmarks/runs/2026-11-04/angel/agents/director/angel_d1.json --out benchmarks/runs/2026-11-04/angel/agents/director/angel_d1 --draft 640` (11.4 s render; mp4 md5 b2a142e3c4b88650a6d9dc999316dd3e).
- Measures (`angel_d1/measure.json`): 84 frames, 3.36 s, step mean 0.95, step max 2.05 at frame 20, seam step 1.56, smallest step 0.36 (no step below 0.3, so the holds never stop), 2 faces on every frame, double-exposure share at most 2.3 %. The a2 draft at 960 px has step max 3.41 and mean 1.67. The two drafts differ in resolution, so the comparison is indicative only.
- Sheet (`angel_d1/sheet.jpg`): a continuous lean-in and smile, then a slow settle-back. The ring is unchanged in place and size on every thumbnail, and no doubled face shows at sheet size. The crop `angel_d1_crop_mouths_f0_f22_f44_f60.jpg` shows the left woman's smile half-open at frames 22 and 60 with faint teeth and a single lip line. The right woman's face is clean.

### Confidence: 70%
Measured: the exposure step, the ring-brightness series and I1's numbers. Inferred: whether 3.4 s reads as "breathing" to him, and how visible I2's edge stretch would be.

### Gaps
- No full-size render and no skeptic pass on d1. Mouths and hands at mid-leg are judged at 640 px only.
- The main thread changed `angel_a2.json` parallax `amp` from 0.009 to 0.014 between my two reads; d1 carries 0.014.
- I2 is not built. Its 0.4 px and 11 px figures are hand arithmetic from the depth values in the brief.
- The glow box [0.03, 0.22, 0.42, 0.50] holds 0 (k0) and 15 (k1) pixels above 235 in rows 0.42–0.50, so a3's bloom barely reaches the hair. Measured on the stills, not on rendered frames.
- The prose pass's cold read by a reader with no session context was skipped (time budget).
