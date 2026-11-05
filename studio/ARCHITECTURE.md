# reveal-studio: architecture

This file maps the modules of reveal-studio 0.2.0 (as of 2026-11-05, after phase A2 and its fix round). It also
covers the data flow, the import contracts, how the settings reach the code, the test layers, and each hard
constraint with the test that holds it.

The design of record is `.claude/claude-docs/STUDIO.md` at the repo root (its section 13 records the package). The
package ported `scripts/research/studio.py` (phase A1; retired on 2026-11-05 once the acceptance drive passed) and
keeps its URL grammar, its JSON shapes and its job folder layout. Phase A2 (2026-11-05) added the plan schema, the
rulings, the page's variants, the probe and measure stages, the fits table, the stalls and jumps, the stability plot,
the comparator modes and the graph view (`.claude/claude-docs/research/2026-11-05/plan_editor.md`, `views_a2.md`).

## Module map

All modules sit under `src/reveal_studio/`. "Imports" lists the package's own modules only.

| Module | Owns | Imports |
|---|---|---|
| `__init__` | `__version__` ("0.2.0") | nothing |
| `__main__` | `python -m reveal_studio` | `cli` |
| `cli` | the `serve`, `requests` and `check` commands | `config`, `fs`, `jobs`, `runner`, `server`, `views` |
| `config` | `Settings` (frozen), `resolve_settings`, `ConfigError` | the root package, for `__version__` |
| `errors` | `StudioError(msg, code, extra)` | nothing |
| `fs` | file md5 and sha256, JSON read and atomic write, `rel`, `inside`, `tail_lines`, `stamp`, `now_iso`, `log` | nothing |
| `registry.loop` | the loop flow's 10 stages with their knobs (import, registration, readers, probe, plan, render, measure, skeptic, page, grades; probe and measure are branch stages with `parent`, `branch` and `stale_after`): `LOOP_STAGES`, `FLOWS`, `STAGE_ORDER`, `stage_def`, `K` | `errors` |
| `registry.hints` | the hints table `HINTS` (290 keys after the fix round of 2026-11-05: 85 at the port, 145 for the plan keys and the editor, 37 for the views, 23 for the chips and controls the fix round named) and `H` | nothing |
| `registry.schema` | `PLAN_SCHEMA` (151 entries in 21 groups: path, type, default with its source, range, choices, hint key), the plan grammar's lists, `ID_RE`, `NAME_RE`, `validate_plan` (reads its choices from the schema) | `errors` |
| `registry.rulings` | `RULINGS` (7 rows `{knob, value, since, why, source}`, each citing a DECISIONS line or a playbook section) and the matching of a plan or a stage's knobs against them (a warning, never a refusal) | `registry.loop`, `registry.schema` |
| `jobs.store` | `studio_dir`, `job_dirs`, `find_job`, `load_job`, `job_root`, `prep_dir`, `list_stills`, `create_job` | `config`, `errors`, `fs`, `registry`; `jobs.candidates` inside `create_job` |
| `jobs.records` | `records`, `record_dir`, `outputs_of`, `progress_of`, `command_line`, `elapsed_of` (the seconds a record has run, for the rail's running entries), `record_detail` (the pure part of `record_view`) | `config`, `errors`, `fs`, `registry` |
| `jobs.candidates` | `candidates`, `candidate`, `verdicts`, `rounds`, `requests_of` | `config`, `errors`, `fs`, `jobs.store`, `registry` |
| `jobs.plans` | `resolve_plan`, `plans_of`, `frozen_plans`, `plan_diff`, `save_plan` | `config`, `errors`, `fs`, `registry` |
| `jobs.grades` | `write_request`, `save_grade`, `mark_frame`, `owner_frames` | `config`, `errors`, `fs`, `jobs.candidates` |
| `runner.argv` | `ScriptFlags`, `probe_script_flags`, `coerce`, `flags_of`, `argv_for` | `config`, `errors`, `fs`, `jobs`, `registry` |
| `runner.process` | `Runner`: `start_stage`, `finalize`, `after_done`, `pid_alive`, `reconcile`, `reconcile_all`, `cancel` | `config`, `errors`, `fs`, `jobs`, `runner.argv` |
| `runner.lock` | `take_lock`, `LockHeld` (the handle stays open for the server's life; `serve` closes it, which releases the lock) | `config`, `errors`, `fs` |
| `media.pictures` | `jpeg_thumb`, `frames_dir` (one decode lock per render), `thumb_path`; the one cv2 import | `config`, `errors`, `fs`, `jobs` |
| `views.job` | `prep_summary` (with `fits`, `windows`, `windows_jpg`), `readers_summary`, `stage_views` (with the stale rule; a branch stage goes stale only after its `stale_after`), `graph_view` (ports and file edges from the records), `job_view` (with `probe`, `graph`), `job_row(settings, d, runner=None)` (reconciles a running record whose process is gone through the Runner; `running_entry` gives the rail `{id, stage, name, elapsed_s, progress}`), `attempt_note` (a failed or cancelled attempt beside a done tile), `is_draft` (a draft is no upstream of the page), `readers_moved` (the folder a later registration moved), `record_view` | `config`, `fs`, `jobs`, `registry`, `runner.process`, `views.fits`, `views.measures` |
| `views.render` | `render_view` (with `measures`, `stability`, `stalls_and_jumps`, `frame_kinds`), `frame_tag` | `config`, `fs`, `jobs`, `media`, `views.measures` |
| `views.fits` | `fits_summary`: `prep.json`'s named windows under each fit (`all far chain ecc final`) as the registration panel's table | `fs` |
| `views.measures` | `frame_kinds`, `stalls_and_jumps` (the playbook's bars: a stall is two or more steps below 0.3 while motion is open; a jump reaches 0.3 and exceeds 3× its neighbours' mean, outside a cut or a snap), `measure_runs`, `latest_stability`, `probe_view` | `config`, `fs`, `jobs` |
| `views.models` | `models_view`, `open_requests`, `registry_view` (the flows, the hints, `plan_schema`, `rulings`, the frozen plans) | `config`, `fs`, `jobs`, `registry`, `runner.argv` |
| `views.page` | `build_page`: the review gate over the listed candidates (`variants`), `page_variants` | `errors`, `fs`, `jobs`, `registry`, `runner.argv`, `runner.process` |
| `server.app` | `App`, `StudioServer` (bound to 127.0.0.1), `serve` | `config`, `fs`, `jobs`, `registry`, `runner`, `server.handler` |
| `server.handler` | `Handler`: the Host check, the body rules, `_file` with Range, `_safe_file` | `errors`, `fs`, `jobs.store`, `server.routes` |
| `server.routes` | `ROUTES` (26 rows of method, regex, function and name: 23 API and page routes, `GET /favicon.ico` and two 404 fallbacks), `match`, `dispatch`, `WEB_DIR` | `errors`, `fs`, `jobs`, `media`, `registry`, `views` |
| `web/` | `index.html`, 4 style sheets under `css/`, 9 classic scripts under `js/` that share one global `S`: `plan.js` the plan editor (bars, schema forms, undo, "% faster", the JSON tab), `viewer.js` the comparator (single, wipe, A/B, onion, difference at fit, 1:1, 2×) and the plots (steps, stalls, jumps, stability), `graph.js` the graph view, `strip.js` the strip with its branch row and the graph switch, `panels.js` the stage panels (the render's side column with its name, modes, sources and list; from 1800 px the registration, readers and probe panels put their tables beside a sticky viewer), `core.js` the shared helpers (`chipKey` maps a chip's text to its hint key; `focusKey`, `restoreFocus` and `focusQuiet` put the focus back by data attribute after a rebuild without opening a hint; a "?" button and a chip are no Tab stops) | — |

The page's scripts load in this order: `core`, `rail`, `strip`, `panels`, `plan`, `viewer`, `inspector`, `graph`,
`boot`. Each file runs in strict mode. At load time `rail.js` calls `core.js`'s `$()` to bind its buttons, and
`boot.js` calls `core.js`, `rail.js` and `strip.js` to start the page. Every other top-level statement defines a
function or binds a listener. Since phase A2 none of the nine scripts is a placeholder.

## Data flow

1. `Handler` checks the Host header, then for a POST the body rules, then calls `routes.dispatch`. The first row
   of `ROUTES` whose method and regex match answers. A job route calls `load_job` first.
2. `POST /api/jobs/<id>/stages/<name>/run` calls `Runner.start_stage`. The gates run first: the round gate for a
   full render and the busy rule for a registration. `argv_for` builds the argv, and the record is written as
   `running`.
3. The child is `<root>/.venv/bin/python scripts/research/loop_seq.py <command> … --out <path>.part`. It runs in
   its own session with the repo root as its working folder and its output in the record's `log.txt`.
4. When the child exits, `finalize` writes the terminal state. Exit 0 with the stage's terminal file renames the
   `.part` path, writes the `done` marker and lists the outputs with md5s. Exit 2 with a `FAILED:` line is
   `refused`; any other exit is `failed` with the log's last line.
5. A finished page opens a round: `after_done` writes `page.md5` and `rounds/<n>/round.json` with a copy of the page.
6. `GET /api/jobs/<id>` returns `job_view`. Its `stage_views` reconciles every record, then reads the job from disk.
   The page polls every 1 s while a stage runs and every 5 s otherwise.
7. `serve` calls `reconcile_all` at start. A running record whose pid still runs that record's script into that
   record's `.part` path is watched. A gone one is finished from its files or marked `lost`.

## Import contracts

`.importlinter` holds three contracts, and `make audit` runs `lint-imports` over them.

| Contract | Rule it encodes |
|---|---|
| no tool or script import | the package imports none of `reveal`, `transitions`, `loop_seq`, `rife_probe`, `torch`, `transformers`, `kornia`, `huggingface_hub` |
| cv2 only in media | only `reveal_studio.media` imports cv2 directly; a view may call media |
| layered imports | server > views > runner or media > jobs > registry > config, errors or fs |

Modules on one layer line are siblings that never import each other. For that reason `config` raises its own
`ConfigError` instead of a `StudioError`. On 2026-11-05 an `import cv2` added inside a function of `views/render.py`
turned contract 2 red, and the revert turned it green.

## Configuration

`resolve_settings` resolves a frozen `Settings` once, from the flags, the environment and discovery, in that order
(`README.md` has the table). Every function that reads or writes the disk takes `Settings`, or a `Runner` that holds
it. The `App` holds the settings, the `ScriptFlags` probed from the script's `--help` at start, the `Runner` and the
flows. The handler reads it as `self.server.app`.

Module-level state is limited to constants and `media.pictures.DECODE_LOCKS`, one lock per decode folder. Two
modules read their own location: `config`, for the last-resort discovery of the repo root, and `server.routes`, for
the package's `web/` folder.

## Test layers

| Layer | Marker | Files | Needs | Tests (2026-11-05) |
|---|---|---|---|---|
| unit | none | `tests/test_*.py` except `test_compat.py` | a temporary repo root with `tests/fakes/loop_seq.py` and a shell wrapper as its `.venv/bin/python` | 381 |
| integration | `integration` | `tests/test_compat.py`, `tests/integration/test_loopseq_help.py`, the frozen-plan coverage test of `test_registry.py` | the real repo root and `../.venv`; each module skips when they are absent | 14 |
| acceptance | `acceptance` | `tests/acceptance/test_a1_loop_flow.py` (a new job from the owner's stills, the registration against the recorded prep, the full a2 render at its md5, the gates, a restart, a cancel; about 100 s) and `tests/acceptance/test_a2_loop_flow.py` (the fits table, the probe, a ruled knob's warning, the a2 md5 from a saved unchanged copy, the measure's stability with the render's files unchanged, the page's variants; about 85 s), both by `make acceptance`; `tests/integration/test_draft_render.py` (`make draft-check`: a 480 draft into the job `loop_angel_20261104-220719`) | the owner's stills, RIFE, the real tree | 3 |

The fake script has the real subcommands and flags. It writes outputs in the real shapes: `prep.json` with a `lock`
block, `measure.json`, `frames.json`, `plan.json` and an mp4 that cv2 decodes. The environment steers it:
`FAKE_SLOW="render=3"` sleeps inside a command, `FAKE_FAIL` and `FAKE_REFUSE` name the commands that exit 1 and 2,
and `FAKE_NO_FLAGS=1` plays a script without `--progress`, `--frames` and `readers`.

## Hard constraints and their tests

| Constraint | Where it holds | Test |
|---|---|---|
| the server binds 127.0.0.1 only and answers a local Host only | `server.app.HOST`, `Handler._host_ok` | `test_server.py`: `test_the_server_binds_127_0_0_1_only`, `test_the_host_check` |
| the runtime opens no outbound connection | a stdlib HTTP server; the runtime dependencies are numpy and cv2 | the first import contract; deptry over `pyproject.toml` |
| the originals are linked and hashed, never copied or modified | `jobs.store.create_job` | `test_jobs.py::test_a_new_job_links_the_stills_in_order_and_hashes_them` |
| every heavy call is a subprocess of the main venv's python | `runner.argv.argv_for`, `Runner.start_stage` | `test_runner.py::test_a_registration_runs_to_done_with_md5s_and_the_done_marker` |
| neither tool nor any research script is imported; cv2 serves the page's pictures only | `.importlinter` | `make audit` (lint-imports) |
| the job folder is the only state | every view reads the disk on each call | `test_compat.py`: the research script's records load |
| `models/` and the frozen plans are never written | `jobs.plans.save_plan` writes the job's `plans/` | `test_plans.py::test_frozen_plans_lists_the_tree_and_is_never_written` |
| an output that exists is one that finished | the `.part` path renamed in `Runner.finalize` | `test_runner.py`: the cancel and reconcile tests |
| a finished render is never overwritten | `Runner.start_stage` | `test_runner.py::test_a_finished_render_is_never_overwritten` |
| the page refuses unjudged or NOT READY candidates unless overridden, and prints the override | `views.page.build_page` | `test_views.py` (the page gate tests), `test_server.py::test_the_page_gate_over_http` |
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
