<!-- provenance: copied verbatim on 2026-11-05 from benchmarks/runs/2026-11-05/studio/agents/b_seams_research.md (gitignored), the package's 70 loop-only assumptions and the generalization slice of phase B by an Opus 5.5 research subagent (max effort), read-only on the repo; a research artifact whose claims carry the author's own confidence and gaps; the main thread re-verified the mismatch_3 anchors by rendering both argvs (DECISIONS 2026-11-05 eighth and ninth lines) and nothing else -->

<!-- reader: the main thread writing the phase B builder briefs, then a cold reader of the research copy; shape: report; written 2026-11-05 by the studio-seams research track, read-only on the repo except this file -->

## Findings: studio-seams

The studio package assumes the loop flow in 70 places: 44 in the Python source, 13 in the page and 13 in the tests. Of these, 58 need a change and 12 stay loop-only on purpose. Three go wrong on the first pair or director job. A `job.json` without `seq` makes `GET /api/jobs` answer 500 for every job, in the package and in the owner's live server. The Runner's process check marks a live pair or director render `lost` and deletes its `.part` folder after a restart. Every record stamps the loop script's md5.

One generalization slice, built by one builder before the parallel builders start, removes the 58. The loop's argv lists, its strip tiles and the angel a2 render's md5 (c302623f293eacd069218fd7518e0967) stay identical; snapshot tests written first prove it. After the slice, builder P (pair) and builder D (director) own disjoint files. A third builder for the page shell would make P and D wait on it.

Asked of the main thread: approve the slice scope, and adopt the `draft` knob convention. Choose the pair page: written by the studio, or a stdlib script run as a stage. Choose the output path of `director_page.py`: a default-off `--out`, or a staging folder. Open: who owns Reveal's verdict branch, which both two-photo flows share. Confidence 80%.

| Term | Meaning in this report |
|---|---|
| loop-only assumption | a place in the package that holds for the loop flow alone |
| slice | the generalization change that lands alone, with every gate green, before the parallel builders start |
| builder P, builder D | the Opus 5.5 subagents that build the pair transition flow and the director plan flow after the slice |
| snapshot test | a unit test that pins today's output (an argv list, a tile) as literals; it passes before and after the slice |
| enabled flag | a key on a flow's registry entry: a disabled flow is hidden from the page and refused by `POST /api/jobs`, while its jobs still open |
| `draft` knob convention | every render stage carries an int knob `draft` (0 = full size), which the round rule and the views read |
| the owner's live server | his server of 2026-11-04 on port 8380, which still runs the retired `scripts/research/studio.py` from memory (backlog T95) |
| stage, record | a stage is one process with inputs, outputs, knobs and a wall time; the loop has ten: import, registration, readers, probe, plan, render, measure, skeptic, page, grades. A record is one run of a stage (`stages/<stamp>_<name>/stage.json`) |
| the Runner | the class in `runner/process.py` that starts each stage as a subprocess, writes its record and reconciles it after a restart |
| prep, candidate, round | the prep is the loop's registered stills (`in/<seq>/`); a candidate is a full render on the review page; a round is one page over the candidates with his grade text |
| the rail | the page's left column: the jobs, the running records, the open requests |
| the "unchanged" rule, identity patterns | a rerun whose result files have the md5s of the previous run says "unchanged"; the identity patterns name those result files |
| picks | the grade file of director rounds: `best`, and per clip `acceptable`, `note`, `props` |
| the `--set` table | the director renderer's `--set key=value` overrides of its global knobs |
| Reveal's verdict | an optional `reveal.py align` run on the two photos, which the pair track proposes as a branch stage |
| the UI build routine | `.claude/skills/reveal/references/studio.md`: an acceptance drive, a read-only review by a Fable subagent, a critique with impeccable's detector (an automated anti-pattern scan of the served page), a fix round |
| backlog T<n> | a row of `.claude/skills/reveal/references/tracked-backlog.md` |
| phase B | the build phase of `STUDIO.md` section 9 that adds the pair and director flows; "B (continued)" is its second row |

### Key facts

Ranked by what breaks first.

1. One job.json without `seq` breaks the rail for every job. `job_row` reads `job["seq"]` (`views/job.py:465`), and `GET /api/jobs` builds all rows in one list (`server/routes.py:71-73`), so a KeyError answers 500. The owner's live server reads `job["seq"]` in `candidates` and `job_row` (`git show 93af7e9^:scripts/research/studio.py`, lines 849 and 1171) and answers any exception as a 500 (lines 1562-1564). Writing `seq` in every job.json removes the failure; the pair track proposes the same value, the pair's name (`b_pair_research.md:186`).
2. The Runner recognises a live process by the loop script's path in `ps` (`runner/process.py:324`). After a restart, or from a second server (the reconcile defect of backlog T88), a live pair or director child reads as gone. `finalize` then marks it `lost` and deletes its `.part` folder while it still writes (`:211-221`); `cancel` returns without a signal (`:361`). Reading the script from the record's own `argv[1]` fixes this, and loop records carry `scripts/research/loop_seq.py` there.
3. Every record's `script_md5` is the md5 of `loop_seq.py` (`process.py:136`). The "unchanged" rule looks for `loop.mp4` in every stage named `render` (`process.py:44`), so it never fires for a pair or director render. Hashing `root / argv[1]` and putting identity patterns on each stage definition fix both.
4. Six stage names recur in the new flows: import, plan, render, skeptic, page, grades. Four places pick their code by stage name alone, so a director render would run the loop's render code: the tiles (`views/job.py:209-309`), the argv (`runner/argv.py:141-265`), the panels (`web/js/panels.js:8`) and the graph hosts (`web/js/graph.js:11-13`).
5. `director_page.py` writes `RUN/index.html` in place and has no `--out` flag (`director_page.py:26-29, 173`), so the `.part`-then-rename rule cannot hold for it. It lists every child of RUN that holds an `info.json`, splits the folder name at its last `_` (`:41-45`) and opens `scripts/research/plans/<stem>.json` (`:60`). So the resolve outputs go under `<root>/resolve/` and the drafts under `<root>/drafts/`, where the page never looks. A candidate folder is named `<frozen plan stem>_<concept>[-tag]`, with no `_` in the tag.
6. The pair flow has no page script. `loop_seq.py page` reads `measure.json`; `director_page.py` reads `info.json` and a director plan; `scripts/bench_transitions.py` builds a sheet over the fixture catalogue (its docstring, lines 2-11). The pair track recommends a page the studio writes (`b_pair_research.md:188-195`). That page needs the round opening moved out of `Runner.after_done` (`process.py:279-308`).
7. The phase B anchor moved. The 480 px draft of `mismatch_3_r12.json`, concept c1, gives md5 01b3cf3c769ee45e44a73f1ade36a3b6 under renderer 05cd6e1d95adbb3c83313b98b3f43815 (DECISIONS 2026-11-05 eighth line, uncommitted on disk; `STUDIO.md §9` row B amended). The value 5b3ee379… in this track's brief and in the session's memory note (`.serena/memories/project/wip-2026-11-05-studio-phase-b.md`, machine-local) came from renderers older than that build of 2026-10-21.
8. `transitions.py pair` prints zero `PROGRESS` lines, and neither `report.json` nor `info.json` carries the mp4's md5 (`transitions.py:1421-1453`; `director_render.py:2099-2105`). The pair tile shows the elapsed time only. The candidate reader must hash `transition.mp4`, cached by size and mtime as `frames_dir` caches its decode (`media/pictures.py:43-46`).
9. cv2 decodes no HEIC, so `jpeg_thumb` answers 500 for `fixtures/fabra_*.heic` and `match_1_*.HEIC` (`media/pictures.py:25-27`). The phase B pair mismatch_3 is JPEG, and its acceptance is unaffected. A HEIC input's thumbnail must come from a decoded output (`strip.jpg`, `canvas_A.png`), as the pair track also says (`b_pair_research.md:166`).
10. The loop acceptance turns into a skip while any other job's record runs: `wait_quiet` waits, then calls `pytest.skip` (`tests/acceptance/test_a1_loop_flow.py:94-99`). Drives that render in the parallel wave must run one at a time, and the main thread must read "2 passed".

### Every loop-only assumption, with what a second flow needs

Paths are under `studio/src/reveal_studio/` unless they start with `tests/` or `scripts/`. "Kept" marks an assumption that stays loop-only on purpose.

| # | path:line | the loop assumption | what a second flow needs |
|---|---|---|---|
| 1 | `config.py:28, 44, 149` | one script path, `loop_seq` | paths for `transitions.py`, `director_render.py`, `director_page.py`, and `reveal.py` for phase C |
| 2 | `config.py:30, 46, 151` | one plan folder, `scripts/research/plans/loops` | `director_plans` = `scripts/research/plans` (19 plans today) |
| 3 | `config.py:38-52` | the settings lack `fixtures`, `layers_dir`, `mattes_dir` | the fixture pairs and the director's `--layers-dir`, `--mattes-dir` (defaults at `director_render.py:35-36`) |
| 4 | `cli.py:90-115` | `check` prints, hashes and probes `loop_seq.py` alone | one row per new path with its md5 or count; the exit rule unchanged |
| 5 | `server/app.py:14, 30, 35` | `App.flows` is the loop registry; `flags` come from the loop probe | the enabled flows of the new flow registry |
| 6 | `registry/loop.py:258-273` | `FLOWS` holds the loop alone; `STAGE_ORDER` is its order | `registry/flows.py`: every flow, the enabled ones, `stage_def`, the union of stage names |
| 7 | `registry/hints.py:32-1170` | one 290-key table that both builders would edit | a hint module per flow, merged into `HINTS`, with a test that the keys are disjoint |
| 8 | `registry/rulings.py:24, 49, 102-104` | one 7-row table; `is_stage_knob` reads the loop's order | a table per flow; `is_stage_knob(knob, flow)` |
| 9 | `jobs/store.py:75-79` | the refusal names phase A1 and lists the loop | the message built from the enabled flows |
| 10 | `jobs/store.py:63`; `jobs/candidates.py:18`; `jobs/grades.py:50`; `runner/argv.py:136`; `views/job.py:465` | every job has a `seq` | `seq` in every job.json: the sequence, or the pair's name |
| 11 | `jobs/store.py:145-193` | a job is a folder of 2 or more JPGs, linked as `raw/<seq>/<nn>.jpg` | pair: two paths linked as `raw/<seq>/A.<ext>`, `B.<ext>`; director: a fixture pair that has a plan |
| 12 | `jobs/store.py:81-144` | adoption reads `in/<seq>/prep.json` | kept |
| 13 | `jobs/candidates.py:21, 29` | candidates are children of `<seq>/`, `drafts/<seq>/` and `drafts/` that hold `measure.json` | a spec per flow: folders, terminal file, mp4 name, fields to copy |
| 14 | `jobs/candidates.py:35-63` | a row's md5 and numbers come from `measure.json` | the md5 of `transition.mp4`, hashed and cached; the flow's own numbers |
| 15 | `jobs/candidates.py:68` | an adopted job's earlier verdicts are `agents/skeptic*.md` | kept |
| 16 | `jobs/grades.py:75-96` | one grade shape, his round text | the picks shape `{best, clips.<render>.{acceptable, note, props}}` for both two-photo flows |
| 17 | `jobs/plans.py:15-34, 60-75` | `frozen:` and the frozen list read the loop folder | the folder of the job's flow |
| 18 | `jobs/plans.py:78-81` | every `render` run resolves its `plan` knob as a loop plan | loop only: a director plan reference 404s here before its script starts |
| 19 | `jobs/plans.py:124` | `save_plan` validates with the loop grammar | a validator per flow |
| 20 | `runner/argv.py:23-71` | the flag probe runs `loop_seq.py --help` | kept for the loop; the director's flags are facts of its md5 05cd6e1d… |
| 21 | `runner/argv.py:35-37` | `script_arg` names the loop script | the record's own `argv[1]` |
| 22 | `runner/argv.py:74-129` | knob types stop at int, float, bool, list and str | a `dict` type for the director's `--set` table: one `--set k=<json>` per key |
| 23 | `runner/argv.py:141-265` | one chain by stage name with prep paths, `loop.mp4`, `--set in=` and `{seq: notes}` | one argv module per flow behind a dispatcher |
| 24 | `runner/process.py:42-47, 251` | the "unchanged" files by stage name: `loop.mp4` for every render | identity patterns on each stage definition |
| 25 | `runner/process.py:78-86` | the round rule reads stage `render` and knob `draft` | every render stage carries an int `draft` knob (0 = full) |
| 26 | `runner/process.py:87-90` | a `registration` waits while another record runs | kept: the name is loop-only |
| 27 | `runner/process.py:101` | warnings are computed without the flow | the flow passed through |
| 28 | `runner/process.py:136` | `script_md5` hashes `loop_seq.py` for every record | the md5 of `root / argv[1]` |
| 29 | `runner/process.py:163-200` | the output goes to a `.part` path that is renamed on success | every script stage needs an output flag; `director_page.py` has none |
| 30 | `runner/process.py:183-199, 241-250` | the prep move, the kept page and the depth maps are keyed by stage name | kept: the names mean the same in every flow |
| 31 | `runner/process.py:279-308` | only a finished `page` record opens a round | a shared `open_round` that a page written by the studio can call |
| 32 | `runner/process.py:324, 361` | a live process runs the loop script into the record's `.part` | the record's own `argv[1]` |
| 33 | `views/job.py:23-81, 101-109, 163` | the prep and readers views run for every job | the loop's tile context only |
| 34 | `views/job.py:209-309` | the tiles are one chain by stage name | a tile table per flow and stage |
| 35 | `views/job.py:93-98, 316` | `is_draft` reads the `draft` knob | the convention of row 25 |
| 36 | `views/job.py:396-422` | `job_view` adds prep, readers, probe, the frozen plans and the loop flags | extras per flow; the loop's key set kept |
| 37 | `views/render.py:33-34, 53, 62` | the view reads `measure.json`, `frames.json` and `loop.mp4` | a render view per flow |
| 38 | `views/page.py:58-60, 75` | the page knobs are title, intro, footer and variants | knobs read from the flow's page stage; `director_page.py` takes `--title --notes --head --key` and lists every candidate |
| 39 | `views/models.py:18-23, 58-69` | the models list and the registry view hold loop values | the same keys; `stage_order` stays a list |
| 40 | `views/measures.py:156` | `probe_view` reads the prep | kept |
| 41 | `media/pictures.py:53, 69-74` | `frames_dir` decodes `loop.mp4`; `still/<i>` is a prep still | the candidate's mp4 name; `raw/<i>` serves the two inputs |
| 42 | `server/routes.py:84-86, 143` | the frozen-plan route reads the loop folder; `POST /api/jobs` defaults to the loop and reads folder, adopt, seq | a director plan route; `a`, `b`, `pair` passed through |
| 43 | `server/routes.py:201-228` | one route table and one coverage walk | route lists per flow, spliced before the two fallback rows |
| 44 | `server/handler.py:140-148` | files come from the job root and the job folder | read-only `fixtures/`, `layers/`, `mattes/` as well (`STUDIO.md §5`; `director_ui.py:727-741`) |
| 45 | `web/index.html:16-30`; `web/js/rail.js:13-18` | the "new loop job…" and adopt forms post `flow: 'loop'` | a form per enabled flow, supplied by the flow's script |
| 46 | `web/js/rail.js:4, 9`; `web/js/strip.js:8` | labels read `j.seq` and `v.job.seq`; the subtitle counts "stills" | works once every job.json has `seq`; the inputs' word per flow |
| 47 | `web/js/panels.js:7-10` | `renderPanel` picks the panel by stage name | a panel table per flow, declared in `core.js` |
| 48 | `web/js/panels.js:13, 33, 38, 43` | the paths `raw/<seq>/` and `in/<seq>/` | kept |
| 49 | `web/js/panels.js:61, 66` | a candidate row prints step max and seam; the empty text names drafts at 960 | a candidate row per flow |
| 50 | `web/js/panels.js:77-79` | the page panel holds the variants control and the title "<seq>: round n" | a page panel per flow; the director's page lists every candidate |
| 51 | `web/js/panels.js:84, 86` | `wirePanel` starts the viewer for loop stage names | a wire hook per flow |
| 52 | `web/js/viewer.js:9, 14-21, 49-51` | the hosts, the sources and the A and B pictures come from the prep's `k<i>.png` | sources per flow: `canvas_A.png`, `canvas_B.png`, the two inputs, the relation's frames |
| 53 | `web/js/viewer.js:135-150` | the axis plots `steps`, `seam_step`, the stalls and the jumps | the flow's own series, such as the director's motion numbers |
| 54 | `web/js/inspector.js:10` | inputs special-case `measure.render` and a `plan` select | an editor for a `dict` knob (the `--set` table) |
| 55 | `web/js/inspector.js:12, 16-19` | the render note and the measures block use the loop's terms | hooks per flow |
| 56 | `web/js/graph.js:11, 13` | `G_HOSTS` and `G_COST` list loop stages; the cost sentences sit outside the prose test | data per flow, best on the stage definitions |
| 57 | `web/js/plan.js:43, 49, 212, 239-264` | `isStageKnob` reads `S.reg.stage_order`; the loop editor; the variants state | kept, with `stage_order` a list |
| 58 | `tests/conftest.py:25, 78-92` | the tmp root holds the fake `loop_seq.py` and `plans/loops/` | a table of fakes copied when present, and a tree folder copied in |
| 59 | `tests/conftest.py:44, 136-148` | `FLAGS`, `job` and `run()` are loop fixtures | fixtures per flow in the owners' own files |
| 60 | `tests/test_registry.py:66` | `list(FLOWS) == ["loop"]` | every flow listed, the loop first |
| 61 | `tests/test_registry.py:67-78` | the loop's 10 stages in order | kept; each flow pins its own order in its own file |
| 62 | `tests/test_registry.py:90, 103` | every backend starts `loop_seq.py `; every range is null | loop only: `transitions.py` states ranges for `--zoom`, `--color`, `--warp` |
| 63 | `tests/test_registry.py:57, 126, 135` | the hint prefixes, a hint's stage in `STAGE_ORDER`, the page-key regex | new prefixes (`report.`, `info.`, `set.`, `anchors.`); the union of stage names |
| 64 | `tests/test_registry.py:231, 272, 277` | 151 schema rows; 7 rulings that cite `loops.md §` | kept for the loop; the flows' tables pinned apart |
| 65 | `tests/test_jobs.py:49` | the message "the flow is one of ['loop']" | built from the enabled flows |
| 66 | `tests/test_prose.py:23-25` | sentences of the loop's stages and knobs | every flow's stages and knobs |
| 67 | `tests/test_server.py:282-328` | one walk over the table; 26 rows | the 26 shared rows pinned; each flow walks and counts its own |
| 68 | `tests/test_views.py:45-60, 228-249, 348-364` | exact key sets of the job view, the rail row and the registry view | kept for the loop by design |
| 69 | `tests/test_cli.py:27-34` | `check` exits 0 with the loop fake alone | kept: the exit rule stays |
| 70 | `tests/integration/test_loopseq_help.py:43` | knob flags checked against `loop_seq.py --help` | a `--help` test per flow script |

### The generalization slice: scope, order and proof

The simplest version would fix the three faults of the summary and let both builders edit the shared files at disjoint anchors. It breaks the rule that two subagents never own one file, and `registry/hints.py` alone holds 1,170 lines both builders would extend. One builder runs these steps in order instead, with `make qa` and `make test` green after each and `make acceptance` once at the end. Reversal: `[revert: git revert of the slice commit]`. The loop's argv, tiles and md5s are proved identical; the page's pixels change (the rail gains forms), and the detector covers that.

| Step | Files | Change | Proof |
|---|---|---|---|
| 1. Snapshot first | `tests/test_loop_snapshot.py` (new) | Pin as literals the argv of 8 loop runs on the fake job: registration, readers, probe, measure with and without `frames.json`, render full and draft, page with and without variants. Pin the tiles of two jobs and the rail row. | It passes on the tree before any edit (4f564b5) and after the slice. |
| 2. Settings | `config.py`, `cli.py`, `README.md`, `tests/test_config.py`, `tests/test_cli.py` | Add 8 paths: `transitions`, `reveal`, `director_render`, `director_page`, `director_plans` (the brief's `plans_dir`, renamed because the folder also holds `loops/`), `fixtures`, `layers_dir`, `mattes_dir`. Scripts and plans derive from the root, as `loop_seq` does (`config.py:149-151`). Add `REVEAL_STUDIO_LAYERS_DIR` and `REVEAL_STUDIO_MATTES_DIR` (flag, then environment, then the renderer's default). `check` prints each with its md5 or count. | `test_cli.py:27-34` stays green: a missing new script prints MISSING and leaves the exit code alone. |
| 3. Registry | `registry/entries.py` (new: `K`, `H`, `Ruling`); `registry/flows.py` (new); `registry/loop.py`; stubs `registry/pair.py`, `registry/director.py`, `registry/hints_pair.py`, `registry/hints_director.py`; `registry/hints.py`; `registry/rulings.py` | `flows.py` holds every flow, the enabled ones, `stage_def`, `stage_order(flow)` and the union `STAGE_NAMES`. Each loop stage gains `identity` patterns. The stubs carry `enabled: False` and empty stage lists. 7 source files and 7 test files switch their imports to `flows.py`. | `STAGE_ORDER`, the 290 hints, the 151 schema rows and the 7 rulings keep their values. |
| 4. Jobs | `jobs/store.py`, `jobs/candidates.py`, `jobs/plans.py`, `jobs/grades.py`, `jobs/rounds.py` (new) | Every job.json carries `seq`. Add the pair and director creators. `candidates()` keeps the loop function and adds a spec reader with the md5 cache. Plans get a folder and a validator per flow. Add the picks writer and `open_round`. | The loop job.json, its candidate rows and its round.json keep their keys. |
| 5. Runner | `runner/argv.py`, `runner/argv_loop.py` (new), stubs `runner/argv_pair.py`, `runner/argv_director.py`, `runner/process.py` | The loop chain moves verbatim into `argv_loop.py`, one function per stage; the dispatcher imports the flow modules inside `argv_for` (the precedent is `jobs/store.py:83`). Add the `dict` knob type. `process.py` reads `argv[1]` and the identity patterns, and passes the flow to the warnings. | The argv snapshot; `test_runner.py` (24 test functions). |
| 6. Views | `views/job.py`, `views/tiles_loop.py` (new), stubs `views/pair.py`, `views/director.py`, `views/render.py`, `views/page.py` | `stage_views` keeps the base tile and the stale rule and calls a tile table per flow. `job_view` adds extras per flow. `render_view` dispatches by flow. The page gate builds its knobs from the flow's page stage. | The tile snapshot; `test_views.py`; `test_compat.py`. |
| 7. Media and server | `media/pictures.py`, `server/route.py` (new: `Route`, `_r`, `JOB`), `server/routes.py`, stubs `server/routes_pair.py`, `server/routes_director.py`, `server/handler.py`, `server/app.py` | `frames_dir` decodes the candidate's mp4. Flow route lists are spliced before the fallback rows. `POST /api/jobs` passes `a`, `b`, `pair`. The file route adds three read-only prefixes. | `len(routes.CORE) == 26`; the route walk. |
| 8. Contracts | `.importlinter`, `.claude/conventions/studio.md` (a dated row) | Forbid `director_render`, `director_page`, `director_ui`, `layered_probe`, `nest_probe`, `matte_source`, `layer_merge`, `chain_luma`. | `lint-imports`: 3 contracts kept. |
| 9. Page | `web/js/core.js`, `panels.js`, `viewer.js`, `inspector.js`, `graph.js`, `rail.js`, stubs `pair.js`, `director.js`, `web/css/pair.css`, `director.css`, `web/index.html` | `core.js` declares `FLOW_UI`, one table per flow; each script registers its own loop entries at load. The rail draws a "new job" button per enabled flow that has a form. `index.html` gains the stub tags before `boot.js`. | `test_registry.py`'s page scans; a Playwright drive of a loop job; the detector at 2560×1440, 1440×900 and 1280×800. |
| 10. Tests | `tests/conftest.py`, `test_registry.py`, `test_jobs.py`, `test_prose.py`, `test_server.py` | `make_root` copies each fake of a table when its file exists. A `fixture_pair` fixture writes two JPEGs and a minimal director plan with cv2 at test time. The count assertions become per flow (rows 58-67 of the table above). | `make qa` on the slice: the unit count grows and every old test passes. |

The shapes the slice fixes for both builders:

```python
# registry/flows.py (new)
ALL_FLOWS = {"loop": loop.FLOW, "pair": pair.FLOW, "director": director.FLOW}
FLOWS = {k: f for k, f in ALL_FLOWS.items() if f["enabled"]}      # what the page offers and POST /api/jobs accepts
STAGE_NAMES = list(dict.fromkeys(s["name"] for f in ALL_FLOWS.values() for s in f["stages"]))
# a flow's candidate spec, read by jobs/candidates.py (the loop keeps its own function)
PAIR_CANDIDATES = {"full": ["{seq}"], "draft": ["drafts/{seq}"], "terminal": "report.json", "mp4": "transition.mp4",
                   "record_knobs": ["preset"]}   # copied from the render record whose out_final is the folder (b_pair_research.md:186)
DIRECTOR_CANDIDATES = {"full": [""], "draft": ["drafts"], "terminal": "info.json", "mp4": "transition.mp4"}  # the root's own children, as director_page.py reads them
```

| Flow | `seq` | other job.json keys | inputs |
|---|---|---|---|
| loop | the sequence (unchanged) | `source_folder` or `adopted_from` | `raw/<seq>/<nn>.jpg` |
| pair | the fixture pair, or a slug of the two file stems | `fixture` (the pair or null) | `raw/<seq>/A.<ext>`, `B.<ext>`, each with `role` |
| director | the fixture pair | `pair` | `raw/<seq>/A.<ext>`, `B.<ext>` from `fixtures/<pair>_S.*` and `_F.*` |

What the Runner reads from the stage definition after the slice:

| Method | loop-specific today | flow-neutral after the slice |
|---|---|---|
| `start_stage` | the round rule, the registration wait, the warnings, `script_md5` | the `draft` convention; the wait by name; the warnings with the flow; the md5 of `argv[1]` |
| `finalize` | the terminal file under `.part`, the prep move, the kept page, the replace rule, the depth maps, `IDENTITY` | unchanged except the identity patterns, read through `job.json`'s flow |
| `after_done` | a page opens a round and writes `page.md5` | the same, through `jobs/rounds.open_round` |
| `pid_alive`, `reconcile`, `cancel` | the loop script in the `ps` arguments | the record's `argv[1]` |

The import contracts allow `registry/__init__.py` to import the flow modules. The layers contract checks imports between layers only; `rulings.py:24` already imports `registry.loop`, and `lint-imports` kept all 3 contracts on this tree. The slice still keeps `__init__.py` a docstring and puts the flow table in a new `registry/flows.py`. Then importing `registry.schema` loads zero flow modules, and a flow module imports `registry.entries` without a cycle.

The `draft` convention keeps three rules free of new code: the round rule (`process.py:78`), `is_draft` (`views/job.py:93`) and the stale rule for the page (`views/job.py:316`). The rail's last render (`views/job.py:453`) filters by the stage name `render`, so it holds by the naming convention. `argv_director.py` maps `draft` to `--max-long` (draft, or 1920 when 0); the pair track maps it the same way (`b_pair_research.md:46`). The alternative, a `draft` policy field on each stage, costs one field and three call sites.

The fakes the builders write, copied into every tmp root by the slice's table. Fixture images are generated at test time with cv2, as `write_stills` does (`tests/conftest.py:117-128`), and never committed as binaries.

| Fake (copied to) | writes | owner |
|---|---|---|
| `tests/fakes/transitions.py` (`<root>/transitions.py`) | `pair A B --out DIR`: `transition.mp4` by cv2's mp4v, `strip.jpg`, then `report.json` with `class`, `method`, `quality`, `canvas`, `n_frames`; a `FAILED:` line and exit 2 under `FAKE_REFUSE` | P |
| `tests/fakes/director_render.py` (`scripts/research/`) | under `--resolve-only`: `canvas_A.png`, `canvas_B.png`, `anchors.json`, then `info.json`; a render: `transition.mp4`, `montage.jpg`, then `info.json` with the keys of the recorded run (`motion_median_px`, `motion_pauses`, `motion_jumps`, `b_inside_first`, `residual_edge_max`, `halo`; DECISIONS 2026-11-05 eighth line) and `plan_sha256`, `renderer_md5`, `transitions_md5`, `layers_dir`, `mattes_dir` (`director_render.py:2099-2102`); `PROGRESS i n` lines under `--progress`. The full key list is the director track's. | D |
| `tests/fakes/director_page.py` (`scripts/research/`) | `index.html` over the run folder's children that hold `info.json`, to `--out` when D adds that flag | D |
| D's own test fixtures | `layers_v3/<photo>/layers.json` and `layers.npz`; `mattes/<photo>/el_<id>.png`, the shapes of the real folders | D |

### Wave 2 ownership: builder P and builder D in parallel

| Builder | owns | Edit-only | tests it pins |
|---|---|---|---|
| P, the pair flow | `registry/pair.py`, `registry/hints_pair.py`, `runner/argv_pair.py`, `views/pair.py`, `server/routes_pair.py`, `web/js/pair.js`, `web/css/pair.css`, `tests/fakes/transitions.py`; if phase B builds Reveal's verdict, `registry/common.py` and `runner/argv_common.py` | zero files: the picks writer and `open_round` land in the slice | `tests/test_pair_flow.py`, `tests/test_server_pair.py`, `tests/integration/test_transitions_help.py`, `tests/acceptance/test_b_pair_flow.py` |
| D, the director flow | `registry/director.py`, `registry/hints_director.py`, `runner/argv_director.py`, `views/director.py`, `server/routes_director.py`, `web/js/director.js`, `web/css/director.css`, `tests/fakes/director_render.py`, `tests/fakes/director_page.py`; `scripts/research/director_page.py` if the `--out` option wins | `views/models.py` (rows for the layers and the mattes), `media/pictures.py` (a canvas thumbnail) | `tests/test_director_flow.py`, `tests/test_server_director.py`, `tests/integration/test_director_help.py`, `tests/acceptance/test_b_director_flow.py` (mismatch_3 at 01b3cf3c…) |
| the main thread | `studio/ARCHITECTURE.md`, `.claude/conventions/contracts.md`, `studio/GUIDE.md`, `STUDIO.md §13`, DECISIONS | — | the integrated gates |

After the slice, these shared files stay closed to both builders: `server/routes.py`, `registry/hints.py`, `web/js/panels.js`, `web/index.html`, `views/job.py`, `tests/conftest.py`, `runner/process.py`, `jobs/store.py`, `jobs/candidates.py`. D's new routes are `GET /api/pairs` (6 fixture pairs have a director plan today) and `GET /api/plans/director/<name>` (19 plans). An overlay route (`STUDIO.md §5`) is optional: the anchors in `anchors.json` can be drawn as SVG over `canvas_A.png` with zero new routes and zero cv2. P likely needs zero routes, because the relation and the renders ride `GET /api/jobs/<id>` and the existing render routes.

A third builder for the shared page is worse than the slice. P and D need the panel table, the viewer's sources, the new-job forms and the hints split before they write a panel; a shell builder in the same wave would make them wait or edit its files. If the session has capacity, a third builder L can take the loop items of "B (continued)" on disjoint files: the repaint leg in `loop_seq.py`, `plans/loops/SCHEMA.md`, `registry/schema.py`, the loop rows of `registry/hints.py` and `tests/fakes/loop_seq.py`, and sequences up to 10 stills. L touches the loop path, so the a2 md5 must reproduce after it. The request pickup at boot (backlog T74) is the owner's decision on `.claude/**`, and no builder takes it.

Collision points, ranked:

1. The shared test run: a red test in one builder's files fails `make qa` for both. Each builder runs its own test files while building and `make qa` before its report.
2. The drives: `wait_quiet` skips the loop acceptance while another record runs, and a second server re-attaches every job's running records (backlog T88). One rendering drive runs at a time: the loop, then the director, then the pair.
3. The hint keys across three tables: the slice's disjointness test turns red on a duplicate. Flow controls take the prefixes `control.pair_` and `control.director_`.
4. Reveal's verdict, an optional branch that both two-photo flows share (`b_pair_research.md:5, 17`): one owner. P owns it in `registry/common.py` and `runner/argv_common.py` and D imports them, or phase B defers it.
5. Job ids have one-second resolution (`studio/ARCHITECTURE.md`, the known defects table): two drives that create a job of the same pair in the same second share a folder. Each drive uses its own pair.

Order: the slice, its gates and a commit; then P and D in parallel; then the main thread integrates and runs the drives one at a time; then the Fable review, the critique with the detector, and the fix round.

### Risks to the loop path and the check for each

| Risk | what would break | check |
|---|---|---|
| the argv moves into `argv_loop.py` | the a2 md5 and the prep `cmp` | the argv snapshot (unit, on CI); `make acceptance` with a2 c302623f…, the 960 draft 3d453980…, the 480 draft 2955c25c… |
| the tiles move into a table | a tile's state, detail, thumbnail or stale flag | the tile snapshot; the 11 view tests at `test_views.py:42-249`; `test_compat.py` on the three jobs of 2026-11-04 |
| the process check reads `argv[1]` | the re-attach after a restart; the stranger pid on cancel | `test_runner.py:187` (stranger pid), `:278` (re-attach) and its other 22 test functions |
| `script_md5` comes from `argv[1]` | the record's stamp | `test_a1_loop_flow.py:262`, `test_a2_loop_flow.py:186` |
| identity patterns come from the registry | the "unchanged" chip | `test_runner.py:331` (registration rerun), `:426` (same mp4) |
| the panels, viewer and graph dispatch by flow | the page itself, which the API-level tests never load | a Playwright drive of a loop job on a free port with its own `--lock`; the detector at 3 viewports; the keyboard drive |
| the hints merge | the 290 keys and their prose | `test_prose.py`; the disjointness test; `len(HINTS) == 290` right after the slice |
| the route splice | the 26 rows and their order | the route walk; `len(routes.CORE) == 26` |
| new modules in the layers | the three import contracts | `lint-imports` (3 kept on 2026-11-05) |
| the GitHub workflow | `make qa` on ubuntu, unit layer only | the fakes use the dev venv's stdlib, cv2 and numpy; `uv sync --frozen` with zero new packages |
| a job.json written without `seq` | the rail of the package and of the owner's live server | a unit test that every created job.json carries `seq` |

### Radon: split stage_views in the slice

`radon cc src -n C -s` on this tree (2026-11-05) grades `stage_views` F (92), `Runner.finalize` F (57), `argv_for` E (39), `graph_view` E (35), `probe_view` D (25), `fits_summary` D (24), `job_row` D (24) and `create_job` D (22). The average is B (6.07) over 182 blocks. `make audit` prints the grades and passes whatever they are (`studio/Makefile:53`).

Split `stage_views` now. The tile table per flow and stage is what lets P and D add tiles without editing `stage_views`, so the slice touches the function anyway. The cost is about 100 lines moved (`views/job.py:209-309`) into ten loop tile functions with one lazy context object, plus the tile snapshot test. The expected grades after are C or better for `stage_views` and A to C per tile [estimate; radon not run on the new code]. `argv_for` splits into one function per stage by the move. `create_job` splits into four creators. Leave `Runner.finalize` alone beyond the identity hook: the restart, cancel and reconcile rules live there, and the backlog's radon row (T96) stays open for it.

### Relevant artifacts

| path:line | symbol | purpose |
|---|---|---|
| `studio/src/reveal_studio/registry/loop.py:258-273` | `FLOWS`, `STAGE_ORDER`, `stage_def` | the flow table the slice moves to `registry/flows.py` |
| `studio/src/reveal_studio/runner/process.py:42-47, 136, 324` | `IDENTITY`, `start_stage`, `pid_alive` | the three Runner rules that name the loop script or its files |
| `studio/src/reveal_studio/runner/argv.py:132-266` | `argv_for` | the stage chain that moves to `argv_loop.py` |
| `studio/src/reveal_studio/views/job.py:149-334, 437-479` | `stage_views`, `job_row` | the tile chain, the stale rule, the rail row |
| `studio/src/reveal_studio/jobs/candidates.py:15-73` | `candidates` | the loop's candidate reader, kept beside a spec reader |
| `studio/src/reveal_studio/jobs/store.py:71-193` | `create_job` | the job creators, with `seq` for every flow |
| `studio/src/reveal_studio/server/routes.py:201-228` | `ROUTES` | the 26-row table the slice splits into shared rows and flow lists |
| `studio/src/reveal_studio/server/handler.py:140-148` | `Handler._safe_file` | the file route's bases |
| `studio/src/reveal_studio/web/js/panels.js:7-10` | `renderPanel` | the panel chain the slice turns into a table |
| `studio/tests/conftest.py:78-92` | `make_root` | the tmp root that gains a fakes table |
| `studio/tests/test_server.py:282-328` | `test_every_route_in_the_table_is_hit` | the route walk and the count of 26 |
| `studio/tests/acceptance/test_a1_loop_flow.py:94-99` | `wait_quiet` | the skip that hides a missed a2 md5 |
| `scripts/research/director_page.py:26-29, 41-45, 60, 173` | `main` | the page's flags, the folder rule, the plan lookup, the in-place write |
| `scripts/research/director_render.py:2077-2105` | the `__main__` block | the render's flags and its `info.json` |
| `transitions.py:1421-1453` | `render_pair` | the pair outputs, `report.json` written last |

### Constraints discovered

| Constraint | source | consequence |
|---|---|---|
| a layer imports only the layers below it; `runner` and `media` never import each other | `studio/.importlinter` (the layers contract) | the per-flow argv modules stay in `runner/`; the candidate spec reader stays in `jobs/` |
| intra-layer imports pass | `registry/rulings.py:24`; `views/job.py:17-18`; `lint-imports`: 3 kept | `registry/flows.py` and `views/tiles_loop.py` need zero contract changes |
| a research script gains default-off flags only, proved byte-identical on the default path; `transitions.py` and `reveal.py` stay unchanged without his word | `.claude/skills/reveal/references/studio.md`; `STUDIO.md §7` | the pair keeps zero progress lines; a `--out` on `director_page.py` needs a `cmp` of its page before and after |
| `stage_order` stays a list | `web/js/plan.js:43` reads it with `.includes` | the registry view serves the union of stage names as a list, loop's 10 first |
| a stage name must differ from the loop's plan keys (`seq in title gag timeline effects matte crf gif_long crop`) | `registry/rulings.py:102-104`; `web/js/plan.js:43` | a ruling's first segment decides stage knob or plan path |
| the job view, the rail row and the registry view are pinned as exact key sets | `tests/test_views.py:45-60, 228-249, 348-364` | new keys go on the new flows' views only |
| two subagents never own one file | `.claude/conventions/studio.md`; `references/studio.md` | one module per flow in every layer |
| CI runs the unit layer on ubuntu with no main venv | `.github/workflows/studio.yml` | each fake is self-contained Python with cv2 and numpy |
| the director's `--layers-dir` and `--mattes-dir`, passed with the default values, resolve to the default folders | `director_render.py:2086-2092` | the B anchor's md5 holds with both flags passed [INFERRED from the code; not run] |

### Confidence: 80%

The 70 assumptions come from reading every module under `src/reveal_studio/`, the nine page scripts, `index.html` and the test files. The counts (290 hints, 151 schema rows, 7 rulings, 26 routes, 22 loop knobs), the radon grades and the import contracts come from commands run on this tree on 2026-11-05. The slice and the ownership split are design: their cost, their radon grades and their fit with the director track's findings stay UNVERIFIED until a builder runs them. The behaviour of `director_page.py` and of the owner's live server is read from the source and from git, and was not run.

### Gaps

| Gap | effect | who closes it |
|---|---|---|
| the director track's report was absent when this report was written (only `b_pair_research.md` existed at 15:42) | the director's stages, its 26 `--set` keys and its picks props are unchecked against this design | the main thread, when it consolidates the three reports |
| the pair page (written by the studio, or a stdlib script stage) is undecided | the slice's `open_round` hook is needed only for the studio-written page | the main thread or the owner |
| the output path of `director_page.py` (`--out`, or a staging folder) is undecided | the Runner's `.part` rule holds for the director's page only with one of them | the main thread, on builder D's proposal, with a DECISIONS line |
| `info.json`'s per-frame series is unread | whether the shared axis can plot the director's motion is UNVERIFIED | builder D |
| vulture on the stub modules was not run | stubs with unused arguments may need care; the route functions with unused `m` and `body` pass today | the slice builder |
| pytest, the server and the acceptance were not run (the brief forbids them) | every test and drive claim above is a reading of the code | the slice builder |

Tool failures during this track: three MCP servers failed to connect (claude-design with HTTP 403, mcp-memory-service, postgres-mcp with "connection closed"), and this track used none of them. A `grep --include=*.py` failed on a zsh glob and was rerun without the flag. A `find studio/web` named a wrong path; the page lives under `studio/src/reveal_studio/web/`. An `ls scripts/*page*` matched nothing and exited 1. The Serena memory leaves were read as files, without the Serena tools.
