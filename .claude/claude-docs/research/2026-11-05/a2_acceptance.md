<!-- provenance: copied verbatim on 2026-11-05 from benchmarks/runs/2026-11-05/studio/agents/a2_acceptance.md (gitignored), the report of the phase A2 acceptance driver (Opus 5.5, max effort) of the 2026-11-05 session; a research artifact whose claims carry the author's own confidence and gaps; its screenshots stay under benchmarks/runs/2026-11-05/studio/shots/a2_*.png (gitignored); the main thread filed its three defects (T97–T99) and synced the Makefile and ARCHITECTURE.md the same session -->

<!-- reader: the main thread of the 2026-11-05 studio session, cold; shape: report; written by the A2 acceptance driver (Opus 5.5, max effort) on 2026-11-05 between 02:57 and 03:45. -->

# The studio package passes the acceptance of its second build phase (A2): 12 of 12 checks, three low defects

## Summary

The package reveal-studio 0.2.0 passes all 12 checks of the A2 acceptance drive. The new durable test
`studio/tests/acceptance/test_a2_loop_flow.py` passed three times in 81 to 83 s, the last on the tree as of 03:40. With
the `ecc_refine` ruling deleted in a copy of the package, it fails where intended.

- **Reproduced.** An unchanged copy of the a2 plan, saved in the job, renders a2's md5 of 2026-11-04 (`c302623f…`).
  The ring's stability equals `loopseq_a2.md` section 5: 1.18 px sideways at frame 13, 3.96 px up at frame 26.
- **One check passed with a defect.** In check 6 the inspector showed its Stability section only after a second click
  on the render's card (defect 1).
- **Asked of the main thread.**
  1. File the three defect rows below in `.claude/skills/reveal/references/tracked-backlog.md`.
  2. Update the help line of `make acceptance` and the test-layer table of `studio/ARCHITECTURE.md`. The target now
     runs both acceptance files: about 3 minutes and two new jobs per run.
  3. Add to the hint of the registration's `bg_depth` knob that the angel pair needs `min_inliers` 25. Its far-field
     fit has 31 inliers, below the default floor of 40.
- **Open questions for the owner.** There are none.

## Names used below

| Term | Meaning |
|---|---|
| A1, A2 | the studio's first and second build phases, `.claude/claude-docs/STUDIO.md` §9. The A2 row there lists what the owner must be able to do; the brief turned that list into 12 checks. "The A1 test" is `studio/tests/acceptance/test_a1_loop_flow.py`. |
| the brief | the main thread's task message to this driver |
| the owner, "him" | the repository's owner, who grades the loops |
| the main tree | the working copy of `studio/` in the repository at `/Users/yevhens/Projects/personal/reveal-1.5.0`, as against a scratch copy |
| the critique agent, the reviewer | two other agents of the session. The critique agent runs the detector of impeccable (a UI critique tool that lists anti-patterns) on its own server, port 8397. The reviewer, a Fable model, reviews the page against the hard constraints on port 8399. |
| the owner's jobs | `loop_angel_20261104-220708` (the angel run folder of 2026-11-04, adopted) and `loop_angel_20261104-220719`, under `benchmarks/runs/2026-11-04/studio/`; the brief forbade writing into them |
| the stages | the loop flow's ten steps, a tile each on the strip: import, registration, readers (faces, focus and colour per still), probe, plan, render, measure, skeptic (a request for a subagent's verdict on a render), page, grades (his grade text) |
| the drive job | `loop_angel_20261105-030326`, the job I made from the owner's angel stills under `benchmarks/runs/2026-11-05/studio/` |
| the prep, the recorded prep | the registration's output folder `in/angel/` of a job, with the registered stills `k0.png` and `k1.png`; `benchmarks/runs/2026-11-04/angel/in/angel/`, the prep of 2026-11-04 |
| a2, a full render, a draft | a2 is the angel loop plan the owner accepted on 2026-11-04 (`frozen:angel_a2`); a full render is at the prep's canvas, a draft at a smaller long edge under `drafts/` |
| the breath, `z`, `n`, the local box | keys of the a2 plan: the breath is an effect that pushes the frame in and out once per loop, `z` its size; `n` is a transition's frame count; the local box is a region of a RIFE transition with its own ease (the left mouth) |
| the probe, double-exposure share | `loop_seq.py probe` draws in-betweens of two stills by RIFE (a frame-interpolation model), a morph and a dissolve; the share is the part of a frame that reads as both stills at once |
| the lock | `--lock-window`: three windows on the ring light whose mean offset the registration zeroes |
| fits | the registrations `loop_seq.py prep` made for a frame: `all` (every keypoint), `far` (`--bg-depth`), `ecc`, `final` (the frame as written, after the lock) |
| a ruled value | a knob value the owner ruled out, a row of `registry/rulings.py`; the studio warns and never refuses |
| my server | `uv run reveal-studio serve --port 8398` from the main tree: pid 77974 from 03:02:54, then pid 10449 from 03:27 |
| my Chrome | headless Chrome 156 on DevTools port 9398 (pids 79364, then 10697), driven by Node 22 scripts with real key and mouse events |
| T88 | the backlog row: a server start reconciles the running records of every job, not only its own |

## The 12 checks

Record ids are folders under the drive job's `stages/`. I ran check 4's two registrations before the probe of check 2.
A registration rerun moves the prep, and the probe folder inside it, to `in/angel_prev_<stamp>`.

| # | Check | Verdict | Observed |
|---|---|---|---|
| 1 | The registration and the fits table | PASS | Record `20261105-030326_registration`, 4.6 s: 467 inliers of 751 matches, lock shift (−4.93, +11.48), canvas 1366×1770. `k0.png`, `k1.png` and both depth maps are `cmp`-equal to the recorded prep. The registration panel's table "Windows under each fit" has 10 rows and two fit columns. Ring top: `all` +6.14, −12.59; `final` +1.40, −1.09. The `far` column is absent because the prep made no far-field fit without `--bg-depth`. The panel's canvas line says so in its words, "far-field gate 0" (the `bg_depth` knob at 0). "show windows.jpg" put `windows.jpg` (733×960) in the viewer as A. |
| 2 | The probe at a long edge of 960 | PASS | Record `20261105-030429_probe`, 2.8 s, 740×960, RIFE v4.26. The change matte covers 47.51 % of the frame. Double-exposure share inside it at t 0.25 / 0.5 / 0.75: RIFE 0.0413 / 0.0611 / 0.0341. Morph: 0.0233 / 0.0650 / 0.0245. Dissolve: 0.0012 / 0.2310 / 0.0012. The panel prints them in percent. Three strips of 2232×960 loaded, and 6 rows of face crops at 1:1 (2 faces, 3 methods, 5 cells each). |
| 3 | The plan editor on `frozen:angel_a2` | PASS | Loaded: 4 bars (hold 14, rife 12, hold 12, rife 12), 50 frames. Through the breath's bar and form, `z` went 0.018 → 0.02. Through bar 1's form, `n` went 12 → 14 and the local box's x0 0.26 → 0.27. The counter read 1, 2, then "3 changes from frozen:angel_a2". Undo, undo, redo: 2, 1, 2 changes. Saved as `a2_edit` with "A2 drive: z, n, local". Its provenance lists `/effects/0/z` 0.018 → 0.02 and `/timeline/1/n` 12 → 14; the box edit was undone and is absent. |
| 4 | The rulings | PASS | In the editor I set step 1's method to `slices`. The chip beside the field read "ruled out 2026-11-01: His grade on the first seasons round, eight candidates of diagonal cells: "simple 2d pattern transtions, boring, tasteless and junky"." I undid it without saving. In the inspector I ticked `ecc_refine`. Its chip read "ruled out 2026-11-04: Measured on the angel pair: the masked ECC on the far field left the far field 2–9 px worse." I unticked it without running. The registration with `ecc_refine` true and `bg_depth` 0.15 got a 202 (record `20261105-030403_registration`). Its `warnings` hold one entry: knob `registration.ecc_refine`, value true, since 2026-11-04, source "DECISIONS 2026-11-04; loops.md §2". It ran to done, and its record keeps the warning. The restore with the knobs of check 1 (record `20261105-030408_registration`) gave `final` +1.40, −1.09 again. Its prep is `cmp`-equal to the recorded prep. |
| 5 | An unchanged copy, rendered in full | PASS | `frozen:angel_a2` saved as `a2_copy` with "A2 drive: unchanged": 0 changes. Rendered from the inspector as `a2copy` at draft 0: record `20261105-030817_render`, 62.2 s, `loop.mp4` md5 `c302623f293eacd069218fd7518e0967`. That is the md5 of the full a2 render of 2026-11-04 (`.claude/claude-docs/research/2026-11-04/a1_acceptance.md`, check 6). The record carried 27 progress values, the first "15/50 frames" at 3.3 s. On the page, I read the number during a 960 draft of the same plan (record `20261105-031136_render`). The strip's chip read "running 15/50 frames" 2.0 s in. That draft's md5 `3d453980…` is the 960 draft md5 of 2026-11-04. |
| 6 | The measure | PASS, with defect 1: the section exists and shows the right numbers, but late | Run from the render viewer's control: record `20261105-031011_measure`, 1.9 s, output `angel/a2copy/measures/20261105-031011/measure.json`. Ring top: the largest sideways offset is 1.18 px at frame 13, and the largest vertical one 3.96 px at frame 26. The lowest correlation is 0.987, and no frame peaked on the search border. The md5s of the render's `loop.mp4`, `measure.json`, `frames.json` and `plan.json` match before and after. The render folder gained `measures/` only. The plot under the scrubber labels both maxima, and its cursor follows the scrubber. The inspector's Stability section reads "1.18 px f 13, 3.96 px f 26, 0.987", but only after a second click on the render's card. |
| 7 | Stalls and jumps on `a2copy` | PASS | The inspector's rows read "stalls: none, within" and "jumps: none, within". The plot's legend reads "stalls (band) 0 · jumps (tick) 0". There is nothing to raise with the owner. |
| 8 | The comparator | PASS | Frame 20 (generated, t 0.5554) against `k0.png`. Wipe: B clipped at 50 %, the handle at 50. A/B: the `a` key flipped "showing A" to "showing B" and back. Onion: B at opacity 0.5. Difference: a 1366×1770 canvas labelled "\|A − B\| × 4". Each of the five modes (single and the four above) stayed pressed at 1:1 and 2×. The frame image measured 1366 px wide at 1:1 and 2732 px at 2×, and B or the difference canvas matched it. |
| 9 | The graph view | PASS | The toggle hid the strip and showed 9 nodes: import, registration, probe, plan, render, measure, skeptic, page, grades. Readers appeared, as "not run", only after "add". The 10 lines include registration → probe (`prep.json`, `k0.png`, `k1.png`), registration → render, plan → render, render → measure (`loop.mp4`, `frames.json`) and render → page. A click on the render node put its four knobs in the inspector. "show" on the registration node opened `k0.png` as A. From import, the keys right, down and up reached registration, probe and registration; Enter selected it. From render, down reached measure; Enter selected it. |
| 10 | The page with variants | PASS | `{"variants": ["nope"]}`: 400 "variants: nope is not a full render of this job (the full renders are ['a2copy'])", with `unknown` "nope". It wrote no record and no page. `{"variants": ["a2copy"], "override": true, "footer": "A2 drive"}`: 202, record `20261105-031117_page`, done in 0.2 s; its argv ends `--variants a2copy`. `rounds/1/round.json` holds `variants: ["a2copy"]` and page md5 `220911a3…`. |
| 11 | The strip's branch row | PASS | Probe sits in row 2 under registration, and measure in row 2 under render, at their parents' x and width. From registration, down reached probe, right reached measure, up reached render, down returned to measure, and Enter selected it. Left, then up, led back to registration. |
| 12 | The hints (the detector skipped, as briefed) | PASS | I collected 189 distinct `data-hint` keys over 23 page states. The states: the 10 stage panels (A2 added probe and measure to A1's 8), the 4 compare modes other than single, 7 plan-editor states, the inspector with a ruled knob, the graph. 161 keys are in the `hints` table of `GET /api/registry` (267 keys). The other 28 are built at run time from the same response's `flows`. They are 10 `stage.*` keys and 18 `knob.*` keys (registration 9, render 4, measure 3, probe 2). Every popover resolved; none read "no hint recorded". |

Beyond the brief, the A2 row asks him to compare the three fits. With `bg_depth` 0.15 and `min_inliers` 25 (record
`20261105-032720_registration`) the table drew `all`, `far` and `final` side by side. The windows table in section 3 of
`.claude/claude-docs/research/2026-11-05/loopseq_a2.md` lists nine windows, and their nine `far` cells here equal it
(ring top +5.25, −7.32); it has no row for `mirror_edge`, which reads +1.95, +4.27 under `far`. At the
default floor of 40, the far-field fit had 31 inliers and was rejected. The table then showed `all`, `ecc` and
`final`, and only the record's log said why. A last registration (record `20261105-032745_registration`) left the
drive job's prep `cmp`-equal to the recorded prep.

## Hard constraints

| Constraint | Observed |
|---|---|
| The server answers on 127.0.0.1 only | `lsof` listed my server on 127.0.0.1:8398 alone. I did not repeat the A1 drive's Host-header and LAN probes. |
| The originals are never modified | Both stills keep mtime 1793789339 and their sha256s after the drive and the five test runs (checked at 03:42). |
| Every heavy call runs the main venv's python | `argv[0]` of all 35 records of my six jobs is `/Users/yevhens/Projects/personal/reveal-1.5.0/.venv/bin/python`. |
| I wrote into my own jobs only | `find -newer` (02:57:24) at 03:28 and at 03:42 found 0 files in `loop_angel_20261104-220708`, `benchmarks/runs/2026-11-04/angel`, `models/` and `scripts/research/plans/`. In `loop_angel_20261104-220719` it found two thumbnails in `cache/thumbs/` dated 03:01:41. Another server reading that job wrote them before my server started (03:02:54). |
| T88 | All 35 records of mine lack the note "finished after a restart". The reviewer's server on 8399 started at 03:12:41, while none of my records was running. |
| The package stayed as driven | The md5 listing of `studio/src` and `studio/tests` (71 files at 02:57:24) was unchanged at 03:24, except my new test file. At 03:24:51 and 03:25:10 another writer changed four `source` strings in `registry/rulings.py` and one comment in `runner/lock.py`. Two runs of mine used that code: my second server (pid 10449, 03:27 to 03:28, the three-fit registration and the restore) and the test's rerun at 03:40. The listing stayed the same from 03:28 to the end of that rerun. |

## The durable test

`studio/tests/acceptance/test_a2_loop_flow.py` has 251 lines (md5 `8f540dcb…`) and is marked `acceptance`. It covers
checks 1, 2, 4 (the API half), 5, 6 and 10 in the drive's order, plus the restore and the originals. It reuses the
A1 test's helpers. Command: `cd studio && uv run pytest tests/acceptance/test_a2_loop_flow.py -m acceptance -s -q`.

| Start | Version | Result | Job it made |
|---|---|---|---|
| 03:18:10 | first | PASS in 82.8 s | `loop_angel_20261105-031811` (96 MB) |
| 03:20:54 | mutation: the `ecc_refine` row deleted in a scratch copy of the package | FAIL at the `warnings` assertion in 5.9 s, as intended | `loop_angel_20261105-032054` (24 MB) |
| 03:21:47 | the same mutation, after the cleanup change | FAIL at the same assertion in 5.4 s; its registration ended `cancelled` | `loop_angel_20261105-032147` (24 MB) |
| 03:22:26 | final | PASS in 82.9 s | `loop_angel_20261105-032226` (96 MB) |
| 03:40:11 | final, rerun on the tree after the other writer's change to `registry/rulings.py` | PASS in 81.4 s | `loop_angel_20261105-034012` (96 MB) |

- The cleanup change: the first mutation run left its ruled registration `running` on disk. The test had killed the
  process group, then stopped the server. My server's next read of that job reconciled the record to `lost`. The final
  version cancels through `POST …/stages/<id>/cancel` first; the A1 test keeps the old cleanup (defect 3).
- Lint: `uv run ruff check tests/acceptance` passed, and `uv run ruff format --check tests/acceptance` passed with
  "3 files already formatted".
- Types: `MYPYPATH=src uv run mypy tests/acceptance` found no issues in 3 source files.

## Defects: candidate backlog rows

| # | Severity | Symptom and reproduction | Where (read) | The fix I would make |
|---|---|---|---|---|
| 1 | low | After a measure finishes, the inspector lacks its Stability section until the render's card is clicked again. The plot updates at once. Reproduce: select a render, measure a window from the viewer's control, wait for the plot. The inspector still lists Measures, Provenance, The plan as rendered, Knobs, Latest record, 7 s later too. | `web/js/strip.js:15-16`: `openJob` calls `renderPanel`, then `renderInspector` at once. `web/js/panels.js:69`: `wirePanel` starts the async `loadRender`. `web/js/viewer.js:25`: `loadRender` ends with `renderViewer` only. | End `loadRender` with `renderInspector()` when the stage is render or measure and no inspector field has the focus. |
| 2 | low | A draft render marks the page stale, though a page lists full renders only. Observed: page record `20261105-031117_page`, then the 960 draft `20261105-031136_render`. The page's tile and graph node then read "stale after render". | `views/job.py:277-298`: the stale rule takes every earlier stage that is not a branch as upstream. The render stage's latest record may be a draft. | For the page, compare with the latest full render's record (`draft` 0), or skip draft records as its upstream. |
| 3 | low | The A1 test's cleanup leaves a record `running` on disk when an assertion fails just after a 202. The next acceptance run then waits 5 minutes and skips. The next server that reads the job, or starts, marks the record lost. Seen with the same code in my first mutation run (record `20261105-032059_registration`). | `tests/acceptance/test_a1_loop_flow.py:385-392`: it kills the process group and stops the server before the record is finished. | Cancel each running record through `POST …/stages/<id>/cancel` before stopping the server, as `test_a2_loop_flow.py` does. |

One more observation, not filed: at fit, the picture's width changes from 369.66 px to 367.34 px between compare
modes. The control row above it changes height with the mode.

## Screenshots

All under `benchmarks/runs/2026-11-05/studio/shots/`.

| Check | Files |
|---|---|
| 1 | `a2_c1_fits.png`, `a2_c1_windows_jpg.png`, `a2_c1_three_fits.png` (`all`, `far`, `final`) |
| 2 | `a2_c2_probe_table.png`, `a2_c2_probe_crops.png` |
| 3 | `a2_c3_loaded.png`, `a2_c3_three_changes.png`, `a2_c3_saved.png` |
| 4 | `a2_c4_slices_chip.png`, `a2_c4_ecc_refine_chip.png` |
| 5 | `a2_c5_progress.png` (`a2copy` at 3.3 s, before the page's first poll, so the chip reads "running"), `a2_c5_progress_chip.png` (the 960 draft, "running 15/50 frames") |
| 6, 7 | `a2_c6_stability_plot.png`, `a2_c6_c7_inspector.png` (after the second click) |
| 8 | `a2_c8_wipe50.png`, `a2_c8_ab_showing_B.png`, `a2_c8_onion50.png`, `a2_c8_diff_x4.png`, `a2_c8_diff_1to1.png`, `a2_c8_diff_2x.png`, `a2_c8_wipe_2x.png` |
| 9 | `a2_c9_graph.png`, `a2_c9_show_registration_k0.png`, `a2_c9_graph_readers_added.png` |
| 11 | `a2_c11_strip_branch_row.png` |

## Gaps

- The impeccable detector and a Fable review did not run here; they belong to the critique agent and the reviewer.
- I set the `slices` method, the editor's "start from" select and the graph's "add" select by a script `change`
  event. Every other field, button and key got real input events.
- I did not repeat the A1 drive's outbound-connection samples, playback at 25 fps or marking a frame as a fault.
- The editor's keyboard undo (Cmd-Z) is untested here; the buttons were tested.
- The page's progress number during the full `a2copy` render was not captured; the 960 draft shows it.

## What I wrote, and what is stopped

- Six jobs under `benchmarks/runs/2026-11-05/studio/` (gitignored). `loop_angel_20261105-030326` is the drive job
  (154 MB, with four moved-aside preps). `…031811`, `…032226` and `…034012` are the passing test runs (96 MB each).
  `…032054` and `…032147` are the mutation runs (24 MB each).
- `studio/tests/acceptance/test_a2_loop_flow.py`, new and untracked like the rest of `studio/`.
- This report, and the evidence folder `benchmarks/runs/2026-11-05/studio/agents/a2_acceptance/` (49 entries,
  1.0 MB). It holds the server logs, the API call log, one JSON result per step, the five test outputs, the package
  manifests and the driver scripts under `scripts/`.
- 25 screenshots, `benchmarks/runs/2026-11-05/studio/shots/a2_*.png`.
- In the scratchpad
  `/private/tmp/claude-501/-Users-yevhens-Projects-personal-reveal-1-5-0/d9082b8f-cf5b-4b41-ba3c-c8c2ee5b8bc6/scratchpad/`:
  `a2drive/` (348 MB: the drivers, the Chrome profile and `mut/`, the mutation copy of the package) and `a2drive.lock`
  (my server's lock file, 50 bytes).
- Stopped by SIGTERM to their pids: my servers 77974 and 10449, my Chrome 79364 and 10697. Ports 8398 and 9398 are
  free. The owner's server on 8380 (pid 51553) and the critique agent's server on 8397 (pid 68931) were never touched.
