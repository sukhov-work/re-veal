<!-- Provenance: written by a Fable 5.1 review subagent (the read-only review of scripts/research/studio.py, phase A1, against the eight hard constraints and STUDIO.md §4–§5, with a restart drive on port 8390) of the Claude Code session of 2026-11-04 (the studio phase A1 build; DECISIONS 2026-11-04 sixth line); copied verbatim from benchmarks/runs/2026-11-04/studio/agents/a1_review.md (sha256 d96c5c18eb3c94e3) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). The reviewed file was the 22:25 version; the two high findings (a page once per run folder; the registration never rerun) and the medium ones (typed text wiped on a data change, a cancelling record never reconciled, cancel without the pid identity check, two servers on one tree, an empty-body POST without a Content-Type check) were fixed by the main thread at 22:37 (DECISIONS 2026-11-04 sixth line names what changed). A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

<!-- reader: the main thread of the 2026-11-04 evening session and the owner, cold; shape: report (the calling prompt's template). Written by a Fable 5.1 review subagent, read-only, 22:20–22:40 on 2026-11-04. The reviewed file: scripts/research/studio.py, md5 d2acc9b0c4f0600613462ef8f1e3f30e, 1,911 lines, mtime 22:25:28. The file changed on disk at 22:25:28 while this review ran (1,899 to 1,911 lines; the poll guard of lines 1793–1799 was added). Every line number below is from the 22:25:28 file. -->

## Findings: Fable review of studio.py

Summary. `studio.py` keeps seven of the eight hard constraints. The eighth is contested: the review gates exist and fire, but the never-overwrite rule on one fixed `index.html` makes a second round impossible (finding 1). The restart drive passed on job `loop_angel_20261104-220719`. A child alive across a server restart was re-attached and finished as done. A child whose process group was killed came back as lost. A re-attached child was cancelled 4 s after the restart. Nothing crossed the scope fence of `AGENTS.md`: no import of either tool, no new dependency, no network path. The server on port 8380 was not touched. It did reconcile one of my records before my restart, which is finding 6.

### Verdicts (the eight constraints: PASS | FAIL | CONTESTED · file:line · one sentence)

1. PASS · studio.py:1564, 1352–1354 · The server binds `("127.0.0.1", port)`; `Host: evil.example:8390` answered 403, `127.0.0.1:8390` answered 200, and `lsof` showed one LISTEN socket.
2. PASS · studio.py:31–45, 604–605; loop_seq.py:64–65 · The imports are stdlib only, the subprocesses are `loop_seq.py --help`, `ps` and the four stage commands, and `loop_seq.py` sets `HF_HUB_OFFLINE` and `TRANSFORMERS_OFFLINE` at module level (no packet capture: see Gaps).
3. PASS · studio.py:31–45, 1167, 1195 · No `reveal`, `transitions` or research-script import and no `sys.path` edit; `cv2` is imported inside two functions, and numpy is never imported.
4. PASS with a note · studio.py:397–406, 502, 531, 674; loop_seq.py:1644, 1721 · The originals are symlinked and hashed; a run folder receives the prep, a render, the page, `page.md5`, `keys.jpg` (§4 accepts it) and the readers' depth maps (finding 8).
5. PASS · studio.py:697–724, 622–663 · Record `20261104-222712_render` (pid 11813) was re-attached after a restart and finished as done; record `20261104-222804_render` (pid 13452, group killed) came back lost; the reconcile skips `cancelling` (finding 4).
6. PASS · studio.py:320, 480, 518, 556, 830, 1112, 1416–1420, 1514 · Every id in a path or body passes `ID_RE`, `NAME_RE` or a whitelist; the `/file` probes (appendix A) gave 403 or 404 outside the job and 200 inside.
7. PASS · studio.py:727–765, 626 · `cancelling` is written under the lock before `killpg` on the child's group, the wait thread's `finalize` returns unless the state is `running`, and a re-attached child was cancelled in 0.21 s (finding 5: the pid gap).
8. CONTESTED · studio.py:1303–1313, 579–583, 594, 531 · The three gates fired (409 each, appendix A) and the override reaches the page's footer, but the overwrite rule on a fixed `root/index.html` refuses every later page (finding 1).

### Findings (most severe first)

[high] studio.py:531, 594 — a page can be built once per run folder. Impact: `argv_for` fixes the page's `out_final` to `root/index.html`, and `start_stage` refuses any existing `out_final`. Round 2 of a new job and every page of an adopted job (the angel folder holds `index.html`) are refused with "exists: choose another name". The page stage has no name knob. Evidence: the two lines; the same line 594 was observed refusing the registration rerun (finding 2). Not exercised with `override: true` on the adopted job, to leave the owner's angel page alone. Fix: write the page to `rounds/<n>/index.html`, where STUDIO.md §4 already puts "the page, its md5", and copy the latest to the root. Or exempt the page stage from the rule and move the previous page under `rounds/<n-1>/` before the rename. verifiedBy: source.

[high] studio.py:502, 594, 1887 — "rerun registration" is refused for ever after the first success. Impact: the prep's `out_final` is `in/<seq>`, so the inspector's "rerun registration" button can never fit new lock windows. The only way is a new job. Evidence: `POST /stages/registration/run {"knobs":{}}` answered 409 "…/in/angel exists: choose another name (a finished output is never overwritten)". Fix: version the prep (`in/<seq>_<stamp>` with `job.json` pointing at the current one) and mark the stages after it stale, as §2's "rerun from here" asks. verifiedBy: observed.

[medium] studio.py:1793–1799, 1841, 1833, 1838 — his typed grade text is wiped when focus is elsewhere and the job's data changes. Impact: the 22:25:28 guard keeps the panel only while an input inside it has focus. With focus elsewhere, any change of the signature (a draft finishing, a plan saved, a page built) re-renders the panel, and `panelGrades` emits an empty textarea. The skeptic brief, the page title, intro, notes and override box, and the plan name and words share the fault. Evidence (Playwright on 8390, job `loop_angel_20261104-220708`): typed text, `blur()`, a forced signature change, `openJob(id, true)`; the textarea's value was `""`. The same with the textarea focused kept the node and its text. Fix: keep every form value in `S`, as `S.planText` is kept (1822, 1846), and restore it after a render; or re-render only the parts whose data changed. verifiedBy: observed.

[medium] studio.py:706, 733, 763 — a `cancelling` record is never reconciled. Impact: `reconcile` returns for every state but `running`. A server death between cancel's two writes leaves "cancelling" on disk and on the strip for ever, the pending-for-ever class the review of 2026-10-21 named. Evidence: the three lines. Fix: treat `cancelling` as `running` in `reconcile`; when the pid is gone, write `cancelled` and remove the `.part` folder. verifiedBy: source.

[medium] studio.py:736, 741, 745 — cancel signals a process group by the recorded pid without the identity check. Impact: `pid_alive(rec["pid"])` is called without `rec`, so the `ps -o args` check for `loop_seq.py` and the `.part` path is skipped. A stale running record whose pid was reused sends SIGTERM and then SIGKILL to a stranger's group. Evidence: the three lines; `reconcile` (708) does pass `rec`. Fix: `if not pid_alive(rec["pid"], rec): return reconcile(d, rec)` before the first `killpg`. verifiedBy: source.

[medium] studio.py:63, 640, 714–724 — two servers on one tree reconcile the same record. Impact: `STATE_LOCK` is per process. The 8380 server (the main thread's, with a browser tab polling the job) and my 8390 server both scan `benchmarks/runs/*/studio/*/job.json`. The loser of a double `finalize` raises `FileNotFoundError` at `os.replace` inside a daemon thread. Evidence: in drive 2 the record's `ended` is 22:28:09 and my restart is 22:28:10, so the 8380 server wrote `lost` first. Fix: an `flock` on `stage.json` around `finalize` and `cancel`, or a `studio.lock` under `benchmarks/runs/` that refuses a second server and names the first one's port. verifiedBy: observed.

[medium] studio.py:1358–1364 — an empty-body POST passes without a Content-Type check. Impact: the `application/json` requirement runs only when the body is non-empty. A cross-site page can send a simple POST with no body to cancel a running stage, write a skeptic request, build a page when no candidate is unjudged, or run a stage with default knobs. The responses stay unreadable to it. Evidence: `POST …/stages/20261104-220742_render/cancel` with `Origin: http://evil.example` and no body answered 409 "done, not running", so the request reached the handler. Fix: require `Content-Type: application/json` on every POST, or refuse when `Sec-Fetch-Site` is `cross-site`. verifiedBy: observed.

[low] loop_seq.py:1644; studio.py:510–512 — the readers stage writes `depth_k<i>.npy` into `in/<seq>/`, outside its `.part` folder. Impact: the record's `outputs` list (643) never holds those files. On an adopted job this is a write into the run folder beyond a render folder and a rebuilt page. Evidence: the write site; the stage was not run in this review. Fix: let `readers` write the map into its own out folder and let the studio copy it on `done`, or list it in the record. verifiedBy: source.

[low] studio.py:647–650 — a run that ends while the server is down with exit 2 comes back `lost`, not `refused`. Impact: `rc is None` skips the `failed_line` branch although the `FAILED:` line is in hand. Fix: when `rc is None` and `failed_line` exists write `refused`; when the log ends in a traceback write `failed`. verifiedBy: source.

[low] studio.py:435, 579 — `override_round` bypasses the round gate from the API only. Impact: the key is accepted for every stage, is not in STUDIO.md §4, is never sent by the page and is not written into the round. Fix: remove it, or record it in `round.json` as "overridden by his word" with the words. verifiedBy: source.

[low] studio.py:1137, 1156 — `int()` on the `round` and `frame` body fields answers 500. Evidence: `{"error": "ValueError: invalid literal for int() with base 10: 'x'"} [500]` and a `TypeError` 500 for `frame: null`. The reason reaches the page; the code is wrong. Fix: validate both fields and answer 400 with the field's name. verifiedBy: observed.

[low] studio.py:643 — `finalize` md5s every output while holding `STATE_LOCK`. Impact: a full render with `--frames` (50–300 JPEGs plus the mp4 and the gif) blocks cancel and every other finalize for seconds. Fix: compute `outputs_of` after the lock is released, then write the record under the lock. verifiedBy: source.

[low] studio.py:605 — `PYTHONDONTWRITEBYTECODE` is still unset in the child's environment. Impact: the review of 2026-10-21 noted it. `loop_seq.py` imports `transitions` and `rife_probe`, so a change to either rewrites a `.pyc` under `__pycache__` from a studio-launched process. Evidence: not triggered here; the `transitions` pyc (21:48) and the `rife_probe` pyc (18:07) were unchanged after six renders. Fix: `"PYTHONDONTWRITEBYTECODE": "1"` beside `PYTHONUNBUFFERED`. verifiedBy: observed (not triggered).

[low] studio.py:1398, 1341, 1839 — every file answer is `Cache-Control: no-store`, and the page's iframe is re-created on each panel re-render. Impact: the strip's and the viewer's thumbnails are re-fetched on every poll (1–5 s). The review page with its autoplay videos reloads whenever the page panel re-renders. Fix: an ETag or `max-age` for files under `cache/`, and an iframe kept across re-renders. verifiedBy: source.

[low] studio.py:7, 13, 25 — three docstring claims the code does not keep. Impact: "numpy and cv2" (numpy is never imported); "in/raw/<nn>.jpg" (the links are made under `raw/<seq>/<nn>.jpg`, lines 397–401); "never left pending" (a `cancelling` record is, finding 4). Fix: edit the three lines. verifiedBy: source.

[low] studio.py:269, 1756 — the hint `chip.queued` and the class map name a `queued` state the code never writes. Fix: drop the state, or write it between the record and the `Popen`. verifiedBy: source.

[low, CONTESTED] studio.py:1789 — `localStorage` keeps the open job. Impact: the review of 2026-10-21 contested the same choice (a selection, not a tab or a filter). Unchanged; the owner decides. verifiedBy: source.

[info] studio.py:473–487 — `GET /api/plans/frozen/<name>` answered 500 `TypeError` on the file as read at 22:20 and 200 on the 22:25:28 file. Fixed during the review. The plan editor's "load" of a frozen plan (1845) depends on it. verifiedBy: observed.

### Restart drive (what you ran, the record states before and after, the pids)

Setup: `.venv/bin/python scripts/research/studio.py --port 8390 --no-browser --runs-date 2026-11-04` under `nohup` from a non-interactive shell, stderr to a scratch file. SIGINT did nothing: such a child starts with SIGINT ignored, so Python never installs its handler. SIGTERM was used instead. It kills the server outright and skips the `KeyboardInterrupt` message of line 1572 (not exercised). The 480 draft of the first attempt (`revdraft`, record `20261104-222628_render`, pid 10657) finished in 8.0 s under the server that survived the SIGINT. The drives below use a 960 draft so the child outlives the 3 s.

| Drive | Record · child pid (pgid = pid, sess 0) | Before the kill | Action | After the restart |
|---|---|---|---|---|
| 1b: child alive across the restart | `20261104-222712_render` · 11813 | running at t+3 s; SIGTERM to server 9303 at t+4 s; the server gone, the child at 5 s elapsed, the record still `running` | restart at 22:27:17 | the log: "pid 11813 still runs after a restart; re-attached", then "done"; the record `done`, `exit_code: null`, `wall_s 21.0`, note "finished after a restart: the exit code is unknown; the terminal file was present", 6 outputs; `drafts/angel/revdraft960` renamed from `.part`; the `done` marker present |
| 2: child group killed | `20261104-222804_render` · 13452 | running at t+3 s; SIGTERM to server 11961; `kill -9 -- -13452`; the child gone | restart at 22:28:10 | the record `lost`, reason "the server restarted while the stage ran and no terminal file was found: run it again", `wall_s 5.0`, log tail `PROGRESS 19 50 frames`; `drafts/angel/revlost960.part` left in place; `ended` 22:28:09 was written by the 8380 server before my restart (finding 6); the render tile shows `lost` with the reason |
| 3: cancel after a restart | `20261104-222844_render` · 14255 | running at t+2 s; SIGTERM to server 13558 | restart at 22:28:47, re-attached; `POST …/cancel` at 22:28:51 | 200 in 0.21 s; the record `cancelled`, reason "cancelled by you", note "the .part folder was removed"; the child gone 1 s later; no `loop_seq.py` process left |

Side effects, all under `benchmarks/runs/2026-11-04/studio/` (gitignored). Job `loop_angel_20261104-220719` gained four records and the folders `drafts/angel/revdraft`, `revdraft960` and `revlost960.part` (20 MB). Job `loop_angel_20261104-220708` gained `cache/frames/` for its eight renders (105 MB, derived, "safe to delete" per the docstring) from my browser visit. The 8390 server is stopped and the port is free. The 8380 server (pid 6616) was not touched.

### Confidence: 85%

Every verdict row was exercised on the running server or read at the line. All three restart drives were observed on records I made. The 15 % covers the following. The file changed under me at 22:25:28 and I re-anchored by grep rather than re-reading all 1,911 lines. Constraint 2 rests on `lsof` and the imports, not a packet capture. The page build with override was not run. The readers stage was not run.

### Gaps (what you could not check)

- The reviewed file is the 22:25:28 version (md5 d2acc9b0…). If the main thread edited it again after 22:25:28, the line numbers drift.
- Not run: the page build with `override: true` (it would have written into the owner's angel folder, or opened round 1 of the test job). Not run either: the readers stage, a render from a plan saved in the job, the keyboard, the viewer's 1:1 and 2× modes, and playback at 25 fps (source read only).
- Not captured: packets from the server or a child. Constraint 2 is `lsof` plus the imports plus `loop_seq.py:64–65`.
- Unexplained: in my Playwright page `S.stage` moved from `grades` to `page` between two evaluates with no click. Not reproduced; it may be my own `renderPanel` wrapper.
- The SIGINT path of line 1572 was not exercised (see the drive's setup note).
- No tool failed. Two MCP servers failed to connect at session start (`claude-design`, `postgres-mcp`); neither was needed.

### Appendix A — probes against 8390 (curl, 22:25–22:30, job `loop_angel_20261104-220719` unless named)

| Request | Code · answer |
|---|---|
| `GET /api/jobs` with `Host: evil.example:8390` | 403 "the studio answers 127.0.0.1 only" |
| `GET /api/jobs/<id>/file/../../job.json` (`--path-as-is`) | 403 |
| `…/file/..%2f..%2fjob.json` | 404 (the path is not percent-decoded, so the literal name does not exist) |
| `…/file//etc/passwd`, `…/file/etc/passwd` with a leading slash | 403 / 403 |
| `…/file/raw/angel/01.jpg` (a symlink to `~/Downloads`) | 404 (resolves outside the job) |
| `…/file/in/angel/prep.json`, `…/file/stages/<rid>/stage.json` | 200 / 200 |
| `GET /api/jobs/..%2f..%2fx` | 400 "a job id is letters, digits, dot, dash and underscore" |
| `GET …/render/full/..%2fa2` | 400 "a render is full\|draft/<name>" |
| `POST …/requests/evil` | 400 "a request kind is skeptic, plan, reading, director or keyframe" |
| `POST …/picks` with `Content-Type: text/plain` | 415 "POST bodies are application/json" |
| `POST …/stages/render/run` name `a2` (exists) | 409 "…/angel/a2 exists: choose another name" |
| `POST …/stages/registration/run` | 409 "…/in/angel exists: choose another name" |
| `POST /api/jobs/loop_angel_20261104-220708/stages/render/run` draft 0 | 409 "round 1 has no grade text …" |
| `POST /api/jobs/loop_angel_20261104-220708/page` `{}` | 409 "the page is refused: a1 (unjudged …) … a5 …" |
| `POST …/picks` `{"round":"x"}`; `POST …/frames/mark` `{"frame":null}` | 500 ValueError / 500 TypeError |

No record folder was left by any refused request: the `stages/` listing held the two original records after the probes.
