<!-- provenance: copied verbatim on 2026-11-05 from benchmarks/runs/2026-11-05/studio/agents/b_pair_research.md (gitignored), the pair transition flow as studio stages and the continued items of phase B (Reveal's verdict, --layers-dir and --mattes-dir, the request pickup line for T74, sequences up to 10 stills, the repaint leg's spec) by an Opus 5.5 research subagent (max effort), read-only on the repo; it ran transitions.py pair once on mismatch_3 at 480 px; a research artifact whose claims carry the author's own confidence and gaps; the main thread re-verified the mismatch_3 anchors by rendering both argvs (DECISIONS 2026-11-05 eighth and ninth lines) and nothing else -->

<!-- reader: the main thread that builds phase B of the studio, then a cold session through the research copy. shape: report. Written by an Opus 5.5 research subagent of the 2026-11-05 session, read-only on the repo except this file. -->

## Findings: pair-and-continued

The pair transition flow fits the studio as seven registry entries: import, relation, render, skeptic, page, grades, and Reveal's verdict as an optional branch. The render stage takes the 12 knobs of `transitions.py pair --help` plus the studio's own `name` and `draft`. The build also touches six modules that serve the loop flow only today: `config.py`, `runner/argv.py`, `runner/process.py`, `jobs/candidates.py`, `media/pictures.py` and `server/handler.py`. Reveal's verdict goes in an optional branch under import, shared with the director flow and off by default. It costs 2.2–16 s against the relation's 1.89 s and sets no pair knob. The request pickup at boot (backlog row T74) is one hook line, tested on four cases in a scratch copy. It would list 7 stale acceptance-test requests at every boot until they are answered. The repaint leg is about 80–120 lines in `loop_seq.py` and its schema, and I recommend the handover.

Asked of the main thread: choose the page; the studio writing `index.html` is recommended. Answer the 7 stale requests before the hook line goes in. Decide whether phase B builds the "suggest" step of `STUDIO.md §5`, which proposes a flow from the relation; that settles where Reveal's verdict lives.

### Key facts

**Part 1. The pair transition flow as studio stages.** The stages in the order the strip shows them:

| Stage | Kind | What runs | Terminal file | Wall time (source) |
|---|---|---|---|---|
| import | builtin | links A and B under `raw/<pair>/`, each keeping its extension, with a sha256 each | — | — |
| relation | script | `transitions.py pair A B --out <root>/relation.part --max-long 480 --seconds 1` | `report.json` | 1.89 s wall on mismatch_3 (this run, 2026-11-05); 1.6–2.4 s on 2026-10-21 (`research/2026-10-21/ui1_build.md:26–27`) |
| verdict (optional branch under import) | script | `reveal.py align A B --out <root>/verdict.part`, the reshot profile, as `director_ui.py:430–446` ran it | `metrics.json`, absent on a refusal | 2.2–16 s per pair (`benchmarks/2026-09-13-real-pairs.md:115`); mismatch_3 refused in 5.4 s (`:130`) and in 10.3–11.6 s (`ui1_build.md:23–25`) |
| render | script | `transitions.py pair A B --out <root>/<pair>/<name>.part` with the knobs below | `report.json` | morph 1 s at ≤ 1920 px: 4.7–13.4 s (`2026-09-13-real-pairs.md:114`), 1.5–11.7 s (`TRANSITIONS.md:247`); morph 3 s: 13–37 s (`:115`) |
| skeptic | request | `requests/skeptic_<stamp>.json`; the answer `answers/skeptic_<stamp>.json` | — | 5–6 min per round on the loops (`research/2026-11-04/trackB_distill.md:124`) |
| page | builtin | the studio writes `index.html` and `page.md5` at the job root | `index.html` | — |
| grades | builtin | his words verbatim and the picks, per round | — | — |

The brief's "about 5 s" for the 480 px relation has no source I could find; two measurements give 1.6–2.4 s.

The registry entries in the shape of `registry/loop.py` (a proposed `registry/pair.py`). The `script` key is new: it names the Settings path the runner starts and whose md5 the record carries.

```python
PAIR_STAGES: list[dict[str, Any]] = [
    {"name": "import", "title": "import", "kind": "builtin", "optional": False, "terminal": None,
     "what": "Two photos read in place: A, the start (BEFORE), and B, the finish (AFTER). Each is a symlink under raw/<pair>/ that keeps its extension, with a sha256. Pick a fixture pair by name or give two paths; the originals are never copied or modified.",
     "knobs": []},
    {"name": "relation", "title": "relation", "kind": "script", "optional": False,
     "backend": "transitions.py pair", "script": "transitions", "terminal": "report.json",
     "what": "A one-second transition at 480 px, read for the relation it reports. Class A: a sane homography with 30 or more SIFT inliers, so the photos morph along a dense flow. Class B: each photo zooms and pans about its salient blob. Writes transition.mp4, strip.jpg and report.json; a rerun replaces the folder.",
     "knobs": []},  # the argv fixes --max-long 480 --seconds 1 (STUDIO.md §2; director_ui.py:446)
    {"name": "verdict", "title": "Reveal's verdict", "kind": "script", "optional": True,
     "parent": "import", "branch": True, "stale_after": [],
     "backend": "reveal.py align", "script": "reveal", "terminal": "metrics.json",
     "what": "Reveal's strict alignment of B onto A, run on demand. Exit 2 with a FAILED: line is a refusal: the photos share too little detail to align. On success it writes metrics.json and two full-resolution aligned stills, the align flow's outputs.",
     "knobs": []},
    {"name": "render", "title": "render", "kind": "script", "optional": False,
     "backend": "transitions.py pair", "script": "transitions", "terminal": "report.json",
     "what": "The transition from A to B with the knobs below. Writes transition.mp4 (libx264, crf 18, yuv420p), strip.jpg (up to 8 tiles 160 px tall, the first and last frames included) and report.json (the class, the method, the correspondence and the quality basket). A finished render is never overwritten.",
     "knobs": [
         K("name", "str", "", "the render's folder name under <pair>/ (a full render) or drafts/<pair>/ (a draft); a name that exists is refused"),
         K("draft", "int", 0, "render at this long edge into drafts/<pair>/ (480 for a draft); 0 renders in full at max_long"),  # no flag: the pair argv builder sets --max-long from draft or max_long
         K("seconds", "float", 1.0, "the clip's length; it clamps to [0.1, 10] s (TRANSITIONS.md §3; --help gives no sentence)", "--seconds", rng=[0.1, 10.0]),
         K("fps", "float", 30.0, "frames per second, at least 1; the clip holds round(seconds × fps) frames, at least 2 (TRANSITIONS.md §3; --help gives no sentence)", "--fps"),
         K("preset", "str", "morph", "a named spec: morph, dissolve, flow-dissolve, snap-morph, iris, wipe or luma (TRANSITIONS.md §3; --help gives no sentence)", "--preset",
           choices=["morph", "dissolve", "flow-dissolve", "snap-morph", "iris", "wipe", "luma"]),
         K("color", "float", 0.7, "color path strength 0..1", "--color", rng=[0.0, 1.0]),
         K("warp", "float", 1.0, "geometric warp amount 0..1", "--warp", rng=[0.0, 1.0]),
         K("max_long", "int", 1920, "cap the canvas long edge (0 = native)", "--max-long"),
         K("canvas", "str", "finish", "canvas aspect: finish = the AFTER photo's ratio (default); common = the smaller width and height of the two", "--canvas",
           choices=["finish", "common"]),
         K("anchors", "str", "", '"ax,ay,bx,by;..." canvas pixels, A -> B, >= 3 pairs', "--anchors"),
         K("anchor_falloff", "float", 0.45, "anchors: fade the anchored field to zero at the canvas border over this fraction of the short edge (default 0.45; 0 = the plain MLS field, whose frame edge shows; T16)", "--anchor-falloff", rng=[0.0, 0.5]),
         K("force_class", "str", "", "force the pair class", "--class", choices=["", "A", "B"]),
         K("camera", "str", "flat", "class B camera move: flat = the pan-and-zoom as is; ramp = near content (bottom rows) moves more, no model; model = the same from Depth Anything V2 Small (needs `transitions.py warmup` once)", "--camera",
           choices=["flat", "ramp", "model"]),
         K("zoom", "float", 0.1, "class B zoom fraction per frame, clamped to [0.02, 0.5]", "--zoom", rng=[0.02, 0.5]),
     ]},
    {"name": "skeptic", "title": "skeptic", "kind": "request", "optional": False, "terminal": None,
     "what": "A request file for the Claude Code session. An Opus 5.5 subagent crops every candidate at full size and answers with a verdict per candidate on the transition.mp4 md5 it judged. The page refuses an unjudged candidate unless he overrides.",
     "knobs": []},
    {"name": "page", "title": "page", "kind": "builtin", "optional": False, "terminal": "index.html",
     "what": "The review page the studio writes over the listed full renders, in their order: A and B, then per candidate the player, the labelled strip, the class, the method and the quality basket with its bars. Built behind the review gate; its md5 opens a round.",
     "knobs": [K("title", "str", "", "the page's title"), K("intro", "str", "", "one paragraph under the title: what the round is"),
               K("footer", "str", "", "one line at the end; an override is printed here"),
               K("variants", "list", [], "the full renders the page lists, in this order; empty lists every full render in name order")]},
    {"name": "grades", "title": "grades", "kind": "builtin", "optional": False, "terminal": None,
     "what": "His grade for a round, saved with the page md5 it was given on: his words verbatim, the best render or none, and per render acceptable, a note and three boxes (one picture, content transforms, nothing invented).",
     "knobs": []},
]
FLOWS["pair"] = {"title": "pair transition", "stages": PAIR_STAGES,
                 "what": "Two photos, related or not, animated from one into the other by transitions.py: the relation first, then the renders, then the review."}
```

Knob notes, each with its evidence:

| Knob | Note | Evidence |
|---|---|---|
| `warp` | the CLI always passes `warp_amount=args.warp`, which overrides the preset's own value; `flow-dissolve` renders at warp 1.0, never the 0.6 of `PRESETS` and `TRANSITIONS.md §3`, unless `--warp 0.6` is given | `transitions.py:248, 258–262, 1569`; `benchmarks/runs/2026-09-13/match_1/flow-dissolve_1s/report.json` records `warp_amount` 1.0 with `mix_delay` 0.1 |
| `preset` | `bench_transitions.py`'s legend prints flow-dissolve at warp 0.6, because it calls `spec_from` without the warp | `scripts/bench_transitions.py:215–223` |
| `max_long` | the CLI's default is 0 (native); I propose 1920 for the full render, naming its source in the hint: the default of the fixture sweep (`scripts/bench_transitions.py`, which runs every fixture pair through `transitions.py pair`), under which every expectation in `fixtures/MANIFEST.md` was measured | `scripts/bench_transitions.py:105`; a native render of a 48 MP HEIC pair is unmeasured |
| `camera`, `zoom` | act on class B only; with anchors or on class A the camera is ignored and one INFO line says so | `transitions.py:842–845` |
| `draft` | carries no flag of its own: `flags_of` emits every int knob that has one, so two `--max-long` flags would reach one argv; the pair's argv builder takes `--max-long` from `draft` when it is above 0, else from `max_long` | `runner/argv.py:111–129` |
| `seconds`, `fps` | the frame count is `max(2, round(seconds × fps))` | `transitions.py:202–203` |
| `anchors` | 0 pairs or 3 and more; fewer than 3 is `FAILED:` with exit 2 | `transitions.py:1549–1563` |

The keys of `report.json` (all present on the mismatch_3 run unless the column says otherwise):

| Key | Meaning | When present | Source |
|---|---|---|---|
| `tool_version` | `transitions.VERSION`, "0.1.0" | always | `transitions.py:98, 1447` |
| `spec` | the clamped spec as rendered (seconds, fps, style, curves, mix_delay, warp_amount, color_strength, portal, portal_feather, max_long_edge, canvas, anchors, force_class, camera, zoom, anchor_falloff); the preset's name is absent | always | `:181–203, 1447` |
| `class` | A or B (the rule below) | always | `:834–835` |
| `method` | class A: `homography+dis`, or `dis-only` when forced without a sane homography, with `+anchors` and `+falloff` suffixes; class B: `saliency-panzoom` with `+ramp` or `+model`, or `mls-anchors` | always | `:852–896` |
| `sparse_inliers`, `sparse_rmse` | the SIFT and MAGSAC++ inliers between A and B on the canvas (0 when none), and their rmse in px (null) | always | `:836–837` |
| `pan_fraction` | [A, B]: the share of the distance between the two salient centres each photo pans | class B without anchors | `:882` |
| `camera`, `zoom` | the class B camera move and zoom fraction | class B without anchors | `:883` |
| `disparity_mean` | [A, B]: the mean disparity behind the camera move | class B with `ramp` or `model` | `:897` |
| `mean_certainty` | the mean splat weight: class A the forward-backward consistency (1 = every pixel agrees both ways), class B a fixed 0.5 | always | `:886, 903` |
| `median_disp_px` | the median displacement A to B in canvas px | always | `:903–905` |
| `correspondence_s`, `render_s`, `total_s` | clock seconds; the decode is outside `total_s` | always | `:1326, 1442, 1451` |
| `canvas`, `canvas_policy` | [w, h] with even sides; finish or common | always | `:356–380, 1449` |
| `n_frames` | frames written | always | `:1449` |
| `quality.warping_error` | the mean absolute difference after warping each next frame back by DIS flow, 0..1 grey | always | `:1142–1153` |
| `quality.flicker` | `mean`, `max`, `spikiness` of the adjacent-frame change; `edge_ratio` is the larger endpoint step over the interior mean, the hidden-cut detector | always | `:1156–1164` |
| `quality.goal` | `feat_floor`, `laplace_floor`, `contrast_floor`, `dissolve_fit`, `motion_share` (the goal numbers of 2026-09-26) | always; zeros under 3 frames | `:1114–1136, 1198–1249` |
| `quality.endpoint` | `first_vs_A`, `last_vs_B`: frame 0 against A and the last frame against B on the 480 px proxies, before encoding | always | `:1167–1171` |
| `quality.n_frames`, `quality.proxy_long` | frames assessed; the proxy's long edge, 480 | always | `:152, 1297` |
| `outputs` | `transition.mp4`, `strip.jpg`, `report.json` | always | `:1452` |

Class A needs a homography from SIFT and MAGSAC++ that passes `_sane` and holds 30 or more inliers; any other pair is class B (`transitions.py:834–835`). `--class` forces either. `_sane` keeps the warped quad's area between 0.15 and 6 times the canvas (`TCFG area_ratio`, `:122`). The class is measured on the run's own canvas. At 480 px mismatch_3 found 0 inliers, against 6 at 1920 (`fixtures/MANIFEST.md`). A pair near the 30-inlier floor at 1920 can therefore route B at 480 [INFERRED]. So the relation panel labels its class "at 480 px", the render's report is the class of record, and a differing class gets a warning chip.

The strip holds `min(8, n_frames)` tiles 160 px tall at evenly spaced frames, the first and last included (`StreamStats`, `transitions.py:1273–1300`; `TCFG` `:155–156`). Tile 0 is A on the canvas and the last tile is B. The probe's strip is 1704×160: 8 tiles of 213×160 for a 480×360 canvas.

The probe ran on the fixture pair mismatch_3 (a crowded bar and a lounge group, `fixtures/MANIFEST.md`): `transitions.py pair fixtures/mismatch_3_S.jpg fixtures/mismatch_3_F.jpg --max-long 480 --seconds 1` on 2026-11-05 and exited 0. It reported class B, `saliency-panzoom`, 0 sparse inliers, pan 0.09 / 0.25 and mean certainty 0.5. The median displacement was 24.71 px on a 480×360 canvas, with 30 frames at 30 fps. The basket read `edge_ratio` 0.132, warping error 0.0207, `feat_floor` 0.0826 and endpoints 0 / 0. The workbench, the director's page `scripts/research/director_ui.py` on 127.0.0.1:8379 that phase B retires, gave the same 24.71 px and 0 inliers on 2026-10-21 (`ui1_build.md:26–27`). The mp4's md5 is 25c0f77ce05ce8ed53580bb36da24acb and the strip's 8bd77a4dbbd9763ccd1fd95ca9cdddef. The report's md5 (b40aee46554e9525e5db5d04a973629b) changes from run to run, because it holds the three clock keys.

The bars each quality measure is read against:

| Measure | Bar | Source |
|---|---|---|
| `quality.endpoint` | 0 and 0: frames 0 and n−1 are A and B byte for byte | invariant 4 (`TRANSITIONS.md §1`); harness checks 21 and 31 |
| `quality.flicker.edge_ratio` | below 1.5 for every preset; below 1.0 for the CLI morph on the harness pair | checks 21 and 31 (`transitions_harness.py:326–333, 396–400`); `TRANSITIONS.md §5` |
| `quality.flicker.max` | below 0.12 on 0..1 grey, about 31 levels | check 21 |
| `quality.warping_error` | a fixed bar is absent; a coherent pan reads below 0.03 and unrelated frames above 0.1 | check 26 (harness section G); "compare a pair against itself" (`transitions.py:1116, 1134`) |
| `quality.goal` | a bar is absent; references for match_4 and mismatch_4 at morph 2 s | the goal table of `TRANSITIONS.md §6`; `§11`: the basket does not separate his crossfade verdicts from his closest picks (AUC 0.46–0.48) |
| real pairs, for reading | `edge_ratio` at most 0.79 on the smooth presets; 0.13–0.66 on morph 1 s class B; `snap-morph` inflates it by design | `TRANSITIONS.md:241, 247` and `§3` |

The decoded-mp4 observables of the harness (section H, a synthetic pair):

| Check | Observable | Bar |
|---|---|---|
| 28 | size, fps and frame count of the decoded mp4 | the canvas, 30 fps, 30 frames for 1 s |
| 29 | the first decoded frame against A, the last against B | mean absolute difference below 6 levels and below 20 % of the A–B gap; yuv420p alone costs about 3.5 |
| 30 | the darkest frame | every frame's mean above 5 (no black frame) |
| 33 | two CLI runs | identical decoded frames |

The studio can check 28 and 30 on its own decode, since `media/pictures.py` decodes mp4s with cv2, against the report's `n_frames` and `canvas`. Check 29 needs A and B on the canvas, which only `transitions.py` makes. The strip's first and last tiles are a 160 px stand-in, and their bar is unmeasured.

Reveal's verdict: an optional branch stage under import, defined once and shared by the pair and director flows, kept out of the relation stage. Phase C's align flow reuses its argv and adds `--video`. If phase B builds neither the director's relation panel with the verdict nor the "suggest" step, the stage moves to phase C.

| Reason | Evidence |
|---|---|
| a record holds one argv that reproduces its stage, so the relation cannot also run Reveal | `runner/process.py:73–148` (`start_stage` writes one `argv`) |
| inside the relation it would hold a 1.89 s read behind a 2.2–16 s align | this run; `2026-09-13-real-pairs.md:115` |
| the class, the method and the certainty come from the transitions router; Reveal sets no pair knob | `transitions.py:834–835` |
| on success it writes two full-resolution stills, the align flow's outputs | `reveal.py:1406` (`_render_pair(job, 10 ** 6, …)  # full resolution`), `:2526–2530` |
| the workbench's relation panel showed it beside the class, and phase B retires the workbench | `director_ui.py:430–446` (both started together), `:461–474` (the sentence that joins them, for example "unrelated (Reveal refused, class B)") |
| the "suggest" step reads it to route a refused pair to the pair flow | `STUDIO.md §5` (line 100) |

The runner already reads exit 2 with a `FAILED:` line as `refused` (`runner/process.py:208`). A refusal writes no `metrics.json` (`reveal.py:2523–2525`; `ui1_build.md:23–25`). Reveal exits 2 for a decode failure too, so the reason's text separates the two (`STUDIO.md §7`, the align row).

The readers that decode the import's photos:

| Extension | Reader in `transitions.py` | Note | The studio's own thumbnail (cv2 5.0.0, 2026-11-05) |
|---|---|---|---|
| .jpg .jpeg .png .webp .tif .tiff .bmp | PIL with EXIF orientation and ICC to sRGB (`:271, 289–323`) | — | JPEG and PNG read; webp, tiff and bmp untested |
| .heic .heif .hif | pillow_heif through PIL (`:270`) | 6048×8064 decodes in 1.9 s (`TRANSITIONS.md:243`) | `cv2.imread` returns None on `match_1_S.HEIC` and `fabra_17_S.heic` |
| .dng .arw | rawpy, which applies the camera flip itself (`:269, 296–308`) | never decoded from a real file (`TRANSITIONS.md §5`) | untested |
| anything else | `FAILED: Unsupported file type` with exit 2 | — | — |

The fixture picker reads `fixtures/<group>_<N>_S.<ext>` and `_F.<ext>`. The sweep's pattern takes the groups match and mismatch only (`bench_transitions.py:38`), while `fixtures/MANIFEST.md` also lists the fabra pairs. A picker that reads any group offers 19 pairs: match_1–5, mismatch_1–7 and seven fabra pairs. Extensions mix inside a pair (mismatch_7: a JPEG and a PNG) and in case (`match_1_S.HEIC`).

The studio's thumbnails go through `cv2.imread` (`media/pictures.py:21–34`), and its runtime holds numpy and opencv-python-headless only (`studio/pyproject.toml:9–10`). A new decoder there is a dependency decision. So A and B on the page come from the relation's outputs. The strip's first and last tiles show them at 160 px. Frames 0 and n−1 of the relation's 480 px mp4 show them larger, and cv2 decodes the mp4. Both show the cover-cropped canvas, never the whole photo.

`transitions.py pair` prints no progress lines (`:1566–1580`), so its tile shows the elapsed time only. That stays so, because neither tool changes without his word (the rule of backlog row T68).

The candidate and the job folder, consistent with `STUDIO.md §4` and the loop job (`jobs/store.py` docstring):

```
benchmarks/runs/<date>/studio/pair_<pair>_<stamp>/   the job folder; job.json's "root" names this folder
  job.json          {id, flow: "pair", created, ui_version, root, seq: "<pair>",
                     inputs: [{role: "A"|"B", name, path, sha256, bytes, link}], fixture: "<pair>"|null, adopted: false}
  raw/<pair>/A.<ext>, B.<ext>    symlinks to the originals; the extension kept, since transitions.py picks its reader by suffix
  stages/<stamp>_<stage>/        stage.json (argv, knobs, inputs with sha256, outputs with md5, the md5 of the stage's own script), log.txt, done
  relation/                      transition.mp4, strip.jpg, report.json at 480 px and 1 s; a rerun replaces it, as the loop's readers folder
  verdict/                       metrics.json, before.jpg, after_aligned.jpg on success; a refusal leaves an empty verdict.part
                                 (finalize renames only a done record), which the next run's start_stage removes; the record holds the reason
  <pair>/<name>/                 a full render: transition.mp4, strip.jpg, report.json; never overwritten
  drafts/<pair>/<name>/          a draft at 480 px
  index.html, page.md5           the review page the studio writes over the listed full renders
  requests/ answers/ rounds/<n>/ picks/ owner_frames/ cache/     as in the loop job
```

`seq` for a pair job is the pair's name: the fixture id (`mismatch_3`), or for two paths a slug of the two file stems that passes `NAME_RE`. A candidate is a render folder holding `report.json`: `{name, kind: full|draft, dir, md5_mp4, class, method, sparse_inliers, median_disp_px, mean_certainty, canvas, n_frames, preset, quality}`. `md5_mp4` is the md5 of `transition.mp4`, taken from the record's outputs or hashed. `preset` comes from the record's knobs, because the report keeps the expanded style only. A verdict's `judged_md5` is that mp4 md5. Two CLI runs decode to identical frames (harness check 33). The camera sweep of 2026-09-23 reproduced the mp4 md5 on all six pairs (`TRANSITIONS.md §6`).

The page: there is no page script for a pair. I recommend that the studio writes the page itself, as a builtin stage, into `index.html` and `page.md5` at the job root. The round-opening code of `after_done` writes `page.md5`, `rounds/<n>/round.json` and the round's copy of the page. It moves into a function the page builder calls, because `after_done` runs only from a script record's `finalize`. The round's shape stays the loop's. The page follows the sweep's page: A and B, then per candidate the player, the labelled strip, the numbers with their bars, and the three boxes.

| Option | Verdict | Evidence |
|---|---|---|
| `bench_transitions.py --render-only` | rejected | it rebuilds from a `sheet.json` of fixture-pattern pairs (`:38`), and its legend reports flow-dissolve at warp 0.6 while the CLI renders 1.0 (`:215–223`) |
| `director_page.py` | rejected | it reads the director's plans and `info.json` (`research/2026-11-04/trackA_inventory.md:339`) |
| the candidates panel alone, without a page file | weaker | `after_done` opens a round from the page file and its md5 (`runner/process.py:279`); a round without a page needs a second round shape |
| the studio writes `index.html` | recommended | one round shape for every flow; a static page he can open, the shape he graded the sweeps and the director rounds on |

The grades take the director picks shape, which `STUDIO.md §3` keeps for director rounds: `{date, page, best: {<pair>: <render>|"none"}, clips: {<render>: {acceptable, note, props: {one_picture, transforms, not_invented}}}}` (`benchmarks/runs/2026-10-17/director_r11/director_picks_11.json`). The sweep's shape (`bench_transitions.py:364–370`, `{date, picks: {<pair>: {best, note, props}}}`) is its ancestor and lacks `acceptable`. One shape then serves both two-photo flows.

The skeptic of a pair crops at full size. It compares frame 1 with A and frame n−2 with B, the frames beside the endpoints (`TRANSITIONS.md §12.13`). It also crops the mid frame and the frame pair behind `edge_ratio`. It looks for double exposure and invented content, two of the three failure modes of `TRANSITIONS.md §11`. On class B it also looks for a moved frame's edge inside the canvas, the frame-border defect of `TRANSITIONS.md §6`. The answer keeps the loop's shape.

**Part 2. `--layers-dir` and `--mattes-dir`.** Both roots are module constants of `director_render.py` (`:35–36`, under `ROOT = Path(__file__).resolve().parents[2]` at `:29`). The two flags override them (`:2086–2092`), and `info.json` records both (`:2102`). `director_ui.py:49–50` hard-codes the same paths and never passed the flags (`STUDIO.md §7`).

| Root (size) | Per photo | At the root | Coverage on 2026-11-05 | Writer |
|---|---|---|---|---|
| `benchmarks/runs/2026-09-28/layers_v3` (190 MB) | `<photo>/layers.json` (keys canvas, canvas_mode, elements, frame, merge, photo, provenance; 75 elements on mismatch_3_S), `layers.npz` (the `element` id map), `timing.json` | no manifest; two non-photo folders, `_candidates/` and `_det_run2/` | 24 photo folders: match_1–5 and mismatch_1–7, S and F | `layer_merge.py --out-root` (`layer_merge.py:89`) |
| `benchmarks/runs/2026-10-17/mattes` (210 MB) | `<photo>/el_<id>.png` (uint8 alpha at the layer source's canvas), `mattes.json`, `sheet.jpg` | `MATTE_MANIFEST.json` (two ViTMatte small models, revision and sha256 per file), `hf_home/` (the weights) | 14 photo folders: match_1 and mismatch_1–6; match_2–5, mismatch_7 and the fabra pairs have none | `matte_source.py run` (`matte_source.py:13–19`) |

A missing matte falls back to the hard element mask with one INFO line (`director_render.py:212–228`). A second layer root exists: `benchmarks/runs/2026-10-09/fabra/layers_v3` holds fabra_17_S and fabra_17_F, which the default root lacks. A director job on that pair needs its own root, recorded in its `job.json` over the Settings default.

The Settings additions, in `config.py`'s style:

```python
ENV_LAYERS = "REVEAL_STUDIO_LAYERS_DIR"   # mirrors --layers-dir, as REVEAL_STUDIO_RUNS_DATE mirrors --runs-date
ENV_MATTES = "REVEAL_STUDIO_MATTES_DIR"
TRANSITIONS = Path("transitions.py")
REVEAL = Path("reveal.py")
DIRECTOR_RENDER = Path("scripts/research/director_render.py")
LAYERS_DIR = Path("benchmarks/runs/2026-09-28/layers_v3")   # director_render.py --help, the default
MATTES_DIR = Path("benchmarks/runs/2026-10-17/mattes")      # director_render.py --help, the default
# Settings gains: transitions, reveal, director_render, layers_dir, mattes_dir (all Path)
```

Resolution follows the file's order: the flag, then the environment, then discovery, which is the renderer's own `--help` default under the root. A relative value resolves against the working folder, as the lock does (`_absolute`). A missing folder raises nothing at resolve time, because the loop flow runs without it. The director flow's resolve stage refuses with a 409 that names the folder. The `common` parser of `cli.py` (`:32`) gains both flags.

The director's argv passes both flags on every run, repo-relative, so the record's argv names the roots. The renderer resolves them against the working folder, the root (`:2090, 2092`), which gives the same paths as its defaults [INFERRED from `:29, 35–36`; not run]. `info.json` then records the same roots.

`reveal-studio check` gains five rows in `cmd_check`'s style (`cli.py:90`):

```
transitions   transitions.py md5 7ef5dcae070c223e360c9c2e533df6c1
reveal        reveal.py md5 d859dfb4dc1198babe05d372404b7236
director      scripts/research/director_render.py md5 05cd6e1d95adbb3c83313b98b3f43815
layers        benchmarks/runs/2026-09-28/layers_v3 (24 photo folders with layers.json; the renderer's default)
mattes        benchmarks/runs/2026-10-17/mattes (14 photo folders with el_<id>.png; MATTE_MANIFEST.json present; the renderer's default)
```

A missing root prints MISSING and leaves the exit code alone; it stays 1 only for a missing python or loop script, as today. A photo folder counts when it holds `layers.json` (layers) or an `el_<id>.png` (mattes); folders that start with `_` and `hf_home` are skipped.

The file route serves the job's run folder and the job folder only (`server/handler.py:140–148`). The workbench also served `fixtures/`, the layer root and the matte root (`ui1_build.md:31–33`), and `STUDIO.md §5` lists them. The director overlays need those three bases, read-only, with a test per base.

**Part 3. The request pickup at boot (backlog row T74).** `reveal-studio requests` lists every unanswered request across the jobs, oldest first, with a summary line (`cli.py:68`, `views/models.py` `open_requests`). A request counts as answered when `answers/<request file name>` exists (`jobs/candidates.py:111`). The hook prints its instruction block from a heredoc that ends at line 75 and exits 0 at line 76. The `compact` branch exits at line 22 first, so a new line runs on startup, resume, clear and fork. The hook's md5 is 91d03df413b222112ab32faa53748375, unchanged by this track.

The line to add between line 75 (`EOT`) and line 76 (`exit 0`) of `.claude/hooks/session-start.sh`:

```bash
RS="$mem_root/studio/.venv/bin/reveal-studio"; if [ -x "$RS" ]; then REQ="$("$RS" requests --root "$mem_root" 2>&1 | tail -n 12)"; [ "$REQ" = "no open requests" ] || printf '%s\n' "Studio inbox: open requests (the newest 11; studio/.venv/bin/reveal-studio requests lists all). Answer each into its job's answers/ under the request's file name, or carry it in the handover:" "$REQ"; elif ls "$mem_root"/benchmarks/runs/*/studio/*/requests/*.json >/dev/null 2>&1; then echo "Studio inbox: request files exist, but studio/.venv is missing: run make -C studio install, then studio/.venv/bin/reveal-studio requests."; fi
```

I ran the line in a scratch script on 2026-11-05; the hook itself is untouched:

| Case | Output |
|---|---|
| the real root | the header, 7 requests and the summary line; the listing took 0.07 s |
| a root with no open request | nothing |
| `studio/.venv` missing, a request file present | the one install line |
| `studio/.venv` missing, no request file | nothing |

Every case exits 0. The line calls the console script directly because `uv run` creates the project environment when it is missing and syncs it when stale. `--frozen` still installs from the lock, and only `--no-sync` skips the sync (the uv documentation through Context7: `docs/concepts/projects/layout.md` and `sync.md`). A boot hook that syncs would reach PyPI at session start. `--root "$mem_root"` names the main worktree, where the gitignored jobs live, so the working folder plays no part.

`studio/Makefile` has no `requests` target (its `.PHONY` line 11 lists help install run test test-fast test-cov acceptance draft-check lint fix typecheck audit prose qa detector). For his manual use, and never from the hook:

```make
requests:  ## list the open requests across every job (the session's inbox)
	@$(RUN) reveal-studio requests
```

The 7 open requests on 2026-11-05 are all skeptic requests that acceptance drives wrote in jobs of the angel portrait pair, 4 to 13.5 hours old. `studio/tests/acceptance/test_a1_loop_flow.py:299` writes `{"brief": "acceptance test", "candidates": ["a2"]}` and never answers it, so each `make acceptance` adds one. Proposed backlog row: after it checks the listing, the loop flow's first acceptance test answers its own request with `answers/<request name>` holding `{"at": …, "candidates": {}}`. An empty `candidates` map marks the request answered and adds no verdict, because `verdicts` reads only entries whose verdict is one of the three words (`jobs/candidates.py:85–100`). The 7 existing requests get the same answer once, a write under the gitignored `benchmarks/runs/`.

The handover row, for "Open for the owner" in `NEXT_SESSION_PROMPT.md`:

> T74, the request pickup at boot: his decision, because `.claude/**` is his. Proposed: one line in `.claude/hooks/session-start.sh`, between the closing `EOT` (line 75) and `exit 0` (line 76). It runs `studio/.venv/bin/reveal-studio requests --root <main worktree>` (0.07 s on 2026-11-05) and prints the open requests under a "Studio inbox" header, and nothing when none is open. When `studio/.venv` is missing and request files exist, it prints one line naming `make -C studio install`. It calls the console script, never `uv run`, because `uv run` syncs the environment from PyPI even with `--frozen`. The exact line is in `benchmarks/runs/2026-11-05/studio/agents/b_pair_research.md` (its research copy: `.claude/claude-docs/research/2026-11-05/b_pair_research.md`), Part 3. Before it goes in, answer the 7 requests the acceptance drives left open, or every boot lists them.

**Part 4. The loop items.** (a) Sequences up to 10 stills. The code sets a floor of two stills and no ceiling: `cmd_prep` (`loop_seq.py:455–457`), `probe` (`:1976–1977`) and `create_job` (`jobs/store.py:71`, "need 2 or more") check the floor only. `scripts/research/plans/loops/SCHEMA.md` states no count. The ten comes from the design. `STUDIO.md` line 21 reads "stills per sequence 2–10 (the boxes repaint had 7)", written in commit bf72dbf on 2026-11-04. The second skeptic review of the design (lens 2) had found a draft's 2–6 cap and asked for "no upper bound on stills" (`research/2026-11-04/lens2_intent.md:22, 73`). The registry copied the range as "Two to ten stills" (`registry/loop.py:262`). `loop_seq.py`'s docstring still says "2–6 developed stills" (line 2).

| Path | Largest sequence run so far | Source |
|---|---|---|
| `loop_seq.py prep` | 6 stills (`evgen-thug`) | `benchmarks/runs/2026-10-30/halloween/in/evgen-thug/k0.png` to `k5.png` |
| the studio | 2 stills, in all 20 jobs (the angel portrait pair) | `benchmarks/runs/2026-11-0[45]/studio/*/job.json` |
| `chain_luma.py` | 7 stills (the boxes: his seven photos of two utility boxes during a repaint, 2026-10-09) | `.claude/claude-docs/benchmarks/2026-10-09-fabra-boxes.md` (the fabra sheet), stage 6 |

Recommendation: the import accepts any count of 2 or more and shows a hint chip above 6 and above 10. Above 6 the chip says the count passes every sequence registered so far (6, `evgen-thug`); above 10 it names the 2–10 range of `STUDIO.md §1`. A refusal would state a limit that no script states, and `.claude/conventions/studio.md` forbids an invented range. The real-surface check makes a new job from `benchmarks/runs/2026-10-09/fabra/draw7_3s/aligned/`: seven JPGs, `0_1.jpg` to `6_7.jpg`, in capture order by name. It runs the registration and a `through` chain dissolve draft at 480 px [UNVERIFIED until run]. It proves 7 stills through the import, the strip and the render, and it gives the repaint leg its test input.

(b) The repaint sequence as a loop leg. The leg is a new value of a step's `method`:

```json
{"to": 6, "method": "repaint", "through": [1, 2, 3, 4, 5], "n": 75, "ease": "smooth",
 "front": 0.35, "overlap": 0.35, "zone_erode": 15}
```

It ports `chain_luma.py --variant draw` (the draw) onto registered stills. Outside a zone, one dissolve runs from the first still to the last. Inside the zone, each repaint spreads as a soft front of width `front` in a per-pixel order, and consecutive repaints overlap by `overlap` of a step (`chain_luma.py:629–641`). The order is a weighted sum of three ranks, ranked again (`:556–568`). The distance to the new still's Canny edges weighs 0.5, so the new lines come first. The old still's negated brightness weighs 0.3, so its bright parts come early. Noise at two scales weighs 0.2 (Gaussian sigma 6 and 24 px, seeded k + 1). The zone is the union of `loop_seq.py`'s own change matte over the consecutive pairs (`change_matte`, `:611–630`), eroded `zone_erode` px and blurred at sigma 8 px. Chain_luma builds it from Reveal's changed-region masks instead (`tr14_variants.py:78–83`, `chain_luma.py:583–591`). `overlap` acts only across a chain of two or more repaints: its lead and tail terms are 0 for a single segment (`chain_luma.py:634–635`).

| Change | Lines [estimate] |
|---|---|
| `elif method == "repaint":` in `render_plan`, placed before `elif "through" in step:` (`loop_seq.py:1661`), because a `through` key sends a step to `frames_chain`, which knows RIFE and dissolve only (`:704–736`) | 3 |
| `frames_repaint(keys, knots, n, ease, step, matte_kw, rows)`: the orders, the zone, the frame loop, one `tick` per frame for `--progress`, and rows `{"generated": "none (repaint)", "u", "segment"}` | 45–60 |
| `rank_order` and `reveal_mix`, copied from `tr14_variants.py:111–135` (numpy only) | 15–20 |
| the docstring's render paragraph, and line 2's "2–6" | 5–8 |
| a dated `repaint` section in `SCHEMA.md` with the three keys, their defaults and chain_luma's sentences (`chain_luma.py:283–285`) | 12–20 |
| the studio: `METHODS` gains `repaint` (`registry/schema.py:33`), three schema entries naming their default's source, hints, `frame_kinds` reading "none (repaint)" as a blend (`views/measures.py:46`), tests | 30–50 |

What `loop_seq.py` may import: it imports `transitions` for the decode, the cover and the morph, and `rife_probe` for RIFE, both lazily inside functions (docstring lines 4–6; `:453, 644, 751`). Importing `chain_luma` would buy nothing, because the draw lives inline in its `main()` and offers no function to call. It would also load `reveal`, `transitions` and `tr14_variants` at module level (`chain_luma.py:61–63`; `tr14_variants.py:43–44`). Measured with `python -B` on 2026-11-05: `import chain_luma` takes 0.168 s, `transitions` 0.122 s, `reveal` 0.135 s and `cv2` 0.071 s. The wall-time cost is small. The import-graph cost is a research script tied to Reveal's internals (`changed_region_mask`, `warp_valid_mask`) through `tr14_variants`. Copying about 35 lines keeps the import set the docstring states.

What the leg leaves out of the boxes clip:

| Part of the boxes clip | Where `chain_luma.py` does it | Why the leg cannot carry it |
|---|---|---|
| registration onto the last photo by Reveal's strict aligner, the uncovered pixels filled from the neighbouring still | `:97–115`, `:323–343` | `prep` registers onto frame `--ref` by SIFT and MAGSAC (`loop_seq.py` docstring) |
| a pin per box on the box's own SIFT features, position and size | `:409–436` | `prep --lock-window` adds a translation only; under a wall pin the left box sat 13.99 px off at scale 0.984 on still 5 (fabra sheet, stage 6) |
| the light match over the wall rings | `:512–517` | it changes the stills that the lead and the hold also show; a leg that matched light inside itself would step against the byte-exact holds [INFERRED] |
| a one-way clip with a 3 s end hold | the lead and hold frames of `main()` | a loop's seam then reads the whole repaint as one step; lens 2 asked for a one-way mode (`lens2_intent.md:73`) |
| the HEIC originals | `fixtures/fabra_*.heic` | `cmd_prep` keeps `.jpg` and `.jpeg` only (`loop_seq.py:455`), though its reader decodes HEIC |

His record on the boxes: on 2026-10-09 he asked for "really gradual and elaborate drawing process on those boxes", which became the draw (fabra sheet, stage 5). On 2026-10-17 he closed the experiment as "not fully satisfied". He named a mix of luma, edge-grow and melt-soft and added "Do not redraw anything this is simply my feedback" (fabra sheet, lines 143–151). The draw clips of stages 5 and 6 stayed ungraded. The DECISIONS line of 2026-11-05 (seventh) closed the loops work and routes new requests through the studio.

The proof of the default path renders the angel loop a2 (`angel_a2.json`, md5 c302623f293eacd069218fd7518e0967) and the seasons loop s6 (`seasons_s6.json`, 5908af3d5300046579548848679b0cbb) before and after the edit. That is four full renders of 56–67 s and 64–74 s each, about 5 minutes (`research/2026-11-05/loopseq_a2.md:78–79`). The new branch runs only for `method: "repaint"`, and the 48 frozen plans hold no such step (grep, 2026-11-05).

`loop_seq.py` has no harness, so the self-check is four runs:

| Check | Expected |
|---|---|
| a repaint between two identical stills | every in-between equals the still (an empty zone) |
| two renders of one repaint plan | one mp4 md5, since the noise is seeded k + 1 |
| the holds beside the leg | byte-equal to `k<i>.png` (frames.json "none (photo)") |
| the step series on the seven fabra JPGs | no peak at a segment's first frame; chain_luma's seven-still draw peaked at 4.10 on frame 36 (the door) with mean 1.14 (fabra sheet, stage 6) |

Size: about 80–120 lines in `loop_seq.py` and `SCHEMA.md`, and 30–50 in the studio. Time: about 3.5–4 hours with the proofs [estimate; the four default-off additions of 2026-11-05 to `loop_seq.py` took one Opus subagent, `research/2026-11-05/loopseq_a2.md`].

Recommendation: the handover, with the spec above. His last word on the draw was "not fully satisfied" and "Do not redraw anything", and no open request asks for a repaint loop. The leg alone leaves the boxes clip short of the studio. The box pin, the light match, the HEIC input and the one-way clip are four more changes, in `prep` and in the plan grammar. Phase B's two flows, the workbench's retirement, the mismatch_3 acceptance and the UI build routine of `.claude/skills/reveal/references/studio.md` each took a whole session in the studio's first two phases. Inside this session, the 7-still check of Part 4(a) costs one job, one registration and one draft, and it gives the leg its test input.

### Relevant artifacts

| Path:line | Symbol | Purpose |
|---|---|---|
| `transitions.py:181–243` | `TransitionSpec`, `clamp` | the spec and the ranges every knob is clamped to |
| `transitions.py:245–262` | `PRESETS`, `spec_from` | the seven presets; the CLI's arguments override a preset's fields |
| `transitions.py:269–323` | the extension sets, `load_image_rgb` | the readers of the import |
| `transitions.py:813–907` | `dense_displacement` | the class A/B router and the correspondence keys of the report |
| `transitions.py:1114–1261` | the quality basket, `assess`, `goal_numbers` | the `quality` block and its meaning |
| `transitions.py:1421–1454` | `render_pair` | writes `transition.mp4`, `strip.jpg`, `report.json` |
| `transitions.py:1566–1628` | `cmd_pair`, `main` | the CLI; exit 2 with `FAILED:` |
| `transitions_harness.py:319–432` | checks 21–36 | the render bars and the decoded-mp4 observables |
| `reveal.py:1406, 2517–2534` | `export_images`, `cmd_align` | full-resolution stills; exit 2 on a refusal; `metrics.json` last |
| `scripts/bench_transitions.py:38, 105, 215–223, 364–370` | `PAT`, `--max-long`, `preset_legend`, the picks export | the sweep's pair pattern, its 1920 default, the warp legend, the grade shape |
| `scripts/research/director_ui.py:49–50, 430–474` | `LAYERS`, `MATTES`, `start_analyze`, `verdict_text` | the workbench's roots and its relation panel |
| `scripts/research/director_render.py:29, 35–36, 2086–2102` | `ROOT`, `LAYERS`, `MATTES`, the CLI | the two roots and their flags |
| `studio/src/reveal_studio/registry/loop.py:14–24, 27–264` | `K`, `LOOP_STAGES`, `FLOWS` | the shape the pair entries copy |
| `studio/src/reveal_studio/runner/process.py:42–47, 73–148, 155–237, 279` | `IDENTITY`, `start_stage`, `finalize`, `after_done` | loop-only identity and script md5; the refused rule; the round from a page file |
| `studio/src/reveal_studio/runner/argv.py:40–70, 132–262` | `probe_script_flags`, `argv_for` | the loop script's flag probe and argv builder |
| `studio/src/reveal_studio/jobs/candidates.py:15–72, 85–100, 111–131` | `candidates`, `verdicts`, `requests_of` | candidates from `measure.json`; the verdict and answered rules |
| `studio/src/reveal_studio/media/pictures.py:21–34` | `jpeg_thumb` | thumbnails by `cv2.imread` |
| `studio/src/reveal_studio/server/handler.py:140–148` | `_safe_file` | the file route's two bases |
| `studio/src/reveal_studio/config.py:20–53` | the constants, `Settings` | where the new paths and environment names go |
| `studio/src/reveal_studio/cli.py:32, 68, 90` | `common`, `cmd_requests`, `cmd_check` | the flags, the inbox listing, the settings print |
| `studio/Makefile:11` | `.PHONY` | no `requests` target |
| `.claude/hooks/session-start.sh:22, 75–76` | the `compact` exit, the heredoc's end, `exit 0` | where the request line goes |
| `studio/tests/acceptance/test_a1_loop_flow.py:299` | the skeptic request | the source of the stale requests |
| `scripts/research/loop_seq.py:2, 455–457, 611–630, 704–736, 1626–1686` | the docstring, `cmd_prep`, `change_matte`, `frames_chain`, `render_plan` | the still count, the JPEG filter, the matte, the chain and the method dispatch |
| `scripts/research/chain_luma.py:61–63, 282–289, 512–517, 556–568, 583–591, 629–641` | imports, argparse, the light match, the draw | what the repaint leg copies |
| `scripts/research/tr14_variants.py:43–44, 78–83, 111–135` | imports, `changed_mask`, `rank_order`, `reveal_mix` | the two helpers to copy; the Reveal-based mask to replace |
| `.claude/claude-docs/benchmarks/2026-10-09-fabra-boxes.md:22–25, 104–151` | his pick, stages 5–6, his verdict | the repaint's record |
| `benchmarks/runs/2026-10-09/fabra/draw7_3s/aligned/` | 7 JPGs at 1536×1920 | the seven-still test input |

### Constraints discovered

| Constraint | Where | What the phase B build does |
|---|---|---|
| every record's `script_md5` hashes `loop_seq.py` | `runner/process.py:136` | hash the stage's own script, named by its `script` key |
| Settings knows one script, and the flag probe reads `loop_seq.py --help` only | `config.py:28`; `runner/argv.py:40–70` | add the paths of Part 2; probe per script, or skip the probe where the studio uses no added flag |
| `argv_for` is one if/elif over the loop's stage names | `runner/argv.py:132–262` | one argv builder per flow |
| a candidate is a folder with `measure.json`, whose `md5_mp4` it reads | `jobs/candidates.py:29` | a pair branch that reads `report.json` and takes the mp4 md5 from the record |
| the render's identity file is `loop.mp4` | `runner/process.py:44` | `transition.mp4` for the pair flow |
| the frame decode opens `<render>/loop.mp4` | `media/pictures.py` `frames_dir` | the pair's `transition.mp4` |
| thumbnails use `cv2.imread`, which reads no HEIC | `media/pictures.py:21–34`; measured 2026-11-05 | A and B from the relation's strip or mp4 |
| `create_job` takes a folder of JPEGs, and `FLOWS` holds the loop only | `jobs/store.py:67–193`; `registry/loop.py:258` | a `{flow: "pair", a, b}` or `{flow: "pair", fixture}` body, the shape `STUDIO.md §5` names |
| the file route serves the two job folders only | `server/handler.py:140–148` | add `fixtures/` and the two roots, read-only, with tests |
| `transitions.py pair` prints no progress | `transitions.py:1566–1580` | the tile shows the elapsed time; the tool stays unchanged without his word (backlog row T68) |
| the CLI's `--warp` default overrides every preset's `warp_amount` | `transitions.py:258–262, 1569`; the flow-dissolve report on disk | the warp hint says so; a backlog row asks his word on the tool |
| `report.json` holds three clock keys and lacks the preset name and the input paths | `transitions.py:1326, 1442, 1451`; this run | watches compare the mp4 and strip md5s; the record carries the preset and the inputs |
| the class depends on the canvas: 0 inliers at 480 against 6 at 1920 on mismatch_3 | this run; `fixtures/MANIFEST.md` | the relation's class is labelled "at 480 px" |
| Reveal exits 2 for a refusal and for a decode failure and writes no `metrics.json` on either | `reveal.py:2523–2525`; `STUDIO.md §7` | the `FAILED:` text tells them apart |
| the A1 acceptance test leaves one open request per run | `test_a1_loop_flow.py:299` | the test answers it; the 7 existing ones are answered once |
| `uv run` syncs the environment even with `--frozen` | the uv documentation (Context7) | the hook calls the console script |
| `cmd_prep` reads `.jpg` and `.jpeg` only, though its reader decodes HEIC | `loop_seq.py:455` | the fabra originals need a JPEG export, or the `aligned/` JPEGs serve |
| the draw lives inline in `chain_luma.py`'s `main()` | `chain_luma.py:556–568, 583–591, 629–641` | copy it; there is nothing to import |
| a refused or failed record leaves its `.part` folder in place until the stage's next run | `runner/process.py:155–237` (`finalize` renames on done, removes on cancelled and lost); `:109–110` (`start_stage` removes it) | the pair's panels read the record, never a `.part` folder |
| `after_done` runs only from a script record's `finalize` | `runner/process.py:150–153, 279` | factor the round opening out for the builtin page |

### Confidence: 80%

The facts carry file lines, documents or command output from 2026-11-05. The estimates carry their label. They cover the repaint leg's size and hours, the class shift at 480 px on borderline pairs, and the director flags' resolved roots. The request line ran in a scratch copy, never inside the hook.

### Gaps

| Gap | Effect | How to close |
|---|---|---|
| the relation ran once on one pair, mismatch_3; its reproduction is untested | the proposed watch (mp4 25c0f77c…, strip 8bd77a4d…) is one sample | run it twice in the build; harness check 33 argues determinism |
| the uv documentation came through Context7 for the current release; this laptop runs uv 0.7.8, and I ran no uv command | the `--frozen` and `--no-sync` behaviour is UNVERIFIED on 0.7.8 | the proposed line calls no uv, so it stands either way |
| a native (`--max-long 0`) render of a 48 MP HEIC pair was never timed | the cost of `max_long` 0 is unknown | time one in the build, or keep 1920 as the full default |
| DNG and ARW were never decoded from a real file | their rows in the reader table rest on the code | the "Wanted next" line of `fixtures/MANIFEST.md` |
| the studio cannot compare the decoded first and last frames with A and B on the canvas | the endpoint check rests on the report's proxy numbers (0 / 0) | compare with the strip's first and last tiles, with a bar measured first [UNVERIFIED] |
| the repaint leg was never rendered; its zone from `change_matte` differs from chain_luma's zone from Reveal's detector | the zone's share is unknown (chain_luma's seven-still draw: 34.6 % of the canvas) | the seven-still draft in the build |
| tool failures: one `ls` with its flag after the path failed (BSD `ls`); one zsh glob found no `*.json` at the layer root, which is the evidence that the root has no manifest | none on the findings | — |
| the MCP servers claude-design, mcp-memory-service and postgres-mcp failed to connect | unused by this track | — |
| I read `STUDIO.md` §0–§13 and the A2 reports' summaries, not the reports in full | a ruling inside a report could be missed | — |
| the no-slop pass's cold read, a second reader with no session context, was not run; the checker ran clean (0 blocks, 1 advisory: 13 sentences of 26–30 words) | a term only this session knows could remain | the main thread's copy step can run it |
