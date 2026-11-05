<!-- provenance: copied verbatim on 2026-11-05 from benchmarks/runs/2026-11-05/studio/agents/b_slice.md (gitignored), the generalization slice of phase B built by an Opus 5.5 subagent (max effort) on the package studio/ (commits 0eb09d8 and 9c78b83 on main; the builder's final test fixes rode the second); a research artifact whose claims carry the author's own confidence and gaps; the main thread re-ran make qa and make test (468, then 473 passed) on its tree before the commits and nothing else -->

<!-- reader: the main thread and the two flow builders of phase B (P, the pair flow; D, the director flow), cold. shape: report. Written 2026-11-05 by the slice builder (Opus 5.5) on the package studio/; the evidence sits beside it in b_slice/ (gitignored). This version supersedes the copy committed in 5ad01f6, which predates the shared-test fixes and the reruns on HEAD 5ad01f6. -->

## Phase B's generalization slice: built, every gate green on HEAD 5ad01f6

The slice is built and green as of 2026-11-05 on HEAD 5ad01f6: `make qa` passes 459 tests, `make test` 473, `make acceptance` 2 (the a2 md5 c302623f293eacd069218fd7518e0967 reproduced), and the impeccable detector returns `[]` at 2560×1440, 1440×900 and 1280×800.

Every layer of the package now dispatches by flow. The pair and director flows are registered and disabled, with empty stage lists. The loop's argv, strip tiles, rail rows and rounds match the untouched package byte for byte; so does the page's HTML, apart from one wrapper around the rail's new-job button. The main thread committed the slice as 0eb09d8 and 9c78b83. Reversal: `[revert: git revert of 0eb09d8, then of my test files in 9c78b83]`.

Asked of the main thread:
1. Re-copy this report over `.claude/claude-docs/research/2026-11-05/b_slice.md`; the copy in 5ad01f6 predates the fixes below.
2. Update `studio/ARCHITECTURE.md`'s module map and the Layout block of `.claude/conventions/studio.md` from "Steps and files".
3. Record the "Decisions taken" table as a DECISIONS line; its rows 2 and 3 extend `b_design.md`.

Open: an `object` knob's flags come in sorted key order, my reading of "in key order" in the brief the main thread gave me.

| Term | Meaning here |
|---|---|
| the slice | the change of wave 1 in `b_design.md`: the package made flow-neutral before the pair and director builders start |
| wave | a step of `b_design.md`'s build order: 1 the slice, 2 the three builders, 3 the drives and reviews, 4 the fix round |
| builder P, builder D, builder L | the Opus subagents of wave 2 that build the pair flow, the director flow, and the loop's repaint leg |
| the loop path | what the loop flow produces through the studio: its argv, tiles, rail rows, rounds, page HTML and the a2 render's md5 |
| the A1 and A2 drives | `studio/tests/acceptance/test_a1_loop_flow.py` and `test_a2_loop_flow.py`, which `make acceptance` runs on the owner's angel stills |
| HEAD's package | `studio/` as committed at 4f564b5, extracted with `git archive` and served from the copy for comparison |
| snapshot test | `studio/tests/test_loop_snapshot.py`: the loop path as literals, pinned before the first edit |
| shared file | a file `b_design.md` closes to the wave-2 builders, or one the slice made for every flow; listed under "What a flow builder must not touch" |
| tile function | a function that fills one stage's tile of the strip (the row of stage tiles); each flow has a table of them |
| base tile | the tile every stage starts from: its registry fields and its latest record's state |
| record | one run of a stage: `stages/<stamp>_<stage>/stage.json` with its argv, knobs, inputs and outputs |
| skeptic request | a file `requests/skeptic_<stamp>.json` asking the Claude Code session for a verdict per render; `answers/<the same name>` answers it |
| spec reader | `jobs/candidates.spec_candidates`: lists another flow's renders from the spec in its registry entry |
| `FLOW_UI` | the page's table of per-flow entries, declared in `web/js/core.js` |
| shared stage | a stage defined once for several flows in `registry/common.py`; today Reveal's verdict |
| the detector | impeccable's automated scan of the served page for UI anti-patterns; the bar is `[]` (no finding) |

### Tree and gates

The tree's HEAD at my start was 4f564b53ed6c65824e8d1a8742d16415533b1df1. Its working tree held 4 modified and 4 untracked files under `.claude/` (the main thread's documents); I touched none of them. The main thread committed them during the slice as 0325a69, which changes 0 lines under `studio/`.

| Gate | Before (4f564b5) | After (HEAD 5ad01f6) |
|---|---|---|
| `make qa` | 381 passed, pytest 71.3 s, wall 79.8 s | 459 passed (457 of the slice, 2 of 9c78b83), pytest 79.3 s, wall 83.6 s |
| `make test` | not run | 473 passed (459 unit, 14 integration), 78.1 s |
| `make acceptance` | not run | 2 passed in 195.2 s, run alone with no other record running (jobs `loop_angel_20261105-175022` and `loop_angel_20261105-175209`) |
| import contracts | 3 kept | 3 kept; the forbidden names gained 8 |
| the detector, `--json --no-advisory`, port 8397 | not run | `[]` at 2560×1440, 1440×900 and 1280×800 (on the slice's source) |
| snapshot test | 6 passed in 2.4 s | 5 passed (its registry digests moved to `test_registry.py`); the final file passes on HEAD's package too (2.8 s) |

The first acceptance run, on the slice's source before 9c78b83, passed 2 in 180.6 s. Both runs gave the anchors of `STUDIO.md §9`: a2 c302623f293eacd069218fd7518e0967 twice (the A1 full render and the A2 copy), the 960 draft 3d453980f80eff43014646a6f65398a6, and the 480 draft 2955c25c2611565b3ee57d2d081f8669, re-attached across a server restart. The A1 job of the first run, `loop_angel_20261105-171251`, answered its own skeptic request (`answers/skeptic_20261105-171420.json`); `reveal-studio requests` then printed "no open requests".

**The tree changed under me.** These events touched files I was editing:

| Time | Event | Effect |
|---|---|---|
| 17:38–17:40 | the main thread committed the slice as c8e70f2, then rewrote it as 0eb09d8 | it holds the slice and part of my shared-test fixes; the rest landed in 9c78b83 |
| 17:39 | my mutation check pointed `pid_alive` at the loop script for about 3 s, then restored my copy of `runner/process.py`; the main thread was adding its in-place rule to the same file | the committed file in 9c78b83 equals my restore copy (checked by `diff`), so no edit was lost |
| 17:39–17:41 | I ran `ruff check --fix` and `ruff format` over all of `studio/tests/` while the main thread edited `tests/test_plans.py` | `ruff format` reported 2 files reformatted, most likely my two flow test files; I did not record which |
| 17:43 | the main thread committed 9c78b83: its three shared-file rules (below) and my last six test files | the working tree now equals HEAD |

### Steps and files

Paths are under `studio/src/reveal_studio/` unless they start with `tests/` or `studio/`.

| Step | Files | Change |
|---|---|---|
| 1. snapshot | `tests/test_loop_snapshot.py` (new) | the argv of 10 loop runs, the tiles of three job states, the rail rows and the rounds, pinned as literals |
| 2. settings | `config.py`, `cli.py`, `studio/README.md`, `tests/test_config.py`, `tests/test_cli.py` | 8 paths; `--layers-dir`, `--mattes-dir` and their environment names; `check` prints each with an md5 or a count, MISSING without changing the exit code |
| 3. registry | `registry/entries.py`, `flows.py`, `common.py`, `pair.py`, `director.py`, `hints_pair.py`, `hints_director.py` (new); `loop.py`, `hints.py`, `rulings.py` | the flow table, the stubs, the verdict stage, `script` and `identity` on the loop's script stages, the hints merged, two chip hints |
| 4. jobs | `jobs/rounds.py` (new); `jobs/store.py`, `candidates.py`, `grades.py`, `plans.py` | the pair and director creators, `open_round`, the picks writer, the spec reader with its md5 cache |
| 5. runner | `runner/argv_loop.py`, `argv_common.py`, `argv_pair.py`, `argv_director.py` (new); `runner/argv.py`, `process.py` | the loop chain moved verbatim, the dispatcher, the `object` type, `argv[1]`, the identity lookup, `open_round` |
| 6. views | `views/base.py`, `tiles_loop.py`, `pair.py`, `director.py` (new); `views/job.py`, `render.py`, `page.py`, `models.py` | one tile function per loop stage in a table per flow, the job view's per-flow keys, `render_view` by flow with `fps`, the page knobs from the flow's page stage |
| 7. media, server | `server/route.py`, `routes_pair.py`, `routes_director.py` (new); `media/pictures.py`, `server/routes.py`, `handler.py`, `app.py` | `frames_dir` reads the candidate's `mp4`, the route splice, the file route's read-only bases, `POST /api/jobs` passes `fixture`, `a`, `b`, `pair` |
| 8. contracts | `studio/.importlinter`, `.claude/conventions/studio.md` (one dated row, as the brief allows) | 8 forbidden names |
| 9. page | `web/js/pair.js`, `director.js`, `web/css/pair.css`, `director.css` (new); `index.html` and 9 scripts | `FLOW_UI`, registered by the loop's own scripts, the plain panel, the new-job buttons per enabled flow, the playback rate from `fps`, the import panel's chips |
| 10. tests | `tests/fakes/reveal.py`, `test_flows.py`, `test_pair_flow.py`, `test_director_flow.py` (new); `tests/conftest.py`, `acceptance/test_a1_loop_flow.py` and 9 other test files | the fakes table, the fixture pair, the per-flow counts, the A1 drive answering its request |
| 11. shared tests | `tests/test_server.py`, `test_jobs.py`, `test_flows.py`, `test_views.py`, `test_runner.py`, `test_registry.py`, `test_loop_snapshot.py`, `test_pair_flow.py`, `test_director_flow.py` | after the advisor's review: every slice test in a shared file holds once P and D fill their flows (the rule is under "What a flow builder must not touch") |

### Shapes the flow builders rely on

**The registry.** A flow entry is `{title, what, enabled, stages}` plus an optional `candidates` spec. `registry/flows.py` holds `ALL_FLOWS`, `FLOWS` (the enabled ones), `STAGE_NAMES` (the union in flow order, the loop's ten first), `flow_def`, `stage_def(flow, name)` (404 when absent), `stage_order(flow)` and `identity_of(flow, name)`. A script stage carries `script`, one of `loop_seq`, `transitions`, `reveal`, `director_render`, `director_page`, and `identity`, the fnmatch patterns of its result files. The loop's identity lists: registration `["*.png", "*.npy"]`, readers `["readers.json"]`, render `["loop.mp4"]`, probe, measure and page `[]`. A shared stage's name is reserved in every flow: `verdict`. The verdict's definition is the brief's, plus `"identity": ["metrics.json"]`. `K` (a knob) and `H` (a hint) are imported from `registry/entries.py`. `hints_pair.HINTS` and `hints_director.HINTS` merge into `registry.hints.HINTS`; a key in two tables fails the import.

**The candidate spec** (`FLOW["candidates"]` of a flow; the loop has none and keeps its reader):

| Key | Meaning | Pair stub | Director stub |
|---|---|---|---|
| `full`, `draft` | folder templates; `{root}` the run folder, `{job}` the job folder, `{seq}` the job's seq | `["{root}/{seq}"]`, `["{root}/drafts/{seq}"]` | `["{root}"]`, `["{job}/drafts"]` |
| `terminal` | the file that marks a finished render | `report.json` | `info.json` |
| `mp4` | the clip's name in the folder | `transition.mp4` | `transition.mp4` |
| `record_knobs` (optional) | knobs copied from the done record whose `out_final` is the folder | `["preset"]` | `[]` |
| `fields` (optional; an extension of the design) | the terminal file's keys copied onto the candidate | class, method, sparse_inliers, median_disp_px, mean_certainty, n_frames, quality | the 13 scalars of `b_design.md`'s candidate paragraph |

A spec candidate carries `name, kind, dir, path, mp4, md5_mp4, frames, seconds, fps, canvas, draft, has_frames, mtime, record, verdict, unjudged`, `unjudged_reason` when unjudged, then its `fields` and `record_knobs`. `md5_mp4` is the done record's output md5 for the mp4. Without a record, the file is hashed once and kept at `cache/md5/<sha256 of its path, 16 hex>_<size>_<mtime_ns>`. `frames` reads `frames`, else `n_frames`; `seconds` and `fps` read the top level, else under `spec`. A draft's `draft` is the record's `draft` knob, else the canvas's long side. Every loop candidate gains `mp4: "loop.mp4"`.

**The `object` knob type.** `coerce` takes a dict or its JSON text, with keys of one dotted segment at most (`^[A-Za-z0-9_]+(\.[A-Za-z0-9_]+)?$`); anything else answers 400 "knob set takes a object". `flags_of` emits one `<flag> k=<json.dumps(v)>` per key, keys sorted, and nothing for `{}`. A dict default is copied per run.

**The argv.** `runner/argv.argv_for` sends a shared stage to `argv_common.ARGV` first, else to the job's flow module (`builder_of(flow, stage)`). A flow module exports `argv_for(settings, flags, stage, d, job, knobs, rec_dir) -> (argv, out_final, out_part, inputs)`, one function per stage as `argv_loop.py` does. The two stubs answer 501 "the pair flow's render stage is not built yet". The verdict's argv is `[<python>, "reveal.py", "align", <job>/raw/<seq>/A.<ext>, <job>/raw/<seq>/B.<ext>, "--out", <job>/verdict.part]`, its inputs the originals' paths with their sha256s, its output `<job>/verdict`.

**The Runner.** `script_md5` is the md5 of `<root>/argv[1]`; a missing script answers 409 before any child starts. `pid_alive` and `cancel` look for the record's own `argv[1]` and `.part` path in the process's arguments. The "unchanged" files come from `identity_of(<the job's flow>, <stage>)`; the record's shape is unchanged. `run_warnings` resolves a plan for the loop's render only. The round gate keeps its rule: a new round's first full render (stage `render`, knob `draft` 0) waits for the last round's grade. The registration still waits while another record runs. Since 9c78b83, a stage whose `out_part` equals its `out_final` is written in place: its previous file is kept as `<record>/previous_<name>`.

**Rounds and grades.** `jobs/rounds.open_round(d, page, names, *, variants=None, record=None, override=None)` returns the round. It writes `page.md5` beside the page, copies the page into `rounds/<n>/` and writes `round.json` with the loop's ten keys in their order. `POST /api/jobs/<id>/picks` with `{round, picks, text}` checks the picks as `director_ui.py:688–707` did. It writes `picks/director_picks_<stamp>.json` (`_2` for a second save in one second), then sets the round's grade `{at, page_md5, picks: "picks/director_picks_<stamp>.json", text}`. A bad shape answers 400 and writes nothing. `{round, text}` and `{round, ungraded_by_his_word, words}` behave as before.

**The creators.** `create_pair_job(settings, fixture=None, a=None, b=None, seq=None)` and `create_director_job(settings, pair)` are what tests and builders call. `create_job` refuses a disabled flow with "the flow is one of ['loop'] (pair and director are registered but not built yet)". A pair or director input is `{role, name, path, sha256, bytes, link}`, with `link` the repo-relative `raw/<seq>/A.<ext>`; a loop input's `link` is written as before. A director job without a plan naming its pair answers 400 before any folder exists. Its `tables`, `mattes` and `helpers` follow `b_design.md`; `mattes.<side>.missing` is null when the photo has no layer table.

**The views.** A flow's view module holds `TILES` (stage name to `fn(ctx, tile, latest)`), `extras(settings, d, job)` (keys merged into the job view) and `render_view(settings, d, job, kind, name)`. The context `views/base.TileContext` reads lazily: `root`, `cands`, `full`, `drafts`, `reqs`, `rounds`, `plans`, and `once(key, read)` for a flow's own reads. A stage without a tile function shows its base tile. Every job view carries the loop's 14 keys, with `prep`, `readers` and `probe` None and `frozen_plans` `[]` outside the loop. `base_render_view(..., default_fps)` takes the candidate's `fps`, else the record's `fps` knob, else the default (30 in both stubs). It builds the mp4 URL against the run folder, then the job folder, because a director's drafts sit outside `run/`.

**The routes and the file route.** `server/route.py` holds `Route`, `_r`, `JOB` and `RouteFn`. `ROUTES` is `CORE`'s 24 rows that are not fallbacks, then `routes_pair.ROUTES`, then `routes_director.ROUTES`, then the two fallbacks; `CORE` holds the 26 shared rows. The file route tries the run folder and the job folder first, then, read-only, `fixtures/<name>`, `layers/<photo>/<file>` and `mattes/<photo>/<file>` under the job's recorded roots, then the exact repo paths in `job["helpers"]`. A link out of the job folder, such as `raw/<pair>/A.jpg`, is not served, as before.

**The page.** An entry of `FLOW_UI` is `{panels: {stage: fn}, wire, sources, candRow, plots, measures, newJob, inputsWord, hosts, graph: {hosts, cost}}`. `hosts`, `graph` and `measures` extend the design's seven keys: `viewer.js`, `graph.js` and `inspector.js` named the loop's stages there. A script registers with `flowEntry(flow)` at its end; `flowUI()` returns the open job's entry. A stage without a panel shows its sentence (`plainPanel`), and a flow without `candRow` gets `plainCandRow`. The rail draws one "new <flow> job…" button per enabled flow with `newJob`: id `btnNew_<flow>`, hint key `control.<flow>_new_job`, a row the builder adds. Forms go into the empty `#flowForms` in the rail. Playback steps every `1000/fps` ms. The import tile carries `warnings` only above 6 stills: `chip.above_6` "above every sequence registered so far (6)" and above 10 also `chip.above_10` "above the design's range of 2 to 10 stills".

**The test fixtures.** `tests/conftest.FAKE_TABLE` maps each fake under `tests/fakes/` to its place in a tmp root; `make_root` copies the ones whose file exists. `fixture_pair` (or `write_fixture_pair(root)`) returns `"tiny_1"` after writing these files:
- `fixtures/tiny_1_S.jpg` and `_F.jpg`, written by cv2 at test time;
- `scripts/research/plans/tiny_1_r1.json` (`DIRECTOR_PLAN`), which names one keyframe (`HELPER`);
- a layer table per photo with elements 1 to 3;
- mattes `el_1.png` and `el_2.png` for `tiny_1_S` only.

The fake `reveal.py` answers `align A B --out DIR`, steered by `FAKE_SLOW`, `FAKE_REFUSE` or `FAKE_FAIL` set to `align`.

### What a flow builder must not touch

- The files `b_design.md` closes: `server/routes.py`, `registry/hints.py` (builder L's loop rows excepted), `web/js/panels.js`, `web/index.html`, `views/job.py`, `tests/conftest.py`, `runner/process.py`, `jobs/store.py`, `jobs/candidates.py`, `config.py`.
- The slice's shared modules: `registry/flows.py`, `registry/entries.py`, `runner/argv.py`, `views/base.py`, `views/render.py`, `server/route.py`, `jobs/rounds.py`, `jobs/grades.py`, `web/js/core.js`.
- `tests/test_loop_snapshot.py`: never regenerated. A red test there means the loop path moved.
- The loop's page scripts (`viewer.js`, `inspector.js`, `graph.js`, `strip.js`, `rail.js`, `boot.js`): register through `FLOW_UI` instead; ask the main thread for anything it cannot carry.

The rule the shared tests follow: a slice test in a shared file holds whatever the flows' own modules hold. It sets the state it needs itself: the enabled flows (`store.FLOWS`), a fixed candidate spec, an empty tile table, or a direct call of `base_render_view`. The route walk of `test_server.py` covers `CORE`; each flow walks its own list with a spy of its own. What P and D replace sits in their own files, `tests/test_pair_flow.py` and `tests/test_director_flow.py`. Those hold the disabled state, the 501 answers, the empty route lists and tile tables, and the verdict's argv as the slice left it. A builder who needs a shared test changed asks the main thread.

The main thread built three of the requests this report first listed, in 9c78b83: the in-place page, `resolve_plan` and `frozen_plans` by flow, and names of 60 characters. Two stay open:

| Need | Where | Why it is open |
|---|---|---|
| rulings of another flow | `registry/rulings.py` | the 7 rows match any flow's stage of the same name; a stage named like a loop plan key (seq, in, title, gag, timeline, effects, matte, crf, gif_long, crop) would read as a stage knob |
| a HEIC input's thumbnail | `media/pictures.py` | cv2 reads no HEIC, so `thumb/raw/<i>` answers 500 for one (`b_seams_research.md`, key fact 9) |

### Proof the loop path held

**The snapshot test.** It pins 10 argv cases with their output paths and inputs: registration, readers, probe, render full, render draft, measure with and without `frames.json`, page with and without variants. It pins the tiles of a new job, of a job through every stage, and of that job after a later registration (the stale rule: a stage whose upstream ran later turns stale). It also pins both jobs' rail rows and rounds. It passed 6 of 6 on the untouched tree before my first edit. The later changes left the literals as they were. The build gained two waits for a round file: it graded a round before `after_done` had opened it, and that race failed once under `make qa`'s load. The digests of the loop's registry rows (the stage definitions with `script` and `identity` left out, the 290 hints, the 151 schema rows, the 7 rulings) moved to `test_registry.py`, so builder L updates them with the loop counts. The final file (md5 52ddc22afbc0a9a0b4d00dd61b36bd61) passes 5 of 5 on HEAD's package and on HEAD 5ad01f6.

**The page drive.** I served HEAD's package on 8398 and the slice on 8397, both from the real tree with their own lock files. One headless Chrome (DevTools port 9397), driven by Node 22 scripts, opened two jobs: `loop_angel_20261105-171428` (the A2 drive's) and `loop_angel_20261105-171251` (the A1 drive's). All 40 comparisons were identical: the panel's and the inspector's HTML for each of 10 stages in 2 jobs. So were the strip's and the graph's HTML. The viewer matched: 25 fps, 50 frames, 2 and 1 plots, the same sources. Neither page logged a console error. The rail differs by one wrapper, `<span id="newJobs">`, and a `data-flow="loop"` attribute on the same button. The playback delay was 40 ms at 25 fps on both; for a render set to 30 fps it was 33.3 ms on the slice and 40 ms on HEAD's package. The frames advanced in 2 s were 0 or 49 on both servers, varying run to run [INFERRED: headless Chrome's timer throttling]. The drive ran on the slice's source before 9c78b83.

**Mutations shown red**, each reverted and green again:

| Mutation | Red line |
|---|---|
| the loop render's `identity` set to `[]` | `test_a_render_with_the_same_mp4_says_unchanged`: `KeyError: 'unchanged_from'`; `test_every_loop_script_stage_names_its_script_and_identity`: `{'render': []} != {'render': ['loop.mp4']}` |
| `pid_alive` looking for `scripts/research/loop_seq.py` in every record | `test_reconcile_reattaches_a_live_child_of_another_flows_script`: `assert ('lost' == 'running')`, before and after the test was rewritten to run a script of its own |
| `import director_render` inside `views/director.py` | `lint-imports`: "no tool or script import BROKEN … reveal_studio.views.director -> director_render (l.32)" |

### Radon

Radon grades a block's cyclomatic complexity from A (simplest) to F; the number in parentheses is the score.

| Block | Before (4f564b5) | After the slice (0eb09d8) |
|---|---|---|
| `stage_views` | F (92) | B (6); its stale rule moved verbatim into `views/base.mark_stale`, D (22); the 10 tile functions grade A (3) to C (17) |
| `argv_for` | E (39) | A (1), the dispatcher; the loop's argv functions grade A to C, the highest `argv_page` C (14) |
| `create_job` | D (22) | B (10); `create_pair_job` and `create_director_job` B (8), `adopt_loop_job` C (12) |
| `Runner.finalize` | F (57) | F (58), one point for the identity lookup; left whole, as the brief asks (backlog row T96) |
| `graph_view`, `job_row` | E (35), D (24) | unchanged |
| average | B (6.07) over 182 blocks | B (5.29) over 262 blocks |

On HEAD 5ad01f6, after the main thread's in-place rule, `Runner.finalize` grades F (63), `Runner.start_stage` D (23), and the average B (5.36) over 264 blocks.

### Decisions taken

| Choice | Why | Revert |
|---|---|---|
| an `object` knob's flags in sorted key order | one dict gives one argv whatever order the page sends; the renderer keeps a repeated key's last value, so order cannot change a render | sort by insertion in `runner/argv.flags_of` |
| `FLOW_UI` gains `hosts`, `graph` and `measures` | otherwise P and D would both edit `viewer.js`, `graph.js` and `inspector.js` | fold them back into those scripts |
| the spec gains `fields`; folders are templates over `{root}`, `{job}`, `{seq}` | the flow's numbers reach the candidate without an edit of `jobs/candidates.py`; a director's drafts live outside `run/` | drop the key; fixed folders |
| the enabled-flow gate sits in `create_job`, and each creator is callable | the tests make pair and director jobs while the flows stay disabled | move the gate into `post_job` |
| the import tile's `warnings` key appears only above 6 stills | the loop's tiles keep their keys byte for byte | always write the key |

Smaller choices: a missing script answers 409 before the child starts (the loop never meets it). `write_request` reads `plan_sha256` with `.get`. The tests' `write_stills` wraps its grey level at 256, so a job can hold more than 5 stills.

### Not done

- The read-only review by a Fable subagent, the critique by impeccable's method and the keyboard drive: steps of the UI build routine (`.claude/skills/reveal/references/studio.md`) that belong to waves 3 and 4.
- Detector scans of single screens through `--cdp` (graph view, import panel): not run. The URL scans covered the newest job's render view, and every other screen's HTML equals HEAD's.
- The page drive and the detector on HEAD 5ad01f6: they ran on the slice's source before 9c78b83, which changed `runner/process.py`, `jobs/plans.py` and `registry/schema.py` and 0 lines under `web/`.
- `studio/ARCHITECTURE.md`, `STUDIO.md`, `contracts.md` and DECISIONS: not edited; they are the main thread's.
- Rulings per flow and a tile function for the verdict: not in the brief. The verdict shows its base tile.
- `reveal-studio check` prints "director plans" one column wider than the other rows: the label is 14 characters against a column of 13.
- A playback frame count as a timing measure: not reliable in headless Chrome, so I measured the interval's delay instead.

### Appendix: evidence and the final `git status`

The evidence sits in `benchmarks/runs/2026-11-05/studio/agents/b_slice/` (gitignored):
- `drive/`: the Node scripts (`cdp.mjs` copied from `port_acceptance/`, `drive.mjs`, `play.mjs`, `play2.mjs`), `drive.json` and 8 screenshots, one strip and one graph per server and job;
- `logs/`: `make qa`, `make test` and `make acceptance` before and after, radon, the three mutations, the detector's JSON at three viewports, and the snapshot as first generated with its first file.

`git status --short` at the end, HEAD 5ad01f6: empty. The report and its evidence are gitignored. `studio/uv.lock` has 0 diff lines against 4f564b5. My servers on 8397 and 8398 and my Chrome on 9397 are stopped; `scripts/session_sweep.sh` lists 0 session processes.
