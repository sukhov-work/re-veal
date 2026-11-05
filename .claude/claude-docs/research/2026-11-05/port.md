<!-- provenance: copied verbatim on 2026-11-05 from benchmarks/runs/2026-11-05/studio/agents/port.md (gitignored), the report of the port-builder subagent (Opus 5.5, max effort) of the 2026-11-05 session; a research artifact whose claims carry the author's own confidence and gaps; the main thread re-ran `make qa` (green, 42 s) and `make test-fast` (147 passed) after the copy and moved the draft-render test to the acceptance marker -->

<!-- reader: the main thread, cold; shape: report; written by the port-builder subagent on 2026-11-05 (00:20–01:25). -->

# The studio as a package: the port report

The package `studio/` (reveal-studio 0.2.0) is built, and `make qa` is green: exit 0 in 47 s. Its parts are lint 0.4 s,
typecheck 0.5 s, 147 unit tests in 42 s, audit 10 s and prose under 1 s. `make test` adds the 11 integration tests:
158 pass in 49 s. The acceptance layer has 0 tests.

Asked of the main thread:

1. Commit `studio/` with `studio/uv.lock` (68 files; every cache is already in `.gitignore`).
2. Decide whether the draft-render integration test becomes opt-in. It runs in `make test`, as the main thread's
   instructions for this port placed it, and each run adds an 8 MB draft and a record to the owner's job
   `loop_angel_20261104-220719`.
3. Retire `scripts/research/studio.py` once the acceptance drive passes on the package. That drive is the scripted
   check of STUDIO.md section 9 on the owner's stills; it is the main thread's to run.

## Summary

- Verdict: the port keeps the research script's behaviour. A real 480 px draft of the frozen plan
  `scripts/research/plans/loops/angel_a2.json`, rendered through the package, gave `loop.mp4` md5
  `2955c25c2611565b3ee57d2d081f8669`. The research script's own 480 px draft of that plan had the same md5 on 2026-11-04. The
  acceptance report of the studio's first build phase names that draft a2r
  (`.claude/claude-docs/research/2026-11-04/a1_acceptance.md`).
- At 2560×1440, the served page differs from the research script's page in 1,706 of 3,686,400 pixels. The version
  label and the hint button beside it account for all but 4 of them; those 4 differ by at most 2 levels.
- Records written by the research script load in the package. A compatibility test reads all 17 records of
  2026-11-04, and they open read-only.
- Four defects of the research script were reproduced on the package and kept. They are listed under "Found, not
  changed".

Names used below:

- "the research script": `scripts/research/studio.py` (md5 `51be0198…`, untouched), the studio before this port;
- "the brief": the main thread's instructions for this port, which fixed the package layout and the test list;
- "`loop_seq.py`": `scripts/research/loop_seq.py`, the research script whose subcommands do the heavy work;
- "the fake script": `studio/tests/fakes/loop_seq.py`, which stands in for `loop_seq.py` in the unit tests;
- "the concurrent agent": another agent that added default-off commands to `loop_seq.py` on 2026-11-05.

## Module map as built

`studio/ARCHITECTURE.md` holds the full map with each module's imports. Lines per module, as of 01:20:

| Layer | Modules (lines) |
|---|---|
| server | `server/app.py` 72, `server/handler.py` 173, `server/routes.py` 247 (26 routes) |
| views | `views/job.py` 308, `views/render.py` 63, `views/models.py` 69, `views/page.py` 46 |
| runner, media | `runner/argv.py` 212, `runner/process.py` 396, `runner/lock.py` 57; `media/pictures.py` 95 |
| jobs | `jobs/store.py` 193, `jobs/records.py` 80, `jobs/candidates.py` 131, `jobs/plans.py` 139, `jobs/grades.py` 122 |
| registry | `registry/loop.py` 202, `registry/hints.py` 339, `registry/schema.py` 43, `registry/rulings.py` 20 |
| base | `config.py` 158, `errors.py` 14, `fs.py` 87; `cli.py` 139 above every layer |
| web | `index.html`, 4 CSS files and 9 JS files, 375 lines |

In total, `src` holds 3,419 lines of Python in 32 files and `tests` holds 2,655. The brief's layout is kept, with four
placements to note:

- `progress_of` lives in `jobs/records.py`, because the pure part of `record_view` reads it there.
  `runner/process.py` re-exports it, and `Runner.progress_of` names it.
- `record_view` is in `views/job.py`: it is the runner's `reconcile` followed by `jobs.records.record_detail`.
- `registry_view` (the payload of `GET /api/registry`) is in `views/models.py`.
- `owner_frames(d)` in `jobs/grades.py` replaces three inline copies in the research script.

The web split moved code only. A scratch check shows every one of the old page's 165 script lines appears exactly
once across the 9 JS files. Three of those lines carry an edit, listed under "Sentences changed". `node --check` passes on all 9
files. `studio.css` equals the old `<style>` body byte for byte.

## Configuration as built

`resolve_settings` builds a frozen `Settings` from an explicit argument, then the environment, then discovery. Failure
raises `ConfigError` with the missing file's name.

- The root comes from `--root`, else `REVEAL_STUDIO_ROOT`, else discovery. Discovery walks from the working folder
  upward, then upward from the package's own path, for a folder holding both `reveal.py` and `AGENTS.md`. An explicit
  root must hold both too ("the root X (from --root) has no AGENTS.md").
- The main venv's python comes from `REVEAL_STUDIO_PY`, else `<root>/.venv/bin/python`. The CLI has no flag for it.
- The port comes from `--port`, else `REVEAL_STUDIO_PORT`, else 8380, and must lie in 1..65535. The lock comes from
  `--lock`, else `REVEAL_STUDIO_LOCK`, else `<root>/benchmarks/runs/studio.lock`.
- The runs date comes from `--runs-date`, else `REVEAL_STUDIO_RUNS_DATE`, else today; it is unvalidated, as in the
  research script.
- `ui_version` is "reveal-studio 0.2.0"; the body cap is 2 MiB.
- Two modules read their own path: `config.py` for the last-resort discovery, and `server/routes.py` for the
  package's `web/` folder.

## What `make qa` reports

| Gate | Result on 2026-11-05 |
|---|---|
| `ruff check` and `ruff format --check` | 0 findings; 50 files formatted |
| `mypy --strict` | 0 errors in 32 files; 0 `type: ignore` lines; no overrides (cv2 5.0 and numpy ship stubs) |
| `vulture --min-confidence 80` | 0 findings |
| `deptry .` | "Success! No dependency issues found." (32 files) |
| `pip-audit` | "No known vulnerabilities found"; the editable reveal-studio is skipped |
| `lint-imports` | 3 contracts kept, 0 broken (54 files, 210 dependencies) |
| `radon cc -n C` | 18 blocks at grade C or worse (list below) |
| prose | README.md and ARCHITECTURE.md: 0 blocks, 0 advisories |

The ruff ignores and what each one suppresses, counted with the config bypassed:

| Ignore | Files | Hits | Reason (dated in `pyproject.toml`) |
|---|---|---|---|
| S603 (a subprocess call), S607 (a partial executable path) | `runner/*.py` | 4 and 1 | the runner starts the main venv's python and `ps` by design |
| E501 (a line over 120 characters) | `registry/*.py` | 69 | one sentence per line, diff-able against the scripts' `--help` and SCHEMA.md |
| S101 (`assert`), S603, S607 | `tests/**` | 454, 4 and 1 | tests assert, and start the fake script and `sleep` (a stranger process for the cancel test) |
| `allowed-confusables` × − – | all | 17 | the typographic signs of the scripts' own sentences |
| `# noqa: SIM115` | `runner/lock.py:30` | 1 | the lock file's handle stays open for the server's life |

Ruff's other findings were fixed in the code. Its insecure-hash rule cleared with
`hashlib.md5(usedforsecurity=False)`, and every digest stayed the same. Its rule against a bare raise inside `except`
cleared with `raise … from None`, and every message stayed the same.

radon grades by cyclomatic complexity (the number in brackets). Two functions are F: `stage_views` (74) and
`Runner.finalize` (57). Three are D: `job_row` (23), `argv_for` (22) and `create_job` (22). Thirteen are C, from
`validate_plan` (20) down to the `Runner` class (11).
Each ported function keeps the research script's branches, since a refactor was out of scope. Of the 18, only
`resolve_settings` (C, 17) is new code.

Unit-layer coverage is 94% of 1,692 statements, branches included. The lowest file is `server/app.py` at 62%:
`serve()` itself runs only in the real-surface check.

## Mutations applied

| Mutation | Result | Restored |
|---|---|---|
| `Runner.finalize` stops writing the `done` marker | 2 of 28 runner tests red: `test_a_registration_runs_to_done_with_md5s_and_the_done_marker`, `test_reconcile_after_a_restart_finishes_a_complete_part` | 28 of 28 green |
| `import cv2` inside a function of `views/render.py` | `lint-imports`: "cv2 only in media BROKEN … reveal_studio.views.render -> cv2 (l.16)" | 3 contracts kept |

## Real-surface check

1. `uv run reveal-studio check` ran in 1.1 s and exited 0. It printed the root
   `/Users/yevhens/Projects/personal/reveal-1.5.0`, the python `…/.venv/bin/python (exists)`, `loop_seq.py` md5
   `474d57b324c6c7b815aa13c4444862bb`, 3 jobs, 48 frozen plans, and "progress yes, frames yes, readers yes".
2. `uv run reveal-studio serve --port 8390 --no-browser --lock <scratchpad>/studio-port.lock` started as pid 88502.
   Its log: "reveal-studio 0.2.0: serving http://127.0.0.1:8390/ (… 3 job(s) found)". `lsof` showed one LISTEN socket,
   on 127.0.0.1:8390.
3. The curl results:

| Request | Answer |
|---|---|
| `GET /` | 200, `text/html; charset=utf-8`, `no-store`, `Server: reveal-studio/0.2.0`, 9 script tags |
| `GET /static/js/core.js`, `/static/css/studio.css` | 200, `text/javascript` 4,123 B; 200, `text/css` 11,541 B |
| `GET /static/../x` | 404 |
| `GET /api/registry` | 85 hints, 8 stages, ui "reveal-studio 0.2.0", port 8390, all three script flags true, 48 frozen plans |
| `GET /api/jobs` | the three jobs: `…220708` (a run folder adopted as a job; its round 1 page graded by the owner; 5 candidates), `…220719` (1 candidate), `…223204` (round 2 ungraded, 2 candidates) |
| `GET /api/jobs/loop_angel_20261104-220708` | round 1, grade "record that for angel page, options 2 and 3 are fine , close this effort", page md5 `72dadc4f5ea4db16152fe0c7062a3f94`; tiles import, registration, render and page done, grades graded |
| `GET /api/jobs` with `Host: evil.example:8390` | 403 |

4. The integration draft render (`tests/integration/test_draft_render.py`) produced record `20261105-010146_render`.
   It took 7.6 s of wall time, with `wall_s` 7.0 in the record. The record's `script_md5` and `measure.json` both read
   `474d57b324c6c7b815aa13c4444862bb`. The draft has 50 frames at canvas [370, 480], with `plan_sha256`
   `94660b229f541b52` and `render_s` 4.8.

| Output | md5 |
|---|---|
| loop.mp4 | `2955c25c2611565b3ee57d2d081f8669` |
| loop.gif | `c03763768d79027cf072c5aac593824a` |
| sheet.jpg | `23223375a5e8767b5c6c924e9ce5f0e4` |
| plan.json | `c67cbe9831d27d448ce891771fe37348` |
| measure.json | `0768dd1dda4a07b9f88c6266f0732bf1` |
| frames.json | `a39b1b6b31a78a7ff29a9b62f7521ddd` |

5. `make test` and a second integration run made records `20261105-011034_render` and `20261105-011123_render`. Both
   reproduced loop.mp4, loop.gif, sheet.jpg, plan.json and the frame JPEGs byte for byte. `frames.json` and
   `measure.json` differ in their wall-time fields only.
6. Screenshots, all at 2560×1440 under `benchmarks/runs/2026-11-05/studio/shots/`:
   - `port_2560x1440.png` is the first look: rail, strip, render panel, viewer, step plot and inspector all drawn.
   - `package_2560x1440.png` and `research_script_2560x1440.png` were taken with identical Chrome flags.
   - `diff_research_vs_package.png` marks the 1,706 differing pixels in red.
   For this comparison the research script served its page on port 8391 (pid 89046). It ran with `--second`, the
   flag that lets a review server run beside the owner's, and only answered reads.
7. Both of my servers got SIGTERM by their own pids, found through `lsof` on 8390 and 8391. Pid 51553 on 8380 kept
   running, and `benchmarks/runs/studio.lock` still reads "port 8380 pid 51553 since 2026-11-04T23:50:19.078".

Writes outside `studio/`: three drafts under
`benchmarks/runs/2026-11-04/studio/loop_angel_20261104-220719/drafts/angel/port_check_*` (24.5 MB), their three
records under that job's `stages/`, and the screenshots. All of these are gitignored.

## Found, not changed

Each item below was reproduced on the package on 2026-11-05 and kept, as the brief asks.

| Defect | How it showed | Effect |
|---|---|---|
| a job id has one-second resolution (`<flow>_<seq>_<stamp>`) | a test adopted a run folder in the same second as a new job of the same sequence; a probe did the reverse | a new job then an adoption: `mkdir` raises FileExistsError, a 500. An adoption then a new job: the new job's `job.json` overwrites the adopted one's, and one job is listed instead of two |
| cancel and the child's wait thread both finish the record | in the runner's cancel test the wait thread wrote first, and the log read "cancelled (cancelled; the server restarted before the record was written)" | the final record says "cancelled by you" without its note "the .part folder was removed"; the folder is removed either way |
| a registration rerun finishing in the same second as the previous rerun | a probe ran four registrations in a row | the move to `in/<seq>_prev_<stamp>` meets an existing folder: OSError in the wait thread; the record stays `running` and blocks the next registration until a later read |
| `--runs-date` is unvalidated | a probe with `../escaped` | new jobs land under `benchmarks/escaped/studio/`, which `job_dirs` never lists |

Oddities kept without a probe:

- `rel()` resolves a symlink, so `inputs[].link` in `job.json` is an absolute path (seen in the real records).
- `outputs_of` lists a render folder's top level only: the frame JPEGs carry no md5 in the record (6 outputs).
- The page's `alertMsg()` is defined in `rail.js` and never called.
- The brief counted 86 hint keys. HINTS holds 85: after the Fable review of 2026-11-04 (`a1_review.md`), the main
  thread dropped `chip.queued`, a state the code never writes.

## Sentences changed

The prose test (`tests/test_prose.py`) runs `slop-check.py --json --profile file` over every hint, stage, flow and
knob sentence. Before the port, 1 sentence blocked it.

| Key | Before | After |
|---|---|---|
| `plan.effects.parallax` | one sentence of 69 words, from "One remap per frame in which a pixel…" to "…blended per frame by the in-between's t." | "One remap per frame. A pixel at relative depth d moves by amp × W × (d − ref) × wave(u) along `dir` (…), plus amp2 × that along `dir2` with `shape2` (an orbit). The plane at depth `ref` (…) stays put. The maps are blurred `sigma` px and blended per frame by the in-between's t." |

The test now reports advisories only: 32 sentences over 25 words, and "seam" 4 times. The port changed these texts
for the new package, not for prose:

| Text | Where | Before | After |
|---|---|---|---|
| the hint `chip.waiting` | `registry/hints.py` | `studio.py requests` | `reveal-studio requests` |
| the skeptic panel's empty-list line and its "written" message | 2 lines of `web/js/panels.js` | `studio.py requests` | `reveal-studio requests` |
| the popover for a key without a hint | 1 line of `web/js/core.js` | "the hints table in studio.py" | "… in registry/hints.py" |
| `ui_version` of new records | `config.py` | studio A1 2026-11-04 | reveal-studio 0.2.0 |
| the `Server` header | `server/handler.py` | studio/A1 | reveal-studio/0.2.0 |

## Gaps

- Every run of the draft-render test adds an 8 MB draft and a record to the owner's job `loop_angel_20261104-220719`.
  Three runs on 2026-11-05 added three. The test stays in `make test` until the main thread decides (ask 2 above).
- The acceptance layer is empty: pytest collects no test, exits 5, and `make acceptance` fails with make's exit 2.
- The browser behaviour was compared by screenshot on the render panel only. The keyboard, playback, the scrubber,
  the hint popovers, the focus rules and the 1 s and 5 s poll cadence were never driven in a browser (UNVERIFIED). The
  evidence for them is the line-for-line move plus `node --check`.
- The impeccable detector was not run: the `detector` target prints its command only, as specified.
- At start the integration server skips `reconcile_all`, the pass that settles records left running by a dead
  server, because the owner's server holds the tree's lock. Two servers may still finish the same record: if the
  owner's page polls job `loop_angel_20261104-220719` while a port-check render runs, both `finalize` it. That did
  not happen on 2026-11-05.
- `pip-audit` needs PyPI to run.
- The concurrent agent changed `loop_seq.py` from md5 `eba20856…` to `474d57b3…` and edited `SCHEMA.md`. The edits add
  commands (windows, probe, measure, variants), not methods, eases or plan keys. The help contract test and the draft
  render passed on `474d57b3…`.
- A cold read of this report by a second agent ran once; its findings are fixed in this version.
