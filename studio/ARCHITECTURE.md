# reveal-studio: architecture

This file maps the modules of reveal-studio 0.2.0 as of 2026-11-06, after phase B (commit 0a5a260) and its fix round. It
also covers the data flow, the import contracts, how the settings reach the code, the test layers, and each hard
constraint with the test that holds it.

The design of record is `.claude/claude-docs/STUDIO.md` at the repo root (its section 13 records the package). The
package ported `scripts/research/studio.py` (phase A1; retired on 2026-11-05 once the acceptance drive passed) and
keeps its URL grammar, its JSON shapes and its job folder layout. Phase A2 (2026-11-05) added the plan schema, the
rulings, the page's variants, the probe and measure stages, the fits table, the stalls and jumps, the stability plot,
the comparator modes and the graph view (`.claude/claude-docs/research/2026-11-05/plan_editor.md`, `views_a2.md`).

## Phase B (2026-11-05)

Phase B made every layer dispatch by the job's flow and added the pair transition and director plan flows beside the
loop; all three flows are enabled. The package grew from 34 Python files and 5,450 lines (commit 4f564b5, after phase
A2) to 55 files and 11,785 lines, and to 11,875 lines after the fix round. The reports are under `.claude/claude-docs/research/2026-11-05/`, beside the design
note `b_design.md`.

| Part | What it adds | Report |
|---|---|---|
| the generalization slice | the flow table (`registry/flows.py`) and Reveal's verdict as one stage the two-photo flows share. Eight Settings paths, `jobs/rounds.open_round` and the argv dispatcher over one module per flow. One tile function per stage, each flow's route list spliced before the two fallbacks, and the page's `FLOW_UI` table | `b_slice.md` |
| the pair transition flow | seven stages over `transitions.py pair`: import (two photos linked), verdict, relation (480 px, 1 s), render (14 knobs), skeptic, page (written by the studio), grades (the picks shape) | `b_pair_build.md` |
| the director plan flow | eight stages over `director_render.py` and `director_page.py`: import (by pair name), verdict, resolve, plan (the renderer's `--set` table as data, 112 rows), render, skeptic, page (written in place), grades (the picks shape) | `b_director_build.md` |
| the loop flow | the `repaint` leg method of `loop_seq.py`, default-off, with 4 schema entries and 4 hint rows (builder L); the import chips above 6 and 10 stills (the slice) | `b_loop_build.md`, `b_slice.md` |
| the fix round (2026-11-05 22:30 to 2026-11-06 00:20) | 49 of the 50 items the review, the critique and the acceptance drive listed. The restart rule for an in-place record and for a record another server finalizes. A button inert while its request runs. The director's knobs read-only in the inspector, its next render's controls in the side column, one grade form per round, and its timeline keys | `b_fixes.md` |

## Module map

All modules sit under `src/reveal_studio/`. "Imports" lists the package's own modules only, as their import lines name
them on 2026-11-05.

| Module | Owns | Imports |
|---|---|---|
| `__init__` | `__version__` ("0.2.0") | nothing |
| `__main__` | `python -m reveal_studio` | `cli` |
| `cli` | the `serve`, `requests` and `check` commands; since phase B `check` also prints `flow_rows`: the md5s of the pair's and the director's four scripts and the counts of the director plans, the fixture pairs, the layer tables and the mattes | the root package, `config`, `fs`, `jobs.store`, `runner.argv`, `runner.lock`, `server.app`, `views.models` |
| `config` | `Settings` (frozen; since phase B it adds `transitions`, `reveal`, `director_render`, `director_page`, `director_plans`, `fixtures`, `layers_dir`, `mattes_dir`), `resolve_settings`, `ConfigError` | the root package, for `__version__` |
| `errors` | `StudioError(msg, code, extra)` | nothing |
| `fs` | file md5 and sha256, JSON read and atomic write, `rel`, `inside`, `tail_lines`, `stamp`, `now_iso`, `log` | nothing |
| `registry.entries` | `K` (a knob, of type `int float str bool list plan object`), `H` (a hint) and `merge_hints` (a key in two hint tables fails the import); every flow and hints module imports them from here | nothing |
| `registry.flows` | `ALL_FLOWS` (loop, pair, director), `FLOWS` (the enabled ones), `STAGE_NAMES` (the union of the stage names in flow order, 13), `flow_def`, `stage_def`, `stage_order`, `identity_of` | `errors`, `registry.common`, `registry.director`, `registry.loop`, `registry.pair` |
| `registry.common` | `VERDICT_STAGE` and `COMMON_STAGES`: Reveal's verdict, the optional branch under the import that the pair and director flows share; its name is reserved in every flow | nothing |
| `registry.loop` | `LOOP_STAGES`, `FLOW`, `STAGE_ORDER`: the loop flow's 10 stages with their knobs (import, registration, readers, probe, plan, render, measure, skeptic, page, grades). Probe and measure are branch stages with `parent`, `branch` and `stale_after`. A script stage names its `script` and its `identity` files | `registry.entries` |
| `registry.pair` | the pair flow's 7 stages (import, verdict, relation, render, skeptic, page, grades), the render's 14 knobs with the 5 ranges `TransitionSpec.clamp` states, `PRESETS` (7), `RELATION_LONG` (480), `RELATION_SECONDS`, `RESERVED_NAMES` (12 folder names a pair may not take), the candidate spec | `registry.common`, `registry.entries` |
| `registry.director` | the director flow's 8 stages (import, verdict, resolve, plan, render, skeptic, page, grades). `SET_KEYS` is the renderer's `--set` table as data, 112 rows: table A 26 top-level keys, B 18 sky keys, C 60 transform keys, D 8 read-only keys that change no frame. Also `set_key_problem` and the candidate spec | `registry.common`, `registry.entries` |
| `registry.hints` | `LOOP_HINTS`, the loop's 296 rows: the 290 of A2's fix round, the 2 still-count chips, the 4 repaint rows. `HINTS` merges them with the pair's and the director's into the one table the page and the tests read: 559 rows since the fix round, 555 before | `registry.entries`, `registry.hints_director`, `registry.hints_pair` |
| `registry.hints_pair` | the pair flow's 67 hint rows: `control.pair_` 22, `report.` 32, `relation.` 6, `verdict.` 7 | `registry.entries` |
| `registry.hints_director` | the director flow's 196 hint rows: `control.director_` 26, `director.` 14, `resolve.` 9, `anchors.` 9, `info.` 26, `set.` 112 (built from `SET_KEYS`). The fix round added 4 `director.` rows, among them `director.plans` and `director.set_group` | `registry.director`, `registry.entries` |
| `registry.schema` | `PLAN_SCHEMA`: 155 entries in 22 groups since the repaint leg, each with path, type, default with its source, range, choices and hint key. The plan grammar's lists (`METHODS` holds 12), `ID_RE`, `NAME_RE` (60 characters since phase B), and `validate_plan`, which reads its choices from the schema | `errors` |
| `registry.rulings` | `RULINGS` (7 rows `{knob, value, since, why, source}`, each citing a DECISIONS line or a playbook section) and the matching of a plan or a stage's knobs against them (a warning, never a refusal) | `registry.flows` (for `STAGE_NAMES`), `registry.schema` |
| `jobs.store` | `studio_dir`, `job_dirs`, `find_job`, `load_job`, `job_root`, `prep_dir`, `list_stills`, `fixture_photos`, `director_plans_of`. `create_job` refuses a disabled flow, then calls the flow's creator: `create_loop_job`, `adopt_loop_job`, `create_pair_job` (a fixture pair or two photos; a name in `RESERVED_NAMES` is a 400) or `create_director_job` (a pair that a director plan names) | `config`, `errors`, `fs`, `registry.flows`, `registry.pair`, `registry.schema`; `jobs.candidates` inside `adopt_loop_job` |
| `jobs.records` | `records`, `record_dir`, `outputs_of`, `progress_of`, `command_line`, `elapsed_of` (the seconds a record has run, for the rail's running entries), `record_detail` (the pure part of `record_view`) | `config`, `errors`, `fs`, `registry.schema` |
| `jobs.candidates` | `candidates` (by flow), `loop_candidates` (the loop's renders, read from `measure.json`), `spec_candidates` (another flow's renders, read by the spec in its registry entry), `cached_md5` (an mp4's md5 kept under `cache/md5/`), `candidate`, `verdicts`, `rounds`, `requests_of` | `config`, `errors`, `fs`, `jobs.records`, `jobs.store`, `registry.flows`, `registry.schema` |
| `jobs.plans` | `frozen_dir` (the loop's `scripts/research/plans/loops/`, the director's `scripts/research/plans/`), `resolve_plan` and `save_plan` by the job's flow, `validate_director_plan`, `plans_of`, `frozen_plans`, `run_warnings`, `plan_diff` | `config`, `errors`, `fs`, `registry.rulings`, `registry.schema` |
| `jobs.rounds` | `open_round`, the one way a round opens: `page.md5` beside the page, a copy of the page under `rounds/<n>/` and `round.json` with the id of the record that wrote the page | `fs`, `jobs.candidates` |
| `jobs.grades` | `write_request` (for a director job the answer's shape adds `look` and `faults`), `check_picks`, `save_picks` (`picks/<flow>_picks_<stamp>.json` after the shape check), `save_grade`, `mark_frame`, `owner_frames` | `config`, `errors`, `fs`, `jobs.candidates` |
| `runner.argv` | `ScriptFlags`, `probe_script_flags`, `coerce`, `as_object`, `as_list`, `SCRIPTS` (the 5 Settings keys a stage's `script` may name), `script_rel`, `builder_of`. `flags_of`: an object knob gives one `--set k=<json>` per key, keys sorted. `argv_for` dispatches: a shared stage goes to `runner.argv_common`, any other stage to its job's flow module | `config`, `errors`, `fs`; inside `builder_of`, `runner.argv_common`, `runner.argv_director`, `runner.argv_loop` and `runner.argv_pair` (each of them imports this module) |
| `runner.argv_common` | `argv_verdict`: `reveal.py align A B --out <job>/verdict.part` on the job's two linked photos | `config`, `errors`, `fs`, `runner.argv` |
| `runner.argv_loop` | the loop's argv, one function per `loop_seq.py` stage (registration, readers, probe, render, measure, page), moved verbatim from `runner.argv` by the slice | `config`, `errors`, `fs`, `jobs.candidates`, `jobs.plans`, `jobs.store`, `registry.schema`, `runner.argv` |
| `runner.argv_pair` | `argv_relation` (480 px and 1 s into `<job>/relation.part`), `argv_render` (one `--max-long`: the `draft` knob when above 0, else `max_long`), `render_name`, `photos` | `config`, `errors`, `fs`, `jobs.store`, `registry.pair`, `registry.schema`, `runner.argv` |
| `runner.argv_director` | `argv_resolve` (into `<job>/resolve/<stamp>`), `argv_render` (into `<job>/run/<stem>_<concept>[-<tag>]`, a draft into `<job>/drafts/`) and `argv_page` (`director_page.py <job>/run …`, written in place). The checks before a script starts: the concept against the plan, `check_set` (a `--set` key that reaches no frame is a 400), and fewer than 3 frames | `config`, `errors`, `fs`, `jobs.candidates`, `jobs.plans`, `jobs.store`, `registry.director`, `registry.schema`, `runner.argv` |
| `runner.process` | `Runner`: `start_stage`, `finalize`, `after_done` (a done page record opens its round through `jobs.rounds`), `pid_alive`, `reconcile`, `reconcile_all`, `cancel`. `script_of`: the script is the record's own `argv[1]`. The in-place rule: a stage whose `.part` path equals its final path keeps the previous file as `<record>/previous_<name>`. Since the fix round: `_written_since` (a terminal file written after the record started), `Runner._finished_elsewhere` (a record another server finalizes is left to it), and a refused stage's `.part` folder removed | `config`, `errors`, `fs`, `jobs.candidates`, `jobs.plans`, `jobs.records`, `jobs.rounds`, `jobs.store`, `registry.flows`, `runner.argv` |
| `runner.lock` | `take_lock`, `LockHeld` (the handle stays open for the server's life; `serve` closes it, which releases the lock) | `config`, `errors`, `fs` |
| `media.pictures` | `jpeg_thumb`, `frames_dir` (one decode lock per render; it decodes the candidate's `mp4`), `thumb_path` (since phase B also a director job's latest resolve canvas), `DECODE_LOCKS`; cv2 is imported inside its functions | `config`, `errors`, `fs`, `jobs.candidates`, `jobs.store` |
| `media.pair` | `step_series`: the step series of a pair's decoded `transition.mp4` (the mean grey difference between neighbouring frames on a 480 px proxy) with the decode's frame count, size, rate and darkest frame, cached under `cache/steps/` by the mp4's md5 | `fs` |
| `media.overlays` | `overlay_png` (a director job's four overlays `base`, `elements`, `disparity`, `matte_<id>`, cached under `cache/overlays/`), `step_series` (a director render's decoded steps), `photo_of`, `table_dir`, `matte_dir`, the colours of the 22 element groups | `config`, `errors`, `fs`, `media.pictures` |
| `views.base` | `TileContext` (the lazy reads a tile function takes), `base_tile`, `mark_stale` (the stale rule over a flow's tiles), `attempt_note` (a failed or cancelled attempt beside a done tile). Also `is_draft` (a draft is no upstream of the page), `render_fps`, `file_url`, and `base_render_view` (the frames, the mp4 URL, `fps`, `frames_tags`). Since the fix round, `skeptic_state`: a two-photo skeptic tile reads waiting, answered, or "answered (0 verdicts)" | `config`, `fs`, `jobs.candidates`, `jobs.grades`, `jobs.plans`, `jobs.records`, `jobs.store`, `media.pictures`, `registry.schema` |
| `views.job` | `stage_views`: each stage's base tile, then its flow's tile function, then `mark_stale`. `graph_view` (ports and file edges from the records), `job_view` (the 14 keys every flow shares plus the flow's `extras`), `record_view`. `job_row(settings, d, runner=None)` reconciles a running record whose process is gone through the Runner; `running_entry` gives the rail `{id, stage, name, elapsed_s, progress}` | `config`, `fs`, `jobs.candidates`, `jobs.grades`, `jobs.plans`, `jobs.records`, `jobs.store`, `registry.flows`, `runner.process`, `views.base`, `views.director`, `views.measures`, `views.pair`, `views.tiles_loop` |
| `views.tiles_loop` | the loop's tile functions (`TILES`, one per stage), `prep_summary` (with `fits`, `windows`, `windows_jpg`), `readers_summary`, `readers_moved` (the folder a later registration moved), `still_count_warnings` (the chips above 6 and 10 stills), `extras` (the loop's frozen plans) | `config`, `fs`, `jobs.candidates`, `jobs.plans`, `jobs.store`, `views.base`, `views.fits`, `views.measures` |
| `views.pair` | the pair's tiles (`TILES`), `extras` (`relation`, `verdict`), `relation_view`, `relation_frames`, `verdict_view`, `fixture_pairs`, `bars` (the report's numbers against their recorded bars), `render_view`, and `build_pair_page`: the page the studio writes (`index.html`, `page_A.jpg`, `page_B.jpg`) with a builtin page record | `config`, `errors`, `fs`, `jobs.candidates`, `jobs.records`, `jobs.rounds`, `jobs.store`, `media.pair`, `media.pictures`, `registry.pair`, `registry.schema`, `runner.argv`, `views.base` |
| `views.director` | the director's tiles (`TILES`); `extras` (`director`, `resolve`, `verdict`, and this pair's plans as `frozen_plans`); `pairs_view`, `map_knob`, `last_round`, `render_view`. `plan_view`: the concept's knob map in both name forms, the `--set` rows with this concept's defaults and conditions, the beats as bars, and the last round's knobs for the button | `config`, `errors`, `fs`, `jobs.candidates`, `jobs.plans`, `jobs.records`, `jobs.store`, `media.overlays`, `registry.director`, `views.base` |
| `views.render` | `render_view` by flow (`RENDER_VIEWS`): the loop's `loop_render_view` (with `measures`, `stability`, `stalls_and_jumps`, `frame_kinds`), the pair's and the director's from their own modules; `frame_tag`; every render view carries `fps` | `config`, `fs`, `jobs.candidates`, `jobs.grades`, `jobs.records`, `media.pictures`, `views.base`, `views.director`, `views.measures`, `views.pair` |
| `views.fits` | `fits_summary`: `prep.json`'s named windows under each fit (`all far chain ecc final`) as the registration panel's table | `fs` |
| `views.measures` | `frame_kinds` (a repaint frame reads as a blend since the repaint leg), `measure_runs`, `latest_stability`, `probe_view`. `stalls_and_jumps` applies the playbook's bars: a stall is two or more steps below 0.3 while motion is open; a jump reaches 0.3 and exceeds 3× its neighbours' mean, outside a cut or a snap | `config`, `fs`, `jobs.records`, `jobs.store` |
| `views.models` | `models_view` (the models, and since phase B the layer tables and the mattes with their counts from `director_inputs`), `open_requests`, `registry_view` (the enabled flows, `stage_order` as the union of the stage names, the hints, `plan_schema`, `rulings`, the frozen plans) | `config`, `fs`, `jobs.candidates`, `jobs.plans`, `jobs.store`, `registry.flows`, `registry.hints`, `registry.rulings`, `registry.schema`, `runner.argv` |
| `views.page` | `build_page`: the review gate over the listed candidates (`variants`), then the page stage's record, or for a builtin page stage the writer in `BUILTIN_PAGES` (the pair's); `page_variants` | `errors`, `fs`, `jobs.candidates`, `registry.flows`, `runner.argv`, `runner.process`, `views.pair` |
| `server.app` | `App` (the settings, the probed flags, the Runner, the enabled flows), `StudioServer` (bound to 127.0.0.1), `serve` | `config`, `fs`, `jobs.store`, `registry.flows`, `runner.argv`, `runner.lock`, `runner.process`, `server.handler` |
| `server.handler` | `Handler`: the Host check, the body rules, `_file` with Range, `_safe_file`; `read_only_file` (the file route's read-only bases) | the root package, `config`, `errors`, `fs`, `jobs.store`, `server.routes`; `server.app` for type checking only |
| `server.route` | `Route`, `_r`, `JOB`, `RouteFn`: the row every route list is built from | `fs`; `server.handler` for type checking only |
| `server.routes` | `CORE` (the 26 rows every flow shares, the two fallbacks among them), `ROUTES` (35 rows: `CORE`'s 24 other rows, the pair's 4, the director's 5, then the 2 fallbacks), `match`, `dispatch`, `WEB_DIR` | `errors`, `fs`, `jobs.candidates`, `jobs.grades`, `jobs.plans`, `jobs.records`, `jobs.store`, `media.pictures`, `registry.flows`, `server.route`, `server.routes_director`, `server.routes_pair`, `views.job`, `views.models`, `views.page`, `views.render`; `server.handler` for type checking only |
| `server.routes_pair` | the pair's 4 rows: `GET /api/fixtures`, `GET /api/jobs/<id>/relation`, `…/relation/frame/<i>`, `…/verdict` | `errors`, `fs`, `jobs.store`, `server.route`, `views.pair`; `server.handler` for type checking only |
| `server.routes_director` | the director's 5 rows: `GET /api/pairs`, `GET /api/plans/director/<stem>`, `GET /api/jobs/<id>/director/plans/<name>`, `…/overlay/(A\|B)/<kind>.png`, `…/thumb/canvas/(A\|B)` | `errors`, `fs`, `jobs.store`, `media.overlays`, `media.pictures`, `server.route`, `views.director`; `server.handler` for type checking only |
| `web/` | `index.html`, 6 style sheets under `css/` (`pair.css` and `director.css` since phase B) and 11 classic scripts under `js/` that share one global `S`. `plan.js` is the loop's plan editor (bars, schema forms, undo, "% faster", the JSON tab). `viewer.js` is the comparator (single, wipe, A/B, onion, difference at fit, 1:1, 2×) with the plots (steps, stalls, jumps, stability). `graph.js` is the graph view, and `strip.js` the strip with its branch row and the graph switch. `panels.js` holds the stage panels: the render's side column with its name, modes, sources and list; from 1800 px the registration, readers and probe panels put their tables beside a sticky viewer. `pair.js` holds the pair flow's panels, form and plots. `director.js` holds the director flow's panels, with the plan panel's timeline bars, `--set` table and knob map. `core.js` holds the shared helpers. `FLOW_UI` is the table of each flow's page entries, and `chipKey` maps a chip's text to its hint key. `focusKey`, `restoreFocus` and `focusQuiet` put the focus back by data attribute after a rebuild without opening a hint. A "?" button and a chip are no Tab stops. Since the fix round, `core.js` `busy(btn, fn)` keeps a button inert while its request runs, and `rail.js` `closeForms` closes the other new-job forms before one opens. Five `FLOW_UI` hooks came with it. `inspectorKnobs` lets a flow draw a stage's knobs in the inspector (the director's are read-only), and `runKnobs` gives the knobs a graph rerun sends. `vside` and `wireSide` draw and wire the side column's own controls; `skepticPlaceholder` is the skeptic form's example text | — |

The page's scripts load in this order: `core`, `rail`, `strip`, `panels`, `plan`, `viewer`, `inspector`, `graph`, `pair`,
`director`, `boot`. Each file runs in strict mode. At load time `rail.js` calls `core.js`'s `$()` to bind its buttons.
Each script that draws for a flow registers its entries with `core.js`'s `flowEntry(<flow>)`: the loop's come from
`rail.js`, `panels.js`, `plan.js`, `viewer.js`, `inspector.js` and `graph.js`, the pair's from `pair.js`, the
director's from `director.js`. `boot.js` calls `core.js`, `rail.js` and `strip.js` to start the page; the rail then
draws one "new <flow> job…" button per enabled flow. Every other top-level statement defines a function or a constant,
sets a key of `S`, or binds a listener. None of the 11 scripts is a placeholder.

## Data flow

1. `Handler` checks the Host header, then for a POST the body rules, then calls `routes.dispatch`. The first row
   of `ROUTES` whose method and regex match answers: the shared rows first, then the pair's and the director's, then
   the two fallbacks. A job route calls `load_job` first.
2. `POST /api/jobs/<id>/stages/<name>/run` calls `Runner.start_stage`. The gates run first: the round gate for a
   full render and the busy rule for a registration. `argv_for` builds the argv through the stage's module (the table
   below), and the record is written as `running`.
3. The child is `<root>/.venv/bin/python` with one of five scripts as `argv[1]`, named by the stage's `script` key. It
   runs in its own session with the repo root as its working folder and its output in the record's `log.txt`. The
   record's `script_md5` is the md5 of that `argv[1]`.
4. When the child exits, `finalize` writes the terminal state. Exit 0 with the stage's terminal file renames the
   `.part` path, writes the `done` marker and lists the outputs with md5s. Exit 2 with a `FAILED:` line is
   `refused`, and since the fix round a refusal removes its `.part` folder; any other exit is `failed` with the log's
   last line.
5. A stage written in place (since 2026-11-05, commit 9c78b83; as of that day the director's page) has a `.part` path equal to
   its final path. `start_stage` copies the existing file to `<record>/previous_<name>` before the child runs, the
   record carries `in_place` and `previous`, and `finalize` renames nothing. After a restart such a record is `done`
   when its file is newer than the record's start, and a page then opens its round; an older file leaves it `lost`.
   The fix round changed this on 2026-11-06 (`_written_since`; the Fable review's finding F5): before, a restart
   always marked such a record `lost`.
6. A finished page opens a round through `jobs.rounds.open_round`: `page.md5` beside the page, a copy of the page
   under `rounds/<n>/`, and `round.json` with the id of the page's record. The Runner's `after_done` calls it for a
   page record (`loop_seq.py page`, `director_page.py`). The pair's page has no script: `views.page.build_page` runs
   the review gate, then `views.pair.build_pair_page` writes the page, a builtin page record and the round.
7. `GET /api/jobs/<id>` returns `job_view`. Its `stage_views` reconciles every record, then reads the job from disk.
   The page polls every 1 s while a stage runs and every 5 s otherwise.
8. `serve` calls `reconcile_all` at start. A running record whose pid still runs that record's own `argv[1]` into
   that record's `.part` path is watched; for an in-place record the pid check looks for the output's folder. A gone
   one is finished from its files or marked `lost`. Since the fix round a server leaves a record to another server
   that finalizes it: the evidence is its done marker, its terminal file renamed into `out_final` after it started,
   or a finished state on disk (`Runner._finished_elsewhere`; backlog T88).

The argv by flow (`runner/argv_*.py`; the paths are repo-relative and `A`, `B` are the job's links under
`raw/<pair>/`):

| Flow | Stage | `argv[1]` and its arguments |
|---|---|---|
| loop | registration, readers, probe, render, measure, page | `scripts/research/loop_seq.py <command> … --out <path>.part` |
| pair, director | verdict (the shared branch) | `reveal.py align A B --out <job>/verdict.part` |
| pair | relation | `transitions.py pair A B --out <job>/relation.part --max-long 480 --seconds 1` |
| pair | render | `transitions.py pair A B --out <job>/<pair>/<name>.part --max-long N` and the knobs' flags; a draft (`draft` above 0) goes under `drafts/<pair>/` |
| director | resolve | `scripts/research/director_render.py PLAN <job>/resolve/<stamp>.part --resolve-only --concept C --max-long N [--set k=<json> …] --layers-dir L --mattes-dir M` |
| director | render | `scripts/research/director_render.py PLAN <out>.part --concept C --max-long N --seconds S --fps F [--set k=<json> …] --progress --layers-dir L --mattes-dir M`; a full render under `<job>/run/<stem>_<concept>[-<tag>]`, a draft under `<job>/drafts/` |
| director | page | `scripts/research/director_page.py <job>/run --notes <record>/notes.json --title T --key K [--head H] [--keyframes J]`, written in place |

## Import contracts

`.importlinter` holds three contracts, and `make audit` runs `lint-imports` over them. On 2026-11-05 at 21:43 it
analyzed 82 files and 441 dependencies and kept all three (`make -C studio audit`).

| Contract | Rule it encodes |
|---|---|
| no tool or script import | the package imports none of 16 names: `reveal`, `transitions`, `loop_seq`, `rife_probe`, `director_render`, `director_page`, `director_ui`, `chain_luma`, `layer_merge`, `matte_source`, `layered_probe`, `nest_probe`, `torch`, `transformers`, `kornia`, `huggingface_hub` (the eight from `director_render` to `nest_probe` since phase B's slice) |
| cv2 only in media | only `reveal_studio.media` imports cv2 directly (`pictures`, `pair` and `overlays`; the last two import numpy as well); a view may call media |
| layered imports | server > views > runner or media > jobs > registry > config, errors or fs |

Modules on one layer line are siblings that never import each other. For that reason `config` raises its own
`ConfigError` instead of a `StudioError`. On 2026-11-05 an `import cv2` added inside a function of `views/render.py`
turned contract 2 red, and the revert turned it green. During phase B's slice an `import director_render` added to
`views/director.py` turned contract 1 red, and its removal turned it green (`b_slice.md`).

## Configuration

`resolve_settings` resolves a frozen `Settings` once, from the flags, the environment and discovery, in that order
(`README.md` has the table). Since phase B the settings hold eight more paths, each derived from the root:
`transitions`, `reveal`, `director_render`, `director_page`, `director_plans`, `fixtures`, `layers_dir` and
`mattes_dir`. The last two also come from `--layers-dir` and `--mattes-dir`, or from `REVEAL_STUDIO_LAYERS_DIR` and
`REVEAL_STUDIO_MATTES_DIR`. Every function that reads or writes the disk takes `Settings`, or a `Runner` that holds
it. The `App` holds the settings, the `ScriptFlags` probed from the loop script's `--help` at start, the `Runner` and
the enabled flows. The handler reads it as `self.server.app`.

Module-level state is limited to constants and `media.pictures.DECODE_LOCKS`, one lock per decode folder. Two
modules read their own location: `config`, for the last-resort discovery of the repo root, and `server.routes`, for
the package's `web/` folder.

## Test layers

| Layer | Marker | Files | Needs | Tests collected (2026-11-06) |
|---|---|---|---|---|
| unit | none | `tests/test_*.py`, less the integration tests below | a temporary repo root with the five fakes of `tests/fakes/`, a shell wrapper as its `.venv/bin/python`, and the fixture pair `tiny_1` with a director plan, layer tables and mattes | 555 |
| integration | `integration` | `tests/test_compat.py` (5), `tests/integration/test_loopseq_help.py` (7), `test_transitions_help.py` (4), `test_director_help.py` (6), and one test each in `test_registry.py` (the frozen plans' keys against the schema) and `test_fits.py` (the real angel preps) | the real repo root and `../.venv`; each module skips when they are absent | 24 |
| acceptance | `acceptance` | `make acceptance` runs four drives, one at a time, in about 8 minutes. `tests/acceptance/test_a1_loop_flow.py`: a new job from the owner's stills, the registration against the recorded prep, the full a2 render at its md5, the gates, a restart, a cancel. `test_a2_loop_flow.py`: the fits table, the probe, a ruled knob's warning, the a2 md5 from a saved unchanged copy, the measure, the page's variants. `test_b_pair_flow.py` on mismatch_3: the relation at its two md5s, the verdict's refusal, a 1920 morph, the page gate, a grade, a restart. `test_b_director_flow.py` on mismatch_3: the two-knob and four-knob drafts at their md5s, a full render across a restart, the page, a grade. `make draft-check` runs `tests/integration/test_draft_render.py`: a 480 draft into the job `loop_angel_20261104-220719` | the owner's stills, the fixture pair mismatch_3, RIFE, the real tree | 5 |

The counts come from `pytest tests --collect-only -q -m <marker>` in `studio/` at 00:28 on 2026-11-06; 584 tests in
all, 579 of them in `make test`. On the tree of commit 0a5a260 `make qa` was green, `make test` passed 574 and `make
acceptance` passed 4 in 528 s (the commit message). On the fix round's tree `make qa` was green in 121.2 s with 555 unit
tests, `make test` passed 579 in 114.2 s and `make acceptance` 4 in 372.7 s (`b_fixes.md`, 2026-11-06).

`tests/test_prose.py` runs the no-slop checker over the registry's sentences twice. The first check holds every hint,
stage, flow, knob and `--set` sentence to the checker's 60 words. The second, since the fix round, holds the hints and
the phase B flows' sentences to 40 words; the loop's stage and knob sentences keep 60, because a digest pins them.

The fakes have the real subcommands, flags and `--help` text and write their outputs in the real shapes and order.
`tests/conftest.py` `FAKE_TABLE` maps each fake to its place in the tmp root.

| Fake | Command | Writes | The environment steers |
|---|---|---|---|
| `loop_seq.py` | `prep`, `readers`, `probe`, `render`, `measure`, `page` | `prep.json` with a `lock` block, `measure.json`, `frames.json`, `plan.json`, an mp4 that cv2 decodes | `FAKE_SLOW="render=3"` sleeps inside a command; `FAKE_FAIL` exits 1; `FAKE_REFUSE` exits 2; `FAKE_NO_FLAGS=1` plays a script without `--progress`, `--frames` and `readers`; `FAKE_NO_RIFE=1` makes the probe skip its RIFE strips |
| `reveal.py` | `align A B --out DIR` | `before.jpg`, `after_aligned.jpg`, then `metrics.json` | `FAKE_SLOW`, `FAKE_FAIL`, `FAKE_REFUSE` |
| `transitions.py` | `pair BEFORE AFTER --out DIR` | `transition.mp4`, `strip.jpg`, then `report.json` | `FAKE_SLOW`, `FAKE_FAIL`, `FAKE_REFUSE` |
| `director_render.py` | `PLAN OUT`, with or without `--resolve-only` | the canvases, `anchors.json` and `info.json`; a render's `transition.mp4`, `montage.jpg`, then `info.json` | `FAKE_SLOW`, `FAKE_FAIL` |
| `director_page.py` | `RUN --notes --title --key` | `RUN/index.html` in place | `FAKE_FAIL` |

## Hard constraints and their tests

| Constraint | Where it holds | Test |
|---|---|---|
| the server binds 127.0.0.1 only and answers a local Host only | `server.app.HOST`, `Handler._host_ok` | `test_server.py`: `test_the_server_binds_127_0_0_1_only`, `test_the_host_check` |
| the runtime opens no outbound connection | a stdlib HTTP server; the runtime dependencies are numpy and cv2 | the first import contract; deptry over `pyproject.toml` |
| the originals are linked and hashed, never copied or modified | `jobs.store`: `create_loop_job`, `create_pair_job` and `create_director_job` link each input and record its sha256 | `test_jobs.py`: `test_a_new_job_links_the_stills_in_order_and_hashes_them`, `test_a_pair_job_links_the_two_photos_with_their_extensions` |
| every heavy call is a subprocess of the main venv's python | `runner.argv.argv_for` and the four argv modules, `Runner.start_stage` | `test_runner.py`: `test_a_registration_runs_to_done_with_md5s_and_the_done_marker`, `test_argv_for_routes_a_shared_stage_before_the_flow_module` |
| the Runner hashes, watches and cancels the script a record's own `argv[1]` names, so a live child of any flow re-attaches after a restart (since phase B) | `runner.process.script_of`, `Runner.pid_alive`, `Runner.cancel` | `test_runner.py`: `test_reconcile_reattaches_a_live_child_of_another_flows_script`, `test_a_stage_whose_script_is_missing_is_refused_before_it_starts` |
| neither tool nor any research script is imported; only `media/` imports cv2, for the page's pictures and, since phase B, the decoded step series | `.importlinter` | `make audit` (lint-imports) |
| the job folder is the only state | every view reads the disk on each call | `test_compat.py`: the research script's records load |
| `models/` and the frozen plans are never written | `jobs.plans.save_plan` writes the job's `plans/` | `test_plans.py::test_frozen_plans_lists_the_tree_and_is_never_written` |
| an output that exists is one that finished | the `.part` path renamed in `Runner.finalize`; a stage written in place (since phase B) keeps the previous file beside its record instead | `test_runner.py`: the cancel and reconcile tests, `test_a_stage_written_in_place_keeps_the_previous_file_beside_the_record`, `test_an_in_place_record_after_a_restart_is_done_when_its_file_is_newer_than_its_start` |
| a server never writes `lost` over a record another server finishes (since the fix round; the rest of backlog T88 stays open) | `Runner._finished_elsewhere` | `test_runner.py::test_a_second_server_never_writes_lost_over_a_record_another_server_finishes` |
| a finished render is never overwritten | `Runner.start_stage` | `test_runner.py::test_a_finished_render_is_never_overwritten`, `test_pair_flow.py::test_a_finished_render_is_never_overwritten` |
| the page refuses unjudged or NOT READY candidates unless overridden, and prints the override | `views.page.build_page`, for every flow; the pair's writer runs after it | `test_views.py` (the page gate tests), `test_server.py::test_the_page_gate_over_http`, `test_server_pair.py::test_the_page_through_the_shared_route_behind_the_gate` |
| the file route serves the run folder and the job folder. Since phase B it also serves, read-only, `fixtures/`, the job's layer and matte roots and the helper files its `job.json` names. `..`, an absolute path and a link out of the job are refused | `Handler._safe_file`, `server.handler.read_only_file` | `test_server.py`: `test_the_file_route_answers_ranges_and_refuses_escapes`, `test_the_file_route_serves_the_read_only_bases_of_a_director_job` |
| PyPI is the only index: the lock names `pypi.org` and `files.pythonhosted.org`, never a machine's mirror | `pyproject.toml` `[[tool.uv.index]]`, the Makefile's `UV_DEFAULT_INDEX` export | `test_lock.py` (both tests; the GitHub workflow's `uv sync --frozen` is the live check) |

## Changed from the research script

`scripts/research/studio.py` was retired on 2026-11-05 after the acceptance drive passed on the package
(`.claude/claude-docs/research/2026-11-05/port_acceptance.md`: 15 of 15). The port changed these on purpose:

| Change | The research script | The package |
|---|---|---|
| `ui_version` in new records | `studio A1 2026-11-04` | `reveal-studio 0.2.0`; records of both load |
| the `Server` header | `studio/A1` | `reveal-studio/0.2.0` |
| the command named by a hint, the skeptic panel and its message | `studio.py requests` | `reveal-studio requests` |
| the text for a key without a hint | "add it to the hints table in studio.py" | "… in registry/hints.py" |
| the hint `plan.effects.parallax` | one sentence of 69 words | five sentences, the same symbols and numbers |
| a busy port at `serve` | a traceback | one line on stderr, exit 1 |

The package keeps the script's known defects as they were. Each one below was reproduced on the package on 2026-11-05.

| Defect | Effect |
|---|---|
| a job id has one-second resolution (`<flow>_<seq>_<stamp>`) | two jobs of one sequence made in the same second share a folder. A new job then an adoption: `mkdir` raises and the request answers 500. An adoption then a new job: the new job's `job.json` overwrites the adopted one's |
| cancel races the wait thread of the server's own child | when the wait thread finishes first, the log says "the server restarted before the record was written" and the record lacks the note that the `.part` folder was removed |
| a registration rerun that finishes in the same second as the previous rerun | the move to `in/<seq>_prev_<stamp>` meets an existing folder: the wait thread raises OSError, and the record stays `running` until a later read finishes it |
| `--runs-date` is not validated | `--runs-date ../escaped` makes new jobs under `benchmarks/escaped/studio/`, where `job_dirs` never lists them |
