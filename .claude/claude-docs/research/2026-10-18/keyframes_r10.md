<!-- Provenance: written by an Opus 5.5 subagent (Track K, the FLUX.3 keyframes on the box, 2026-10-17 late night to 2026-10-18) of the Claude Code session of 2026-10-17/18 (the round-10 session; DECISIONS 2026-10-18), copied verbatim from benchmarks/runs/2026-10-17/agents/keyframes_r10.md (sha256 5b306138426507b2) on the owner's standing order of 2026-10-17; folded into `TRANSITIONS.md §13.17`, the tooling list (helpers), DECISIONS 2026-10-18. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

## Findings: keyframes_r10

Ten FLUX.3 image klein runs (distilled, bf16, 16 steps, cfg 1.0, seed 20260926) finished on the Strix Halo box on 2026-10-17 between 21:50 and 22:32 BST, each with `run_rc=0`. Four keyframes pass the owner's conditions by my screen: café k1, k2 and k3, and window pane. k2r fails on one patch: a jacket cuff with no arm in it. The three turn keyframes from the coordinator's follow-up keep A's man but lose the woman in the dark green top, and they show no visible turn. pane2 removes the crowd completely and adds cream-white flowers that I do not find in either photo. r10_m2_k1b is byte-identical to r10_m2_k1 (`cmp` on the box and on the Mac). The box was left clean: no hold file, 0 containers (checked from the Mac at 22:32:28 BST and again at the end).

### Key facts
- Determinism holds on this box tonight: r10_m2_k1 and r10_m2_k1b have the same inputs and the same md5, `b531e765d670976a1ef9d5f959494c08`. The check is `cmp` printing IDENTICAL, run both on the box and on the Mac.
- Timing per keyframe: 180–203 s wall at 608×800 with two references (sampling 173.7–196.6 s), 309 s for pane and 392 s for pane2 at 1024×768 (sampling 297 s and 378 s). The sources are each run's `run_begin`/`run_end` and the line `sampling completed, taking …s`.
- Memory: MemAvailable was 39.1–39.3 GiB before every run. Its minimum was 19.09–20.32 GiB for every run except pane2, which reached 14.44 GiB (a 24.89 GiB drop; GTT used 55.83 → 81.25 GB). The pre-flight line was always `MemAvailable 39 GB, GTT free 71 GB, need 26 GB`. The 10 GiB watchdog never fired: no `watchdog_stop` appears in any log.
- Reference order sets which picture is kept. When B was image 1, B's layout, the two women and the wall were kept: MAD to B outside B's man's box is 6.05 levels for k1 and 4.86 for k2. When the prompt asked for a blended face, the model gave one man's face or the other's, never a blend. k2 ("two thirds of the way", references B then A) came out as B's man in a yellow T-shirt (MAD to B 14.85 levels).
- Two things worked for the two-thirds point. One was a change from the end side: k3 put A's man's face onto k2's body (references k2 then A). The other was one step from the start side: k2r, references k1 then B, which gave a yellow T-shirt and a phone but not B's raised pose. The face change happens in one step either way: between k2r and k3, or between k3 and k2.
- Turn requests do not turn the head. turn1 (a quarter turn) and turn2 (half, three-quarter view), both from the composite, are 6.19 levels apart. turn2p (references turn1 then B) is 4.96 levels from turn1. By eye, none shows a turn beyond the composite's own head pose. Using the previous keyframe as reference did not keep the layout better: it repeated turn1's layout, including the lost woman.
- Sizes: the café keyframes are 608×800 because 608 is the multiple of 16 nearest the 602 px canvas width. 592×784 would need an upscale of both axes; 608×800 needs only a 0.990 horizontal resize. The renderer must apply `cv2.resize(608x800 → 602x800, INTER_AREA)` to the café keyframes and `cv2.resize(1024x768 → 1920x1440)` to pane and pane2 (A's frame, 4:3). The references were resized to the generation size first (café INTER_CUBIC, A of mismatch_3 INTER_AREA) from canvases made by `transitions.load_image_rgb` + `transitions.cover`.

### Relevant artifacts
| path | purpose |
|---|---|
| `benchmarks/runs/2026-10-17/keyframes_r10/keyframes.json` | index: per run the pair, role, generated size, renderer resize, references in order, prompt file and sha256, seed, steps, cfg, run_rc, wall s, sampling s, MemAvailable min, GTT max, screen numbers, my face/hand notes, md5, sha256 |
| `benchmarks/runs/2026-10-17/keyframes_r10/sheet.jpg` | review sheet in three rows: café A, k1, k2r, k3, k2, B; the composite, turn1, turn2, turn2p, k1; window A, pane, pane2, B with the view crop boxed. The sheet's head says these are helper candidates, not transition candidates |
| `benchmarks/runs/2026-10-17/keyframes_r10/out/` | 10 PNGs, 10 manifests, 10 run logs, 10 memory logs, queue logs `r10_queue{1..4}.log` |
| `benchmarks/runs/2026-10-17/keyframes_r10/prompts/` | 8 prompt files, mirrored on the box as `~/keyframes/prompts/r10_*.txt` (same sha256, checked by `sha256sum` on the box) |
| `benchmarks/runs/2026-10-17/keyframes_r10/in/` | canvases, references at generation size, the B view crop (`r10_m3F_view.png` = canvas[230:620, 760:1920], below the ceiling rods), the main thread's composite |
| `benchmarks/runs/2026-10-17/keyframes_r10/screen/` | `keyframe_screen.py` JSON per run; `regions.json` (region and pairwise MAD) |
| `benchmarks/runs/2026-10-17/keyframes_r10/scripts/` | `r10_queue{1..4}.sh` (hold file removed in the EXIT trap), `post.py`, `region.py`, `sheet.py` |

### Runs
| name | size | refs (image 1; image 2) | prompt sha256 | wall s | sampling s | MemAvailable min GiB | GTT max GB | run_rc | md5 |
|---|---|---|---|---|---|---|---|---|---|
| r10_m2_k1 | 608×800 | B; A | d7c6ef8fb7bc… | 183 | 176.15 | 20.12 | 75.55 | 0 | b531e765d670976a1ef9d5f959494c08 |
| r10_m2_k2 | 608×800 | B; A | 7c155f83def0… | 185 | 176.90 | 20.19 | 75.55 | 0 | dd7b20e13bbff46480cb6da2279429bf |
| r10_m3_pane | 1024×768 | A; B view crop | d0b75267aed7… | 309 | 296.95 | 19.09 | 76.76 | 0 | 1d9fb964be43f540f63c60947f31ea11 |
| r10_m2_k1b | 608×800 | B; A | d7c6ef8fb7bc… | 183 | 176.80 | 20.17 | 75.55 | 0 | b531e765d670976a1ef9d5f959494c08 |
| r10_m2_k2r | 608×800 | k1; B | 8a707accf444… | 181 | 174.03 | 20.32 | 75.52 | 0 | 617a0d0254a63acf722a5dade7b4fb10 |
| r10_m2_k3 | 608×800 | k2; A | a3305ec3727b… | 203 | 196.64 | 20.20 | 75.52 | 0 | 769401a774253231bdaac2defdb2d060 |
| r10_m2_turn1 | 608×800 | composite; B | a004f6de289b… | 184 | 176.79 | 20.11 | 75.55 | 0 | b225fd7eae3ebe57cdb4dc375de0541f |
| r10_m2_turn2 | 608×800 | composite; B | 06791049a420… | 184 | 177.07 | 20.10 | 75.55 | 0 | ea5990711fdba095c5443cc494767da9 |
| r10_m2_turn2p | 608×800 | turn1; B | 755b7f28f69d… | 180 | 173.71 | 20.28 | 75.52 | 0 | 8329a83c9dac6c8534348cd772440e99 |
| r10_m3_pane2 | 1024×768 | pane; B view crop | 72db3499ad9c… | 392 | 378.11 | 14.44 | 81.25 | 0 | e3e06b56ece48aa37fa5dc29a92b06ef |

The full sha256 of each prompt is in `keyframes.json`.

### Screening
Faces and hands were counted by eye on the full-size PNG and on 2× crops of the lower half. MAD is in 8-bit levels, from the keyframe to the canvas resized to the keyframe's size. Laplace is the variance of the Laplacian on the 480 px proxy (café A 131.4, B 897.5; window A 2789.0, B 2887.5).

| keyframe | faces / hands | verdict by the owner's conditions | MAD to A / B | laplace |
|---|---|---|---|---|
| k1 | 3 faces (A's man, the woman in green, the woman in black) / 5 hands | PASS. A's man with his face, jacket and clasped hands in B's man's place; B's man and phone gone; A's sleeve label kept. The woman in green's lower face, hidden by B's hand in B, is drawn complete. A turn of about a third is not clearly visible: his body faces the camera much as in A | 77.66 / 34.70 | 1020.0 |
| k2 | 3 / 5 | PASS on the conditions; not the two-thirds keyframe. It is B's photo with the T-shirt turned yellow, and A's face is absent | 77.26 / 14.85 | 831.9 |
| k2r | 3 / 5 | FAIL on "realistic" at one patch: a jacket cuff with A's black label floats at the bottom edge (about x 255–330, y 740–800) with no arm in it. Otherwise A's man in a yellow T-shirt holding a phone in clasped hands | 74.72 / 34.74 | 1297.1 |
| k3 | 3 / man 2 (B's hands on the phone) plus the women's | PASS. A's man's face, goatee and hair on B's body and pose, in a yellow T-shirt; the face skin is lighter than A's, which I read as the in-between. No third person | 74.26 / 20.83 | 973.3 |
| turn1 | 2 (A's man, the woman in black) / 4 | FAIL on "consistent": the woman in the dark green top, present in B, the composite and k1, is removed. A's identity is kept. The man is drawn larger and about 70 px to the right of the composite. No turn visible. The other man's half face, T-shirt and phone hand are removed as asked | 73.00 / 41.08 | 888.7 |
| turn2 | 2 / 4 | FAIL, same as turn1 (6.19 levels from turn1); the three-quarter view did not appear | 73.29 / 39.74 | 878.3 |
| turn2p | 2 / 4 | FAIL, same as turn1 (4.96 levels from turn1) | 72.31 / 42.23 | 1095.3 |
| pane | the crowd of A kept person for person in place (no added or lost person in two half-frame crops) | PASS. The upper half is B's view (pines, the building, the glass panel); the wheels, air conditioner, flag, sequins and wall are gone. The fence is kept at full strength, not fading. Two small changes: the yellow-shirt man's V sign is now a closed hand, and sunglasses were added on the seated blonde woman | 52.56 / 66.29 (to the view crop 60.59); rows below 55 % to A 30.05 | 2011.8 |
| pane2 | 0 / 0 | PASS on faces and hands. The brief's "two or three figures far back" is not met: there are none. The upper half is kept (12.99 levels from pane above 45 % of rows). A piece of A's chain-link fence stays at the left middle, a low dark fence at the right, and A's painted panel at the right edge. A lawn and a bush with cream-white flowers fill the lower half; I do not see those flowers in either photo (B's bushes show red flowers), so they may be a new object. The owner's eye decides | 67.57 / 68.26 (to the view crop 55.81) | 3303.8 |

Region MAD to B outside B's man's box, which covers 52.2 % of the frame: k1 6.05, k2 4.86, k2r 9.61, k3 (not computed). Source: `screen/regions.json`.

### Constraints discovered
- The wrapper `fx_run.sh` and the recipe pass at most two references (`REFS3` takes A and B only). A third reference, for example both men's crops plus the café, needs a recipe change that I did not make.
- Prompts that ask for a fraction of a change ("a third", "two thirds", "a quarter turn", "half way") do not produce that fraction. Each run made one discrete edit: a person swapped, a shirt recoloured, a face swapped, or a pose change applied in full or not at all.
- The model removed a person the prompt said to keep when the same prompt asked it to fill a nearby region with "the café of image 2". This happened in turn1, turn2 and turn2p, where the fill sentence named the woman in green as something to show. [INFERRED cause; one prompt form, three runs.]
- pane2 used 4.9 GiB more MemAvailable than pane at the same size and the same second reference. The cause was not measured. On a day with about 35 GiB available, the minimum would be about 10 GiB, which is the watchdog's line [INFERRED].

### Confidence: 75%
The run facts (run_rc, md5, cmp, wall time, memory) come from logs and hashes. The face, hand and defect counts are my eye on single images, and I may have missed a small hand in a crowd of 24 in pane. The owner grades quality.

### Gaps
- Turn keyframes: no run produced a visible quarter or three-quarter turn. I did not try a turn with A as image 1, a prompt naming the head angle in degrees, or more steps.
- k2 was retried once (k2r), and k3 ran under the brief's "k3 if k2 is not yet two thirds". No further retries of turn1, turn2 or pane2 were made.
- The two-thirds point exists only as k3 (face from A, everything else B). No keyframe shows a face blended between the two men.
- The renderer-side test of these keyframes (flow consistency, double exposure) was not run by this track. The coordinator's numbers (consistency 0.06 and 0.04) refer to k1 and pane.
- pane2's extra 4.9 GiB of memory is unexplained. `journalctl -k` was not read.
- No tool failures. One MAD value (k3 against B outside B's man's box) is missing because `region.py` ran before k3 existed.
- Nothing was written to DECISIONS.md, the memory leaf or the handover. Nothing was committed.
