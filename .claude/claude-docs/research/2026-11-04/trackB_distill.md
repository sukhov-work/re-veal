<!-- Provenance: written by an Opus 5.5 subagent (Track B, the distillation of the sessions since 2026-10-21 into UI requirements) of the Claude Code session of 2026-11-04 (the studio design; DECISIONS 2026-11-04 second line); copied verbatim from benchmarks/runs/2026-11-04/studio/agents/trackB_distill.md (sha256 f980ab9c1864e987) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). The operator's loop per session, the knobs turned with his words, twelve operator failure patterns, his words on the UI, the requirements V1–V11, T1–T7, R1–R5, the quantities to automate. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

---
reader: the UI design session of 2026-11-04 (main thread) and the next session's builder; cold
shape: report
---
## Findings: Track B (distillation)

Summary. The operator's loop ran the same nine steps in every session since 2026-10-21. These steps came out the same each time: intake, registration, probe, plan, draft, full render, skeptic pass, page, his grades. Four steps were done by hand every round and are what a UI must take over or show:
- reading boxes and windows on a still;
- choosing the registration anchor;
- writing the plan JSON;
- turning knobs between rounds.

Two steps stay with the agent session: the skeptic pass and the planner or director track. The request-file pattern (ui_design.md §9 Q2) was answered by the owner on 2026-10-21 and was never built. The owner's own words name about 30 knobs across five pieces (table B). Eight quantities were computed by hand in almost every round (table F). The Strix Halo box ran no job in the loop era; its last jobs were the FLUX.3 keyframes of 2026-10-17/18.

Sources are cited as file plus section or line. "DECISIONS:n" is a line of `.claude/claude-docs/DECISIONS.md` as read on 2026-11-04. Paths without a folder are under `.claude/claude-docs/`.

Glossary for a cold reader:
- **Plan**: a hand-written JSON of holds, transitions and effects that `scripts/research/loop_seq.py render` executes. The director's plans are executed by `director_render.py`.
- **RIFE**: the offline frame-interpolation model that draws in-between frames.
- **Skeptic pass**: an Opus 5.5 subagent that crops every candidate at full size before the owner sees a page. Its verdicts are READY, READY WITH A NOTE, NOT READY.
- **Director track**: a subagent that proposes one alternative plan per sequence.
- **Readings**: a subagent that reads boxes and anchors from gridded crops, with ±px.
- **Lock** (`--lock-window`): the registration translation that keeps listed windows still.
- **Step series**: the mean absolute difference between consecutive decoded frames.
- **Seam step**: the step from the last frame to the first.

### A. The operator's loop (table)

Legend: S = done by a script, H = done by hand (main thread), A = done by a subagent. Times are cited, or marked UNVERIFIED.

| Session | Intake | Registration | Probe | Plan | Draft → full render | Skeptic pass | Page | His grades → next round |
|---|---|---|---|---|---|---|---|---|
| Duck loop 2026-10-20/21 (`research/2026-10-20/loop_report.md`) | H: two stills; the default morph fell to class B on 12 inliers (T53) | S: `transitions.py --canvas common` | H: c1–c5 variants and legs under `c1..c5`, `leg2_*` | H: 7, then 15, then 29 hand anchors read by eye from 1.4–3× crops (±8–15 px); `--anchor-falloff` 0.25 | S: `transitions.py pair` + `work/build_loop*.py`; 11.0 + 8.5 s per loop | none (the track's own eye, UNVERIFIED) | S+H: `loop/index.html` | 4 grades in 2 days (glide2→glide5); every change was speed ×1.5, more anchors, or a breath. The track ran as an A subagent; its Write was refused and the main thread copied its report |
| Director rounds 11–13, 2026-10-18 to 10-21 (`TRANSITIONS.md §13.19–13.23`) | S: layer source, mattes, `--resolve-only` (7.8 s) | S: the renderer's camera | H: compose probes (§13.23) | A: planner subagent, prompt sha256 recorded (6406cc1b…, eb8589e7…, e2c7615e…, 1ddc5725…), brief = his grades or blind | S: 480 px draft, then full; each render twice for md5. H: operator knobs set after the first render (§13.19 "Operator knobs") | A: two passes per round (`skeptic_r11b`, `r12`, `r12b`, `r13`, `r13b`) | S: `director_page.py`, picks JSON | His picks JSON → the next brief. Rounds: r11 02:00–02:10 EEST; r12 00:40–01:05 EEST; r13 01:00–03:20 EEST (§13.19/21/23 headings). Grades at 19:28 and 21:27 UTC on 2026-10-20 (§13.20, §13.22). The workbench was built by A in round 13 (01:53–02:01 acceptance, `ui1_build.md`) |
| Halloween 2026-10-30 (10 sequences, 4 rounds; sheet `2026-10-30-halloween.md`) | H: thumbnails and a Lab diff per sequence (`loops.md §1`, about 10 min) | S: `prep` (SIFT+MAGSAC, chain, ECC, `--cut`). H: inlier check, montage, a cut declared for the thug's 2 stills | H: morph vs RIFE strips on 19 pairs (§13.24) | H: 24 plans. A: director tracks A and B (one alternative each, 640 px drafts, 5–11 min). A: readings (boxes, wand anchors, about 12 min) | S: full size, RIFE about 1.3 s per in-between at 1900 px (`loops.md §7`) | A: 4 passes (`skeptic.md`…`skeptic4.md`), 5–6 min, 20–60 tool calls each | S: `loop_seq.py page`; md5s 31a2d93b → 3c69dc16 → 6f1ec2c7 → d84820d7 | Grades round 2, 3, 4 the same day → round 4 accepted. Budget per round: prep and probes 30 min, renders 10, skeptic 6, page 2, record 20; a fix round about 40 min (`loops.md §7`). Wall clock per round: UNVERIFIED |
| Seasons 2026-11-01 (3 stills, 4 rounds; sheet `2026-11-01-seasons.md`) | H: labels from him, EXIF read | S: `prep` 1920, then 3600 px (k1 242, k2 via k1 146 inliers). H: phase correlation on 5 static patches (±0.5 px) | H: DIS morph, dissolve and RIFE at 960 px, t 0.25/0.5/0.75 | H: c1–c8, then s1–s10. A: director track (barcode c8). A: readings (7 object boxes, ±4 px). S: `gen_seasons_bands.py` writes s7–s10 | S: 640 px drafts, then full; render 7–594 s per candidate (sheet "render s") | A: 6 passes | S: page md5 73aeeec7 → 19da6b2b → c77a929e | Round 1 was rejected from the run folder before the page existed. s4 "ok" → s5/s6 → s6 "perfect" → s7–s10 ungraded. Wall clock: UNVERIFIED |
| Angel 2026-11-04 (2 stills, 1 round; sheet `2026-11-04-angel.md`) | H: what moves; depth at named points; Lab >14 covers 19.6 % | S: `prep` 6 s. H: 3 fits compared on 9 named windows by template match; the lock windows drawn and checked by eye; 2 rejected fits parked | H: RIFE, DIS and dissolve at 960 px | H: a1–a3. A: director track (a4 tempo, a5 depth push; it read the exposure step) | S: 960 px drafts, then full; a2 about 60 s (NEXT_SESSION §1) | A: 2 passes; pass 1 forced a re-registration and four fixes (round 1a → 1b) | S: md5 72dadc4f | Ungraded |

### B. Knobs turned, with his words (table)

| Piece | His words (verbatim, short) | Knob | Value |
|---|---|---|---|
| Duck | "make it 1.5 times faster" (×2) | frames per leg | 30 → 20 → 13 (`loop_report.md` glide3/4) |
| Duck | "iris movements more natural … top of the head" | hand anchors (iris, eye corners, hair) | +8 anchors (glide2) |
| Duck | "more anchors around headphones and metal bar" | anchors | 29 in all (glide4; reverted) |
| Duck | "make duck and white foreground (monitor ) breath a bit" | per-object breath | lid 1.5 %, duck 4 % in a 120 px disc (glide5) |
| Café r11 | "should never clip to underlaying next/last frame in advance" | `tree_goes_away.hole_reveal`; later the guard `reveal_ahead` | true → off; guard on (§13.20–13.21) |
| Café r11 | "weird pauses and in very linear way" | `motion: continuous`, `edge`, `overlap`, `times: "arc"`, `arc_floor` | 0.35 / 0.1 / arc / 0.5, then 0.05 (§13.21, §13.23) |
| Sunset r12 | "rapidly shrink at the very small core" | `rate` fast_in, `profile` geometric, `end_shape` b_blob, `blob_frac` | 0.85 (§13.21) |
| Sunset r12–13 | "still a bit of limb around sun" | `sun_recedes.window` | [0.15, 0.6] (§13.23) |
| Sun-to-sun r12 | "too distinct orange halo" | `sky.shape` radial_out, `sky.radial_width`, `sky.out_border` | 0.35 / 0.6, false (§13.23) |
| mismatch_1 r12 | "should have been a rapid zoom out" | container rect at scale 0.5 (the camera has no rate field, T58) | plan rewrite (§13.23) |
| Halloween, all | "not like 1-2 (small pause) 2-3" | `through` chain, `weights`, `soft`, `knot_margin` | soft 0–0.5, knot_margin 0.04 (§13.25, `loops.md §3`) |
| evgen-thug | "slower in the begiining with big speed ramp up for last 3 frames" | chain ease accel, `weights` last legs | 0.45, 0.35 (§13.25) |
| wand / group1 / group-teleport | "20% faster" / "30% faster" / "whole scene 20% faster" | holds and `n` | 28 → 22 frames; 48 → 34; 56 → 46 (sheet rounds 3–4) |
| talk / group1 | "no breathing effect" / "no breathing" | `breath` | removed |
| group-teleport | "do not beam … super swift fluid lateral move"; then "just dissolbe morph person into background" | method teleport → slide fly → slide `mode: dissolve`; windows [0, 0.55] / [0.45, 1]; GrabCut boxes with `exclude` | (§13.25–13.26) |
| zeke-back | "more immediat snap … with slight motion blur" | method `snap`, `blur_frac` | 3 frames, 2.2 % (§13.26) |
| zeke-bite | "a bit more fluide ( with same speed )" | `n` in-betweens, ease | 4, then 3 each way, sine (sheet round 3) |
| Seasons r1 | "simple 2d pattern transtions … junky"; "sliding diagonal wipes … 3 pictures" | method slices → `sheets` | (§13.27) |
| Seasons r2 | "make wipes purele lateral … 50% slower … tiny bit 3d depth" | `motion: lateral`, `n`, `edge_depth` | lateral; 90 → 135; 60 / 120 px (sheet round 3) |
| Seasons r2 | "horribly misaligned" (the carried pictures) | `carry` | 0 only |
| Seasons r3 | "around 10 consequtive bands … 6 -10 lateral wipes … more blurry and transparent" | `--bands`, `--stagger`, `--dur`, `--feather`, `layer`, `layer_y`, `shadow`, seed | 10–16 bands, stagger 9–11, dur 100–150, feather 80–120 (sheet round 4) |
| Angel (his order) | "ffluid , brathing , nice depth" | `breath.z`, `parallax.amp`, `glow.gain`, `breath.depth_k`, holds and `n`, `margin`, `local` box ease, `--lock-window` | 0.018, 0.014, 0.15, 1.0, 14/12 + 12/12 or 8/6 + 30/40, 0.04, snap (sheet round 1) |

What "full control" must reach first: timing (holds, `n`, % faster), the ease and chain profile, the method per leg, the breath on/off and its centre, mattes and boxes, the registration anchor, and the sheets' band parameters.

### C. Operator failure patterns

| # | Pattern | Session | Cost |
|---|---|---|---|
| 1 | Measurement windows named for an object sat 150 px off it; they reported 0.4 px where the ring's top was 7.9 px off | angel (sheet, Registration) | skeptic pass 1 caught it; re-registration, four fixes, five re-renders (round 1a parked) |
| 2 | A standing-watch md5 was recorded before a later code change in the same session. The graded s6 (5ec0fe31) cannot be reproduced by any later code; the s7 healthy value is stale | seasons (NEXT_SESSION §1) | the graded file has no reproducible plan + code pair |
| 3 | Fixes applied after a skeptic pass and shown unjudged | Halloween rounds 2–4 (2 + 4 + 4 fixes, plus 3 more teleport renders); seasons s5/s6 reach fix, s9/s10 (sheet) | the round-3b slide and rise he graded "very dirty", "ugly"; the teleport rim remained |
| 4 | A fix recorded that changed nothing ("f451d90d → f451d90d") | Halloween (DECISIONS:135) | three renders and a matte rule to find out |
| 5 | Drafts or crops hid a defect. The slices fixes were checked on 640 px only. The 75 % crop hid the slow ends of the ease (61 still frames). No skeptic pass ever played a clip at speed | seasons (sheet pass 3; T69); every session | a defect found a round later; at-speed motion is UNVERIFIED on every page |
| 6 | The owner saw intermediate renders in the run folder before the page or any skeptic pass | seasons round 1 (DECISIONS:150) | 8 candidates rejected as a set; the rule "a draft is said to be a draft in its folder name" was added (NEXT_SESSION, Standing order) |
| 7 | A candidate he did not ask for, or a NOT READY one, stayed on the page as a peer | seasons s1 (DECISIONS:151) | the page was rebuilt with a new intro (md5 73aeeec7) |
| 8 | An operator knob broke a recorded ruling. `hole_reveal=true` was set after the skeptic pass, against the 2026-10-18 rule | director r11 (§13.20) | the tear he named "kills all point of doing transformation" |
| 9 | Plans had no provenance. Loop plans carry `title` and `gag` and no planner block (`angel_a3.json`). Director knobs live outside the plan: `parallax_push` came from the last `info.json` (`ui1_build.md` Constraints) | all loop sessions; director | a knob's origin is recoverable only from sheets |
| 10 | The exposure step was not read before an effect was added (the second still is +3.7 levels, the ring 7 % brighter already) | angel (`research/2026-11-04/director.md`) | the glow was designed before the director track found the step |
| 11 | Pair-specific knobs piled up: 51 hand-set knobs over 15 clips; a fix for one grader broke the other | director r8–r11 (`retrospective.md §3a, §3h`) | 18 pages, one acceptance |
| 12 | Recording traps: an unquoted heredoc blanked backticks; `prep` canvas flips at scale about 1.00; `page` lists every directory | Halloween (DECISIONS:135); angel (`loops.md §8`; NEXT_SESSION §7) | hand repairs; a wrong comparison; drafts on the page |

### D. His words on the UI (verbatim) and the answered questions

- 2026-10-20 (`DECISIONS_ARCHIVE.md:252`): "lay a groundwork ( plan …) to move this whole tool in more user-friendly (only me for now ) direction ( I just want some UI I can start playing with , you can still keep it highly technical and bare in terms of polishing , this is simply to speed up our iterations, UI with all tweaks and all the tools for director , loading progress , maybe ability to annotate part of pics, play wiwh layering and other sub-tools , etc ( both match and mismatch pairs, analysis on how much mismatch , suggestions for given cases , think deeply of how you can expose everything useful in consistent and efficient manner ( also should work on sequences , and mix photo to video and vice versa ."
- 2026-10-21 (`DECISIONS_ARCHIVE.md:253`): "for item 2: UI and where it lives, ok with your suggeestion, for items 3, 4 - ok as well." These are the handover's item numbers. The DECISIONS line maps them to §9 Q1–Q2, to T50 (RIFE allowed) and to a held-out pair.
- 2026-10-30 (DECISIONS:149): "also for the next session make sure to add task to make this functiaonality a tunable part of our main app and UI ( separate additional flow )".
- 2026-11-04 (this session's brief; the DECISIONS line is not yet appended): "enrich UI tool with ability (maybe additional mode, or just more tweaks) to handle these loops and general sequences, so i have full control over everything from UI … expose all the tool, show visually all the processes (and let me tune them) that you do under the hood each time i ask you to do any transition and loop, regardless on type of match / mismatch, should be able to flexibly adapt and handle, with external and internal models, optional halo box support for the flows etc, also original reveal features."
- Standing order (NEXT_SESSION, Standing order): "mindboggling transitions that i would be able flexibly tune and control per scene".

The six questions of `ui_design.md §9`:

| Q | Question | State (T52) |
|---|---|---|
| Q1 | Where the UI lives | ANSWERED 2026-10-21: `scripts/research/director_ui.py` |
| Q2 | How it reaches the planner | ANSWERED 2026-10-21: a request file the session picks up. NOT BUILT: `ui1_build.md` lists no `requests` endpoint; UI3 is open |
| Q3 | Port 8379 | adopted by the build; no answer recorded |
| Q4 | Copy new photos into `fixtures/` and run the layer source | OPEN |
| Q5 | May he grade 480 px drafts | OPEN |
| Q6 | Which video option first | OPEN (V1 recommended) |

### E. Requirements (grouped 1–6, each with a source)

**(1) Visible**

| ID | Requirement | Source |
|---|---|---|
| V1 | The registration table per still: method, inliers / matches, residual px, canvas, crop, scale | sheets' Registration sections |
| V2 | Named measurement windows drawn on the still, with each window's dx, dy under every candidate fit, side by side | angel sheet; failure C1 |
| V3 | A montage of the registered stills, plus a flicker or overlay toggle between them | `loops.md §2.1` |
| V4 | The probe strips: morph, RIFE and dissolve at t 0.25 / 0.5 / 0.75 per adjacent pair | `loops.md §2.2`; seasons and angel probe sections |
| V5 | The change matte, GrabCut mattes, `local` boxes and glow boxes as overlays on the still | Halloween §13.25; angel a3 glow box (`skeptic1.md`) |
| V6 | The depth map, with the depth read at a clicked point | angel intake; seasons `edge_depth`, `layer` |
| V7 | A scrubber with each frame's source tag: hold, generated by RIFE (with its t), blend, snap | `loops.md §2.5`; page notes |
| V8 | The step series under the scrubber, with stalls and jumps marked, and the seam step | `loops.md §6` |
| V9 | The skeptic's faults as frame markers, with his crops beside them | `ui_design.md §3`; `skeptic.md` defect tables (frame, region, defect, rule) |
| V10 | The plan timeline: holds, legs, chain knots, effect windows, the band schedule | `ui_design.md §3`; seasons s7–s10 |
| V11 | Rejected and parked registrations and rounds, listed beside the live ones | angel `in/*_rejected/`; `round<N>/` folders |

**(2) Tunable**

| ID | Requirement | Source |
|---|---|---|
| T1 | Every plan key of `plans/loops/SCHEMA.md`, with range and default, so a "% faster" applies to the frame counts | table B; `loops.md §3` |
| T2 | Registration controls: reference still (`--ref`), `--cut`, `--bg-depth` and `--min-inliers`, `--lock-window` drawn as boxes | angel sheet; `loops.md §2.1` |
| T3 | Boxes, points and exclusion boxes drawn on a still, stored in plan coordinates (mattes, `local`, glow, object plates, anchors) | ui_design phase 3; Halloween readings; duck anchors |
| T4 | Method per leg (rife, dissolve, morph, snap, cut, slide, sheets), the ease, `margin`, the chain's `weights` and `soft` | sheet round tables; §13.25–13.26 |
| T5 | Effects with on/off and amount: breath (z, centre, `depth_k`), parallax, glow | angel round 1; T67 |
| T6 | A seeded generator: bands, stagger, dur, feather, layers | `gen_seasons_bands.py` |
| T7 | The director's knobs (`--set`) and windows dragged on the timeline, as UI1 already does | `ui1_build.md` |

**(3) Recorded**

| ID | Requirement | Source |
|---|---|---|
| R1 | Every render writes plan sha256, mp4 and gif md5, draft or full, and a script version. Today `loop_seq.py` stamps `plan_sha256` and the md5s (lines 1513–1514) and no script md5; `director_render.py` stamps `renderer_md5` | code; failure C2 |
| R2 | Saved plans carry a provenance block (author: owner, planner or operator; the parent plan; the knobs changed; his words). Director plans already record the prompt sha256 | failure C9; ui_design phase 2 |
| R3 | His grades verbatim per candidate, saved before the next render, with the page md5 | `loops.md §9`; NEXT_SESSION §0 |
| R4 | Each candidate's state: skeptic-judged, judged with a note, or unjudged after a fix. Drafts are labelled as drafts | failures C3, C6; Standing order |
| R5 | Source sha256s, never-modified originals, and a restart that rebuilds state from the files | angel sheet; T60 |

**(4) Kept by the agent session.** The planner, the skeptic pass, director tracks and readings stay in the agent session (`loops.md §7`; NEXT_SESSION, per-model routing). The UI writes `requests/<kind>_<stamp>.json` (kind = plan, skeptic, reading, director, keyframe) carrying his notes, boxes and grades. The session writes the answer into the job folder. The UI shows "waiting" until the answer file appears (`ui_design.md §9 Q2`, answered and not built). A page is offered only after a skeptic answer file exists for the shown md5s (failure C6).

**(5) Models and the Strix Halo box.** No tracked document since 2026-10-21 records a box job.

| Model | Where it runs | Used for | Source |
|---|---|---|---|
| RIFE v4.26 | local, offline behind `RIFE_MANIFEST.json` | in-betweens in every loop | §13.23; `fl4_rife.md` |
| YuNet face model | local | faces per frame | §13.19 |
| Depth model (`transitions.model_disparity`) | local | parallax, `edge_depth`, layers, `--bg-depth` | §13.27–13.28 |
| GrabCut, Poisson clone | local OpenCV (not models) | mattes, object plates | §13.25, §13.27 |
| SAM 3, OneFormer, ViTMatte | local layer source, scratch environment | director layers; SAM for the seasons layers named "not run" | DECISIONS:80–87, :153 |
| FLUX.3 klein distilled bf16 | the box, via `scripts/research/strix_keyframe.sh MODEL=flux3`, 180–392 s per image | director keyframes and plates, last run 2026-10-17/18; r13 concept c2 asked for one and was not rendered | DECISIONS:116, :121; tooling §5; `keyframes_r10.md` |

The box rules: pre-flight free memory, `~/halo-hold`, one job at a time, no host change (DECISIONS:67, :74, :102). Its memory leaf `mem:project/strix-halo-box` is machine-local, not tracked. A UI job for the box needs a job kind for keyframes or plates with a queue, a pre-flight result and the box's logs.

**(6) Reveal's original features to keep.** These are `reveal.py align` (metrics, aligned stills, `--mode loose`, `--video --style wipe|fade --aspect`), the slider page on 127.0.0.1:8378, and the exports. The workbench already wraps `align` as the relation reader (`ui_design.md §2`). UI4 plans match pairs with Reveal's aligned stills and change mask as overlays (`EXPLORATION_PLAN.md` UI4). Neither tool changes without his word (T68; `AGENTS.md` invariant 7).

### F. Quantities to automate

| Quantity | Computed by hand in | Source |
|---|---|---|
| Residual dx, dy on named windows under each fit (template match, ±30 px, sub-pixel) | angel; seasons (phase correlation on 5 patches) | sheets' Registration sections |
| Step series: mean, max with frame, stall runs (<0.3), jumps (>3× neighbours), still-frame count (≤0.05) | every round | `loops.md §6`; seasons "still frames" |
| Seam step; the corner-box pixel count of the last frame against frame 0 | every loop; seasons r3–r4 | seasons sheet |
| Object stability per frame (the ring-top window against frame 0) | angel | angel sheet |
| Double-exposure share per generated frame; generated share | every RIFE loop | `loops.md §6` |
| Faces per frame against the keyframes' count | Halloween, angel | `loops.md §6`, §8 |
| Lab-difference share above 14 and 30; the diff view | intake | angel sheet; `loops.md §1` |
| Depth at named points | angel, seasons | angel intake |
| Exposure and focus difference between stills (mean levels, clipped pixels, Laplacian variance per region) | angel | `director.md`; `skeptic1.md`; T73 |
| Bands moving at once per frame | seasons s7–s10 | `skeptic6.md` |
| Director measures already in `info.json`: `motion_px` pauses and jumps, `b_inside`, `residual_edges`, `halo` | director r12–r13 | tooling §6 |

### Confidence: 80%

The tables rest on the sheets, `TRANSITIONS.md §13.19–13.28`, the DECISIONS lines and the backlog, all read on 2026-11-04. The figure is held down by the timings (per-session wall clocks do not exist) and by the skeptic reports, most of which were read through summaries.

### Gaps

- The DECISIONS lines were read truncated at 1,800–3,500 characters. The skeptic and director reports were read through their READMEs and the sheets; only `skeptic.md` (2026-10-30), `skeptic1.md`/`skeptic2.md` excerpts and `director.md` (2026-11-04) were opened.
- The director sheet `benchmarks/2026-10-17-director.md` was cited through `TRANSITIONS.md §13.19–13.23`, not opened. `2026-10-09-fabra-boxes.md` was not opened (it is before 2026-10-21; the playbook summarises it).
- Per-session wall-clock times for Halloween, seasons and angel: UNVERIFIED (only `loops.md §7` budgets and per-render seconds exist).
- The 2026-11-04 UI order is quoted from the task brief; the leaf `wip-2026-11-04-studio-design` cites a DECISIONS "second line" that did not exist when this was read.
- Q3's status is inferred from the build, not from an answer.
