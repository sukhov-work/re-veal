<!-- provenance: copied verbatim on 2026-11-05 from benchmarks/runs/2026-11-05/studio/agents/b_director_build.md (gitignored), the director plan flow of phase B built on the package by builder D (Opus 5.5, max effort): eight stages, the --set table as data (112 rows), the overlays, eight panels, 52 tests, the acceptance on mismatch_3 with both recorded md5s; a research artifact whose claims carry the author's own confidence and gaps; the main thread re-ran make qa, make test and the acceptance tests on the integrated tree before the commit -->

<!-- reader: the main thread, the phase B acceptance driver and the reviewer, cold. shape: report. Written 2026-11-05 by builder D (Opus 5.5) on the package studio/. -->

## The director flow is built and enabled; both recorded mismatch_3 md5s reproduce through the studio

The director plan flow runs end to end in the studio package as of 2026-11-05. Its acceptance test passed once on the real tree in 219 s: the two-knob 480 px draft gave md5 01b3cf3c769ee45e44a73f1ade36a3b6, and the workbench's four-knob draft gave 5b3ee379776ae4e8ce2dec4fa3293740. The page built by `director_page.py` behind the review gate has md5 20d444cad34b6d74f82968fd77dd2819.

Gates: `make qa` passed at its first run (549 tests). Its final run and `make test` (573 passed) each failed one test, the loop registry's digest test in builder L's `tests/test_registry.py`; mine are green.

Asked of the main thread (the table in "Requests"):
1. Let `views/page.build_page` pass `variants` only to a page stage that has the knob.
2. Add `look` and `faults` to the skeptic answer shape of a director job.
3. Fix the pid check for a page record written in place across a restart.
4. Keep or rewrite my three assertions in two shared test files.
5. Update `studio/ARCHITECTURE.md` and `contracts.md` with the new modules and routes.

Open: the full 1920 render took 152.6 s, against 32.8 to 66.4 s in the director research report (`b_director_research.md`). The load average was 8.06; that load as the cause is UNVERIFIED.

| Term | Meaning here |
|---|---|
| builder D, P, L | the three Opus subagents of phase B's second wave: the director flow (me), the pair flow, the loop's repaint leg |
| the slice | the generalization slice of phase B (`b_slice.md`), which made the package flow-neutral |
| the renderer | `scripts/research/director_render.py` at md5 05cd6e1d95adbb3c83313b98b3f43815 |
| the page script | `scripts/research/director_page.py`, which writes `run/index.html` in place |
| the workbench | `scripts/research/director_ui.py`, the director web page the studio replaces |
| the set dict | the render's knob `set`, a JSON object sent as one `--set k=<json>` per key, keys sorted |
| the review gate | the studio's rule that the page refuses an unjudged or NOT READY full render unless the owner overrides; the page prints the override |
| the skeptic | the stage that writes a request file; a reviewing subagent answers with a verdict per render |
| mismatch_3, c1 | the fixture pair of the acceptance (photo A `fixtures/mismatch_3_S.jpg`, photo B `mismatch_3_F.jpg`) and concept c1 of its plan `mismatch_3_r12.json` |
| a round | one page over the full renders, then his grade on it; round 1 is the job's first page |
| the picks shape | his grade per clip: three boxes (`one_picture`, `transforms`, `not_invented`), acceptable as-is and a note |
| tables A to D | the renderer's `--set` keys of `b_director_research.md` §2: top-level, sky, transform, and the eight without effect |
| a fake | a stand-in script under `studio/tests/fakes/` with the real flags, the real `--help` and the real output shapes |

### What I built

Paths are under `studio/`. I own the first 13 rows (14 files: the two fakes share a row). The next 2 rows are my Edit-only files; the last 2 are edits outside my lists.

| File | What it holds |
|---|---|
| `src/reveal_studio/registry/director.py` | the eight stages (import, verdict, resolve, plan, render, skeptic, page, grades), `enabled: True`, the `--set` table as data (`SET_KEYS`, 112 rows) and `set_key_problem` |
| `src/reveal_studio/registry/hints_director.py` | 192 hint keys; the 112 `set.*` rows are built from the table, so a sentence lives once |
| `src/reveal_studio/runner/argv_director.py` | the resolve, render and page argvs, with the checks run before a script starts |
| `src/reveal_studio/views/director.py` | the tiles, the job view's keys, `pairs_view`, `plan_view` (the knob map in both name forms) and `render_view` |
| `src/reveal_studio/server/routes_director.py` | five routes: `GET /api/pairs`, `GET /api/plans/director/<stem>`, `GET /api/jobs/<id>/director/plans/<name>`, `GET /api/jobs/<id>/overlay/<A or B>/<kind>.png`, `GET /api/jobs/<id>/thumb/canvas/<A or B>` |
| `src/reveal_studio/media/overlays.py` | the four overlays, the 22 group colours and the decoded step series; numpy and cv2 stay here |
| `src/reveal_studio/web/js/director.js` | the `FLOW_UI.director` entry: eight panels, the new-job form, the viewer's sources, plots, measures and candidate rows |
| `src/reveal_studio/web/css/director.css` | the panels' styles |
| `tests/fakes/director_render.py`, `tests/fakes/director_page.py` | the two fakes; each prints the real script's `--help` byte for byte |
| `tests/test_director_flow.py` | 39 tests of the registry, the argv through the Runner, the views and the media |
| `tests/test_server_director.py` | 6 tests over HTTP, with a route spy of its own |
| `tests/integration/test_director_help.py` | 6 tests against the real `--help` of both scripts |
| `tests/acceptance/test_b_director_flow.py` | the acceptance drive of `b_director_research.md` §7 |
| `src/reveal_studio/views/models.py` (Edit-only) | two rows in the models panel: the layer tables and the mattes, with their counts in the name |
| `src/reveal_studio/media/pictures.py` (Edit-only) | `thumb_path(..., "canvas", "A" or "B")`: the latest resolve's canvas as the import tile's picture |
| `tests/test_server.py` (outside my list) | `test_post_jobs_refuses_a_bad_folder` sets the enabled flows itself; `test_models_route` names the two new rows |
| `tests/test_views.py` (outside my list) | `test_models_view_reads_the_manifests` counts 6 rows |

The routes `GET /api/jobs/<id>/director/plans/<name>` and `GET /api/jobs/<id>/thumb/canvas/<A or B>` are beyond the brief's three. The first opens a plan saved in the job in the plan panel's shape. The second gives the import tile a picture whatever the photo's format, since cv2 reads no HEIC.

### The stages as built

Terminal is the file whose presence marks a run finished; identity, the files whose md5s say a rerun changed nothing; stale after, the stages whose later run makes this one stale.

| Stage | Kind | Script | Terminal | Identity | Stale after | Knobs |
|---|---|---|---|---|---|---|
| import | builtin | — | — | — | — | none |
| verdict | the shared branch of `registry/common.py` | reveal | `metrics.json` | `metrics.json` | nothing | none |
| resolve | script | director_render | `anchors.json` | `anchors.json` | the import only, a builtin | plan, concept, max_long 1920, set |
| plan | builtin | — | — | — | — | none: the plan panel holds the plan, the concept and the set dict |
| render | script | director_render | `info.json` | `transition.mp4` | nothing (`[]`) | plan, concept, name (the tag), draft 0, max_long 1920, seconds 3.0, fps 30, set |
| skeptic | request | — | — | — | — | none |
| page | script | director_page | `index.html` | none | the render (`["render"]`) | title, key, head, keyframes, variants |
| grades | builtin | — | — | — | — | none |

The render's argv: `director_render.py PLAN <out>.part --concept C --max-long N --seconds S --fps F [--set k=v ...] --progress --layers-dir L --mattes-dir M`. A full render goes to `<job>/run/<stem>_<concept>[-<tag>]`, a draft to `<job>/drafts/...`. `N` is `draft` when above 0, else `max_long`. The resolve writes `<job>/resolve/<stamp>`, outside `run/`. The page writes `run/index.html` in place, so `out_final` equals `out_part`. The Runner copies the previous page to `<record>/previous_index.html` first.

### The --set table

| Table | Rows | Scope and set key | Read-only |
|---|---|---|---|
| A | 26 | top-level, `<key>` | 0 |
| B | 18 | sky, `sky.<key>` | 0 |
| C | 60 | transform, `<name>.<key>`; one row per key, with the code's default per transform kind | 0 |
| D | 8 | 5 transform keys (`ease`, `edge`, `rate`, `depth`, `hide_target`), 2 top-level (`hole_reveal_from`, `hole_reveal_over`), 1 sky (`key_end`) | 8 |

Every row carries its type, the code's default, the default's source, the reading line of the renderer, its condition, the plan path it mirrors, the sentence and its source. The plan view adds each row's default for the open concept and whether the concept meets the condition.

### Hint keys added

192 keys in `registry/hints_director.py`: 26 `control.director_*`, 10 `director.*`, 9 `resolve.*`, 9 `anchors.*` (the nine keys of `anchors.json`), 26 `info.*` and 112 `set.*`. The prose test (`tests/test_prose.py`, the no-slop checker over every hint) passes them: no negated contrast and no sentence over 60 words.

### Tests

52 tests: 45 unit (39 in `test_director_flow.py`, 6 in `test_server_director.py`), 6 integration and 1 acceptance.

One mutation shown red, then reverted (the file compared identical to its backup afterwards): with `*roots_flags(settings)` deleted from `argv_resolve`, `test_the_resolve_runs_outside_run_with_the_settings_roots` failed with "Right contains 4 more items, first extra item: '--layers-dir'". The restored file passed the test again.

### Gates

| Gate | Result | Wall |
|---|---|---|
| `make qa`, first run (before the panel fixes) | exit 0: ruff, mypy strict (55 files), 549 passed, 3 import contracts kept, deptry clean, prose clean | 2 min 22 s |
| `make qa`, second run | 548 passed, 2 failed: `tests/test_pair_flow.py` (builder P's reserved names, since fixed) and `tests/test_registry.py` (builder L's loop registry digest test) | 2 min 7 s |
| `make qa`, final run | ruff and mypy clean; 549 passed, 1 failed (builder L's loop registry digest test), so make stopped before the audit | 2 min 10 s |
| `make audit prose` on the same tree | vulture and deptry clean, pip-audit found no known vulnerability, 3 import contracts kept, prose 0 blocks | 11 s |
| `make test` | 573 passed, 1 failed: builder L's loop registry digest test in `tests/test_registry.py` | 2 min 12 s |
| acceptance, first run | failed at the page with 500 "ImportError: cannot import name 'RESERVED_NAMES'": builder P's `registry/pair.py` was mid-edit when the restarted server imported it (infra, another builder's file) | 3 min 29 s |
| acceptance, second run | 1 passed | 3 min 39 s |
| the page drive, headless Chrome over a tmp root with the fakes, 1440×900 and 1280×800 | every panel opened with 0 console errors; a bar moved by the keyboard and by a drag; the command preview held exactly the set dict's keys | — |

Radon grades `overlay_png` D (26), `map_knob` D (25) and `render_view` D (22); every other block of my modules grades C or better.

### The acceptance's observed values

Job `director_mismatch_3_20261105-185502` under `benchmarks/runs/2026-11-05/studio/`.

| Check | Observed | Recorded or asked |
|---|---|---|
| a job by pair name | A 75 elements, 43 mattes; B 56 and 51, missing 9, 19, 24, 26, 32; `mismatch_7` 400 with no folder | the same |
| the resolve at 1920 | 10.6 s; both canvases 1920×1440; the nine keys; camera homog; anchors `{}`; one layer `pane_becomes_view` [0.3, 0.92]; matte fallbacks `mismatch_3_F` 19, 24, 26, 32 | under 30 s; the research report's values |
| the plan | c1's three knobs map to `front_per_element`, `pane_becomes_view.times` [0] and `pane_becomes_view.window` [1]; `parallax_push` 2.5; two bars, [0.3, 0.92] and [0.92, 1.0] | the same |
| the two-knob draft | 19.1 s; md5 01b3cf3c769ee45e44a73f1ade36a3b6; 17 progress values, the last 89 of 90; exactly two `--set`; renderer 05cd6e1d…, transitions 7ef5dcae070c223e360c9c2e533df6c1, plan sha256 adec1345aeb6cc96100b29c63a5e440c95ce37cadc720780207b7bc47a9e5aaa | `.claude/claude-docs/DECISIONS.md`, the eighth entry of 2026-11-05 |
| the four-knob draft | 15.2 s; md5 5b3ee379776ae4e8ce2dec4fa3293740 | the same file, the ninth entry of 2026-11-05 |
| a re-render from the first draft's record knobs under a new tag | md5 01b3cf3c… again; the first draft's three files unchanged; the same tag again 409 | the same |
| the measures | motion median 2.37 px, 4 pauses, 0 jumps, B first above 1 % at frame 84, residual_edge_max 0.09647 (9.6 % of the pixels, above the 0.2 % bar), halo null (no luminary in the pair), matte fallbacks 24, 26, 32 (the 1920 resolve lists 19 too: the list depends on the canvas and the knobs, as the research report recorded); series 89, 31 and 29 long; 89 decoded steps, the first 0.27 | the same |
| a marked frame | frame 47 saved with the md5 01b3cf3c…; frame 90 answered 400 | the same |
| the full render across a restart | done after the restart, md5 78a58a0cc76815078a3e35112869e6eb, 152.6 s; the first run gave the same md5 in 147.1 s | 32.8 to 66.4 s in the research report |
| the page | md5 20d444cad34b6d74f82968fd77dd2819, round 1, built on the override; the rebuild md5 1fc446abd5f18c96fa23cc5c69a97264, with `previous_index.html` equal to the first page | — |
| the page's keyframe tile | its `<img>` source `benchmarks/runs/2026-10-17/keyframes_r10/out/r10_m3_pane.png` resolves through the file route's helper rule (`read_only_file`) to the file, sha256 ecbfa92e…, the job's recorded helper; checked by a function call after the run, not over HTTP | UNVERIFIED in `b_director_research.md` §6 |
| the grade | `picks/director_picks_20261105-185839.json`; an extra top-level key and props without `not_invented` answered 400 | the same |
| the originals and frozen files | unchanged mtimes and sha256s; 0 files newer than the run under the plans, `fixtures/`, the layer root and the matte root | the same |

The test as run swept the pair's own layer and matte folders. The test file now sweeps the whole roots; that version has not run. The same whole-root sweep, run by hand with `find -newer` against the run's start, found 0 files.

### Decisions taken

| Choice | Why | Revert |
|---|---|---|
| A `--set` key that reaches no frame is refused with 400 before the script starts: an unknown top-level or sky key, a dotted key naming no transform of the concept, and table D's 8 keys. Any other transform param passes. | the renderer stores such a key and never reads it (`director_render.py` lines 881-889 and 1439-1441), so the record would claim a knob the render never used | delete the two `check_set` calls in `runner/argv_director.py` |
| The page stage has a `variants` knob without a flag; a non-empty list is refused. | `views/page.build_page` passes `variants` to every flow, and `coerce` refuses an unknown knob | after request 1, drop the knob |
| The review gate's override reaches the page through `--head`: `<record>/head.html` holds the given head file's text and the override. | the page script has no footer flag, and the review gate prints its override | drop the override branch of `argv_page` |
| A director job's view lists the pair's director plans under `frozen_plans`, in round order. | the inspector's plan select (`inspector.js`, closed to me) lists `frozen_plans` | drop the key from `views/director.extras` |
| The canvas thumbnail URLs carry `?r=<resolve record>`, the overlay URLs `?v=<the table's sha256, 8 characters>`. | the file route caches these answers for an hour by URL | drop the queries |

### Requests to the main thread

| # | File | Change asked | Why |
|---|---|---|---|
| 1 | `src/reveal_studio/views/page.py` | set `knobs["variants"]` only when the flow's page stage has that knob | the director page stage carries a knob that only exists so `coerce` accepts it |
| 2 | `src/reveal_studio/jobs/grades.py` (`write_request`) | for a director job, name `look` and `faults` per candidate in the answer shape | `b_design.md` gives the skeptic's answer both; `page_notes` already reads them into `notes.json` |
| 3 | `src/reveal_studio/runner/process.py` (`pid_alive`) | for an in-place record, look for the output's folder in the process's arguments | the page's argv names `run/` and never `run/index.html`; if the server restarts while the page script runs, the pid check finds no match and marks the record lost (the script takes about 1 s) |
| 4 | `tests/test_server.py`, `tests/test_views.py` | keep or rewrite my three assertions | enabling the flow and the two models rows turned them red |
| 5 | `studio/ARCHITECTURE.md`, `.claude/conventions/contracts.md` | add `media/overlays.py`, the five routes, the 192 hints, the job view's `director`, `resolve` and `verdict` keys, the test counts | both are closed to the builders |

### Not done

| Item | Why |
|---|---|
| a "save this plan" control in the plan panel | the route `POST /api/jobs/<id>/plans` saves a director plan with its provenance, but writing the set dict back into the plan's JSON is a reverse map I did not build |
| the review by a Fable subagent, the critique with impeccable's anti-pattern detector at three viewports, the keyboard drive | the third wave of `b_design.md`: the drives, the review and the critique that follow the builders |
| the acceptance test's widened sweep run inside the test | checked by `find -newer` after the run instead (0 files) |
| the full render inside 66.4 s | 152.6 s at load average 8.06; that load as the cause is UNVERIFIED |
| a green `tests/test_registry.py` (the loop registry's digest test) | builder L's file; reported, not fixed |

### Appendix: evidence and the tree

The two acceptance jobs are `director_mismatch_3_20261105-184707` (the run that failed at the page) and `director_mismatch_3_20261105-185502` (the passing run), both under `benchmarks/runs/2026-11-05/studio/` (gitignored). The drive's screenshots and logs sat in this session's scratchpad, which a later session will not find.

`git status --short` at the end. The tree holds builders P and L's work and the main thread's edits beside mine; mine are the director files of "What I built".

```
 M .claude/skills/reveal/references/tracked-backlog.md
 M scripts/research/loop_seq.py
 M scripts/research/plans/loops/SCHEMA.md
 M studio/Makefile
 M studio/src/reveal_studio/jobs/grades.py
 M studio/src/reveal_studio/jobs/store.py
 M studio/src/reveal_studio/media/pictures.py
 M studio/src/reveal_studio/registry/director.py
 M studio/src/reveal_studio/registry/hints.py
 M studio/src/reveal_studio/registry/hints_director.py
 M studio/src/reveal_studio/registry/hints_pair.py
 M studio/src/reveal_studio/registry/pair.py
 M studio/src/reveal_studio/registry/schema.py
 M studio/src/reveal_studio/runner/argv_director.py
 M studio/src/reveal_studio/runner/argv_pair.py
 M studio/src/reveal_studio/server/routes_director.py
 M studio/src/reveal_studio/server/routes_pair.py
 M studio/src/reveal_studio/views/director.py
 M studio/src/reveal_studio/views/measures.py
 M studio/src/reveal_studio/views/models.py
 M studio/src/reveal_studio/views/page.py
 M studio/src/reveal_studio/views/pair.py
 M studio/src/reveal_studio/views/tiles_loop.py
 M studio/src/reveal_studio/web/css/director.css
 M studio/src/reveal_studio/web/css/pair.css
 M studio/src/reveal_studio/web/js/director.js
 M studio/src/reveal_studio/web/js/pair.js
 M studio/tests/fakes/loop_seq.py
 M studio/tests/test_director_flow.py
 M studio/tests/test_jobs.py
 M studio/tests/test_pair_flow.py
 M studio/tests/test_registry.py
 M studio/tests/test_server.py
 M studio/tests/test_views.py
?? studio/src/reveal_studio/media/overlays.py
?? studio/src/reveal_studio/media/pair.py
?? studio/tests/acceptance/test_b_director_flow.py
?? studio/tests/acceptance/test_b_pair_flow.py
?? studio/tests/fakes/director_page.py
?? studio/tests/fakes/director_render.py
?? studio/tests/fakes/transitions.py
?? studio/tests/integration/test_director_help.py
?? studio/tests/integration/test_transitions_help.py
?? studio/tests/test_repaint.py
?? studio/tests/test_server_director.py
?? studio/tests/test_server_pair.py
```
