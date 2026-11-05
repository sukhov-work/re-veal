<!-- provenance: copied verbatim on 2026-11-06 from benchmarks/runs/2026-11-05/studio/agents/b_fixes.md (gitignored), the fix round of phase B by an Opus 5.5 subagent (max effort) on its own server and headless Chrome: 49 of 50 items fixed (the review's F5, F6, F8, F9; the drive's 8 defects; the critique's P1 by option (a), P2 rows 1 to 9 and the minor rows), every gate green, the detector [] on 39 scans, the keyboard drive 25 of 25; a research artifact whose claims carry the author's own confidence and gaps; the main thread re-ran make qa, make test and the acceptance drives on the final tree before the commit -->

50 items: 49 fixed, 1 left (the critique's minor row 11: the director's list of renders does not show how many of a render's frames a model drew, which needs per-render frame data from the server)

<!-- reader: the main thread of the 2026-11-05 studio session and the owner, both cold. shape: report. Written by the phase B fix-round builder (Opus 5.5, max effort) between 2026-11-05 22:30 and 2026-11-06 00:20. The tree is main at 0a5a260 plus uncommitted changes. My server ran on 127.0.0.1:8431 and my headless Chrome on DevTools port 9431; both are stopped. -->

# Phase B fix round: 49 of 50 items fixed, every gate green, the detector at 0 on 39 scans

**Result.** On the final tree, as of 2026-11-06 00:13:

- `make qa` is green in 121.2 s; `make test` passes 579 tests in 114.2 s.
- The acceptance files pass alone (the director in 158.6 s, the pair in 39.4 s), then `make acceptance` passes 4 of 4 in 372.7 s. Every md5 the earlier runs recorded came back.
- The detector's three URL scans print nothing; its 36 screen scans answer `[]`.
- The keyboard drive passes 25 of 25 checks and the page checks 45 of 45, with 0 hint misses.
- 27 mutations (13 in Python, 14 in the page's scripts and style sheets) each turned a test or check red.

**Asked of the main thread.**

1. Commit the tree, the drive's two acceptance files included.
2. Sync the documents listed in "Documents to sync".
3. File the rows of "What I left" as backlog rows.
4. Remove `scripts/research/director_ui.py` if you rule so: its last function the studio lacked, the grade form pre-filled from the newest picks file (retirement row 22), now works (check C13).

**Open question for the owner**, through the handover: should the director's 16 measures read as words, the file key in parentheses?

## Names used below

| Name | Meaning |
|---|---|
| the brief | the main thread's task file for this round, `brief_fix.md`, with its last section "The main thread's decisions (22:15)" |
| the studio, the three flows | the local page under `studio/` over Reveal's research scripts and tools; its flows are the loop (stills into a looped clip), the pair transition (two photos animated into each other) and the director plan (a planned clip from a fixture pair) |
| a tile, a chip, a knob, the skeptic | a stage's box in the strip at the top; a small state word with a hint; one input of a stage; a request file a Claude session answers with a verdict per render |
| the handover, his words | the session's note to the next session, which carries questions for the owner; the owner's grade text, kept verbatim |
| A1, A2, phase B | the studio's build phases (`STUDIO.md` §9): the shell and the loop flow, the plan editor and the views, then the pair and director flows |
| the review, F5 to F9 | `b_review.md`, the read-only review of phase B by a Fable model, and its findings by id |
| the critique, P1, P2 row n, minor row n | `b_critique.md`, the critique by impeccable's method, which scored the page 26 of 40: its major issue, its nine issues the owner would notice, its 17 minor rows |
| the drive, defect n | `b_acceptance.md`, the acceptance drive through the served page, and the eight build defects of its table "Defects found" |
| the detector; URL scan, CDP scan | impeccable's anti-pattern scanner (`impeccable detect`); a scan where the detector loads the page itself (it opens the newest job), or reads a screen I set up in my Chrome through the DevTools protocol |
| the director job, the pair job, the loop job | `director_mismatch_3_20261105-212526`, `pair_mismatch_3_20261105-214138` and `loop_angel_20261105-045354`: the drive's two jobs and an A2 acceptance job with an ungraded round, read and never written. The fixture pair mismatch_3 has two unrelated photos, so Reveal refuses it, as expected; `mismatch_3_r12_c1` names the frozen plan `mismatch_3_r12` and its concept `c1` |
| the plan panel, the set dict | the director's plan stage panel, which holds the renderer's `--set` overrides as one dict per job in the page's memory |
| the side column | the column beside the viewer's frame: the render's name and modes, the sources A and B, the list of renders |
| the page checks C1 to C16, the keyboard checks K1 to K9 | my drive scripts over real input through DevTools (`checks.mjs`, `keys.mjs`, in the appendix); each prints PASS or FAIL with the observed value. Some ids hold several checks: C1 to C16 make 45, and K1 to K8 at three sizes plus K9 make 25 |
| a mutation | one change that breaks a fix (a line removed or restored to the old code); the test or check named for it must turn red, and the file is restored byte for byte |
| T88, T104, T106, T108 | backlog rows of `references/tracked-backlog.md`: a second server re-attaching another server's records; the review gate's grouped wording; A2's hardening rows; `transitions.py`'s `--warp` overriding every preset's own value |
| the terminal file, `out_final`, to reconcile | the file a stage writes last, which says the run finished (`info.json` for a director render); the stage's final output path, which its `.part` twin is renamed to; what a server does to a `running` record whose process it did not start: watch the process if alive, else finish the record from its files |
| a record, the done marker, an in-place record | one run of a stage, `stages/<id>/stage.json`; the file `done` the runner writes in a record's folder when the run finished; a run whose script writes its output where it stands (`director_page.py`'s `run/index.html`) with no `.part` twin |
| the workbench, the retirement checklist | `scripts/research/director_ui.py`, the director's earlier page; the list in `b_director_research.md` §8 of each workbench function and where the studio does it (row 22: the grade form pre-filled from the newest picks file) |
| a two-server race | two studio servers watching one record (T88): the one that started the process and one that re-attached it after reading the record as running |

## Every item

"Fixed with" points at the row that holds the change. Paths under `studio/src/reveal_studio/`; tests under `studio/tests/`.

| Source | State | File and change | Test or check |
|---|---|---|---|
| review F5, an in-place record across a restart | fixed | `runner/process.py` `finalize`: after a restart a gone page script's record compares its file's mtime with the record's start (`_written_since`); newer is `done` and the page opens its round, older is `lost` | `test_an_in_place_record_after_a_restart_is_done_when_its_file_is_newer_than_its_start` (hand-written records) |
| review F6, the `--set` texts outside the prose test | fixed | `tests/test_prose.py` `sentences()` gains each row's `when`, `readonly` and `default_from`; none blocked at 60 words | `test_no_registry_sentence_blocks_the_prose_checker` |
| review F8, the director page's `variants` knob | fixed | `registry/director.py` drops the knob; `runner/argv_director.py` `argv_page` drops its guard; `views/page.py` reads `stage["knobs"]` | `test_director_flow.py`: the page's four knobs; no `variants` in a page record |
| review F9, three director hints without a source | fixed, and a fourth | `registry/hints_director.py`: `info.step_second`, `info.step_last` and `info.step_max` cite `director_render.py:2014, 2052`; `resolve.front_elements` cites `:713-731` | `test_every_director_measure_hint_names_the_line_it_reads` |
| drive defect 1, a poll answer after a job switch | fixed | `web/js/strip.js` `openJob` returns before it touches the page when the open job changed; `web/js/viewer.js` `loadRender` drops an answer whose job or render changed | C1, C2 |
| drive defect 2, "lost" written over "done" by a second server | fixed | `runner/process.py`: a server reconciling a gone process's record now writes nothing when another server is finishing it. Its evidence (`_finished_elsewhere`): the record's done marker, the terminal file renamed into `out_final` after the record started, or a finished state on disk re-read just before "lost" | `test_a_second_server_never_writes_lost_over_a_record_another_server_finishes` |
| drive defect 3, the plan panel's 910 px knob table at 1440×900 | fixed | `web/css/director.css`: the knob and `--set` tables take fixed columns, long keys and values wrap | the measure table below: 832 of 832 px |
| drive defect 4, the inspector's 351 px Measures table | fixed with P2 row 1 | | 287 px in the 319 px column |
| drive defect 5, the plots' cut y labels | fixed with P2 row 1 | | leftmost label at x 7 (was −22) |
| drive defect 6, the grade form blank after a reload | fixed with P2 row 5 | | C13 |
| drive defect 7, a refused stage's `.part` folder | fixed | `runner/process.py`: the refused branch removes a `.part` inside the runs folder, as a cancel does; the fake `reveal.py` makes its work folder before it refuses, as the real one does | the refusal tests in `test_runner.py` and `test_director_flow.py` |
| drive defect 8, two `<summary>` rows without a hint key | fixed | `web/js/director.js`: each folded group's summary carries `director.set_group` (a new row) | C12 |
| critique P1, two run buttons over two knob sets | fixed, the main thread's option (a): read-only knobs in the inspector, no run button there | `web/js/inspector.js`, the hook only (two comment lines, two code lines, and its `if` turned into `else if`): a flow's `inspectorKnobs` may draw a stage's knob section. `director.js` `dInspector` draws the knobs the panel sends, read-only, with the command, and no run button. `graph.js` "rerun from here" asks the flow's `runKnobs` first, so the graph sends the same knobs | C7, C10 |
| P2 row 1, the measures cut on the plots and in the inspector | fixed | `director.js` `dPlot`: the title, the unit and the plot's one "?" on a line above it; tick labels of at most five characters. `dMeasures`: the verdict and the bar's sentence on a second row | C15 (minor 10); the measure table |
| P2 row 2, no focus ring on a checkbox | fixed | `web/css/studio.css`: `input[type=checkbox]:focus-visible` and the radio's take the 2 px amber ring | C6 |
| P2 row 3, ten buttons that fire twice | fixed: 24 buttons use the helper, 16 of them driven | `web/js/core.js` `busy(btn, fn)`: "working…" and a second press ignored until the request settles; the button keeps its focus. Used by the director's resolve, verdict, draft, full, re-render, skeptic, page and grade buttons, the pair's relation, verdict, skeptic, page, grade and skip buttons, the rail's four create buttons, the loop's page, grade, skip, plan save and skeptic buttons, and the viewer's mark button | C3 (16 of 16) |
| P2 row 4, the director's frame small at 1440 and 1280 | fixed | `director.js` `dRenderCtl`: the next render's controls, the `--set` line and the re-render button sit in the side column under the renders; `viewer.js` gains the `vside` and `wireSide` hooks that draw and wire them | the measure table: the scrubber inside the window at 1280×800 |
| P2 row 5, the grade form over renders the page never showed | fixed | `director.js` `dGrades`: every round, newest first; a graded round read-only with its picks; an ungraded round's form over that round's renders, pre-filled once from the newest picks file (boxes, notes, best; never his words) | C13 |
| P2 row 6, the poll's late answer | fixed with defect 1 | | C1, C2 |
| P2 row 7, the timeline below the planner's prose | fixed | `director.js` `dPlan`: the timeline, the knob table, the command and the set-dict buttons first; the Idea and Risk in a closed `<details>` last | C12 |
| P2 row 8, the timeline's keys, undo and "clear" | fixed | `director.js`: Alt with the arrows moves a window's start, Page Up and Page Down move it by 0.1; Cmd-Z and Shift-Cmd-Z undo and redo the set dict (300 steps); "clear all knobs" asks first, "no" focused, Escape answers no | C8 |
| P2 row 9, 137 Tab stops on the import | fixed | `director.js` `dElements`: one Tab stop per element table; up and down move between rows | C9: 8 stops |
| minor row 1, two new-job forms at once | fixed | `web/js/rail.js` `closeForms()`, called by every opener; `director.js` `dNewJob` appends its own form, so the pair's form survives; a heading per form (`index.html`, `pair.js`, `director.js`) | C11 |
| minor row 2, a bar's drag without `pointercancel` | fixed | `director.js` `dDragCancel` on `pointercancel` and `lostpointercapture` | C5 |
| minor row 3, the angel example in the director's skeptic form | fixed | `web/js/panels.js`: the placeholder comes from the flow; the loop keeps its own, the director shows none | C15 |
| minor row 4, the loop's `--variants` wording on the pair page | fixed | `web/js/plan.js` `variantsControl`: a builtin page's sentence names no flag | C14 |
| minor row 5, the pair's refusal three times | fixed | `views/pair.py` and `views/director.py`: a refused verdict's tile carries no reason for the panel head; the panel's box prints it once | `test_the_verdict_view_shows_the_refusal_and_its_reason`, `test_a_refused_verdict_shows_its_reason_once_and_keeps_no_part_folder`; C14 |
| minor row 6, no run button on the director's verdict | fixed | `director.js` `dVerdict`: the pair panel's button and wording | C15 |
| minor row 7, the pair's source B at frame 0 | fixed | `web/js/pair.js`: source B starts at the render's last frame | C14 |
| minor row 8, an emptied title refilled by the poll | fixed | `panels.js` `restoreForms` restores an empty value too | C4 |
| minor row 9, the director page's white iframe | fixed | `director.js` `dPage`: the pair's `pair-frame` class | C15 |
| minor row 10, four "?" in a row under the plots | fixed with P2 row 1 | | C15 |
| minor row 11, no generated share on the director's render rows | left | see "What I left" | none |
| minor row 12, a green "answered" over unjudged renders | fixed | `views/base.py` `skeptic_state`: an answer naming no verdict reads "answered (0 verdicts)" in a muted chip with the hint `chip.answered`; the pair and director tiles use it | `test_the_skeptic_request_carries_the_pairs_crops` (extended) |
| minor row 13, the plan tile's "none" | fixed | `views/director.py` `tile_plan`: "5 plans", its hint key `director.plans` (a new row) passed to the chip as `chip_key` by `strip.js`, `graph.js` and `panels.js` | `test_a_director_jobs_view_carries_its_keys_and_tiles` (extended); C15 |
| minor row 14, "1 candidates" | fixed | `rail.js`: the singular for one | C15 |
| minor row 15, two checkboxes in a boolean `--set` row | fixed | `director.js` `dSetInput`: a true or false select; `dReadSet` reads it | C12 |
| minor row 16, knob keys in the pair's empty render sentence | fixed | `pair.js` `pairRender`: "render a 480 px draft, or the full size at 1920 px" | none: a pair job without a render is not on disk; the sentence is a literal |
| minor row 17, an amber edge on a selected element row | fixed | `director.css`: the raised face alone | C15 |
| the detector, `line-length` twice on the plan panel | fixed | `director.css`: the planner's paragraphs at 50ch, a rule that now outranks `.panel p.muted`'s 62ch; two new findings that appeared midway, the knob table's sentence column and the verdict panel's sentence, fixed the same way | 0 on 39 scans |
| the copy pass, five sentences over 40 words | fixed | `registry/hints.py`: `region.viewer`, `region.axis`, `region.inspector`, `control.render`; `registry/director.py`: the skeptic stage. Also over 40 and split: `control.page`, `prep.windows_jpg` and the two `plan.timeline.slide` rows | `test_no_hint_or_phase_b_sentence_runs_over_40_words` |
| the copy pass, script lines cited in 18 `--set` rows | fixed in 16 of 18 rows; the 2 kept are in "What I left" | `registry/director.py`: the lines move to the rows' `read_at` and `source`, which the hint prints; the read-only reasons of `pane.edge` and `pane.rate` keep `SCHEMA.md:221` and `:222`, the lines of the plan grammar that list those keys as knobs, which the reasons say reach no frame; four tests pin the citation | `test_prose.py` |
| the copy pass, "Exit 2 with a FAILED: line" and two pair hints | fixed | `registry/common.py`, `registry/hints_pair.py`: the refusal in words | `test_prose.py` |
| the copy pass, inline citations in hints | fixed | "(backlog T108)", "(loops.md §6)" and three "(TRANSITIONS.md §3; --help gives no sentence)" move to code comments | `test_pair_flow.py` pins T108's absence |
| the copy pass, "= n_frames 90" and "0..1 grey" | fixed | `views/pair.py`: the decode rows read "the report's 90 frames"; the units, three hints and the pair plot's title read "grey from 0 to 1" | none: literals |
| the clarify pass, three times the records contradict | fixed | `hints_director.py`: a draft 14 to 18 s, a full render about 150 s (146 to 153 s), the resolve about 9 s; `hints_pair.py`: the verdict 2 to 18 s; dated 2026-11-05 | `test_prose.py` |
| the clarify pass, two hints that leave part out | fixed | `control.director_timeline` names every key; `control.director_clear` names the extra lines and the confirmation | `test_prose.py` |
| the clarify pass, the empty-pair refusal | fixed | `jobs/store.py`: "choose a pair: a director job starts from a fixture pair that a plan names" | `test_a_director_job_needs_a_plan_and_makes_no_folder_without_one` |
| the harden rows: double press, drag, typed form | fixed with P2 row 3, minor row 2, minor row 8 | | C3, C5, C4 |
| backlog T106, raised again for the buttons and the wipe drag | fixed: the two parts raised again | `viewer.js`: the wipe drag ends on `pointercancel` and `lostpointercapture`; the buttons with P2 row 3 | C3 |

## The gates

Run from `studio/` on the final tree, after my server and Chrome were stopped, under `caffeinate -i`.

| Gate | Command | Result | Wall time |
|---|---|---|---|
| qa | `make qa`: ruff check and format, mypy strict over 55 files, the unit tests, vulture, deptry, pip-audit, 3 import contracts, the prose checker over the three docs | exit 0; 555 unit tests passed (550 at the start: 5 added) | 121.2 s |
| test | `make test` | 579 passed; the 5 acceptance tests deselected | 114.2 s |
| acceptance, the director file alone | `.venv/bin/pytest tests/acceptance/test_b_director_flow.py -m acceptance -s` | 1 passed | 158.6 s |
| acceptance, the pair file alone | `.venv/bin/pytest tests/acceptance/test_b_pair_flow.py -m acceptance -s` | 1 passed | 39.4 s |
| acceptance, the four drives | `make acceptance` | 4 passed: A1, A2, the director and the pair | 372.7 s |
| syntax | `node --check` on the 11 scripts of `web/js/` | 11 clean | not timed |

The baseline `make qa` on the untouched tree ran at the start: exit 0, 550 unit tests, 115.7 s.

## The acceptance values

| Drive | Job | Values |
|---|---|---|
| director, alone | `director_mismatch_3_20261106-000000` | the two-knob draft `01b3cf3c769ee45e44a73f1ade36a3b6` in 13.7 s; the four-knob draft `5b3ee379776ae4e8ce2dec4fa3293740` in 11.0 s; the re-render `01b3cf3c…` again; the full render `78a58a0cc76815078a3e35112869e6eb` in 98.5 s across a restart; Reveal's verdict refused in 9.4 s, no `verdict.part` left |
| pair, alone | `pair_mismatch_3_20261106-000413` | the relation's mp4 `25c0f77ce05ce8ed53580bb36da24acb` and its rerun "unchanged"; the full render `7262bb06a58194fe7993e01a1eff1eda`; the verdict refused in 5.1 s with "the .part folder was removed"; a render re-attached after a restart |
| `make acceptance`, the loop's A1 drive | `loop_angel_20261106-000624` | the a2 render `c302623f293eacd069218fd7518e0967` in 60.5 s; the 960 draft `3d453980f80eff43014646a6f65398a6`; the 480 draft `2955c25c2611565b3ee57d2d081f8669` re-attached after a restart |
| `make acceptance`, the loop's A2 drive | `loop_angel_20261106-000759` | the a2 copy `c302623f…` in 60.9 s; the ring's stability 1.18 px at frame 13 and 3.96 px at frame 26 |
| `make acceptance`, the director drive | `director_mismatch_3_20261106-000921` | `01b3cf3c…` in 13.9 s, `5b3ee379…` in 11.2 s, the re-render `01b3cf3c…` again, the full render `78a58a0c…` in 99.8 s across a restart |
| `make acceptance`, the pair drive | `pair_mismatch_3_20261106-001156` | the relation `25c0f77c…`, the full render `7262bb06…`, a render re-attached after a restart |

None of the six jobs holds a running, cancelling or lost record. The date changed during the runs, so the jobs sit under `benchmarks/runs/2026-11-06/studio/`.

## The detector

The final run, on the final tree: `impeccable detect --no-advisory`, with `IMPECCABLE_BIN` set as step 4 of the build routine (`references/studio.md`) states, against my server.

| Scan | 2560×1440 | 1440×900 | 1280×800 |
|---|---|---|---|
| URL scan (the newest job) | exit 0, no output; `--json` `[]` | the same | the same |
| CDP scans of 12 screens: the director's plan, the plan with its folded groups open, render, resolve, import, grades and verdict; the pair's relation, render and verdict; the rail with the director's form; the director's graph | 12 × `[]` | 12 × `[]` | 12 × `[]` |

No `.impeccable/` folder exists after the scans. Midway the scans still found the planner's Risk paragraph at 86 characters a line, because `.panel p.muted` (62ch) outranked `.d-prose` (56ch then, 50ch now). They also found two new ones: the knob table's sentence column, widened by its fixed layout, and the verdict panel's sentence at 86 characters a line. All three are fixed.

## The keyboard pass

`keys.mjs` sends real key events through DevTools; 25 of 25 checks pass.

| Check | 2560×1440 | 1440×900 | 1280×800 |
|---|---|---|---|
| director plan panel: Tab stops from the plan select to the panel's end, none a "?" or a chip | 67 | 67 | 67 |
| every stop carries a hint key that resolves and opens its hint on keyboard focus | 67 of 67 | 67 of 67 | 67 of 67 |
| the walk reaches the timeline's 2 bars and the 3 folded groups | yes | yes | yes |
| pair render panel: Tab stops from the zoom buttons to the panel's end, none a "?" or a chip; each opens its hint | 17 | 17 | 17 |
| on the scrubber: right steps 1 frame, Shift+right 10; Space plays and pauses | yes | yes | yes |
| Enter on "wipe" keeps the focus; the wipe handle moves 1 % by the arrows | yes | yes | yes |

The critique counted 66 stops on the director plan with its groups closed; the 67th is the new fold of the planner's Idea and Risk. The drive's pair walk (24 stops) ran a different span, from source B into the inspector's knob fields, so the two counts do not compare.

The page checks (`checks.mjs`, 45 of 45) add the hint audit over 69 screens: the 19 stages of the three jobs and the 4 new-job forms, at each size. They found 2,826 hint keys in use, 0 misses, 0 chips without a hint, 0 controls without a key and 0 page exceptions.

## The tests added, each with its mutation shown red once

The Python tests, run through `mutate.py` (apply, run the named test, restore the file and check its md5):

| Test (`studio/tests/`) | Mutation | Red |
|---|---|---|
| `test_runner.py::test_an_in_place_record_after_a_restart_is_done_when_its_file_is_newer_than_its_start` | `have = False`, the old rule for an in-place record | 1 failed |
| the same test | the done-marker return removed (a second server would open a second round) | 1 failed |
| `test_runner.py::test_a_second_server_never_writes_lost_over_a_record_another_server_finishes` | `_finished_elsewhere` without its `out_final` check | 1 failed |
| `test_runner.py::test_a_verdict_refusal_is_refused_with_reveals_failed_line` (extended) | the refused branch keeping its `.part` folder | 1 failed |
| `test_director_flow.py::test_the_page_runs_in_place_behind_the_gate_and_keeps_the_previous_page` (extended) | `build_page` passing `variants` to every flow | 1 failed |
| `test_director_flow.py::test_every_director_measure_hint_names_the_line_it_reads` | `info.step_last` without its source | 1 failed |
| `test_director_flow.py::test_a_refused_verdict_shows_its_reason_once_and_keeps_no_part_folder` | the director's verdict tile keeping its reason | 1 failed |
| `test_director_flow.py::test_a_director_jobs_view_carries_its_keys_and_tiles` (extended) | the plan tile's old "saved" or "none" | 1 failed |
| `test_pair_flow.py::test_the_skeptic_request_carries_the_pairs_crops` (extended) | every answer read as "answered" | 1 failed |
| `test_pair_flow.py::test_the_verdict_view_shows_the_refusal_and_its_reason` (extended) | the pair's verdict tile keeping its reason | 1 failed |
| `test_prose.py::test_no_registry_sentence_blocks_the_prose_checker` | a hedge ("should work") in a `default_from` text, which no hint carries | 1 failed |
| `test_prose.py::test_no_hint_or_phase_b_sentence_runs_over_40_words` | `region.viewer`'s 54-word sentence put back | 1 failed |
| `test_jobs.py::test_a_director_job_needs_a_plan_and_makes_no_folder_without_one` (a row) | the old refusal for an empty pair | 1 failed |

The page's scripts and style sheets, run through `mutjs.py` (apply to the served file, reload, run the named check, restore and check the md5). The checks are drive scripts in my scratchpad, not repo tests: the package has no browser driver, and adding one is a dependency decision.

| Check | Mutation | Red, the observed value |
|---|---|---|
| C1 | `openJob` without its return for a job the page left | the title "mismatch_3 · pair" under the director job's id |
| C2 | `loadRender` without its check | the full render shown though the draft `two` was chosen after it |
| C3 | `busy` without its second-press guard | 2 posts from one double press of "resolve" |
| C4 | `restoreForms` skipping an empty value again | the title back as "mismatch_3: round 2" |
| C5 | the bar's `pointercancel` handler removed | the bar moved from 30 % to 36 % after the cancel |
| C6 | the checkbox ring's rule removed | outline `none` on the focused checkbox |
| C7 | the director's `inspectorKnobs` removed | the inspector's run button back, two amber buttons |
| C8 | Alt read as a plain arrow | the window's end moved with its start |
| C8 | "clear all knobs" clearing without asking | no "yes, clear" button; the set dict emptied at once |
| C9 | every element row a Tab stop again | 137 stops |
| C10 | the director's `runKnobs` removed | the graph sent the last run's knobs: no tag, no `--set` key |
| C11 | `closeForms` leaving `#flowForms` open | two forms shown at once |
| C13 | the grade form's seeding removed | 0 boxes ticked, an empty note |
| C14 | the pair's source B default removed | source B at frame 0, photo A |

The first run of the "clear" mutation read green: under it the check crashed on the missing "yes, clear" button, and my runner then counted only FAIL lines. The runner now counts a crash as red, the check reports a FAIL instead of throwing, and the rerun is red.

## The screens before and after

Measured by `measure.mjs` in my Chrome on the director job's full render `mismatch_3_r12_c1-full` (1920×1440) and its plan panel, before the first edit and on the final tree. "On screen" means the scrubber's bottom lies inside the window.

| Screen | Size | Before | After |
|---|---|---|---|
| director render: the frame box's height · the picture's share of its source height · the scrubber's bottom | 2560×1440 | box 781 px · 54.0 % · y 1302 | box 853 px · 59.0 % · y 1296 |
| the same | 1440×900 | box 320 px · 21.9 % · y 892 | box 434 px · 26.6 % · y 892 |
| the same | 1280×800 | box 240 px (the floor) · 16.4 % · y 813, below the 800 px window | box 334 px · 22.9 % · y 792, on screen |
| director render: the inspector's width and its Measures table | 2560×1440, 1440×900 | 367 px of content in a 319 px column; the table 351 px | 319 of 319 px; two tables of 287 px |
| director render: the plots' leftmost y label | every size | x −15, 7, −22, −7 (cut) | x 7 on all four plots |
| director render: amber buttons on the screen | every size | two: "render a 480 draft" and the inspector's run button | one: "render a 480 draft" |
| director plan: the knob table in the panel | 1440×900 | 910 px in 832 px; the third `--set` table 923 px | 832 px; every table 832 px |
| director plan: the timeline's top · the command's top, in the panel's scroll | 2560×1440 | y 1065 · y 2728 | y 671 · y 1089 |
| the same | 1440×900 | y 1079 · y 3934 | y 686 · y 1348 |
| the same | 1280×800 | y 1079 · y 3218 | y 686 · y 1216 |
| director import: Tab stops inside the panel | every size | 137 | 8 |
| director grades: the clips of round 2's form | every size | 4: the full render and three drafts the page never showed | 1: the full render, pre-filled from round 1's picks |
| pair render: source B | every size | frame 0, photo A | the last frame, photo B |

At 1440×900, with four renders listed, the next render's controls and the amber "render a 480 draft" sit below the list, inside the side column's own scroll; at 2560×1440 all of it shows (the final screenshots). The critique named this place, under the renders; a long list of drafts pushes the button further down.

A sideways-scroll scan of all 15 director and pair stages at the three sizes (`hscroll.mjs`) finds 0 px on `#work`, `#panel` and `#inspector` on the final tree. Midway it found the director's grades panel 111 px too wide at 1440×900, from the graded round's picks table; fixed columns cure it.

## What I left, and why (candidate backlog rows)

The first row is the one item of the 50 left. The other rows are residual risks of my changes and findings outside the brief's list.

| Source | What | Why it is left |
|---|---|---|
| critique minor row 11 | the director's render rows show no generated share (55 of the full render's 90 frames are generated) | a candidate carries no frame tags; the share needs each render's keyframe windows computed on the server for the job view, more than the two lines the brief allows |
| the copy pass, beyond the five | six loop sentences over 40 words: the registration's `windows` knob, the readers, the probe (two), the render and the skeptic stages | `tests/test_loop_snapshot.py` pins their digest and is never regenerated; the 40-word test skips the loop's stage and knob sentences for that reason |
| the copy pass | the read-only reasons of `pane.edge` and `pane.rate` still cite `SCHEMA.md:221` and `:222` | they name the grammar line that lists a knob reaching no frame; four tests pin the citation |
| drive defect 2, the rest of T88 | two servers that both find the `.part` before either renames it can both finalize the record; a page record could then open two rounds | the window is the milliseconds between one server's read of the record and its done marker; closing it needs a lock across processes (a lock file per record), a runner change beyond this round |
| drive defect 2, the crash window it moves | a finalizer that dies after its rename or its done marker and before its record write now leaves the record `running` at every later reconcile, where the old code wrote `lost`; the rail then lists a dead process as running, a restart does not clear it, and a registration waits on it | the window is the microseconds between those writes. A time bound closes it: defer only while the done marker or the renamed file is under a minute old, then finalize as usual. A lock file per record would close it too. Both change the runner beyond this round |
| backlog T106, the parts not raised again | the m key marks a fault frame that no route removes; a probe of many pairs runs to 4,264 px | the critique did not raise them; untouched |
| backlog T104 | the review gate's grouped wording | the critique did not raise it; untouched |
| the critique's harden row "long values" | the import's cell of 32 element ids, the loop inspector's plan select cut at "frozen:mismatch_" | outside the brief's three harden rows; untouched |
| the critique's question 3 | the director's measures named by their `info.json` keys | the main thread's ruling: the owner's question, through the handover |

## Documents to sync

I edited none of these; the brief reserves them for the doc-sync writer. One pinned value I did update, in a test: the loop hints' digest in `studio/tests/test_registry.py` moved to `9af43c6c9d8c8c39`, and the comment above it names the ten rows that moved; the loop snapshot test is untouched.

| Document | What changed in the code |
|---|---|
| `.claude/conventions/contracts.md` | a stage view may carry `chip_key`, the hint key of its state chip (the director plan tile: "5 plans", `director.plans`); the two-photo skeptic tile reads "answered (0 verdicts)" when the answer names no verdict; a refused verdict's tile carries `reason: null` |
| `STUDIO.md §4`, `conventions/studio.md` | the restart rule: an in-place record is done when its file is newer than its start (review F5); a reconciled record leaves a record with a done marker, or a terminal file renamed into `out_final` after its start, to the server that finalizes it; a refused stage's `.part` folder is removed |
| `studio/ARCHITECTURE.md` | `runner.process`: `_written_since`, `Runner._finished_elsewhere`; `views.base.skeptic_state`; `core.js` `busy`; the `FLOW_UI` hooks `inspectorKnobs`, `runKnobs`, `vside`, `wireSide` and `skepticPlaceholder`; `rail.js` `closeForms`; 555 unit tests, 579 in `make test`; 559 hint rows (the director's 196); the prose test's second check at 40 words |
| `.claude/conventions/studio.md` | a button inert while its request runs (`busy`), keeping its focus; the hints and the phase B sentences held to 40 words a sentence |
| `studio/GUIDE.md` | the director's timeline keys (Alt with the arrows, Page Up and Page Down, Cmd-Z and Shift-Cmd-Z); "clear all knobs" asks first; the next render's controls in the side column; the inspector's read-only knobs for the resolve and the render; one grade form per round, pre-filled from the newest picks file |
| `references/tracked-backlog.md` | the rows of "What I left"; T106's buttons and wipe drag done |
| `DECISIONS.md`, the phase B line's `[revert: …]` | a clean revert of the commit restores the earlier tree; `tests/test_loop_snapshot.py` is untouched; the comment above the loop hints' digest in `test_registry.py` names the ten rows that moved |

## The prose pass

- The registry's sentences: `tests/test_prose.py` runs the checker over every hint, stage, flow, knob and `--set` sentence at 60 words, and over the hints and the phase B sentences at 40 words; both pass.
- The page's new literal sentences, 44 of them from `director.js`, `pair.js`, `plan.js`, `rail.js`, `index.html`, `views/base.py` and `views/pair.py`, went through the checker once at 40 words: 0 blocks, 0 advisories (`out/page_sentences.md`).
- This report: the checker gives 0 blocks; a cold read by a subagent with no session context, whose findings I applied.

## Appendix: what I ran and what I wrote

- My server: `studio/.venv/bin/reveal-studio serve --port 8431 --no-browser --lock <scratchpad>/fix/fix.lock` under `caffeinate -i`, pid 3147, then pid 15123 after the Python changes. Its log holds its two start lines and nothing else: no record was started, since every request a check provoked was held inside the page. My Chrome: headless on DevTools port 9431, pid 3210. Both stopped before the gates; `scripts/session_sweep.sh` then listed 0 session processes. The owner's port 8380 was never addressed.
- The drive scripts sit in `/private/tmp/claude-501/-Users-yevhens-Projects-personal-reveal-1-5-0/9041ff2b-bcdd-448e-b55d-c8250e7a4b44/scratchpad/fix/`: `cdp.mjs`, `measure.mjs`, `hscroll.mjs`, `scan.mjs`, `checks.mjs`, `keys.mjs`, `mutate.py`, `mutjs.py` and `mutall.py`. Their results are under `out/` and the logs under `logs/`. 18 screenshots under `shots/` show the director render and plan panels at the three sizes: `before_`, `after1_` (midway) and `final_`.
- Jobs I made: none by hand. The acceptance runs made theirs under `benchmarks/runs/2026-11-06/studio/`.
- Files changed, under `studio/src/reveal_studio/`: `jobs/store.py`, `registry/common.py`, `registry/director.py`, `registry/hints.py`, `registry/hints_director.py`, `registry/hints_pair.py`, `registry/pair.py`, `runner/argv_director.py`, `runner/process.py`, `views/base.py`, `views/director.py`, `views/page.py`, `views/pair.py`, `web/index.html`, `web/css/director.css`, `web/css/studio.css`, and `web/js/` `core.js`, `director.js`, `graph.js`, `inspector.js` (the hook only), `pair.js`, `panels.js`, `plan.js`, `rail.js`, `strip.js`, `viewer.js`. Under `studio/tests/`: `fakes/reveal.py`, `test_director_flow.py`, `test_jobs.py`, `test_pair_flow.py`, `test_prose.py`, `test_registry.py`, `test_runner.py`, `test_views.py`. The acceptance files are the driver's edits, untouched by me.
- `studio/src/reveal_studio/__init__.py` shows a docstring change from 22:27, before my first edit: the doc-sync writer's, not mine.

## git status at the end

```
 M .claude/claude-docs/EXPLORATION_PLAN.md
 M .claude/claude-docs/STUDIO.md
 M .claude/claude-docs/research/director-tooling.md
 M .claude/conventions/contracts.md
 M .claude/conventions/studio.md
 M .claude/skills/reveal/references/tracked-backlog.md
 M studio/ARCHITECTURE.md
 M studio/GUIDE.md
 M studio/README.md
 M studio/pyproject.toml
 M studio/src/reveal_studio/__init__.py
 M studio/src/reveal_studio/jobs/store.py
 M studio/src/reveal_studio/registry/common.py
 M studio/src/reveal_studio/registry/director.py
 M studio/src/reveal_studio/registry/hints.py
 M studio/src/reveal_studio/registry/hints_director.py
 M studio/src/reveal_studio/registry/hints_pair.py
 M studio/src/reveal_studio/registry/pair.py
 M studio/src/reveal_studio/runner/argv_director.py
 M studio/src/reveal_studio/runner/process.py
 M studio/src/reveal_studio/views/base.py
 M studio/src/reveal_studio/views/director.py
 M studio/src/reveal_studio/views/page.py
 M studio/src/reveal_studio/views/pair.py
 M studio/src/reveal_studio/web/css/director.css
 M studio/src/reveal_studio/web/css/studio.css
 M studio/src/reveal_studio/web/index.html
 M studio/src/reveal_studio/web/js/core.js
 M studio/src/reveal_studio/web/js/director.js
 M studio/src/reveal_studio/web/js/graph.js
 M studio/src/reveal_studio/web/js/inspector.js
 M studio/src/reveal_studio/web/js/pair.js
 M studio/src/reveal_studio/web/js/panels.js
 M studio/src/reveal_studio/web/js/plan.js
 M studio/src/reveal_studio/web/js/rail.js
 M studio/src/reveal_studio/web/js/strip.js
 M studio/src/reveal_studio/web/js/viewer.js
 M studio/tests/acceptance/test_b_director_flow.py
 M studio/tests/acceptance/test_b_pair_flow.py
 M studio/tests/fakes/reveal.py
 M studio/tests/test_director_flow.py
 M studio/tests/test_jobs.py
 M studio/tests/test_pair_flow.py
 M studio/tests/test_prose.py
 M studio/tests/test_registry.py
 M studio/tests/test_runner.py
 M studio/tests/test_views.py
```

The commit on main is still 0a5a260; I committed nothing. My changes are the `studio/src/` and `studio/tests/` files of the appendix. The two acceptance files are the drive's edits. The `.claude/` files, `studio/ARCHITECTURE.md`, `GUIDE.md` and `README.md` are the doc-sync writer's. So are `studio/pyproject.toml` (the description and a comment) and the docstring of `studio/src/reveal_studio/__init__.py`, both edited at 22:27, before my first edit.
