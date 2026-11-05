<!-- provenance: copied verbatim on 2026-11-05 from benchmarks/runs/2026-11-05/studio/agents/port_acceptance.md (gitignored), the report of the acceptance-drive subagent (Opus 5.5, max effort) of the 2026-11-05 session; a research artifact whose claims carry the author's own confidence and gaps; its evidence folder (server logs, JSON results, screenshots, the driver scripts) stays under benchmarks/runs/2026-11-05/studio/agents/port_acceptance/ (gitignored) -->

<!-- reader: the main thread, cold; shape: report; written by agent F, the acceptance driver of the studio package, on 2026-11-05 between 01:36 and 02:35. -->

# The studio package passes the acceptance of its first build phase (A1): 15 of 15 checks

The package reveal-studio 0.2.0 reproduces the acceptance drive of the studio's first build phase (A1), first run on
2026-11-04: 15 of 15 checks pass. The package code came from a snapshot of `studio/` taken at 01:36:52; the jobs, the
stills, the main venv and the research script were the real ones. The old script `scripts/research/studio.py` can be
retired once the test below also passes from the main tree.

- **Reproduced.** Four render md5s of 2026-11-04 came back byte for byte: the full a2 `c302623f…`, the full a3
  `2b425fdb…`, the 960 px draft `3d453980…` and the 480 px draft `2955c25c…`.
- **The durable test.** `studio/tests/acceptance/test_a1_loop_flow.py` passes on the snapshot in 99 s. It did not
  run from the main tree: `make qa` there stopped at lint, on a file another agent is writing.
- **Asked of the main thread.**
  1. Run the durable test from the main tree once `make qa` is green there.
  2. Then retire the old script. The owner's server (pid 51553 on port 8380) still runs it, so moving his server to
     the package is his call.
  3. File the five defect rows below; defect 1 is medium.
- **Open questions.** There are none for the owner.

Names used below:

- "A1": the first build phase of the studio, in section 9 of `.claude/claude-docs/STUDIO.md`. Its 15 acceptance checks were
  first driven on 2026-11-04, against the old script (`.claude/claude-docs/research/2026-11-04/a1_acceptance.md`).
- "the real tree": the repository at `/Users/yevhens/Projects/personal/reveal-1.5.0` with its real jobs under
  `benchmarks/runs/`, its main venv and `scripts/research/loop_seq.py`, the script every stage runs.
- "the main tree": the working copy of `studio/` in the real tree, which two other agents were editing during the
  drive.
- "the skeptic": a Claude Code subagent that judges each full render; its answer file gives a render a verdict.
  A render with no verdict is "unjudged", and the page gate refuses it.
- "the drive": this run of the 15 checks through the API, the CLI and a headless Chrome, 01:42 to 02:03.
- "the snapshot": an rsync copy of `studio/` at 01:36:52 with its own `uv sync` venv, at
  `/private/tmp/claude-501/-Users-yevhens-Projects-personal-reveal-1-5-0/d9082b8f-cf5b-4b41-ba3c-c8c2ee5b8bc6/scratchpad/snap/studio`.
  Every server and test run below used it.
- "the drive job": `loop_angel_20261105-014715`, the job check 3 made under `benchmarks/runs/2026-11-05/studio/`.
- "the adopted job": `loop_angel_20261104-220708`, the run folder `benchmarks/runs/2026-11-04/angel` adopted as a
  job on 2026-11-04.
- "the recorded prep": `benchmarks/runs/2026-11-04/angel/in/angel/`.
- Servers 1, 2 and 3: the three successive servers of the drive on 127.0.0.1:8395, pids 8990, 17318 and 18490. Each
  was started from the snapshot with
  `REVEAL_STUDIO_ROOT=/Users/yevhens/Projects/personal/reveal-1.5.0 uv run reveal-studio serve --port 8395 --no-browser --lock <snapshot>/../acc.lock`.
- The evidence folder: `benchmarks/runs/2026-11-05/studio/agents/port_acceptance/` (server logs, JSON results,
  screenshots, the driver scripts).

## The 15 checks

The checks follow `.claude/claude-docs/research/2026-11-04/a1_acceptance.md`. Record ids are folders under the drive
job's `stages/`.

| # | Check | Verdict | Observed |
|---|---|---|---|
| 1 | `GET /api/jobs` | PASS | The three jobs of 2026-11-04 (`…220708`, `…220719`, `…223204`); four after check 3, the drive job last. |
| 2 | The adopted job opens | PASS | Round 1's grade text equals "record that for angel page, options 2 and 3 are fine , close this effort" (Python `==`). Page md5 `72dadc4f5ea4db16152fe0c7062a3f94` in the view and the round. Five full candidates, a1 to a5. The studio holds no verdict for them, so each is unjudged; the view notes the skeptic reports of 2026-11-04 written before the studio existed (`skeptic1.md`, `skeptic2.md`). `render/full/a2`: 50 frames (26 photo, 24 generated). Frame 25: a 1366×1770 JPEG of 324,835 bytes from the existing decode cache. The job's folder gained no file. |
| 3 | A new loop job | PASS | `loop_angel_20261105-014715`. `raw/angel/01.jpg` and `02.jpg` are symlinks to the two originals; `job.json` holds sha256 `c0bb68c6…` and `b2a1dd82…`. |
| 4 | The registration | PASS | Record `20261105-014725_registration`, done in 5.6 s. `prep.json` frame 1 has the method "sift+magsac + lock": the fit, then the shift that holds the three lock windows still. It has 467 inliers of 751 matches, shift [-4.93, 11.48] and crop [29, 0, 1395, 1770]. `cmp` against the recorded prep: `k0.png` (`ccdb458c…`), `k1.png` (`558688ea…`), `depth_k0.npy` (`be5f197b…`) and `depth_k1.npy` (`abc01630…`) identical. |
| 5 | The readers (`loop_seq.py readers`: faces, focus and colour difference per still) | PASS | Record `20261105-014758_readers`, 0.4 s. The Lab distance between the two stills is above 14 on 0.3021 of the pixels (above 30 on 0.1343). Faces at the 1366×1770 canvas: k0 has 3 and k1 has 2. The third face in k0, box [616, 1087, 114, 114] at score 0.758, is the face printed on the cookie the two women hold. |
| 6 | The full a2 render | PASS | Record `20261105-014819_render`, done in 60.9 s. The progress number read "15/50 frames" at 3.1 s; 26 distinct values in all. `loop.mp4` md5 `c302623f293eacd069218fd7518e0967`, equal to `measure.json`'s `md5_mp4`. Six outputs with md5s. The record's `script_md5`, the md5 of `scripts/research/loop_seq.py`, is `474d57b324c6c7b815aa13c4444862bb`, the value the brief expects and the one `measure.json` carries. |
| 7 | The 960 draft | PASS | Record `20261105-014945_render`, 19.3 s. Progress "15/50 frames" at 1.6 s; 25 values. The candidate is a draft with `draft` 960, and its card's chip reads "draft 960" in the browser. `loop.mp4` md5 `3d453980f80eff43014646a6f65398a6`, the 960 draft md5 of 2026-11-04. |
| 8 | The viewer and a marked frame | PASS | `render/full/a2` lists 50 frames: 26 tagged photo and 24 tagged generated with their t (f14 has t 0.0534). The step series has 49 values. The generated runs are f14 to f25 and f38 to f49, drawn as 24 violet bands. The plan a2 has no dissolve frame (tag blend) and no motion-blurred blend (tag snap), so those tags do not appear. The mark wrote `owner_frames/full_a2_f0025.json` with the note and md5 `c302623f…`. |
| 9 | The skeptic request | PASS | `requests/skeptic_20261105-015036.json` names a2 with its md5, carries the f25 mark and states the answer's shape (verdict "READY \| READY WITH A NOTE \| NOT READY", `judged_md5`, note). `reveal-studio requests` from the snapshot listed it at 6 s old ("1 open request(s)"); `GET /api/requests` at 7 s. |
| 10 | The page gate | PASS | `POST /page {}`: 409 "the page is refused: a2 (unjudged: no skeptic verdict for this candidate)…", `refused` ["a2"]; no `index.html` and no record. With the override and the footer "F: override": 202, record `20261105-015052_page` done in 0.3 s. The page holds "Override: built on his word with a2 (…) (2026-11-05T01:50:52.236)." and the footer. `index.html` md5 `3a8e4f668fab9b469bb34465e40d302d` equals `page.md5`, round 1's `page_md5` and `rounds/1/index.html`. |
| 11 | The round gate | PASS | The full a3 before a grade: 409 "round 1 has no grade text: …". `POST /picks {"round": 1, "text": "F: acceptance grade text"}`: 200, saved with page md5 `3a8e4f66…`. The same a3 request: 202. I let it finish: record `20261105-015119_render`, 79.1 s, `loop.mp4` md5 `2b425fdb2abf1ef06d2e31e858bad93f`, the a3 md5 recorded on 2026-11-04. |
| 12 | A restart during a render | PASS | Second attempt, the 480 draft a2restart2, record `20261105-015431_render`. Server 2 got SIGTERM 2.97 s after the start; child 18151 kept running. Server 3's log: "pid 18151 still runs after a restart; re-attached", then "reconciled 1 running record(s) at start". The record ended done after 9.0 s with 6 outputs and `loop.mp4` `2955c25c…`. Its note reads "finished after a restart: the exit code is unknown; the terminal file was present". The terminal file is the stage's last output, `measure.json` for a render. The first attempt is under Gaps. |
| 13 | Cancel | PASS | The 480 draft a2cancel2, record `20261105-015541_render`. The cancel went 1.03 s after the start and was answered in 0.01 s: cancelled, "cancelled by you", exit code −15. The `.part` folder is gone, no final folder exists, the child is dead, and a second cancel answers 409. |
| 14 | The page in headless Chrome | PASS | At 2560×1440 with no localStorage the page opened the drive job. The rail lists 4 jobs and the strip 8 tiles; the render panel lists 2 full renders and 4 drafts. The viewer showed a2 at 2× as 2732×3540 for a 1366×1770 frame, a scale of 2.0 (the 2026-11-04 fail was 1.27). At 1:1 the scale was 1.0. The shown aspect is 0.7718, equal to the canvas's, in all three modes. The mark field's placeholder: rgb(138, 145, 152) on rgb(20, 22, 24), contrast 5.69:1 (the 2026-11-04 fail was 3.9:1). Hints: 94 `data-hint` keys on the 8 panels, and no popover says "no hint recorded". 74 keys are in the `hints` table of `GET /api/registry`. The other 20 (8 `stage.*`, 12 `knob.*`) resolve from the same response's `flows`, as `strip.js:21` and `inspector.js:9` read them. 0 console errors. |
| 15 | The impeccable detector | PASS | `[]` (0 anti-patterns, exit 0) at 2560×1440, 1440×900 and 1280×800; the next section has both scans. |

## Hard constraints

| Constraint | Observed |
|---|---|
| The server answers 127.0.0.1 only | `lsof -nP -iTCP:8395` listed one line, `Python 8990 … TCP 127.0.0.1:8395 (LISTEN)`; server 3 likewise (pid 18490). A `Host: evil.example:8395` request got 403 `{"error": "the studio answers 127.0.0.1 only"}`; `Host: 127.0.0.2` and a POST with a foreign Host got 403. The LAN address 192.168.50.46:8395 timed out after 3 s; `[::1]:8395` refused. |
| The server opens no outbound connection | I ran `lsof -nP -a -p <pid> -i` 4 s and 24 s into the a2 render. Server 1 showed its LISTEN line only; the render child (pid 11243, alone in its process group) showed none. After each of the three text-mode URL scans of check 15, server 3 showed no socket beyond LISTEN. |
| The originals are linked and hashed, never copied or changed | `raw/angel/01.jpg -> /Users/yevhens/Downloads/Telegram Desktop/angel-portrait/PXL_20261104_103732636.PORTRAIT~2.jpg`, `02.jpg -> …/PXL_20261104_103736727.PORTRAIT~2.jpg`. After the drive and the four test runs (the last ended at 02:25), both files keep mtime 1793789339 (2026-11-04 12:48:59) and their sha256s. A `diff` at 02:28:51 of the listings taken before and after is empty. |
| Every heavy call is a subprocess of the main venv's python | `argv[0]` of all 10 records of the drive job is `/Users/yevhens/Projects/personal/reveal-1.5.0/.venv/bin/python`, and `argv[1]` is `scripts/research/loop_seq.py`. |
| The job folder is the only state | Servers 2 and 3 started from the disk alone. Server 2 finished a record from its files; server 3 re-attached a live child (check 12). |
| Only my jobs gained files | `find -newer` (the drive's start, 01:42:16) at 02:13 and at 02:28 found no file in `benchmarks/runs/2026-11-04/angel`, the adopted job's folder, `models/` or `scripts/research/plans/`. At 02:13 the jobs `…223204` and `…220719` held 0 newer files. By 02:28 they held 69 and 57, from 02:20:42 on: agent D's plans (`d_a2_copy.json`, `d_a2_z.json`) and records of the stages `probe` and `measure`, which the snapshot's package does not have. Agents D and E serve those jobs on ports 8393 and 8394; none of my servers got a request for them. The owner's server (pid 51553, port 8380) still runs, and `benchmarks/runs/studio.lock` still reads "port 8380 pid 51553 since 2026-11-04T23:50:19.078". |

Before each server start I listed the running records of every other job and found none each time. The check exists
because `serve` reconciles every job of the tree (defect 1).

## The detector at three viewports

impeccable-engine 0.1.18, run from the repo root with `DO_NOT_TRACK=1` and `IMPECCABLE_BIN` set to the engine binary in the owner's clone of
the impeccable repository, `/Users/yevhens/Projects/ai/impeccable/skill/scripts/bin/darwin-arm64/impeccable`.

| Viewport | URL scan: `detect --json --no-advisory --viewport <WxH> http://127.0.0.1:8395/` | `--cdp` scan of a known screen |
|---|---|---|
| 2560×1440 | `[]`, exit 0 | `[]`, exit 0 (window 2560×1440, page 2560×1353) |
| 1440×900 | `[]`, exit 0 | `[]`, exit 0 (page 1440×813) |
| 1280×800 | `[]`, exit 0 | `[]`, exit 0 (page 1280×713) |

The text-mode runs, without `--json`, printed nothing and exited 0. The engine's own browser has no localStorage, so
`boot.js` opens the newest job, which was the drive job. What that browser showed cannot be observed from outside. To
know the scanned screen, I also ran `detect --cdp 9396 --target 127.0.0.1:8395` against my own headless Chrome. It
showed the drive job's render panel with a2 in the viewer at fit.

## The durable test

- **Files.** `studio/tests/acceptance/__init__.py` (1 line) and `studio/tests/acceptance/test_a1_loop_flow.py`
  (395 lines, md5 `2a6c0d74a1e908a170a672e57732ce5e`), in the main tree; the snapshot holds identical copies.
- **What it does.** It starts `python -m reveal_studio serve --root <root> --port <free port> --no-browser --lock <tmp>`
  as a subprocess. Then it runs checks 3 to 13 against that server with the recorded values. For check 12 it stops the
  server with SIGTERM while a 480 px draft renders, then starts a second server. It skips when the root, the main venv, the recorded prep
  or the stills are absent. It also skips when the stills' sha256s are not the angel pair's. Before the first `serve`
  start it waits until no other job has a running record; if one still runs after 300 s, the test skips. It waits the
  same way before the render of check 12. Just before the restart it skips at once if another job's record started.
- **Command.** `cd <snapshot> && REVEAL_STUDIO_ROOT=/Users/yevhens/Projects/personal/reveal-1.5.0 uv run pytest tests/acceptance -m acceptance -s -q`.
  The brief's `pytest tests -m acceptance` also runs `tests/integration/test_draft_render.py`, which writes a draft
  into the job `…220719`, so I ran the folder alone.

| Run | Start | Result | Job it made |
|---|---|---|---|
| First version | 02:05:20 | PASS in 107.4 s | `loop_angel_20261105-020522` (67 MB) |
| Mutation: the `lock_window` knob's flag set to None, in a second copy of the snapshot | 02:08:22 | FAIL at check 4 in 5.9 s, as intended | `loop_angel_20261105-020823` (23 MB) |
| Second version | 02:08:49 | PASS in 98.0 s | `loop_angel_20261105-020849` (69 MB) |
| Final version, docstring corrected | 02:23:25 | PASS in 99.3 s | `loop_angel_20261105-022325` (67 MB) |

Between the first and the second run I added two assertions and reworded one. The frozen plan file names its prep
folder in its `in` key. That key points at the recorded prep, which is byte-identical to the job's prep. So the a2
md5 alone cannot show which prep the render read. The new
assertions check that the `--set in=` argument and `plan.json` name the job's prep. The assertion on the lock windows' shift now
prints the values instead of raising `KeyError`. The final version changes the docstring only, where it describes the guard. In
the final run the registration took 4.2 s, the readers 0.4 s, a2 63.4 s with 26 progress values and the 960 draft
20.6 s. The page md5 was `f950fbda…`, and the restart draft re-attached and finished in 8.0 s.

- **Lint.** `uv run ruff check tests/acceptance` and `uv run ruff format --check tests/acceptance` are clean, in the
  snapshot and in the main tree.
- **Types.** `uv run mypy tests/acceptance` reports 9 `import-untyped` errors, all on `reveal_studio` imports: the
  package ships no `py.typed` (defect 3). `MYPYPATH=src uv run mypy tests/acceptance` reports "Success: no issues found
  in 2 source files" under strict mode.
- **The main tree.** The test did not run there. `make qa` at 02:10:37 exited 2 at lint, in
  `tests/test_server_views.py`, a file another agent is writing. Ruff flagged an unused import (F401: `poll`) and a
  list built with `+` (RUF005). A second `make qa` at 02:22:01 stopped on the same ruff findings. In the main tree pytest collects the test,
  and `make test-fast` deselects it.

## The snapshot

- Taken 2026-11-05T01:36:52+0200 by `rsync -a --exclude .venv --exclude '.*_cache' --exclude .coverage --exclude __pycache__`.
- `git -C /Users/yevhens/Projects/personal/reveal-1.5.0 status --short studio | head` printed one line, `?? studio/`:
  the whole package is untracked. HEAD was `4b6b020`.
- 68 files; the md5 of the sorted `md5 -r` listing (`snapshot_manifest.txt` in the evidence folder) is
  `2cec77d45606f505cf59a8986e7c977e`.
- `reveal-studio check` from the snapshot, with the same environment, exited 0 in 1.4 s. It printed the root, the
  main venv's python ("exists"), `loop_seq.py` md5 `474d57b324c6c7b815aa13c4444862bb`, 3 jobs, 48 frozen plans, and
  "progress yes, frames yes, readers yes".
- The main tree changed after it: `tests/test_views.py` at 02:02, a new `tests/test_server_views.py`, and
  `tests/fakes/` at 01:58. By 02:25 `runner/process.py`, `views/job.py` and `README.md` differed from the snapshot.

## Defects: candidate backlog rows

Line numbers are the snapshot's; where the main tree moved a line by 02:25, the table gives both.

| # | Severity | Symptom and reproduction | Where (read) | The fix I would make |
|---|---|---|---|---|
| 1 | medium | A server on its own lock file reconciles the running records of every job at start. The lock stops only a second server that uses the same lock file. Observed at 02:22 inside the drive job: server A (pid 40970) rendered a 960 draft, record `20261105-022232_render`. Server B (pid 41191, port 8396, its own lock) started 1.2 s later and logged "pid 41027 still runs after a restart; re-attached" while A was alive. A's wait thread wrote done first (exit 0, no restart note), so the race went A's way. When B's watcher wins, `finalize` writes the note "finished after a restart" and no exit code (read from the code). | `server/app.py:53` calls `reconcile_all`; `runner/process.py:327-350` (332-355 in the main tree); `runner/lock.py:21-49` | Write the starting server's pid into `stage.json`, and reconcile at start only the records whose server is gone. Until then the test keeps its guard (`wait_quiet`). |
| 2 | low | When a browser drops a keep-alive connection, the server prints one full traceback per socket to its stderr. Server 3's log holds 5 `ConnectionResetError: [Errno 54]` tracebacks from after my headless Chrome sessions closed. The page sees nothing. | `server/app.py`: `StudioServer` has no `handle_error`. `server/handler.py:159` catches resets inside `_handle` only; these come from `handle_one_request` reading the next request line. | Override `StudioServer.handle_error` to drop `ConnectionResetError` and `BrokenPipeError`, with one log line at most. |
| 3 | low | `uv run mypy tests/acceptance` reports 9 `import-untyped` errors: the package ships no `py.typed`, and `[tool.mypy] files = ["src"]` keeps `make typecheck` off the tests. With `MYPYPATH=src`, `tests/integration/test_loopseq_help.py:44` shows 1 error: `"object" has no attribute "__iter__"`. | `pyproject.toml` `[tool.mypy]`; `tests/integration/test_loopseq_help.py:44` | Add `mypy_path = "src"` and `files = ["src", "tests"]`, then fix line 44. |
| 4 | low | `make acceptance` runs `pytest tests -m acceptance`, which includes `tests/integration/test_draft_render.py` (marked acceptance on 2026-11-05). Each run writes an 8 MB draft into the owner's job `…220719`. The main tree's `README.md`, edited after the snapshot, now says so. The test layers table of `ARCHITECTURE.md` still reads "none yet" with 0 acceptance tests. | `Makefile` target `acceptance`; `ARCHITECTURE.md:98` | Give the draft test its own target, so `make acceptance` runs `tests/acceptance` only; update `ARCHITECTURE.md:98`. |
| 5 | low | After a cancelled draft the render tile shows the cancelled attempt's wall time, 1.0 s, beside a "done" chip. The panel heading reads "done · cancelled by you" while 2 full renders and 4 drafts exist. Reproduce: render a2, then start and cancel a draft, then open the render tile (`acc14_render_fit_2560.jpg`). | `views/job.py:123-126` copies the latest record's `wall_s` and `reason`; `:178-181` keep the state "done" (172-174 and 231-234 in the main tree) | Take the tile's wall time and reason from the newest done render, and keep the cancelled attempt in `last_attempt` only. |

A known defect that `studio/ARCHITECTURE.md` lists came back in check 13: the cancel request and the child's wait
thread both finish the record. The log says "cancelled (cancelled;
the server restarted before the record was written)". The final record lacks the note that the `.part` folder was
removed, though the folder is gone. It needs no new row.

## Corrections to the brief

- The grade body: `jobs/grades.py:90` reads `text`. The brief's `{"round": 1, "grade": "…"}` gets 400 "the grade text
  is empty: his words, verbatim"; I sent `{"round": 1, "text": "F: acceptance grade text"}`.
- The a3 md5: the brief's `2b425fdbabf1ef06d2e31e858bad93f` has 31 hex digits. The recorded `measure.json` reads
  `2b425fdb2abf1ef06d2e31e858bad93f`, and the package reproduced that value.
- "The placeholder's aspect": the 2026-11-04 fail was the mark field's placeholder contrast, 3.9:1 against a bar of
  4.5:1. I measured that contrast (5.69:1). For the wording, I also measured the frame's aspect against the canvas's:
  they are equal.
- `POST …/stages/<rid>/cancel` needs a JSON body like every POST: without `Content-Type: application/json` the handler
  answers 415 (`server/handler.py:82-83`), a rule that blocks cross-site forms. My first cancel (record
  `20261105-015505_render`, a2cancel) sent no body, got 415, and the draft ran to done; I repeated it with `{}`. A
  line in `README.md` would save a shell user the same retry.

## Gaps

- The verdict covers the snapshot of 01:36:52. The main tree has changed since; the run from the main tree waits
  for a green `make qa`.
- Check 12's first attempt, record `20261105-015342_render`, missed the re-attach. My guard script took 7.5 s between
  the SIGTERM and the restart, and the 480 draft ended first. Server 2 then finished the record from its files: done,
  note "finished after a restart", `loop.mp4` `2955c25c…`. The second attempt re-attached, so both paths have a record.
- The first browser run of check 14 timed out after 20 s waiting for the frame image. Three later runs had it loaded
  within 0.3 s; the cause is UNVERIFIED, most likely my driver.
- Check 14 ran in my own headless Chrome over its DevTools port 9396, driven by a Node 22 script in the evidence
  folder. I chose that over the Playwright MCP on port 9222, so I shared no browser with the other agents.
- I did not drive playback at 25 fps, keyboard stepping, or a skeptic answer with its verdict chip. They are outside
  the brief's 15 checks; the drive of 2026-11-04 covered playback and keyboard stepping on the old script.
- The outbound check is a set of `lsof` samples (twice during the a2 render, once after each text-mode URL scan), not a
  continuous watch. I did not watch the detector's own Chrome.

## What I wrote, and what is stopped

- Five jobs under `benchmarks/runs/2026-11-05/studio/` (gitignored):
  - `loop_angel_20261105-014715`, the drive, 121 MB, including the 960 draft `a2twoservers` of the defect 1
    observation (`loop.mp4` `3d453980…` again);
  - `loop_angel_20261105-020522`, `loop_angel_20261105-020849` and `loop_angel_20261105-022325`, the three passing
    test runs, 67, 69 and 67 MB;
  - `loop_angel_20261105-020823`, the mutation run, 23 MB.
- `studio/tests/acceptance/` in the main tree: 2 files, untracked like the rest of `studio/`.
- This report and the evidence folder `benchmarks/runs/2026-11-05/studio/agents/port_acceptance/` (49 files, 3.7 MB).
- Four folders in the scratchpad
  `/private/tmp/claude-501/-Users-yevhens-Projects-personal-reveal-1-5-0/d9082b8f-cf5b-4b41-ba3c-c8c2ee5b8bc6/scratchpad/`:
  - `snap/`, the snapshot, 291 MB;
  - `snap_mut/`, the mutation copy, 273 MB;
  - `cdp/`, the browser scripts, Chrome profiles and screenshots, 126 MB;
  - `drive/`, the logs and the drive's scripts.
- Stopped by pid with SIGTERM: servers 1 (8990) and 2 (17318) during check 12, and server 3 (18490) after check 15.
  Servers A (40970) and B (41191) of the defect 1 observation stopped the same way. Ports 8395 and 8396 are free, and none of my headless
  Chrome processes runs. The owner's server on 8380 and agent D's server on 8393 were never touched.
