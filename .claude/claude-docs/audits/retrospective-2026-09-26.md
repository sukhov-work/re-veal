# Retrospective, 2026-09-26: why twelve days of transition work produced no accepted clip

Verdict: every slice since 2026-09-13 changed WHERE pixels go (the correspondence field, the border,
the camera, a parallax) and none changed HOW the two photos are combined, which has stayed an alpha
crossfade since TR1; the owner grades the combination, so every round of picks reads "crossfade".
The numbers in the quality basket cannot see that property, so nothing screened a candidate before
the owner did. The one experiment that touched the combination (the luma reveal on the TR14 page,
2026-09-15) drew the only "promising" note on a changed region. This file states the goal in one
paragraph for the owner to confirm, names what failed in the method, calibrates six candidate goal
numbers against the owner's recorded verdicts, reports one probe that tests the diagnosis, and
proposes the next rank. Sources: the six picks files and sheets under `benchmarks/`, DECISIONS
2026-09-13 to 2026-09-23, `TRANSITIONS.md §7/§10`, the three research reports of this session
(`benchmarks/runs/2026-09-26/research/track_{A,B,C}.md`, copied from the session scratchpad).

## 1. The goal, in the owner's words, then in one paragraph to confirm

Verbatim, by date (sources: the picks files; `benchmarks/2026-09-1{3,4,5}-real-pairs.md`;
`2026-09-15-generative.md §6`; `2026-09-23-camera.md §5`):
- 2026-09-13: "still missing accuracy and those interesing intermediate transformations of parts of
  image"; "such junky transition show how we miss to grasp some themes or objects or ideas about
  given frame and build flows around them even if they are quite detached both physically and
  conceptually from each other"; mismatches are "naive cross-dissolves with very simple frame
  movements animation".
- 2026-09-15: "box itself looks a bit boring as if prev image on it simply fades out and new one
  fades in, no transformations"; "i liked how the box itself holds position"; "I want even more
  transformation … a bit luma looks promising"; "the main problem remains with mismatches, the still
  more reseble simple crossfades with various cheap effects on top and not truthful continous
  transformations … keep as many details from both pictures and bridge them with unexpected cool
  flowing transition".
- 2026-09-22/23: "neural slop … halucinations artifacts in almost all intermediate frames which
  preserve no features and make both images unrecognizable (except skeletons, which are again dumb
  crossfades)"; the depth move "added really cool dynamics to before and after images … at least
  as option".
- 2026-09-25/26: "all are just unnecessary pans and basiacally cross fading between start and
  finish, not usable at all, no transition, that would preserve and gradually morph details and
  different image aspects"; "we are stuck, conceptually"; the depth pass "was not expected to help
  with transition in any way … at most nice additioal touch to image".

The goal as I now read it (the owner confirms or corrects this paragraph; every later metric is a
proxy for one sentence of it):

> A transition is a clip in which every intermediate frame is ONE coherent picture, not two pictures
> superimposed, and that picture is made only of details that exist in photo A or photo B. Over the
> clip those details move and change continuously from where and what they are in A to where and
> what they are in B. For unrelated photos the motion is organised by what the two photos share as
> themes: a sun travels to the other sun, a skyline to the other skyline, a face to a face, a sky to a
> sky. A subject that does not move in reality keeps its place while its surface transforms rather
> than fades. Nothing appears that is in neither photo. A global camera move (pan, zoom, parallax) is
> decoration on top of a transition, never the transition.

Three failure modes follow from that paragraph, and the owner has named each more than once:
- F1 double exposure: the mid frame shows both photos at once ("crossfade", "fade out fade in").
- F2 decoration without transformation: motion that is a global pan, zoom or parallax ("unnecessary
  pans", "cheap effects on top").
- F3 invention: intermediate content that is in neither photo ("neural slop", "hallucinations",
  "preserve no features").

## 2. What each slice varied, and what the owner said

| date | slice | what varied | the combination of A and B | owner verdict |
|---|---|---|---|---|
| 2026-09-13 | TR1 + first sweep (60 clips) | presets, 1 s / 3 s | alpha crossfade (luma / iris / wipe presets existed; none picked) | 0 of 12 usable; 3 closest picks on matched pairs; mismatches "naive cross-dissolves" |
| 2026-09-14 | TR2c pan-and-zoom (class B border) | geometry of the class B frame | alpha crossfade | "didn't notice much difference … more subtle … still junky cross-dissolves" |
| 2026-09-14/15 | TR5 RoMa field (24 clips) | the class A dense field | alpha crossfade | 1 better, 1 same, 3 DIS better, 1 neither; "fades out and fades in, no transformations" |
| 2026-09-15 | TR14 page (66 clips): hold, hold-dis, luma, edge-grow, melt | the changed region's motion; luma and edge-grow changed the combination inside the mask | alpha outside the mask; an ordered reveal inside for two variants | 0 of 4; "even more transformation … a bit luma looks promising"; melt "too wobly" |
| 2026-09-15 | TR6 generative bridge, LTX (≈20 clips) | the pixels themselves (SDEdit, video model) | alpha in the skeleton; generated in the bridge | all none; "horrible neural slop"; LTX "a cut or dumb fade" |
| 2026-09-15 / 09-23 | TR10 depth camera, then `--camera` (43 runs) | parallax on the class B geometry | alpha crossfade | liked as an image effect; as a transition "nothing improved"; 2026-09-25: "unnecessary pans and basically cross fading" |

Count: six review rounds, 343 clips in the run folders (my inventory of 2026-09-26), zero
accepted. Five of the six rounds varied geometry only. The mixing operator of `morph_frame`
(`transitions.py`, the coverage-aware alpha mix) is the same code as on 2026-09-13.

## 3. What did not work in the method

1. **Built before it could be measured.** The basket (warping error, flicker, `edge_ratio`, endpoint
   fidelity) screens defects. The record already says so on 2026-09-15 ("the basket screens defects,
   the owner's verdict grades quality", DECISIONS 2026-09-15), and the plan of 2026-09-23 ranked a
   goal number SECOND, after the camera build. Three more slices went to the owner judged by the same
   basket plus my eye. §5 shows the basket's numbers do not separate the owner's "crossfade" clips
   from the "closest" clips (AUC 0.46–0.48), which is what "cannot see it" means in a number.
2. **My eye stood in for the owner's, and it is not calibrated to the owner's.** The generative sheet
   says "by the agent's eye mismatch_1 reads as a transformation" (2026-09-15, fact 3); the owner:
   "horrible neural slop". The 2026-09-15 TR10 note says "still a crossfade with parallax by eye" and
   the same move was built as an option and swept twelve fixtures eight days later. A judgement my
   eye makes is not evidence in this project; only the owner's verdict and a metric calibrated on
   it are.
3. **The owner's words were mapped onto the slice names of an inherited plan instead of into a
   specification.** "Interesting intermediate transformations of parts" became "that is what the
   generative tier exists for" (2026-09-13 diagnosis); "grasp themes" became TR9; "more transformation"
   became a second TR14 probe that never ran. The research plan (`impossible-0.1.0/RESEARCH-PLAN.md`)
   was written before any owner verdict existed, and its gates (E2, E17) measure routing, flicker and
   "does the motion follow the skeleton", none of which the owner grades. E17 passed on clips the
   owner rejected outright.
4. **The rank changed after every round instead of one line of work converging.** Five rank revisions
   in ten days (2026-09-13 night, 09-14, 09-15, 09-15 late, 09-23). TR14, the only line with a
   positive note ("a bit luma"), was displaced by the generative route the same evening and never
   got its second probe. The cheapest falsification of the "themes" hypothesis, hand-placed anchors
   through the existing `--anchors` path, was available since TR1 and never run on a real pair until
   today (§6).
5. **The review surface asked for a pick, not for the property.** A "best variant" radio and one note
   per pair gave one sentence copied across six pairs. Nothing on the page asked "is the mid frame one
   picture or two", "does the motion transform content or move the frame", "is anything invented", so
   no per-property signal exists to calibrate a metric on, and the same three complaints were re-read
   each round as if new. The "acceptable as-is" box (added 2026-09-15) helped once; the rest did not.

## 4. What blocks a clear reading of the goal

On my side, the items of §3: no goal metric, my eye as judge, plan names in place of a specification,
no convergence, a pick-shaped review page. On the owner's side, three things I do not have:
1. **No positive example.** Twelve days, zero accepted clips, and no external reference either. A
   metric calibrated only on rejections learns what to avoid, not what to reach. One or two reference
   clips (any source: a film title sequence, a music video morph, a demo the owner likes) or, failing
   that, a sentence per fixture pair saying what SHOULD happen at mid-transition (mismatch_4: "the
   sun travels to the other sun while the water stays water").
2. **A yes/no on the goal paragraph of §1**, with corrections. Every metric below is a proxy for one
   sentence of it; if a sentence is wrong the metric is wrong.
3. **Per-property verdicts on the next page**: three yes/no boxes per clip (one picture or two at
   mid-frame · content transforms or frame moves · anything invented), plus the pick. Calibration
   needs about ten clips per box in each state.

## 5. Candidate goal metrics, calibrated on the recorded verdicts

Script `scripts/research/verdict_metrics.py` (research only, imports neither tool). It reads every
clip under `benchmarks/runs/` that a picks file or a sheet graded, computes the numbers below on a
640-px gray proxy of at most 31 sampled frames, and scores each number by AUC: the probability that
a clip of the first group scores above one of the second (0.5 = blind). Labels are hand-coded from
the picks files and the sheets and listed in the script (`label_of`): POS = the owner's closest pick
or "makes sense / more natural / promising"; XFADE = "crossfade / fade in-out / dumb crossfade";
PAN = "unnecessary pans / cheap effect" (the 2026-09-23 cameras and the 2026-09-15 depth clips);
HALLUC = the generative bridge and LTX clips; NEG = rejected for another reason (a slide, wobble, a
cloth effect); none = not graded individually. Full table: `benchmarks/runs/2026-09-26/metrics/scores.md`.

Definitions (endpoints = the clip's first and last frame; interior = every other sampled frame):
- `feat_floor` (F1, F3): SIFT descriptors of A and B (1500 each); per interior frame, ratio-test
  matches to A divided by A's count plus matches to B divided by B's count; the minimum over the clip.
  A frame must still carry features of A or of B. A double exposure halves contrast and loses
  keypoints; an invented frame matches neither.
- `contrast_floor` (F1): the median patch standard deviation (24-px patches) of a frame divided by
  the same statistic interpolated between A and B; the minimum over the clip. A blend of two
  uncorrelated textures has about 0.7 of the endpoint contrast; a partition or an aligned morph
  keeps about 1.0.
- `laplace_floor` (F1, F3): the same ratio on the variance of the Laplacian (sharpness).
- `motion_share` (F1 versus F2): for each frame pair, (mean absolute difference − the same after
  warping by DIS flow) / mean absolute difference; the mean over the clip. The share of the change
  that motion explains. A crossfade scores near 0.
- `local_share` (F2): mean residual DIS flow after fitting a similarity to it, divided by mean flow
  magnitude; the mean over the clip. A pan or zoom scores low; content motion scores high.
  `local_px` is the residual in proxy pixels.
- `dissolve_fit` (F1): for each frame pair, the R² of the fit (frame t+1 − frame t) ≈ β·(B − A) over
  all pixels; the mean over the clip. The share of the frame change that a plain crossfade explains
  (Track C's dissolve-explained fraction). A dissolve scores near 1; higher means more crossfade.

Results (2026-09-26, 343 clips measured; POS 35, XFADE 132, PAN 42, HALLUC 62, NEG 36, none 36).
Pooled AUC (all clips; a value below 0.5 means the metric is higher on the second group, so read
`dissolve_fit` as 1 − the value):

| metric | POS vs XFADE | POS vs PAN | not-HALLUC vs HALLUC |
|---|---|---|---|
| `laplace_floor` | 0.75 | 1.00 | 0.66 |
| `feat_floor` | 0.69 | 0.79 | 0.73 |
| `contrast_floor` | 0.67 | 0.71 | 0.61 |
| `motion_share` | 0.56 | 0.35 | 0.79 |
| `local_share` | 0.57 | 0.72 | 0.23 |
| `dissolve_fit` | 0.21 (0.79 inverted) | 0.42 | 0.61 |
| shipped `warping_error` | 0.48 | 0.47 | - |
| shipped `flicker.mean` | 0.47 | 0.46 | - |
| shipped `edge_ratio` | 0.46 | 0.67 | - |

Within-pair AUC, POS vs XFADE+PAN, on the five pairs that carry both labels (match_1–5; 1 to 11
positives per pair; the mismatched pairs carry no positive at all): `laplace_floor` 0.78,
`feat_floor` 0.76, `motion_share` 0.77, `contrast_floor` 0.69, `dissolve_fit` 0.23 (0.77 inverted),
`local_share` 0.46; shipped `flicker.mean` 0.77, `edge_ratio` 0.74, `warping_error` 0.60. Per-pair
values spread from 0.36 (match_5) to 1.00 (match_1, match_2); full table in `scores.md`.

Reading:
- The shipped basket is blind on the pooled question (0.46–0.48 on "closest" against "crossfade").
  Within a matched pair it separates at 0.60–0.77, because there the picked clip is the one with MORE
  motion (the owner picked `dis` over `hold`), and flicker is a motion proxy. So the basket never saw
  the mismatched pairs' problem, and on the matched pairs it saw motion, not transformation.
- `laplace_floor` and `feat_floor` are the strongest candidates for F1 and F2 (pooled 0.69–1.00,
  within-pair 0.76–0.78); `dissolve_fit` is the cleanest "is it a crossfade at all" number (0.79
  pooled, 0.77 within-pair, both in the expected direction); `motion_share` and `feat_floor` flag F3
  (0.79 / 0.73 against the generative clips).
- The pooled numbers carry a confound: every positive is a matched pair and most negatives are
  mismatched pairs, so a metric that merely sees "unrelated content" scores well. The within-pair
  table removes it and keeps the same three candidates ahead, at a weaker 0.76–0.78 with 1–11
  positives per pair. This is enough to choose candidates, not to set thresholds.
- `local_share`, the F2 candidate, fails within pairs (0.46); its pooled 0.72 against PAN is the
  confound. "Frame moves versus content transforms" has no established number yet; Track C's
  motion-compensated dissolve fraction (fit the frame change to β·(B − A) after removing the global
  motion) is the next candidate to compute.
- On the six mismatched pairs there is no positive clip at all, so nothing is calibrated where the
  problem is. The owner's reference (question 2) and verdict on the anchored probe (question 3) are
  the first positives that could exist there.

What the metrics still miss, found by the probe of §6: a partition front (every pixel from A or B,
switched region by region) scores highest on `feat_floor` and `contrast_floor` and looks, to my eye,
like a wipe in blotches. "Cheap effect on top" has no number yet; the owner's per-property verdicts
on the next page (§4 item 3) are what a seam metric would be calibrated on. Track C's report lists
the candidates (image-fusion metrics Q^{AB/F} and Piella; LPIPS curves to both endpoints; the
motion-compensated residual ratio from video coding).

How the metrics enter the tool (proposal, not built): `assess()` gains `laplace_floor`, `feat_floor`,
`dissolve_fit` and `contrast_floor`, computed on the same 480-px proxy; a transitions harness check renders a crossfade of two unrelated harness
frames (must score `feat_floor` below the calibrated line) and an aligned morph of `affine_pair()`
(must score above it), each with its red-making mutation; the bench sheet and the review page show
the numbers beside every clip so the owner can see whether they agree with the eye.

## 6. The probe: three anchor pairs on mismatch_4

`benchmarks/runs/2026-09-26/probe_mismatch_4/` (scripts `probe_anchors.py`, `probe_partition.py`;
contact sheet `probe_m4_contact.jpg`; numbers `probe_m4_metrics.json`). The anchors were placed by a
brightest-blob sun detector and a horizon row detector, not by hand: sun (939,195) → (955,437),
horizon row 692 → 793 at 10 % and 90 % of the width. Six clips of 2 s at the 1920×1092 canvas (the
two shipped ones and four probe renders):

| clip | combination | feat_floor | contrast_floor | laplace_floor | motion_share | local_share |
|---|---|---|---|---|---|---|
| shipped `flat` pan-and-zoom (2026-09-23) | alpha | 0.170 | 0.884 | 0.471 | 0.392 | 0.498 |
| shipped `model` z25 (2026-09-23) | alpha | 0.127 | 0.834 | 0.469 | 0.304 | 0.590 |
| tool `--anchors` (MLS, 3 pairs) | alpha | 0.284 | 0.873 | 0.603 | 0.600 | 0.635 |
| anchors + partition, luma order | switch | 0.431 | 0.942 | 0.840 | 0.607 | 0.725 |
| anchors + partition, anchor-distance order | switch | 0.586 | 1.001 | 0.868 | 0.641 | 0.711 |
| anchors + partition, edge order | switch | 0.206 | 0.982 | 0.901 | 0.621 | 0.715 |

What the contact sheet shows (my eye; the owner's verdict decides): the shipped clips show two suns at
mid-frame; the anchored clip shows one sun that travels from A's position to B's with the horizon
aligned, and its mid frame is a blend of two ALIGNED skylines rather than a double exposure; the three
partition variants show one picture at every frame and read as a wipe in blotches (luma), an iris
around the sun (distance) and blotches again (edge). Two defects in the anchored clip: the moved
frame's edge shows at the left (the anchors path has no coverage guard; backlog T16, the same
mechanism as the class B frame border T13) and the sun's reflection doubles. The
pair has few SIFT features (75 / 154 at 640 px), so its `feat_floor` is noisy; the direction of every
number is the expected one.

What it says: the double exposure the owner has named six times is a symptom of MISALIGNED content
under a crossfade, and three theme-level anchors remove it at the sun on this pair without any new
mixing operator. The morphing literature says the same in one sentence (Wolberg 1998, §2–3: "Only
after this alignment is maintained does a cross-dissolve … become meaningful"; Track A), and the
hand-drawn feature lines of the 1991 film morphs are the same mechanism (Beier and Neely 1992).
Automatic theme anchors (Track B) are the cheapest route to the same on the other five mismatches; a structured combination (Track A) is the route for the regions that no anchor
aligns.

## 7. Proposed rank (the owner confirms; nothing below is started)

1. **The goal paragraph and a reference**: the owner answers §4 (a yes/no with corrections, one
   reference clip or one sentence per pair). Half an hour of the owner's time; it decides whether the
   metrics of §5 measure the right thing.
2. **Goal metrics into the basket** (Standard): `laplace_floor`, `feat_floor`, `dissolve_fit` and
   `contrast_floor` in `assess()`, two harness checks
   with mutations, the numbers on the sheet and the page beside every clip; the review page gains the
   three per-property boxes. `[revert: commit]`; frames byte-identical.
3. **Theme anchors on all six mismatches, hand-placed first** (a research page, one afternoon): sun,
   horizon, faces, skyline, tree; through the existing `--anchors` path; the owner grades with the
   new boxes. If the anchored clips are graded "one picture, content transforms" on most pairs,
   automate the anchors with Track B's recipe 1 (Mask2Former-tiny panoptic labels + DINOv2-S mutual
   nearest neighbours inside label-matched masks + YuNet face landmarks + a brightest-blob sun
   detector; about 280 MB, Apache-2.0 / MIT; CPU seconds per pair unmeasured) behind warmup +
   manifest. Fix the MLS path's frame edge (the T13 twin) in the same slice.
4. **The combination where nothing aligns** (Design, then a probe): Track A found one published
   method that matches the goal paragraph word for word, Regenerative Morphing (Shechtman, Rav-Acha,
   Irani, Seitz, CVPR 2010): every in-between frame is built only from patches of the two photos, a
   disjoint-coherence term takes each patch from A or from B and never averages, and the authors
   describe the mid frames as "local structures evolve into similar near-by structures, with minimal
   ghosting" on a cloud-to-face and a lion-to-flowers pair. No open-source implementation exists; the
   method is patented (US 8,542,908, active to 2030; personal use) and its PatchMatch search too;
   a numpy port is a large slice with an estimated 2–40 min per 512-px clip. Image Melding (Darabi
   2012) extends it but its code is non-commercial and Windows-only. The cheapest member of this
   family is the per-pixel switch-time reveal (the luma probe's shape): seconds, but nothing moves
   inside a region, and my three partition renders (§6) read as blotchy wipes. Design pass before
   any build; the owner's answer to question 3 decides whether this item is needed at all.
5. **Parked**: the cameras (`--camera` stays an option), the generative tier, TR7 speed.

## 8. Questions for the owner (five)

1. Is the goal paragraph of §1 right? Which sentence is wrong?
2. Is there a transition anywhere (film, music video, app demo) that you would point to and say
   "like that"? A link or a title is enough.
3. On mismatch_4, does the anchored clip (`benchmarks/runs/2026-09-26/probe_mismatch_4/anchors_alpha/transition.mp4`)
   count as "one picture, content transforms" at mid-frame, or is it still a crossfade to your eye?
   (The sun travels; the rest is an aligned blend.)
4. Should the next review page ask three yes/no questions per clip (one picture or two · content
   transforms or the frame moves · anything invented) in addition to the pick?
5. Is a set of automatic theme anchors (weights about 280 MB, offline behind warmup, CPU) acceptable
   as the first build once the hand-placed anchors are graded, or do you want the hand-placed page
   only?
