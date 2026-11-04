<!-- Provenance: written by an Opus 5.5 subagent (skeptic lens 1, feasibility and constraints, on STUDIO.md) of the Claude Code session of 2026-11-04 (the studio design; DECISIONS 2026-11-04 second line); copied verbatim from benchmarks/runs/2026-11-04/studio/agents/lens1_feasibility.md (sha256 1ea91c2ea93cd154) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). Nine verdicts: the registry hand-written with ranges null unless --help states one; the data model to the scripts' real layout; the request pickup missing (T74); the box queue as submit-then-poll; phase A split and its acceptance rewritten around a2's recorded lock windows; port 8380; the breath-by-depth fix crashed without a parallax (fixed the same hour). STUDIO.md §12 records what changed. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

## Findings: lens 1 (feasibility)

The design holds, but it does not build as written. The fix to the two Track A bugs made one of them worse: `breath.depth_k` without `parallax` now crashes with an IndexError. Phase A's acceptance check cannot pass in the form it is written. The registry is promised knob ranges that no file holds. The job-folder layout does not match the one `loop_seq.py page` reads. Port 8379 belongs to the incumbent workbench. Read-only review; the only thing run was a six-line call to `apply_camera` on 8×8 arrays, plus `--help`.

### Verdicts

1. **Generic stage runner: CONTESTED.**
   - What fits the generic shape: argv-only stages such as `reveal.py align`, `transitions.py pair`, `director_render.py`, and `loop_seq.py prep|render|page` (`--help`; `loop_seq.py:1618–1633`).
   - What needs per-stage code:
     - The loop plan editor. `SCHEMA.md` is 134 lines of prose. The keys are nested and depend on the method: about 20 more `slices` keys, `sheets` per-sheet and `objects[]`, `local[]` boxes (Track A, loop-plan table).
     - Plan edits must write a new plan file. `--set` takes top-level keys only (`loop_seq.py:1526–1528`), so a leg's `n` or the breath's `z` cannot go through argv.
     - Registration with "the windows' dx, dy under the three fits" is three `prep` runs into three folders: all-keypoint, `--bg-depth 0.15 --min-inliers 25`, and `--lock-window`. That is a fan-out, not one stage.
     - The probe and the measures do not exist yet (§7).
     - The readers have no CLI to call:
       - `transitions.py` has only `pair|check|warmup`;
       - `rife_probe.py` has only `warmup|matte|run`, with no faces command;
       - `matte_source.py run` is in a scratch venv.
   - Invented ranges: the code holds defaults but no ranges for every loop key. Examples: `breath.z`, `cx`, `cy`, `depth_k`, `depth_clip` (`loop_seq.py:1272–1340`), `parallax.amp`, `amp2`, `ref`, `sigma`, `glow.thr`, `sigma`, `mix`, `gain`, `rife.margin`, `matte.thr`, `grow`, `feather`, `min_share`, `crf`, `gif_long`, `crop`, `n`, `hold`, every `slices` and `sheets` key, and `prep --bg-depth`, `--min-inliers`, `--long`. The same holds for the director `--set` keys outside `map_knob` and for `transitions.py --zoom`. Only `--zoom` (clamped 0.02–0.5) and `--color` and `--warp` (0..1) state ranges in `--help`.
   - Defaults that disagree between SCHEMA and code: the sheets ease, `rife.margin`, and the objects' lead and linger (Track A gap 3).
   - Two more errors in §2: the pair row lists a "style" knob, but `transitions.py pair` has only `--preset`; "the quality knobs" is not defined.
   - Fix for STUDIO.md §2:
     - Say the registry is a hand-written table in `studio.py`. Each knob is `{name, type, default (from the code line, cited), range: null | the --help range}`. A null range renders as a plain number field with the default shown.
     - Add "observed in the plans" min and max as a hint, labelled as such.
     - Name three stages that get their own code: the loop plan editor (from a hand-written per-method key table built from the code, not from SCHEMA), registration (three-fit fan-out), and the readers.
     - Drop "style" from the pair row.

2. **The §7 script additions: FAIL (the list is incomplete; the additions it does list are safe).**
   - Safe:
     - `--progress` writes stderr only; mp4 bytes come from ffmpeg stdin (`loop_seq.py:1462–1469`).
     - `script_md5` and `rife_version` change only `measure.json`, which already varies through `render_s`.
     - `--frames`, `--windows`, `probe` and `measure` add files or commands.
   - Gap in the check: the byte-identity check names only the sheets watch (s6 5908af3d…). The `--progress` hook goes into the RIFE leg loop, which s6 does not exercise. Add a RIFE plan watch: a2 c302623f…, run twice from the shell first.
   - Omitted from §7:
     - **The changed-region mask.** `reveal.py align` writes no mask file. It writes `before.jpg`, `after_aligned.jpg`, the previews and `metrics.json` with `changed_pct` (`reveal.py:1389–1414`, `2517–2530`). The §2 align row's "changed-region mask as an overlay" needs a `reveal.py` change, which T68 forbids, or the studio recomputing it. Recomputing is analysis, not the PNG conversion §5 allows.
     - **align and pair outputs.** `reveal.py align` writes no stage timings and no ladder candidates (Track A gap 4). `transitions.py pair` has no progress.
     - **Refused versus failed.** align exits 2 on any failure (`reveal.py:2521–2523`), so the stage must parse `FAILED: …` from stderr to tell the two apart.
     - **Director stage flags.** `director_render.py --layers-dir` and `--mattes-dir` default to dated folders (`--help`). The director stage must pass them, and §2 omits them.
     - **The reader CLIs** (item 1).
     - **`page` layout** (item 3).
     - **`prep.json` gaps.** It does not record `--min-inliers`, `--ecc-refine`, the requested `--ref` or the `--depth-blend` values (Track A). "Copy a command line that reproduces the stage" therefore depends on `stage.json`'s argv, not on the outputs.
   - Neither tool changes in disguise: `loop_seq.py` imports `transitions` (`loop_seq.py:235`) but changes nothing in it. The mask is the one item that would pull a `reveal.py` change.
   - Fix: add rows for the reader CLIs, for `page` taking explicit paths, and for the mask (the studio computes it, labelled as such, or it is cut). Add the a2 watch.

3. **Data model: FAIL.**
   - **`page` layout.** `loop_seq.py page --root R` reads `R/in/<seq>/prep.json` and `R/<seq>/<variant>/measure.json`, and it writes `R/in/<seq>/keys.jpg` (`loop_seq.py:1564–1590`). §4's `in/`, `stages/<n>_<name>/` and `renders/<rid>/` cannot feed it without symlinks or copies. `page` also writes into the registration stage's output folder after the fact, so a folder-level md5 of that stage drifts.
   - **Two homes for one output.** §4 puts the prep outputs in both `in/` and `stages/<n>_<name>/`, and the renders in both `renders/<rid>/` and `stages/`.
   - **`in` path.** `render` reads `ROOT / plan["in"]` (`loop_seq.py:1374`). a2 points at `benchmarks/runs/2026-11-04/angel/in/angel`, so every studio render of a frozen plan needs `--set in="<job path>"`. The §2 argv template has no `--set`.
   - **Input format.** `prep` reads only `.jpg` and `.jpeg` (`loop_seq.py:237`). The import stage must refuse or flag HEIC, DNG and ARW for loops.
   - **Restart reconciliation.**
     - The rule is sound only with a per-stage "done" file named in the registry: `measure.json` for render (written last, after the mp4 and gif, `:1515–1516`), `prep.json` for prep, `metrics.json` for align, `report.json` for pair.
     - Children run with `start_new_session=True` (`director_ui.py:329–330`), so after a restart the pid is often still alive with no waiter, and the exit code is lost.
     - A reused pid keeps a dead stage "running" (Track A, `director_ui.py:135–138`).
   - **Temp-then-rename.** No script supports it: all write straight into `--out`. The runner must use `--out <stage>.part/` and rename on a zero exit. The rename invalidates any absolute path the script recorded (`director_render.py`'s `layers_dir` in `info.json`; align's `metrics.json` UNVERIFIED).
   - **Cancel.** "SIGTERM to the recorded pid" (§5) misses ffmpeg and torch children. Use `killpg` on the pgid stored in `stage.json`.
   - Fix for §4:
     - One layout per flow, the loop's matching `page`'s: `<job>/in/<seq>/` and `<job>/<seq>/<rid>/`.
     - `stage.json` points at the paths and does not hold the outputs.
     - Run every stage through a wrapper (`sh -c '…; echo $? > exit_code'`) and record the pgid and the process start time.
     - Each registry entry names its done file.
     - The render template gains `--set in=…`.

4. **Request files: FAIL (nothing picks them up).**
   - `.claude/settings.json` has two hooks, SessionStart and PreCompact. `session-start.sh` reads `NEXT_SESSION_PROMPT.md`, memory and `ATTENTION.md`, and never globs `requests/`.
   - Nothing reaches a session that is already running.
   - Smallest fix:
     - `studio.py requests` (CLI) lists the open requests (a request with no answer file), oldest first.
     - `session-start.sh` adds one line: "N open studio requests: run `studio.py requests`". This is a `.claude/**` edit, so the owner's yes.
     - Inside a session, the owner says "answer the studio" or the session runs a Monitor until-loop on the glob.
     - State in §5 that the page's "waiting for the session" chip can wait forever until one of these runs.

5. **The box queue: CONTESTED (it is designed as one blocking call; it needs to be a submit-and-poll protocol).**
   - Facts from `.serena/memories/project/strix-halo-box.md`:
     - Long jobs run under `nohup … &` with short polls, every command under `timeout` (:13). A keyframe takes 18–32 min.
     - `halo-idle.timer` suspends the box every 5 min unless `~/halo-hold` exists (:24–25).
     - Wake goes through `ssh beelink '…/wake-halo.sh'` (:11–12).
     - The Mac's `Tailscale status` hangs and must never be called unguarded (:13).
     - The LLM servers reload at 06:00 and 18:00 BST, `[INFERRED]` in the memory (:86–87). An unconditional reboot runs Thursdays at 05:00 BST (:27).
     - The pre-flight floor is 26 GB (23 for klein, :128). Never two jobs at once (:59).
     - The hold file is removed in the box-side `EXIT` trap (`kf_queue6.sh`, :120).
   - Failure modes:
     - An ssh with no `ConnectTimeout` hangs a server thread.
     - A suspended box reads as unreachable rather than asleep.
     - A Mac-side hold file left by a crashed server keeps the box awake for good, or a Mac-side delete during a run lets it suspend.
     - A run that crosses a reload or the reboot dies.
     - A server restart loses track of a remote job.
     - How outputs come back (scp) is UNVERIFIED (Track A).
   - Fix for §5: every ssh uses `-o ConnectTimeout=10 -o BatchMode=yes` under `timeout`. Submit means `nohup` on the box with the hold touched and removed by the box-side trap. The studio polls a remote state file and never holds a connection open for the job. The pre-flight refuses when the expected end falls within ±30 min of 06:00 or 18:00, or in the Thursday 05:00 window. "Unreachable" offers wake through beelink as a separate click. `remote_queue.json` records the remote pid and log path so a restart can reconcile.

6. **Phase A in one session: FAIL (the 70 % in §11 is not supported).**
   - Size of the precedent: `ui1_build.md` (one subagent session) built 1,161 lines on one flow. The backend already existed in design, and the renderer's three flags were added during the build.
   - Phase A's list is larger:
     - the shell, the registry, reconciliation and the wrapper;
     - eight loop stages;
     - three-fit registration with drawn windows;
     - two new `loop_seq.py` commands (`probe`, `measure`; `measure_ring.py` lives in a scratchpad);
     - three new flags;
     - the per-method plan editor with drag, boxes, undo and provenance;
     - the comparator, and the scrubber with the shared frame axis and plots;
     - skeptic requests, the page and the grades;
     - five impeccable passes, which need §10.1's download answer first;
     - the scripted acceptance drive.
   - Best case: one long session, with the plan editor as a JSON text area plus the timeline read-only.
   - Worst case: three sessions. Session 1 is the shell, runner, registration and render. Session 2 is the editor and viewer. Session 3 is probe, measure and the passes.
   - Cut first, in order:
     1. the timeline drag (keep a form per step);
     2. `probe` (keep the scratch script);
     3. the object-stability plot;
     4. the impeccable passes past `detect`;
     5. the three-fit side-by-side (one fit, then a rerun).

7. **The a2 md5 acceptance: FAIL as written.**
   - **Hand-drawn windows.** a2 depends on the session's prep: `--long 1920 --ref 0 --depth-maps --lock-window "422,371,582,441;248,478,318,618;757,458,827,538"` (`NEXT_SESSION_PROMPT.md:39`). The windows go into the template match (`loop_seq.py:259–273`), so windows "drawn" by hand give another shift, other `k*.png` files and another md5.
   - **Draft size.** The check renders a "960 px draft". a2's c302623f… is the full 1366×1770 render (DECISIONS 2026-11-04), and `--draft 960` changes every frame.
   - **`in` path.** Without `--set in=…` the render reads the session's prep folder, so the md5 proves nothing about the studio's registration.
   - **Never reproduced.** No record shows a2 reproducing twice. Only the s6 sheets path did, three times. RIFE and depth determinism on torch CPU are UNVERIFIED.
   - **`--progress`:** byte-safe by construction (stderr only), but untested on the RIFE path.
   - **Fix for §9:**
     - Step 1: run a2 twice from the shell and confirm c302623f…
     - Step 2: in the studio, run import, then registration with the recorded windows, typed or loaded from `prep.json` `frames[i].lock.windows`. Drawn windows are a separate step that shows dx, dy.
     - Step 3: render at full size with `--set in=<job>`, compare the md5, and `cmp` the `k*.png` and `depth_k*.npy` against the session's.
     - Step 4: the 960 px draft and the edits.

8. **Hard constraints and the scope fence: CONTESTED.**
   - What holds:
     - 127.0.0.1 is kept.
     - Neither tool is imported (§5, inherited from `director_ui.py:6`).
     - Originals are symlinked; `prep` hashes them (`loop_seq.py:245`).
     - No item on the permanently-out list is reopened.
     - §10.1 keeps impeccable's download as a dev-tool action outside the runtime contract.
   - Contradictions and risks:
     - §0 says "no network from the UI process", but §5 `/api/box` runs `ssh strix`, a Tailscale connection, and §2 or §5 "run a warmup" (`rife_probe.py warmup` from Hugging Face and GitHub, `matte_source.py warmup`) downloads. Both run as subprocesses the UI starts.
     - `matte_source.py run --device mps` exists. MPS is permanently out for the tools (decision 9), and the registry must never expose it.
     - Track A lists research scripts with no offline gate (`auto_anchors` fetches YuNet by `urlretrieve`; `gen_bridge`, `roma_probe`, `depth_dolly --depth`). None may be a stage.
     - Port 8379 is `director_ui.py`'s default (`director_ui.py:1140`). The incumbent stays until phase B, so §0's "a new port" is false.
   - Fix:
     - §0 and §5: "the server process opens one listening socket on 127.0.0.1 and nothing else. The subprocesses it starts open a network connection only for an explicit warmup click (the URL and bytes shown first) and for the box (ssh, phase D)."
     - List the excluded scripts and `--device`.
     - Move the port to 8380.

9. **The two Track A bugs: FAIL (one fixed; the other fix crashes).**
   - **`matte.all`: crash fixed.** It is uncommitted (`git diff`). `matte_kw` drops `all` for the chain, teleport, slide and rise methods (`loop_seq.py:1385, 1408, 1416, 1418, 1420`); plain `rife` keeps `matte_cfg` (`:1410`).
     - Side effect: a `through` chain with method `rife` now silently ignores `all` and runs the change matte, while `SCHEMA.md:119` says `rife` runs whole-frame.
     - No frozen plan is affected: a1–a5 use plain `rife` only, and the other methods used to crash.
   - **`breath.depth_k`: the fix crashes.** `breath_by_depth` (`:1443–1444`) now sends a breath-only plan into `apply_camera`, which reads `px[0].get("sigma", 3.0)` with `px` empty (`:1319`).
     - Reproduced: `apply_camera(…, [{"kind": "breath", "z": 0.02, "depth_k": 1.0}], dir_with_depth_k0.npy)` raised `IndexError: list index out of range`.
     - No frozen plan hits it: only a5 has `depth_k`, and a5 also has `parallax`.
     - Fix: `sigma = float(px[0].get("sigma", 3.0)) if px else float(br[0].get("sigma", 3.0))`, plus a breath-only depth render in the watch list.

### The three changes STUDIO.md needs most (ranked)
1. **Rewrite §9 phase A's acceptance (item 7).** Reproduce a2 at full size from the recorded windows with `--set in=<job>`. Check a2 reproduces twice from the shell first. Run the drawn windows and the 960 px draft as separate steps. Split phase A into A1 (shell, runner, wrapper, registration, render, scrubber) and A2 (plan editor, probe, measure, design passes). Fix the `apply_camera` crash before any studio render reaches that path.
2. **Rewrite §4 to match the scripts.** Use `page`'s layout `<job>/in/<seq>/`, `<job>/<seq>/<rid>/`, with one home per output. Run every stage through a wrapper that writes the exit code, the pgid and the start time. Name a done file per stage. Write to `.part` and rename. Cancel by process group. Add `--set in=…` to the render template.
3. **Make §2 and §5 honest about the knobs and the network.** The registry is hand-written, with ranges null unless `--help` states one. Name the stages that need their own code. Replace "no network from the UI process" with the listener-only sentence (item 8). Move the port to 8380. Add the request pickup (item 4) and the box submit-and-poll protocol (item 5).

### Confidence: 80 %
Items 3, 7, 8 and 9 rest on lines read and one reproduced crash. Items 5 and 6 rest on the memory and `ui1_build.md`. The session-count estimate and the box reload times are `[INFERRED]`.

### Gaps
- Nothing was rendered. a2's reproducibility, RIFE and depth-model determinism and the `prep` bytes are UNVERIFIED.
- `director_page.py`'s expected layout, the absolute paths inside `info.json` and `metrics.json` after a rename, and `ui1_review.md` were not read in depth.
- Track A's line anchors beyond the ones cited here were not re-verified.
- The box was not probed (no ssh).
