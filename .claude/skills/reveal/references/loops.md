# Loops and sequences: the playbook (distilled 2026-10-30 from three sessions)

Read this first when the owner asks for a looped clip, a GIF, or a clip from a sequence of his stills.
The sources: the duck loop of 2026-10-20/21 (two stills, a morph with hand anchors; `research/2026-10-20/loop_report.md`,
DECISIONS 2026-10-21 lines two to four), the box sequence of 2026-10-09 (seven stills of a repaint, one gradual
clip; `benchmarks/2026-10-09-fabra-boxes.md`, `TRANSITIONS.md §12.24`, `mem:project/wip-2026-10-09-fabra-boxes`),
and the Halloween loops of 2026-10-30 (ten sequences of 2–6 handheld stills, four rounds; `TRANSITIONS.md §13.24–13.26`,
`benchmarks/2026-10-30-halloween.md`, `research/2026-10-30/`). The tool is `scripts/research/loop_seq.py`
(prep · render · page; the plan grammar in `scripts/research/plans/loops/SCHEMA.md`). Neither `reveal.py` nor
`transitions.py` changes for this work (owner rule); the UI flow is backlog T68.

## 1. Intake (ten minutes, before any render)
- Read the stills as thumbnails and a per-pair diff view (Lab distance) before deciding anything. Say in one line per
  sequence what moves, what appears or vanishes, and what the gag is. Ignore ARW and XMP files; read the sources in
  place, never copy them (the originals are never modified).
- Expect a handheld camera even when the stills look alike: 0.5–3 % shifts and up to 3 % scale between shots. A
  tripod is the exception. Every pair is registered on the background before any in-between.
- Ask nothing up front that the first page can answer; the owner grades a page, not a question. Record his grades
  verbatim before the next round starts (the sheet's "Owner grades", a DECISIONS line).

## 2. The pipeline in order
1. `prep` every sequence (`loop_seq.py prep <raw dir> --out <run>/in/<seq>`): SIFT + MAGSAC to one still, chained
   SIFT, ECC seeded by the chain, else a declared cut (`--cut i,j`). Check the inlier counts and look at a montage of
   the registered stills. A still the subject fills against a plain wall cannot be registered (5–9 inliers; ECC fits
   the subject): join it by a cut or a snap, or read three background anchors by hand (T64).
2. Probe the in-between methods on every adjacent pair before planning (the morph and RIFE strips side by side,
   about ten minutes for twenty pairs). The DIS morph doubles a subject on a large motion; RIFE inside the change
   matte does not; on small motions they are alike. Rule 7's double-exposure share per RIFE in-between runs 3–11 %
   here (17 % into a blurred still); the café probe's 1 % bar is never met and is not the bar for these.
3. One plan per sequence, hand-written (`plans/loops/<seq>[_cN].json`): holds on the stills, transitions, effects.
   A first candidate per sequence; a second only where the shape is a real choice (a cut version beside a morph
   version). Render at full size (a 640 px draft shows nothing a skeptic can judge).
4. The skeptic (an Opus 5.5 subagent) crops every candidate at full size before the page: doubled props, faces and
   hands at mid-leg, box edges, halos, stalls and jumps in the step series. Seven of twelve round-1 candidates were
   NOT READY on crops the contact sheets did not show. A render replaced after the pass is unjudged until the next.
5. The page (`loop_seq.py page`): per sequence the keyframes strip, the mp4 and the gif, the numbers, a note that
   says what moves, which frames are generated, where to look and the skeptic's verdict. One page, every candidate,
   opened in his browser. His grades come back as a short text per sequence.
6. The next round from his words only. Do not add candidates he did not ask for.

## 3. The owner's taste, as rules (each from his words; the date is where the words are)
- A sequence with more than two stills is ONE continuous motion: never a hold on an inner still, never a
  per-segment ease that stops at a still ("not like 1-2 (small pause) 2-3", 2026-10-30). The `through` chain with
  one global profile; `knot_margin` about half a frame's share so no frame hugs a still.
- "no flashes, no double pokes, nothing jerky" (2026-10-30). No stylized beam, flash or squeeze; no repeated beat.
- A person who moves far between two stills dissolves out in place and in at the destination while the others
  morph ("just dissolve morph person into background and do inverse in destination", 2026-10-30). A flight of her
  cutout was "very dirty"; a squeeze to a line "cardboard cut out".
- A sudden appearance is a short blurred snap, not a rise from behind ("a more immediate snap … more fluid and
  with slight motion blur", 2026-10-30). The rise was "ugly and has lots of artifacts".
- He sets the pace in words ("20 % faster", "30 % faster", "1.5 times faster" twice on the duck): holds and
  in-between counts are his knobs; apply the percentage to the frame count.
- The breath (a 1.5–2 % push-in over the loop) is per clip: fine on an idle animation and an object ("make duck
  and white foreground breath a bit", 2026-10-21; "breathing effect is fine here" on the NPC), off where the
  motion is the subject (the talk, the group photo). It resamples every held frame; he did not object.
- An idle animation "resembles NPC selection idle animation in games": a constant-speed cycle through the poses,
  softened near each pose, never stopping.
- Real motion-blur stills are frames he shot: pass them fast inside the chain, do not hide them.
- A repaint sequence (the boxes) is one gradual per-pixel drawing with the changed objects pinned in position and
  size, no synchronized boundary between segments, nothing stepping elsewhere, no crop, a long hold at the end
  ("really seamless", 2026-10-09). Hard jumps between joined clips were the fault he named.
- Eyes and heads need anchors in a morph: the irises slide, they do not dissolve (the duck loop, glide2); a few
  wrong anchors bend a straight rail (glide4, 29 anchors, not graded better).
- "funny (but technically sophisticated and nice looking)": one idea per clip, the joke in the timing, the
  technique invisible.
- A seasons or landscape sequence of one view (2026-11-01, the Ivano-Frankivsk stills): the registered wipe is the piece.
  Content never moves inside a sheet ("all other example are horribly misaligned" on carried and drifting pictures); the
  edges keep a slant and move laterally ("lateral should be movement itself"); the depth cue bends the EDGE by the depth map
  (`edge_depth`), never the pixels; buildings take the coming season early and keep it late by Poisson plates ("very subtly");
  a pattern of cells (bands, a lattice, chevrons) is "simple 2d … junky". s6 of that day ("perfect") is the reference plan.

## 4. Recipes by situation (what to render first)
| Situation | First candidate | Knobs that matter | Do not |
|---|---|---|---|
| Two stills, a small pose change | RIFE in-betweens inside the change matte, sine ease, holds 8–14, a breath if the subject is an object | n 6–10 each way | morph (alike, no gain) |
| Two stills, a big move of one subject (a head turn, a lunge) | three in-betweens each way (the ghost flashes by) or a hard cut; a snap with a motion blur if he wants "fluid" | n 2–3, `blur_frac` 1.5–2.2 % | n ≥ 4 (the ghost doubles), the morph (doubles) |
| One person moves far, the others shift | the slide's `mode: dissolve` (out in place, in at the destination) over a base of RIFE between the stills with her removed; GrabCut mattes with `exclude` boxes; `fill: donor+vertical` at the destination | the windows [0, 0.55] and [0.45, 1]; the boxes from a reading | the flight, the squeeze, a plate by Telea |
| A person present in one still only | a 3-frame `snap` with a vertical blur, then the motion | `blur_frac` 2.2 % | a dissolve over the whole matte (the others double), a rise from behind |
| 3–6 stills of one motion | `through` chain, `ease` linear or accel, `weights` by the motion's size per leg, `soft` 0–0.5, `knot_margin` 0.04; a hold only at the loop's ends | the profile he names (slow start, fast draw) | holds on inner stills, per-segment eases |
| An unregistered still inside a sequence | a cut, or a leg weighted to 0.001 inside the chain (a jump), or RIFE across the jump (reads as a fast zoom) | `--cut` in prep | ECC (fits the subject) |
| A thin rotating prop (a wand) | accept the half-fade at n 3, or a per-person layer (T63) | — | anchors through the morph (both people doubled) |
| Many people (a group photo) | RIFE at n 8 with the ghosts, or hard cuts (spot the difference), both on the page | the pace he names | expecting any in-between to carry 14 people |
| A repaint of fixed objects (the boxes) | the `draw` of 2026-10-09: the objects pinned on their own features, one dissolve with a per-pixel order, no segment boundary | 3 s + a 3 s hold; 4:5 for Instagram | joined per-pair clips (visible stops) |
| Three stills of one view across seasons (a landscape) | `sheets`: two diagonal sheets entering from opposite sides over the held base still, `motion: lateral`, `carry` 0, `overlap_alpha` 0.5, a contact shadow, `edge_depth` 120 from the depth model's map, buildings as Poisson plates with lead 4 / linger 14, a 75 % output crop on a 3600 px prep (`seasons_s6.json`) | `n` (135), `hold` (30), `edge_depth`, `shadow_px`, `lead`/`linger`; many narrow bands by `gen_seasons_bands.py` with depth `layer`s | content motion inside a sheet (`carry` above 0), a pattern of cells, the DIS morph (tears the sky), a reflect or wrap fill beyond the canvas |
| Any loop | the gif at 25 fps (40 ms exact), the mp4 at crf 14, the seam a still or a declared cut | `gif_long` 540 | 30 fps gifs (33 ms is not storable; they run 10 % fast) |

## 5. What failed; reopen only with new evidence
- The teleport as a beam, a flash cut, a squeeze to a line, or a flight with a motion blur (2026-10-30, his words).
- The rise from behind with an occluding matte (2026-10-30, his words): the man's matte stops short, the fill shows.
- Hand anchors through transitions.py's morph on a pair where the bodies move (the talk): both people doubled.
- ECC on a still the subject fills; a masked ECC on a plain wall (scale 0.51); a scale sweep with phase correlation.
- A colour-threshold person matte when the clothes sit within about 16 Lab levels of the wall; a largest-component
  rule (it drops the boots); a Telea inpaint of a person-sized region (a smear).
- A region filled from the other still where someone stood there (the man's old head at the ghoul's spot).
- Per-segment eases on a chain, a sine ease after a snap (a stall), RIFE frames within 4 % of a still (a stop).
- A premultiplied cutout multiplied by its matte again (a halo); an eroded matte in a fade (the outline goes).
- A plain morph on a near-duplicate pair with few inliers (the duck: 12 inliers, class B pan-and-zoom).

## 6. Measures and bars (on the decoded mp4; `measure.json`)
- The step series: no run of steps below 0.3 while motion is open (a stall); no step above 3× its neighbours
  outside a declared cut or snap (a jump); the seam step is a still (about 1–3) or a declared cut.
- Rule 7's double-exposure share per generated frame (3–11 % is the floor on these pairs; a doubled prop is found
  by a crop, not by this number).
- YuNet faces per frame against the keyframes' counts (noisy on a group and under a breath).
- A render reproduces its md5; the page is recorded by md5; every replaced render is kept under `round<N>/`.

## 7. Routing and budget (what it took on 2026-10-30)
- The main thread: the script, every full-size render (RIFE about 1.3 s per in-between at 1900 px), the page, the
  measures. Opus 5.5 subagents: the skeptic (every round, 5–6 minutes, 20–60 tool calls), the readings (boxes and
  anchors at 2–3× with ±px, about 12 minutes), director tracks (one alternative per sequence, drafted at 640 px,
  5–11 minutes each). Waves of at most three.
- A round of ten sequences: prep and probes 30 minutes, the first renders 10 minutes, the skeptic 6, the page 2,
  the record 20. A fix round on two clips: about 40 minutes including the pass.
- Reports under `benchmarks/runs/<date>/<run>/agents/` are copied to `.claude/claude-docs/research/<date>/` with a
  provenance header before the commit.

## 8. Traps that cost time
- An unquoted shell heredoc eats backticks in a Python text: quote it (`<<'EOF'`), pass values by environment variables.
- yuv420p refuses an odd side: crop a draft to even sides.
- A GrabCut needs a long side of about 1000 px (at 450 px it finds nothing) and a neighbour inside the box must be excluded.
- A matte's box that reaches another person's head takes that head when it moved (the girl's face at the sink).
- `git add` with a gitignored path aborts the whole add; the run folders are gitignored, the plans and the script are not.
- The sanity range of a background map must allow a photographer stepping closer (scale 0.5–2.0); a few dozen
  inliers on a subject-filled frame can fit a wrong model: look at the overlay.

## 9. The record (every round)
His grades verbatim in the sheet · the DECISIONS line with the order verbatim, the md5s and the tiers · the sheet's
round section with the table (`candidates.md` regenerated) · `TRANSITIONS.md §13.N` · the backlog states ·
the tooling list rows · the research copies · the handover (the page md5, the watches: `prep` on the talk pair, the
talk and NPC renders by md5) · the memory leaf's Traps · commit on `main`, push.
