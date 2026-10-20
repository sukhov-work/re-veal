<!-- Provenance: written by a Fable 5.1 subagent (the review of scripts/research/director_ui.py against the hard constraints) of the Claude Code session of 2026-10-21 (the round-13 session; DECISIONS 2026-10-21), copied verbatim from benchmarks/runs/2026-10-21/agents/ui1_review.md (sha256 1fe16cf0ad794378) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

# Review: UI1 `scripts/research/director_ui.py` (read-only, 2026-10-21 02:05–02:15)

`director_ui.py` holds all eight hard constraints as worded (8 PASS, two with a note), and its one
real defect is that the job folder does not survive a server restart as the source of truth: work
that finished on disk is reported as "pending", "running" or "lost" for ever, shown live on job
`mismatch_3_20261021-015740_c234`. Nothing crossed the scope fence (no new dependency, no import of
either tool, no network path). Reviewed against `ui_design.md` §4, §5 and §7 phase 1 and the
owner's answers; the server was run on port 8381 with `--no-browser` and stopped afterwards.

## Intent (ui_design.md §4, §5, §7 phase 1; owner's answers)

- Every phase-1 endpoint of §7 exists; two extra ones (`GET /api/jobs`, `GET /api/plans/<stem>`)
  are read-only. Phase 2–4 routes (`/plan`, `/annotations`, `/request/*`, `/import`, `/stitch`) are
  absent, as the plan says.
- A research script under `scripts/research/`, default port 8379 (line 1140), browser opened only
  without `--no-browser` (line 1152). The planner is not reached at all (phase 3). A 480 render is
  saved with `draft: true` in `render.json` (line 615) and in each picks clip (line 1127).
- §4's knob rule ("a knob it cannot map is read-only with the reason") is `map_knob`, lines 213–252.
- §5's job layout is followed; the frozen plan is copied into `plans/` and compared by md5 before
  reuse (lines 606–608); both copies on disk equal the frozen plan (md5 `e45db9c1…`, computed).
- The §7 acceptance check: the build report claims all nine steps PASS in headless Chrome. I
  re-verified steps 7–9 from the files (picks keys, `render.json` knobs, md5) and did not re-run
  steps 1–6 (no browser session in this review; see Gaps).

## Findings, most severe first

### Now

**[medium] director_ui.py:336-359, 386-394, 437-443, 624-636, 650 — completion is recorded only by
the in-process wait thread, so a restart freezes every in-flight result.**
Impact: a task's outputs are written by the subprocess, but its state is written by `wait()`'s
`on_done` closures: Reveal's `verdict.json` only in `reveal_done` (line 441), `render.json`'s
`state` and `md5_mp4` only in `done` (lines 624–634). After a restart those closures are gone. The
page then shows "pending (Reveal still running)"; the grade panel lists only `state=="done"`
renders (line 1112) and `selectRender` refuses the rest (line 1081). `lost` is computed on every
read (line 394) and never written. §5's two sentences "the UI rebuilds its state from it on
restart" and "a render the agent runs from the CLI into the same folder appears in the UI" do not
hold: `list_renders` globs `*/render.json` (line 650) and a CLI render writes only `info.json`.
Evidence: job `c234` (the build agent's server stopped at 01:57 while its analysis ran). On disk:
`analysis/resolve/anchors.json`, `canvas_A.png`, `canvas_B.png`, `info.json`, and the Reveal log
ends with `FAILED: Could not find enough common detail…`. `GET /api/jobs/…c234` at 02:11 returned
`verdict: "pending (Reveal still running)"`, `reveal: null`, tasks `resolve lost pid 95023`,
`reveal lost pid 95019` (both pids gone per `ps`), `transitions done`.
Fix: a reconcile step in `task_status` (and once at startup) for a `running` task not in `PROCS`:
if the kind's output exists (`info.json` + `transition.mp4` for render, `anchors.json` for resolve,
`metrics.json` or a `FAILED:` log line for reveal, `report.json` for transitions) run the same
`on_done` body and persist `done`; otherwise persist `lost`. Let `list_renders` also list a folder
with `info.json` and no `render.json`, building the row from `info.json["knobs"]`.
verifiedBy: observed.

**[low] director_ui.py:329-330, 414-426, 1154-1157 — children outlive the server and cannot be
cancelled after a restart.**
Impact: `start_new_session=True` (line 330) puts each child in its own session, so Ctrl+C on the
server (line 1156) leaves renders running. After a restart `PROCS` is empty and `cancel_task`
returns `{"ok": false}` for any task it did not start; the orphan's exit is never recorded
(finding 1). The same `start_new_session` is what makes cancel safe (constraint 8), so the fix
belongs in the exit path, not in `cancel_task`.
Evidence: `POST …c234/tasks/reveal_20261021-015740_6de4/cancel` → `{"ok": false}` at 02:11;
`ps -p 95019,95023` was empty, so those two orphans had already ended on their own.
Fix: in `main()`'s `except KeyboardInterrupt`, `os.killpg(p.pid, signal.SIGTERM)` for every
`PROCS` entry, persist `cancelled`, print the count.
verifiedBy: observed (the cancel refusal); source (the exit path, not exercised).

**[low] director_ui.py:877, 640-646 — `from_render` is the one id not checked against `ID_RE`.**
Impact: `rerender_spec` builds `d / "renders" / rid / "render.json"` from the request string, so
`..` reaches any `render.json` the owner has, and a non-string gives a 500. `start_render`
re-validates the plan (line 586) and the knob keys (line 600), so nothing outside
`scripts/research/plans/` can be rendered; the traversal string is recorded verbatim.
Evidence: `{"from_render":"../../mismatch_3_20261021-015336_10e3/renders/r20261021-015422_480_483d"}`
→ 200 and a render started (rid `r20261021-021200_480_02e1`, cancelled by me 1 s later); its
`render.json` holds `from_render: "../../mismatch_3_…"`. `{"from_render":["a"]}` → 500
`TypeError("unsupported operand type(s) for /: 'PosixPath' and 'list'")`.
Fix: `rid = str(body.get("from_render")); if not ID_RE.match(rid): raise ValueError("bad rid")`
before `rerender_spec`.
verifiedBy: observed.

**[low] director_ui.py:748-903 — no `Host` check, and JSON is parsed whatever the Content-Type.**
Impact: a web page open in the owner's browser can send a simple cross-origin POST (text/plain
body) to 127.0.0.1:8379 and create jobs, start 1920 renders, cancel tasks or write a picks file; it
cannot read responses (no CORS headers). `reveal.py` has the same model (grep for `Host` and
`Origin` finds no check), so this is the repo's existing threat model, not a regression.
Fix: refuse a request whose `Host` header is not `127.0.0.1:<port>` (DNS rebinding), and require
`Content-Type: application/json` on POST, which forces a CORS preflight the server never answers.
verifiedBy: source (not exercised).

**[low] director_ui.py:1128-1129 — picks `best` and `page` values follow a new convention.**
Impact: the keys equal `director_picks_11.json`'s (constraint 6), but `best[stem]` is
`"c1-<rid>"` where the round files hold `"c1"` or `"none"`, and `page` is `"workbench_<jid>"`.
The planner prompts read the picks files (`PLANNER_PROMPT_2026-10-21_r13_m1.txt` names
`director_picks`), so a consumer that compares `best` with a concept id misses. Nothing under
`scripts/` parses `best` today (`director_page.py` only exports, lines 154–164).
Evidence: `picks/director_picks_20261021-015913.json`:
`best = {"mismatch_3_r12": "c1-r20261021-015839_480_9826"}`,
`page = "workbench_mismatch_3_20261021-015759_1ef2"`.
Fix: write `best[stem] = "<concept>"` and put the rid in a sibling optional key (`best_render`),
or document the `concept-rid` form beside the picks shape in `director_page.py:127-136`.
verifiedBy: observed.

### Later

- [low] director_ui.py:328 — the subprocess env leaves `PYTHONDONTWRITEBYTECODE` unset, so the
  renderer's `import transitions` (director_render.py:30-31) rewrites
  `__pycache__/transitions.cpython-313.pyc` at the repo root whenever `transitions.py` changes:
  a gitignored (`.gitignore:1`) write outside the workbench from a UI-launched process. Not
  triggered this session (pyc mtime 01:40, unchanged by seven renders). Fix:
  `PYTHONDONTWRITEBYTECODE="1"` beside `PYTHONUNBUFFERED`. verifiedBy: source.
- [low] director_ui.py:576-578 — the overlay cache is written with `write_bytes`, not tmp +
  `os.replace` as `write_json` does; two first requests compute twice and a third can read a
  partial PNG. verifiedBy: source.
- [low] director_ui.py:951, 955, 1077, 1117-1123 — `p.pair`, `r.rid`, `r.concept`, `g.key`,
  `t.photo` go into innerHTML and into `onclick="newJob('${p.pair}')"` without `esc()`; a fixture
  or concept name holding `'` or `<` breaks the page. The input is the owner's own file names.
  verifiedBy: source.
- [low, CONTESTED] director_ui.py:945, 958, 1132 — `localStorage` keeps `dui_tab` (allowed) and
  `dui_job`, the open job. The brief allows a tab or a filter; the open job is a selection. The
  owner decides. verifiedBy: source.
- [info] director_ui.py:35 — `import sys` is unused. The favicon 404 is already in the build report.

## Frame challenge: the job folder as the only state

A job folder as the only state is the right choice for a one-owner research tool: every JSON is
written atomically (`write_json`, lines 96–101), a job survives a crash byte for byte, and the
Claude Code session can read it without the server. The premise fails on one point. The folder
stores inputs and outputs, but the transition from running to done lives in a Python thread
(`wait`, lines 336–359) and its `on_done` closures, nowhere on disk, so the folder is a complete
record only while the process that wrote it is alive. After a restart, a task whose pid is gone is
reported `lost` on every read and never persisted; its outputs on disk (`c234`'s `anchors.json`,
the `FAILED:` line) are not consulted; a render that finished after the server died has an mp4 and
an `info.json` beside a `render.json` that says `running`, and the grade panel never lists it. A
task whose pid is still alive (the child sits in its own session and survives Ctrl+C) shows
`running` with a cancel that answers `ok: false`, and a reused pid keeps a dead task `running` for
ever (`os.kill(pid, 0)`, line 390). The design's sentence "the UI rebuilds its state from it on
restart" is true only after the reconcile step of finding 1. Two smaller consequences: `--runs-date`
defaults to today (line 1142), so a restart after midnight shows an empty rail until the flag is
passed; and `cancel_task` can only ever signal a process this server started, which is correct for
safety and wrong for recovery.

## One refutation attempt on this verdict

The build report declared "a server restart while a task is running" untested, and §7's phase-1
acceptance list says nothing about restarts, so a reader could file finding 1 as a known gap rather
than a defect. I keep it as a defect because §5 states the restart property as a property of the
data model, not of a phase, and because the failure is silent: the page says "pending" with no
hint that a restart happened. Against the PASS rows: I did not exercise DNS rebinding or a
cross-origin POST (finding 4); every render was one pair at 480 px; and the "no writes outside"
row rests on reading every write site plus a seven-render file sweep on a machine where other
agents changed `scripts/research/plans/SCHEMA.md` and `director_render.py` (md5 `a1ec3245…` →
`dfa17fa9…`) during the same minutes, so that row is attribution by code path, not by process
accounting.

## Per-constraint table

| # | Constraint | Result | Evidence |
|---|---|---|---|
| 1 | binds 127.0.0.1 only; no outbound connection | PASS | `ThreadingHTTPServer(("127.0.0.1", a.port), Handler)` line 1148; imports lines 25–43 hold no `socket`, `urllib`, `http.client`, `requests`; one `subprocess.Popen` (329). `lsof -nP -i -a -p 7742` → one socket, `TCP 127.0.0.1:8381 (LISTEN)`; `GET /api/pairs` → 6 pairs, flags progress/resolve_only/stamp all true. observed |
| 2 | no import of reveal, transitions or a research script; heavy calls via `.venv/bin/python`; numpy and cv2 only for overlays | PASS (note) | imports lines 25–43 (stdlib, numpy, cv2); no `sys.path`; `PY = ROOT/.venv/bin/python` (47) used at 445, 447, 450, 611. Note: cv2 also decodes the mp4 in `extract_frames` (658–690), which §4 lists under `/frame` and the docstring (line 8) declares. source |
| 3 | path safety; ids by regex; POST cap | PASS (note: finding 3) | 13 `/file` probes → 403 or 404 (appendix A); a symlink in `renders/` to `reveal.py` → 403; job id (`job_dir`, 295), task id (845, 881), rid (850, 885), overlay kind (836), plan stem (823) by regex; `Content-Length: 2000000` → 400 "request too large", a real 1.2 MB body → 400. `from_render` unvalidated (finding 3). observed |
| 4 | argv from a list; no injection | PASS | `Popen([str(a) …])` line 329, no shell; knob keys `[A-Za-z_]\w*(\.[A-Za-z_]\w*)?` (600): `--max-long` → 400 "bad knob key", `a b` → 400; values `"2; echo pwned > /tmp/dui_pwned"` and `"0.3 --max-long 1920"` became single `--set` elements (appendix B), `/tmp/dui_pwned` absent, exit -15 after cancel. observed |
| 5 | writes only under `benchmarks/runs/<date>/workbench/` | PASS (note: finding 6) | every write site (`write_json` callers 315, 334, 346, 441, 454, 622, 635, 636, 683, 707; `write_bytes` 578; `copyfile` 352, 608, 893; `imwrite` 673; `mkdir` 305, 323, 433, 446, 448, 577, 596, 666, 1147) resolves under `WORK/<jid>` or `WORK`; subprocess output dirs (445, 447, 450, 611) are under the job folder. `find fixtures scripts/research/plans models -newer marker` → only `SCHEMA.md`, changed by another actor (the UI has no path to it); `_reveal/` and `models/` untouched; `reveal.py align --out` wrote its `jobs/` under `analysis/reveal/`. source + observed |
| 6 | picks keys = `director_picks_11.json` + {render, draft, frames}; `render.json` per §5; full sha | PASS (note: finding 5) | both picks files: top `{best, clips, date, page}`, clip `{acceptable, note, props}` + `{draft, render}` (+ `frames` in one), props `{one_picture, transforms, not_invented}`; `save_picks` (695–708) rejects an extra top key and an extra clip key (400, observed). `render.json`: all 13 §5 fields plus `draft, ended, exit_code, from_render, process_wall_s, renderer_flags, state, task`; `plan_sha256` 64 hex and equal to sha256 of the plan on disk. computed |
| 7 | determinism; `renderer_md5`; a changed knob changes the md5 | PASS | 5 mp4 on disk all `5b3ee379776ae4e8ce2dec4fa3293740` (computed) under renderer `d8a5f732`, `52630887`, `a1ec3245` ×3; the build's sixth (shell) render is not in the workbench, UNVERIFIED. `parallax_push` 2 → 2.2 gave `a3c2b147fd5311540f35b5a8f07d7600`; re-render from its `render.json` gave the same md5 under renderer `dfa17fa9…` (wall 10.4 s and 10.3 s). `renderer_md5` recorded (616) and equal to `info.json`'s stamp. observed |
| 8 | cancel: SIGTERM to the right pid, state marked | PASS | `os.killpg(p.pid, SIGTERM)` (423) only on a `PROCS` entry; child pid 14548 had pgid 14548 and sess 0, the server pgid 7740; after cancel: task `cancelled`, exit -15, `cancel: true`, pid gone, server alive, `render.json` `cancelled`; a task not started by this server → `{"ok": false}`. observed |
| page | no foreign fetch, CDN, font or script URL; localStorage only tab/filter | PASS / CONTESTED | grep: no `http://`, `https://`, `<link`, `@import`, `url(`; one inline `<script>` (937); `fetch` targets `/api/…` (943–944); font stack `Menlo,Monaco,monospace` (910); `localStorage` at 945 (`dui_tab`), 958 and 1132 (`dui_job`, finding 9). source |

### Confidence: 85%
Every constraint row was exercised against the running server or read at the line, and finding 1
was observed on a job I did not create. The 15 % covers: no browser session (page code read, not
driven), one pair and one size (480), the cross-origin path reasoned from source, and the
"no writes outside" attribution made by code path while other agents wrote in the same tree.

### Gaps
- No tool failed. Two MCP servers failed to connect at session start (`claude-design`,
  `postgres-mcp`); neither was needed. Playwright and Chrome tools were not used: the page was
  reviewed as source, so the §7 acceptance steps 1–6 (verdict within 30 s, overlay toggles, the
  knob edit and the drag, the progress line, the scrubber) rest on the build report's numbers.
- Not run: a 1920 render; any pair other than mismatch_3; the Ctrl+C orphan path (finding 2,
  reasoned from source, only its cancel refusal observed); a cross-origin POST (finding 4).
- The build report's sixth render "from the shell" was not located, so the six-render claim is
  five computed plus one claimed.
- Side effects of this review, all inside `benchmarks/runs/2026-10-21/workbench/` (gitignored):
  job `mismatch_3_20261021-015759_1ef2` gained four renders (`r20261021-021156_480_5f72`
  cancelled, `r20261021-021200_480_02e1` cancelled, `r20261021-021201_480_d1a9` and
  `r20261021-021250_480_532c` done, md5 `a3c2b147…`) and their task files; a symlink
  `renders/evil_link` was created and removed. The server on 8381 (pid 7742) was stopped by
  `kill 7742`; the port is free and no renderer process from these tests remains.

## Appendix A — `/file` probes (job `mismatch_3_20261021-015759_1ef2`, curl, 02:09)

| Path | Code |
|---|---|
| `../../reveal.py` (curl-squashed), `..%2f..%2freveal.py`, `..%2F..%2F..%2F..%2Freveal.py` | 404 / 403 / 403 |
| `../../reveal.py` and `../../../../../../../../etc/passwd` with `--path-as-is` | 403 / 403 |
| `//etc/passwd`, `//Users/…/reveal-1.5.0/reveal.py` (absolute) | 403 / 403 |
| `fixtures/../reveal.py`, `fixtures/../../reveal.py`, `fixtures/..%2f..%2freveal.py` | 403 / 404 / 403 |
| `layers/../../../../reveal.py`, `mattes/../../../../reveal.py` | 404 / 404 |
| `../mismatch_3_20261021-015336_10e3/job.json` (another job) | 404 |
| `renders/evil_link` → symlink to `reveal.py` | 403 |
| `fixtures/mismatch_3_S.jpg`, `renders/<rid>/render.json`, `job.json` | 200 / 200 / 200 |

## Appendix B — argv recorded for the hostile knob values (tasks/render_20261021-021156_86ab.json)

```
.venv/bin/python scripts/research/director_render.py scripts/research/plans/mismatch_3_r12.json
  benchmarks/runs/2026-10-21/workbench/mismatch_3_20261021-015759_1ef2/renders/r20261021-021156_480_5f72
  --concept c1 --max-long 480 --seconds 3 --fps 30
  --set 'cont_feather=14'
  --set 'front_margin="0.3 --max-long 1920"'
  --set 'parallax_push="2; echo pwned > /tmp/dui_pwned"'
  --set 'pane_becomes_view.window=[0.35, 0.97]'
  --progress
```
Each `--set` is one list element (the quotes are JSON inside the element, not shell quoting);
`ps -o pid,pgid,sess` showed the child as pid 14548, pgid 14548, and the server as pgid 7740.
