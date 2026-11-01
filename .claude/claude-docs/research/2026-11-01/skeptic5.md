<!-- Provenance: written by an Opus 5.5 subagent (the skeptic, pass 5) of the Claude Code session of 2026-11-01 (the seasons loop; DECISIONS 2026-11-01 third line); copied verbatim from benchmarks/runs/2026-11-01/seasons/agents/skeptic5.md (sha256 42524ed65e981178) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). The pass on the first round-3 renders (s5, s6: the lateral wipe with a depth-bent edge; now under round3a/): no content motion, the lateral motion with the slant kept, the tempo 1.5× longer, the objects as in s4; both NOT READY on one defect, a wedge of the late-autumn sheet left in the bottom-left corner at the last frame because the reach did not include the depth bend (a seam pop); s6's 120 px bend a stepped notch at the near tree. The reach fix followed and both were re-rendered; the re-renders were checked by the corner numbers, not re-judged. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

# Skeptic pass 5: s5 and s6 against s4 (2026-11-01)

Both candidates are NOT READY for one shared defect: the late-autumn sheet never fully leaves the bottom-left corner. In the last frame (163) a wedge of late autumn is still on screen, about 55 px wide in s5 and about 110 px wide in s6, and the loop seam (frame 163 to frame 0) removes it in one frame. Everything else he asked for holds in both. No content moves, the motion is lateral with the 62° slant kept, the sweep is 1.5× longer, and the objects are those of s4. s5's depth bend reads as a soft curve; s6's shows a stepped notch at the near tree. Rank: s5 over s6. I did not play either clip at speed; all judgements below come from decoded frames, crops and numbers.

## The defect and its cause

| Clip | Pixels > 12 levels off summer, bottom-left 400×400 box, frame 163 | Frame 0, same box |
|---|---|---|
| s4 (frame 118) | 19 | mean 2.77 |
| s5 | 2,609 (mean 3.68) | mean 2.77 |
| s6 | 10,301 (mean 5.64) | mean 2.77 |

Crops: `skeptic5_crops/s5_f163_bottomleft_1x.png`, `s6_f163_bottomleft_1x.png`, `s4_f118_bottomleft_1x.png` (frame left, `k0` right). The wedge holds dark bare branches over bright summer leaves, so the contrast is high. s5's wedge settles (4,003 → 2,609 px over frames 160–163) and the seam drops it. That is a pop on every loop, which breaks his "nothing jerky" rule.

Cause (read from `scripts/research/loop_seq.py`, `band()`): `reach = E / 2 + Wb / 2 + 2.0` does not include `edge_depth`. The bent edge is `ue = u - sign * edge_depth * D0`. At the final displacement `-reach`, the late-autumn sheet ("+") still covers pixels with `u - edge_depth·D0 < u_min + 2`. The near tree fills the bottom-left corner (depth about 0.85), so the residue is about 0.85 × 60 = 51 px in s5 and 0.85 × 120 = 102 px in s6. Entry is clean (frames 31–34: mean |frame − k0| 2.64, equal to the hold).

First knob: this is a renderer fix, not a `SCHEMA.md` knob. Add `edge_depth × max(D0)` to `reach` in `band()`, and lengthen the sweep so the ease still ends at rest. Setting `edge_depth` to 0 also removes the wedge, but it removes the depth bend too.

## Check table

| # | Check | s5 | s6 | Evidence |
|---|---|---|---|---|
| 1 | No content motion | pass | pass | Each frame was matched per pixel against k0, k1, k2 and the k1/k2 mean, with a 0.7–1.0 gain allowed for the shadow. Pixels left unexplained (> 12 levels), outside a 60 px band around the label edges and outside the object boxes: max 34 per frame in s5, 33 in s6, 28 in s4, out of 5.27 M. Codec floor at frame 0: median 1.27, p99.9 7.16. Crop `registration_tower_s4f96_s5f142_1x.png` (both frames show summer at the tower; it shows the same registration and is not an overlap sample) |
| 2 | Lateral motion, slant kept | pass | pass | Early-autumn edge, frames 62 → 70: x at row 300 moves 33 → 503 and x at row 1700 moves 727 → 1224 (s5). The rows are 694 px apart in x, against 744 px for a straight 62° line; the 50 px difference is the bend on the near tree. s6: 676 at row 1700, a difference of 101 px. Late autumn enters from the right (row 300, x 1866 at frame 62) and early autumn from the left; each exits on the opposite side (frame 134) |
| 3 | Depth bend at the fir and the near tree | soft curve; the edge follows the bright tree's crown | visible stepped notch on the near tree's top at the exit | `bend_fir_neartree_f66/68/70_s5_s6_1x.png`, `exit_neartree_f138/142/146_s5_s6_1x.png`, `exit_kink_f146_s5_s6_2x.png` (s6: a shelf about 100 px wide near output y 1575) |
| 4 | Tempo | pass, apart from the seam | same | Hold frames 0–29; first non-summer pixels at frame 37 (s4: 34). Sweep 134 frames (s4: 89), 1.51×. Peak edge speed 77.6 px per frame (s4: 102.7). Maximum step 2.05 at frame 73; largest ratio of a step to its neighbours 1.25 (s6: 1.29), at frame 117 |
| 5 | Objects as in s4 | pass | pass | The same four buildings, lead 4 and linger 14 (plan diff against s4: only `n`, the swapped sides, `motion` and `edge_depth`). Alpha spans, s5: apartments k2 51–112, left_blocks k1 56–115, tower 74–130; the order follows each sheet's direction |

## Defects

- Seam pop at the bottom-left corner, frame 163 → 0. s5: severity medium, a 2,609 px wedge. s6: severity high, a 10,301 px wedge.
- s6 only: the 120 px bend draws a stepped notch where the depth changes from the middle ground to the near tree (`exit_kink_f146_s5_s6_2x.png`). It looks like a cut-out rather than depth. Severity medium.
- Step series, frames 115–117: 0.81 → 1.09 → 1.75, a shelf rather than a spike, under the 3× rule. Cause not determined [INFERRED: an object plate or the overlap area changing].

## s5 against s6

s5 ranks first. Its bend is half as large and does not form a notch, and its seam wedge is a quarter of s6's area. After the reach fix, s5 would be READY on every check here [INFERRED: the other checks do not depend on reach].

## What I could not determine

- How the motion and the pop read at 25 fps, because I did not play the clips.
- The GIFs, which I did not inspect.
- Whether the s5 bend reads as depth or as a wobble in motion: the stills show a smooth contour, but frame-to-frame behaviour at speed is unverified.
- The overlap region at 1:1 at a tower frame. Registration inside the overlap rests on the per-pixel numbers in check 1, not on a crop.
