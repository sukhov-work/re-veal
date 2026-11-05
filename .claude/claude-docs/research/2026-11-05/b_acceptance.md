<!-- provenance: copied verbatim on 2026-11-06 from benchmarks/runs/2026-11-05/studio/agents/b_acceptance.md (gitignored), the phase B acceptance drive through the served page and the API by an Opus 5.5 subagent (max effort) on commit 0a5a260: 53 PASS, 8 FAIL (5 on the build, 3 on the brief's stale counts), 0 BLOCKED over 61 checks; every recorded md5 reproduced; the retirement checklist 15 of 16 rows; eight build defects, which the fix round took; a research artifact whose claims carry the author's own confidence and gaps; the main thread re-ran make qa, make test and the acceptance drives on the final tree before the commit -->

PASS 53 · FAIL 8 · BLOCKED 0, over 61 checks (the 59 rows of the check tables and the two final test runs F1 and F2)

<!-- reader: the main thread and the fix-round builder of phase B, cold. shape: report. Written 2026-11-05 by the phase B acceptance driver (Opus 5.5, max effort) on commit 0a5a260 (tree 4a202bf8), between 21:16 and 22:33; the evidence sits beside it in b_acceptance/ (gitignored). -->

## Phase B acceptance: the director and pair flows reproduce every recorded md5 through the page; five checks fail on the build

The director and pair flows passed their drives through the served page and the API on commit 0a5a260. Every recorded md5 came back: the director drafts 01b3cf3c… and 5b3ee379…, the pair's relation 25c0f77c… and strip 8bd77a4d…, its 1920 render 7262bb06…, and the loop's a2 c302623f… (three runs).

Eight checks fail. Five fail on defects of the build:
- a poll for the previous job lands after a job switch and freezes the page on that job (defect 1, medium);
- the director plan panel scrolls sideways at 1440×900, and the director render's inspector clips its Measures table at 2560 and 1440 px;
- the director grade form starts blank instead of from the last picks file (retirement row 22);
- two controls of the director plan panel carry no hint key.

Three fail on expectations the brief wrote before the build changed them: the number of plots, the number of acceptance files, and the binary `ps` names. A second medium defect surfaced in a test run: when two studio servers watch one record, one can write "lost" over a finished render (defect 2).

Asked of the main thread:
1. File the eight build defects of the defects table; the fix round takes defects 1 and 2 first.
2. Keep `director_ui.py` until retirement row 22 passes, or move the grade form's pre-fill to the drop rows.
3. Commit the two edited acceptance tests and run `make -C studio acceptance` with no other studio server up; run 3 did so and passed 4 in 378.2 s.

Open questions for the owner: none.

| Term | Meaning here |
|---|---|
| the brief | the main thread's task file for this drive, step 2 of the studio build routine (`.claude/skills/reveal/references/studio.md`) |
| the drive | this run: my server on 127.0.0.1:8417 (pid 34367) and my headless Chrome 156 on DevTools port 9417 (pid 34672), driven by Node 22 scripts with real mouse and key events, plus `curl` |
| the director job, the pair job | `director_mismatch_3_20261105-212526` and `pair_mismatch_3_20261105-214138`, the jobs the drive made under `benchmarks/runs/2026-11-05/studio/` |
| builders D, L, P | the phase B builders of the director flow, the loop's repaint leg and the pair flow; their reports `b_director_build.md`, `b_loop_build.md`, `b_pair_build.md` sit beside this file |
| the workbench, U lines | `scripts/research/director_ui.py`, the director page phase B retires; "U 1042–1059" means its lines |
| the retirement checklist | §8 of `b_director_research.md` (beside this file): each workbench function and where the studio must do it |
| decision 2 | `b_design.md` (beside this file), decision 2: the plan stage never fills in the last round's knobs on its own; a button does it on request |
| A1, A2, a2, a2copy | the loop acceptance tests `test_a1_loop_flow.py` and `test_a2_loop_flow.py`; a2 is the angel loop plan `frozen:angel_a2`, a2copy an unchanged copy of it saved in the job |
| class B, saliency-panzoom | `transitions.py`'s class for a pair without a usable homography: each photo pans and zooms about its subject; saliency-panzoom is that method's name |
| skeptic | a Claude subagent that judges each full render; its verdict file under the job's `answers/` lets the page list a render without an override |
| build defect, brief defect | a FAIL caused by the package's code; a FAIL whose expected value in the brief predates the tree |
| T88 | the backlog row: a second studio server re-attaches every running record of the tree |
| a poll | the page's refresh of the open job, every 1 s while a stage runs and every 5 s otherwise (`schedulePoll`, `web/js/core.js`) |
| F1, F2 | the final runs of the two edited acceptance tests, one at a time, counted as checks |

Paths below are under `studio/src/reveal_studio/` when they start with `web/`, `runner/`, `views/` or `server/`.

## The director flow on mismatch_3

| # | Check | Verdict | Observed |
|---|---|---|---|
| D1 | A new director job by pair name from the rail's form | PASS | "new director job…" opened a picker of 6 pairs; the keys `mismatch_3` typed into the focused select picked it. Its line read "A mismatch_3_S.jpg · 75 elements, 43 mattes; B mismatch_3_F.jpg · 56 elements, 51 mattes" with the 5 plans. "create" opened the director job. |
| D2 | The import panel with the layer and matte counts | PASS | A: 75 elements, 43 mattes. B: 56 and 51, without a matte for 9, 19, 24, 26, 32. Element tables of 75 and 56 rows; "Labels in both photos" 6 rows. Overlays at 960×720 on both photos; the opacity slider moved by the arrows (50 to 40). B element 9 showed its hard-mask fallback with a caption saying so. |
| D3 | The resolve of `frozen:mismatch_3_r12` c1: canvases, anchors overlay, layer list | PASS | Record `20261105-212614_resolve`, 8.7 s, with the newest plan and c1 pre-selected. Both canvases 1920×1440; the camera is a homography. The anchors are `{}`, so no anchor circle; the quad is drawn on B. One layer row: pane_becomes_view, keyframe_chain, [0.3, 0.92], inside. Fallbacks mismatch_3_F 19, 24, 26, 32. The folder `resolve/20261105-212614` sits outside `run/`. |
| D4 | `parallax_push` set to 2 in the `--set` table | PASS | Its row (this concept's default 2.5, its condition shown) took End, 3 Backspaces, "2" and Tab. Its "send" box ticked itself. |
| D5 | The `pane_becomes_view` bar dragged to [0.35, 0.97] by real mouse events | PASS | Pressed at the bar's middle, moved 97.6 px (0.05 of the 1952 px timeline) in 14 steps, released: [0.35, 0.97] exactly. Typing was not needed. |
| D6 | The command preview holds exactly two `--set` arguments | PASS | `--set 'pane_becomes_view.window=[0.35, 0.97]' --set parallax_push=2`. The plan opened with an empty set dict, as decision 2 asks. |
| D7 | A 480 px draft with a progress number | PASS | Record `20261105-212821_render`, 18.3 s, tag `two`. The strip chip counted "running 5/90" up to "running 89/90"; the rail read "render · two · 25/90 · 7 s"; 23 distinct texts. |
| D8 | Its md5 01b3cf3c769ee45e44a73f1ade36a3b6 | PASS | The mp4's md5 in the record and on disk. The inputs hold the plan's sha256 adec1345… and the keyframe helper's ecbfa92e…; the script md5 is 05cd6e1d…. |
| D9 | A second draft with the four knobs at 5b3ee379776ae4e8ce2dec4fa3293740 | PASS | `cont_feather` 14 and `front_margin` 0.3 typed into their rows: four `--set`; record `20261105-212955_render`, 15.1 s, md5 5b3ee379776ae4e8ce2dec4fa3293740. |
| D10 | The render panel's measures | PASS | The inspector, draft `two`: motion_median_px 2.37, pauses 4, jumps 0, b_inside_first 84 "within" (bar: at or after frame 31), residual_edge_max 0.09647 "past bar" (0.2 %), halo null, step_first 0.27, step_max 22.38, fallbacks 24, 26, 32. |
| D11 | The three plots on the shared axis | FAIL, brief | 4 plots, against 3 in the brief: motion_px with pauses and jumps, the steps decoded from the mp4, b_inside with its first frame, residual_edges with its 0.2 % bar. Halo is null, so it draws no fifth plot. One axis: at frame 47 the cursor sits at x 1044.43 in all four. §4 of `b_director_research.md` asks for residual_edges too. |
| D12 | A frame marked | PASS | Shift+Right 4 times and Right 7 times reached frame 47; the note typed; the button wrote `owner_frames/draft_mismatch_3_r12_c1-two_f0047.json`, which carries the draft's mp4 md5 01b3cf3c… and the note. A slip of my driver marked frame 36 first. |
| D13 | A page through `director_page.py` behind the gate with an override | PASS | Without the override: "the page is refused: mismatch_3_r12_c1-full (unjudged: no skeptic verdict…)", no record, no `run/index.html`. With it: record `20261105-213617_page`, 0.1 s, md5 d35ba50c63d33e3e7b010bc46ea5c2a0 in `page.md5` and round 1. The override and the typed notes are in the HTML. Its keyframe tile `r10_m3_pane.png` loaded at 1024 px through the file route; builder D had left that tile UNVERIFIED over HTTP. |
| D14 | A grade in the picks shape | PASS | `picks/director_picks_20261105-213708.json`: keys best, clips, date, page. Best `{"mismatch_3_r12": "c1-full"}`, picked by typed keys. The full clip: one_picture true, transforms true, not_invented false, draft false, render `20261105-213215_render`. |
| D15 | The previous page kept beside the record on a rebuild | PASS | The rebuild `20261105-213750_page` opened round 2 at fd703f082ab1f6fc6fab0aac8b62dd69. Its record's `previous_index.html` has md5 d35ba50c…, the first page, and the panel links it. |
| D16 | The durable test, director part | PASS | `studio/.venv/bin/pytest tests/acceptance/test_b_director_flow.py -m acceptance -s -q`, as committed: 1 passed in 150.7 s. The full render ran 102.5 s across a restart, md5 78a58a0c…. |

Also driven, beyond the brief's list:
- the full render from the panel, 146.4 s, md5 78a58a0cc76815078a3e35112869e6eb, builder D's value;
- the re-render button from the draft's record into the tag `two-again`, 14.1 s, 01b3cf3c… again;
- Reveal's verdict on the director job, refused in 11.4 s with its FAILED: line in the panel.

## The pair flow on mismatch_3

| # | Check | Verdict | Observed |
|---|---|---|---|
| P1 | A new pair job from the fixture picker | PASS | "new pair job…" focused a select of 19 pairs and "two photos by path". The keys `mismatch_3` picked it and disabled the two path fields. "create" opened the pair job; the import panel lists both photos with sha256 and their `raw/mismatch_3/` links. |
| P2 | The relation: class B at 480 px, 0 inliers, 24.71 px, the two md5s | PASS | Record `20261105-214140_relation`, 1.9 s: chip "class B at 480 px", saliency-panzoom, 0 inliers, 24.71 px, 480×360, 30 frames. mp4 25c0f77ce05ce8ed53580bb36da24acb, strip 8bd77a4dbbd9763ccd1fd95ca9cdddef. A second run gave both again with the chip "unchanged from 20261105-214140_relation". |
| P3 | The verdict branch on demand, refused with its reason | PASS | Record `20261105-214153_verdict`, 9.0 s, refused. The panel shows "FAILED: Could not find enough common detail between the two photos. They need to show the same scene from roughly the same spot." |
| P4 | A 480 draft of the morph preset, knobs in the inspector | PASS | `name` morph480, `draft` 480 and `seconds` 1 typed into the inspector's fields; `preset` left at morph. Record `20261105-214213_render`, 2.0 s, one `--max-long 480`, mp4 25c0f77c…, the relation's own. |
| P5 | A full render of the morph preset | PASS | `name` morph1920, `draft` 0: record `20261105-214227_render`, 5.9 s, 1920×1440, mp4 7262bb06a58194fe7993e01a1eff1eda. |
| P6 | The viewer: the frames and playback at the spec's fps | PASS | "of 30 · 30 fps"; frames tagged photo, 28 blend, photo; the frame 1920×1440. Playback's interval was 33.3 ms. |
| P7 | The report's numbers and bars | PASS | The 1920 render's report (P5; at 480 px the relation reads 0 inliers): class B, saliency-panzoom, 6 inliers, 121.92 px, certainty 0.5, 30 frames at 30 fps. Frame 0 against A 0, last against B 0, edge ratio 0.1339, flicker max 0.0583: each "within"; 8 rows carry no bar. The decode checks (30 frames, 1920×1440, 30 fps, the darkest frame's level 99 against a bar of 5) each read "within". |
| P8 | A skeptic request | PASS | `requests/skeptic_20261105-214246.json` with its crops (frames 1, 28, 14; steps 0→1 and 28→29) and the answer's shape. `reveal-studio requests` listed it ("1 open request(s)"). After the drive's answer, an empty candidates map, it printed "no open requests". |
| P9 | The studio-written page behind the gate | PASS | Refused first ("the page is refused: morph1920 (unjudged…") with no `index.html`. With a footer, a note and the override: record `20261105-214256_page`, md5 139fc4bf470470fb86b8043b1904a276 in `page.md5` and round 1. Footer, note, override and the mp4's path are in the HTML; `page_A.jpg` and `page_B.jpg` exist. |
| P10 | A grade in the picks shape | PASS | `picks/pair_picks_20261105-214301.json`: best `{"mismatch_3": "morph1920"}` by its radio; one_picture true, transforms false, not_invented true; the typed note. |
| P11 | The durable test | PASS | As committed: 1 passed in 43.4 s. |

## The loop flow

| # | Check | Verdict | Observed |
|---|---|---|---|
| L1 | `make -C studio acceptance`: the A1 and A2 drives with a2 c302623f… | PASS | Three runs. A1: a2 c302623f293eacd069218fd7518e0967 (65.4 s, 62.5 s, 61.3 s), the 960 draft 3d453980…, the 480 draft 2955c25c… re-attached after a restart. A2: a2copy c302623f…; the ring light window drifts 1.18 px at frame 13 and 3.96 px at frame 26. |
| L2 | The same target: 2 passed | FAIL, brief | The target has run four files since 0a5a260: A1, A2, director, pair. Run 1 at 21:47: 3 passed, 1 failed in 394.7 s; the director test failed on an assertion I added (a `..` path answers 403, my test expected 404), since fixed. Run 2 at 21:56: 3 passed, 1 failed in 376.8 s; my drive's server marked the director test's full render "lost" (defect 2). Run 3 at 22:22, with no other studio server up: 4 passed in 378.2 s. |
| L3 | The seven-still job: the import chip and the repaint draft | PASS | `loop_boxes7_20261105-181906`: "7 stills" and the chip "above the longest sequence of the loops work before the studio (6)"; its hint resolves. Builder L's report quotes the earlier wording. The draft `r7`: md5 3feab96cbb06d3be9ae31972f571d01c (builder L's), 112 frames at 25 fps: 37 photo, 75 repaint; stalls [12, 17] and [79, 85]. Frame 12 carries the chips "repaint t 0.0031" and "repaint", both with hints. |

## The retirement checklist

The 15 rows marked "build" and the "decide" row are counted; the 6 "drop" rows are left out, as briefed.

| Workbench function (U lines) | Where the studio does it | Verdict |
|---|---|---|
| 1 the pairs with a plan, layer and matte status (131–147, 950–956) | the director new-job form (`GET /api/pairs`: 6 pairs, each photo's elements and mattes) and the import panel | PASS |
| 2 a job by pair name, both photos hashed (301–314) | the import: links under `raw/`, a sha256 per photo (D1, D2) | PASS |
| 3 Reveal's verdict with its reason; the transitions class (437–473) | the verdict branch of a director job, its FAILED: line in the panel; the class sits in a pair job's relation (P2) | PASS |
| 4 the resolve at job start, newest plan, first concept (447–451) | the resolve stage on request, with the newest plan and its first concept pre-selected (D3) | PASS |
| 5 element tables, labels in both photos (476–509) | the import panel, with the tables of D2 | PASS |
| 6 the four overlays, both-photos toggle, opacity (512–581, 985–999) | the import panel over `/overlay/`: base, elements, disparity, matte_<id> at 960×720, the toggle, the slider | PASS |
| 7 the plan's identity, idea and risk (283–290, 1015–1019) | the plan panel: path, sha256, relation, planner, Idea, Risk | PASS |
| 8 the concept-knob map with read-only reasons (205–252) | the plan panel's knob table in both name forms; read-only rows give their reason | PASS |
| 9 the globals with this concept's defaults (165–187) | the `--set` table: 28 rows, each with this concept's default and its condition | PASS |
| 10 the last round's knobs (decide) | decision 2: an empty set at open; "load the last round's knobs" loaded 3 from `director_r12`; "clear all knobs" emptied it | PASS |
| 11 extra key=JSON lines, the `--set` preview (1034–1040) | the plan panel's text field: a good line reached the preview, a bad one read "not key=JSON: not a line" | PASS |
| 12 the timeline: drag, resize, mute, solo (1042–1059) | drag (D5); a resize by either end (0.92 to 0.90, 0.30 to 0.33); the arrows; mute sends `pane_becomes_view.skip=true`. Solo changes nothing on c1, which has one beat. | PASS |
| 13 draft and full renders with checked inputs (583–637) | the render panel; refused before any record: a key that reaches no frame, an unknown key, 2 frames, a tag with an underscore | PASS |
| 19 the three charts (1083–1099) | the director's series on one axis with the scrubber; the brief's count of 3 against the 4 drawn is D11's failure | PASS |
| 22 the grade form: picks with key checks, pre-filled from the last picks file (688–707, 1108–1130) | the grades panel writes the picks with the key checks (D14). After a reload, round 2's form is blank; round 1's picks file holds the boxes, the note and the best. | FAIL, build (defect 6) |
| 23 files under `fixtures/`, `layers/`, `mattes/` (727–740) | the file route serves the fixtures, the layer tables, the mattes and the plans' helper; repo files, the `raw/` link and `models/` answer 404, a `..` path 403 | PASS |

The rows marked "have" were seen too, uncounted:
- the re-render button, 01b3cf3c… again;
- the progress chip, the log tail, and cancel through the API ("cancelled by you");
- the render rows, and the mp4 under a Range request (206, bytes 0-99/7614562);
- the scrubber, the arrows, the A and B sources and the marked frame.

## The page at three viewports, the hints, the keyboard

| # | Check | Verdict | Observed |
|---|---|---|---|
| V1 | No horizontal scroll at 2560×1440 | FAIL, build (defect 4) | 14 of 15 panels at 0 px. The director render's inspector scrolls 48 px: its Measures table is 351 px wide in the 320 px column, and the verdict column is cut ("withi", "past"). |
| V2 | No horizontal scroll at 1440×900 | FAIL, build (defects 3, 4) | The director plan panel scrolls 78 px and the work column 54 px: its knob table is 910 px wide in an 832 px panel. The render inspector scrolls 48 px, as at 2560. 13 panels at 0 px. |
| V3 | No horizontal scroll at 1280×800 | PASS | 0 px in all 15 panels and both new-job forms; the inspector moves under the work column at this width. |
| V4 | Hints on every new control | FAIL, build (defect 8) | No popover read "no hint recorded" over 15 panels at 3 viewports and the two forms (27 and 31 keys); the director plan panel alone carries 441 hinted elements over 119 keys. Two new controls carry no hint key at all: the folded `<summary>` rows of the `--set` groups. |
| V5 | Tab through the director plan panel | PASS | 67 stops from the plan select to "clear all knobs"; no "?" or chip among them. Each of the 65 with a key opened its hint on focus. A focused bar moved by the arrows: 0.30–0.92 to 0.32–0.93. |
| V6 | Tab through the pair render panel | PASS | 22 controls: source B, two render rows, play, the mark field and button, the scrubber, 14 knob fields, run. Each opened its hint. The walk then reached the inspector's log tail, a scrolling box with no key, and left the page. |
| V7 | Enter on a mode button keeps the focus | PASS | On wipe, 1:1, single and fit, the focus stayed on the pressed button. |
| V8 | The arrows step frames | PASS | From the scrubber: Right, Right, Shift+Right to 12, Left to 11. In the director viewer Shift+Right stopped at frame 89. |
| V9 | 0 console errors | FAIL, build (defect 1) | 0 script exceptions over the drive. Chrome logged two 404s for `/api/jobs/director_…/render/full/morph1920`: a pair render asked for under the director job, by a stale poll. It also logged the 3 409s the drive provoked on purpose. |

## The hard constraints at runtime

| # | Check | Verdict | Observed |
|---|---|---|---|
| H1 | `lsof -p` of the server: 127.0.0.1 only, no outbound socket | PASS | 9 samples during renders (the resolve, two drafts, the full render at its start and at 40 s, two relations, two pair renders): LISTEN 127.0.0.1:8417 and connections from 127.0.0.1 only. `Host: evil.example` got 403; `[::1]:8417` was refused; 192.168.50.46:8417 timed out. |
| H2 | The originals' mtimes and sha256s unchanged | PASS | 666 files, identical by path, size, mtime and sha256 from 21:18 to 22:28, after run 3: the fixtures, the frozen plans, the layer and matte roots, the keyframe helper, the angel and boxes stills. 0 files newer than the drive's start under those roots or `models/`. |
| H3 | Every child is `.venv/bin/python <script>` (`ps`) | FAIL, brief | `ps` shows argv[0] as `/opt/homebrew/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/Resources/Python.app/Contents/MacOS/Python`: the venv's python is a symlink, and macOS's framework build runs that binary. The constraint holds. 10 children sampled, each a child of pid 34367 in its own process group. The 9 checked with `lsof` map 102 to 121 files of the main venv and 0 of `studio/.venv`. Every script record names `<root>/.venv/bin/python`. |
| H4 | A finished render refused a second write | PASS | The tag `two` again from the page: "…mismatch_3_r12_c1-two exists: choose another name (a finished render is never overwritten)". No record was made; the 3 files kept their md5s. |

## Defects found

| # | Class, severity | File | Symptom | Steps to reproduce |
|---|---|---|---|---|
| 1 | build, medium | `web/js/strip.js` (`openJob`), `web/js/core.js` (`schedulePoll`) | A poll's answer for the previous job lands after the switch to another job. The page then draws the previous job under the new one's id, asks a render of one job under the other (404), and stops polling: the stale call cleared the new job's timer. Hit twice in 6 job switches of the viewport drive, with one server. | Open a pair job's render panel. Delay `GET /api/jobs/<pair>` by 800 ms (`drive/v3_race.mjs` wraps `api`), call `openJob(<pair>, true)`, then `openJob(<director>)`. The title reads "mismatch_3 · pair" and the message "no draft render mismatch_3_r12_c1-two-again", still 5.5 s later. A fix: return from `openJob` after its await when `S.jid !== id`. |
| 2 | build, medium | `runner/process.py` (`finalize`) | Two servers finalize one record, and "lost" overwrites "done": `state_lock` is a lock inside one process. One server renamed the `.part` folder and wrote the `done` marker at 22:02:32.305; my drive's server, which had read the record as running, found no terminal file in the vanished `.part` and wrote "lost" at .307. The render is complete in `run/mismatch_3_r12_c1-full/`. T88 is the trigger: a server re-attaches every running record it reads, through `GET /api/jobs` as well as at start. | `make -C studio acceptance` run 2, job `director_mismatch_3_20261105-215955`, record `20261105-220051_render`; `b_acceptance/logs/server1.log` lines 183–190. A fix: before writing "lost", look for the terminal file in `out_final` too and re-read the state. |
| 3 | build, low | `web/js/director.js` (`dKnobTable`), `web/css/director.css` | At 1440×900 the plan panel's knob table is 910 px wide in an 832 px panel. | A director job at 1440×900, the plan stage; `shots/v2_1440x900_director_plan_knobs.png`. |
| 4 | build, low | `web/js/director.js` (`dMeasures`) | In the 320 px inspector the Measures table of a director render is 351 px wide: the verdict column is cut and the inspector scrolls 48 px. | A director render selected at 1440×900 or 2560×1440; `shots/v2_1440x900_director_render_inspector.png`. |
| 5 | build, low | `web/js/director.js` (`dPlot`) | The director plots' y-axis labels are cut at the left: a label wider than the 36 px before the axis loses its first characters, so b_inside's "100.00 %" reads ".00 %". | Any director render at any viewport; the same screenshot. |
| 6 | build, low | `web/js/director.js` (`dGrades`, `dClip`) | The grade form reads only the page's memory, so it starts blank after a reload. The workbench pre-filled it from the newest picks file (U 1113). Retirement row 22. | Grade round 1, rebuild the page, reload, open the grades: round 2's boxes, note and best are empty. |
| 7 | build, low | `runner/process.py` (`finalize`, the refused branch) | A refused stage keeps its `.part` folder: 10 job folders hold a `verdict.part/`. The next run of the stage removes it first, so nothing breaks. | Run the verdict on mismatch_3 in any director or pair job. |
| 8 | build, low | `web/js/director.js` (`dSetTables`) | The two `<summary>` rows of the folded `--set` groups are Tab stops without a hint key; `.claude/conventions/studio.md` asks for a key on every control. | Tab through the director plan panel. |

Not counted as defects:
- The plan panel keeps its set dict in the page's memory, so a reload empties it; builder D lists the missing save control as not done.
- The full director render took 146.4 s at a load average of 3.7 to 5.6. The director research report recorded 32.8 to 66.4 s, and builder D saw 152.6 s at a load of 8.06. Load alone does not account for the gap; the cause is UNVERIFIED.

## The durable tests

I added the API checks of the drive to the two acceptance files; each assertion names the mutation that turns it red. The director file, `tests/acceptance/test_b_director_flow.py`, gained 8 checks:

| Check | Red under |
|---|---|
| a foreign Host header answers 403 | the handler's Host check dropped |
| `GET /api/pairs` lists the pair's 5 plans and both photos' counts | the matte count including `mattes.json` |
| 5 overlay kinds on both photos at 960×720; an unknown kind 404 | the overlay leaving the 960 px scale |
| the canvas thumbnail answers an image | the thumbnail no longer reading `canvas_A.png` |
| Reveal's verdict on a director job is refused with its FAILED: line | the shared stage dropped from the flow |
| a key that reaches no frame, an unknown key and 2 frames answer 400, with no record | `check_set` dropped |
| the page's keyframe tile, fetched over HTTP, equals the helper | the file route's helper rule dropped |
| the file route's bases answer 200, other repo paths 404, `..` 403 | the route serving a repo path |

The pair file, `tests/acceptance/test_b_pair_flow.py`, gained 2 checks. `GET /api/fixtures` must equal the pairs on disk: 19, the seven HEIC fabra pairs and mismatch_7's .jpg and .png included. The request must appear in `reveal-studio requests` before its answer and be gone after. `ruff check`, `ruff format --check` and `MYPYPATH=src mypy --strict` pass on both files.

Two mutations, made in a scratch copy of the package loaded through `PYTHONPATH`, turned the new checks red:
- the fixture scan reading `*_S.jpg` only: the fixture list assertion failed, the fabra pairs missing (0.5 s);
- the render's `check_set` call removed: the refusal assertion failed with 202 against 400 (17.4 s); the test's cleanup cancelled the render it started.

| Run (start) | Files | Result | Jobs made |
|---|---|---|---|
| 21:38:53 | director, as committed | 1 passed, 150.7 s | `director_mismatch_3_20261105-213854` |
| 21:43:22 | pair, as committed | 1 passed, 43.4 s | `pair_mismatch_3_20261105-214322` |
| 21:47:50 | `make -C studio acceptance`, edited files | 3 passed, 1 failed, 394.7 s (my `..` assertion) | `loop_angel_20261105-214751`, `-214934`, `director_mismatch_3_20261105-215100`, `pair_mismatch_3_20261105-215342` |
| 21:56:18, 21:56:27 | the two mutation runs | each failed where intended | `pair_mismatch_3_20261105-215619`, `director_mismatch_3_20261105-215628` |
| 21:56:54 | `make -C studio acceptance`, fixed | 3 passed, 1 failed, 376.8 s (defect 2) | `loop_angel_20261105-215655`, `-215833`, `director_mismatch_3_20261105-215955`, `pair_mismatch_3_20261105-220232` |
| 22:04:55 | F1: the director file alone, final | PASS: 1 passed, 154.1 s, no other server up | `director_mismatch_3_20261105-220456` |
| 22:07:36 | F2: the pair file alone, final | PASS: 1 passed, 38.1 s, no other server up | `pair_mismatch_3_20261105-220737` |
| 22:22:14 | `make -C studio acceptance`, run 3, no other studio server up | 4 passed, 378.2 s | `loop_angel_20261105-222220`, `-222356`, `director_mismatch_3_20261105-222520`, `pair_mismatch_3_20261105-222800` |

## Evidence, processes, what I wrote

The evidence folder `benchmarks/runs/2026-11-05/studio/agents/b_acceptance/` (52 MB, gitignored) holds:
- `drive/`: the 25 scripts: the client `cdp.mjs`, the sampler `sample.mjs`, the director steps `d1` to `d11`, the pair steps `p1`, `p3`, `p4`, the viewport, race and keyboard steps `v1` to `v4`, the retirement steps `r1` and `r2`, `l1_boxes7.mjs`, `manifest.py`, `wait_quiet.mjs`;
- `results/`: one JSON line per check, in `director.jsonl`, `pair.jsonl`, `loop.jsonl`, `retire.jsonl`, `viewports.jsonl`, `keys.jsonl`;
- `logs/`: my server's log, every test run's output, the API checks, the two manifests before and after, the package manifests;
- `shots/`: 68 screenshots.

My processes:
- the server, pid 34367 on 127.0.0.1:8417, with its lock in the session scratchpad;
- its `caffeinate -w`, pid 34368;
- my Chrome, pid 34672.

All three stopped by SIGTERM at 22:04, before the final runs, so my server could not re-attach the tests' records. `scripts/session_sweep.sh` listed 0 session processes at 22:04 and at 22:22. At 22:28 it listed 3, from a `make -C studio qa` another thread of the session started at 22:27; none is mine. The owner's server on 8380 was down the whole time; its lock still names pid 49654. The other agents' servers on 8393 and 8394 were up during parts of my drive and gone by 22:04.

I wrote the two drive jobs (the director job, 100 MB; the pair job, 32 MB), the test runs' jobs of the table, and the two edited test files. Nothing under `studio/src/` changed; the mutated copies sit in the session scratchpad.

## Appendix: the classes of the eight failures, and my own slips

| Failure | Class | Why |
|---|---|---|
| D11, the plot count | brief | the build draws 4 plots by design (§4 of `b_director_research.md`); the brief counted 3 |
| L2, the test count | brief | the target runs 4 files since 0a5a260; run 2's failure is defect 2, with my own server as the second server |
| H3, the `ps` argv[0] | brief | macOS's framework python shows its own binary; the constraint holds |
| row 22, the grade form's pre-fill | build | defect 6 |
| V1, the scroll at 2560×1440 | build | defect 4 |
| V2, the scroll at 1440×900 | build | defects 3 and 4 |
| V4, the hint keys | build | defect 8 |
| V9, the console errors | build | defect 1 |

My slips, each corrected before its check was counted:
- a stepping error marked frame 36 before frame 47;
- my first resize measured the bar before a scroll moved it;
- a wait read a frame image before the viewer drew it;
- my added `..` assertion expected 404, where the handler answers 403 by design (`server/handler.py:173-175`).

Chrome opened a `chrome://settings/help` tab by itself at 21:37; the client now attaches to the studio's tab by its URL.
