<!-- Provenance: written by an Opus 5.5 subagent (the UI1 build of scripts/research/director_ui.py) of the Claude Code session of 2026-10-21 (the round-13 session; DECISIONS 2026-10-21), copied verbatim from benchmarks/runs/2026-10-21/agents/ui1_build.md (sha256 f7bec0ae8b395e01) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

## Findings: UI1

`scripts/research/director_ui.py` is built (1,161 lines), and the phase-1 acceptance check of
`ui_design.md §7` passed every step I drove headless in Chrome 155 through the Playwright MCP tools,
on 2026-10-21 between 01:53 and 02:01. The mismatch_3 test draft (480 px, `mismatch_3_r12.json` c1,
with `parallax_push=2` and the window `pane_becomes_view.window=[0.35,0.97]`) gave mp4 md5
`5b3ee379776ae4e8ce2dec4fa3293740` with renderer wall times from 11.5 to 13.4 s. Six renders gave that
same md5: two first renders, three re-renders from `render.json` through the page, and one from the
shell. They ran under three renderer versions (md5 `d8a5f732…`, `52630887…`, `a1ec3245…`). One
point was not driven: a human at a real (non-headless) browser, including the automatic browser
open (UNVERIFIED).

### Key facts
- The server binds `127.0.0.1` only (`director_ui.py:1148`). `lsof -i -p <pid>` showed one LISTEN
  socket on 127.0.0.1:8379 and one ESTABLISHED socket from the page, and nothing else.
  `grep` finds no `urllib`, `socket` or `http.client` import.
- The UI imports neither `reveal` nor `transitions` nor any research script. Every heavy call is
  `subprocess.Popen([.venv/bin/python, …], start_new_session=True)` (`start_task`, around line 335).
  Cancel sends SIGTERM to that process group only (`cancel_task`, line 414). The cancelled test
  render ended with exit -15, and its pid 98918 was gone after the cancel.
- Reveal on mismatch_3: `reveal.py align` exits 2 with `FAILED: Could not find enough common detail…`
  in 10.3–11.6 s. It writes no `metrics.json` on a refusal, so the refusal has no inlier or rmse
  numbers to show. The page shows the exit code, the reason and the wall time.
- `transitions.py pair --max-long 480 --seconds 1` on mismatch_3: class B, method `saliency-panzoom`,
  median displacement 24.71 px, sparse inliers 0, mean certainty 0.5, 1.6–2.4 s.
- The renderer's three flags landed while I was building: `--progress` and `--resolve-only` at
  `director_render.py:2042-2043`, and `renderer_md5` in `info.json` at line 2058. The first test
  render (01:54) ran without them; every later run used them.
- `/file` refusals, checked with curl: `../../../../../../etc/passwd` → 403,
  `fixtures/../reveal.py` → 403, `layers/…/layers.json` → 200, `mattes/…/el_1.png` → 200,
  `fixtures/mismatch_3_S.jpg` → 200, a job file → 200. `Range: bytes=0-99` on the mp4 → 206 with
  100 bytes. A plan outside `scripts/research/plans/` → 400. A picks object with an extra top-level
  key → 400.

### What was built
- **Endpoints:** `GET /`, `GET /api/pairs`, `GET|POST /api/jobs`, `GET /api/jobs/<id>`,
  `POST /api/jobs/<id>/analyze`, `GET /api/jobs/<id>/overlay/<A|B>/<kind>.png` (kind `base`,
  `elements`, `disparity` or `matte_<id>`), `GET /api/jobs/<id>/file/<path>`,
  `POST /api/jobs/<id>/render` (a spec, or `{from_render: rid}` to re-render from `render.json`),
  `GET /api/jobs/<id>/tasks/<tid>`, `POST /api/jobs/<id>/tasks/<tid>/cancel`,
  `GET|POST /api/jobs/<id>/frame` (POST `{mark: true}` copies the frame into `owner_frames/`), and
  `POST /api/jobs/<id>/picks`. I added two that the brief does not list: `GET /api/jobs` (the job
  list for the rail) and `GET /api/plans/<stem>` (a plan with its knob mapping).
- **State** is the job folder, laid out as in `§5`. Creating a job starts the analysis at once:
  Reveal, transitions and, when the renderer has the flag, `--resolve-only` into `analysis/resolve/`.
  `render.json` holds the fields listed in `§5` plus `draft`, `renderer_flags`, `process_wall_s`,
  `exit_code`, `task` and `from_render`. If the renderer's own `renderer_md5` disagrees with the
  hash taken at launch, the file gets a `renderer_md5_info` key.
- **Plan knob → `--set` key table** (`map_knob`, line 213; `PATH_KEYS`, line 190). It covers every
  knob in the 22 plans on disk:

  | Plan knob name | `--set` key |
  |---|---|
  | `<transform>.window`, `<transform>.window[i]` | `<transform>.window` (the whole list, with index i replaced) |
  | `<transform>.params.<p>`, `….params.<p>[i]` | `<transform>.<p>` (indexed into the plan's value) |
  | `end_effect.window`, `end_effect.window[0]` | `end_window` |
  | `end_effect.params.band` | `end_band` |
  | `pullback.parallax.gain` / `gain_A` / `push` | `parallax_gain` / `parallax_gain_A` / `parallax_push` |
  | `pullback.params.end_scale` | `end_scale` |
  | `container.params.reflect` | `reflect` |
  | `container.params.sky.<k>` | `sky` (the plan's whole sky dict, with `<k>` replaced) |
  | `front_ids`, `front_per_element`, `guard`, `vacated_first`, `parallax_A_elements` | the same name |
  | `container quad vertical scale about the glass midline` (`mismatch_3.json`) | read-only: "not a dotted path; no renderer key" |

  A second table lists 21 renderer globals with the default the renderer would use for the concept,
  read from its `knobs.get(…, fallback)` lines. Examples: `parallax_push` 2.5 for a quad container,
  `cont_feather` 1.0, `motion`, `guard`. A ticked row is sent as `--set`. The table starts from the
  operator knobs of the newest round render of the same plan and concept. For `mismatch_3_r12` c1
  that render is `director_r12/mismatch_3_r12_c1/info.json`, which used `cont_feather=14`,
  `front_margin=0.3` and `parallax_push=1.5`. A free-text box takes any further `key=JSON` lines.
- **Timeline drag:** there is one bar per transform window, plus the end effect's window, on a
  900 px track for clip time 0–1. Dragging the middle of a bar moves it; dragging within 6 px of an
  end resizes it. Values are rounded to 0.01, and the minimum width is 0.02. On mouse-up the result
  is stored as `<name>.window=[a,b]` (`end_window` for the end effect), the same key that the
  indexed plan knobs such as `pane_becomes_view.window[1]` write into. "Mute" sets
  `<name>.skip=true`; "solo" sets `skip=true` on every other beat.
- **Review panel:** a `<video>` served with Range support; a slider, frame buttons and the arrow
  keys; and three SVG charts with a cursor at the current frame: `motion_px` with pauses (orange)
  and jumps (red) computed by the renderer's own rule, the step profile, and `b_inside`. Below them
  sits an A | frame | B strip, where A and B are the clip's first and last frames. `info.json` keeps
  only four step values, so the UI computes the full step profile itself when it decodes the frames
  (`extract_frames`, line 658). Its values match the renderer's: frame 1 = 0.69 and frame 2 = 0.02,
  against `step_first` 0.69 and `step_second` 0.02.
- **Grade panel:** one form per finished render. The tag is `<plan>_<concept>-<rid>`, following the
  variant-folder convention of `director_page.py`. A 480 render is saved with `draft: true`, along
  with `render: rid` and an optional `frames` list.

### Acceptance check (Playwright MCP against headless Chrome on CDP port 9222; server with `--no-browser` on 8379, which was free)
1. Start and open 127.0.0.1:8379: PASS for the start. The server printed its URL and pid, and the
   page loaded. The automatic browser open was not exercised (UNVERIFIED), because I ran with
   `--no-browser` as instructed.
2. Pick mismatch_3; the verdict appears within 30 s: PASS in **10.5 s** on a fresh job
   (`mismatch_3_20261021-015759_1ef2`). The page read "unrelated (Reveal refused, class B)" with
   Reveal's exit 2, reason and wall time, and the transitions numbers above. The first run took
   13.1 s, but that run had no `--resolve-only`.
3. Element and depth overlays toggle on both photos: PASS. Both were on for A and B at 11.0 s
   (960×720 PNGs) and off again after unchecking. A matte overlay shows when an element row is
   clicked. Toggles survive a panel redraw (tested with a forced redraw).
4. Change two knobs: PASS. `parallax_push` started at 1.5 (seeded from round 12) and was set to 2.0.
   A real mouse drag of `pane_becomes_view` moved it from 0.30–0.92 to 0.35–0.97. The `--set`
   preview listed both.
5. Press draft and see a progress line move to done: PASS. The line read "building the scene"
   through about 4 s, then frame 10/90, 30/90 … 89/90, then done at 13.3 s with exit 0. (The frame
   numbers in that run were 0-based; I fixed the display to 1-based, and the later runs ended at
   90/90.)
6. Scrub frame by frame with the motion profile under it: PASS. Frames 40→43 via the "frame >"
   button; each step updated the frame PNG, the video time, the chart cursor and the readout,
   e.g. "frame 42/89 … motion 3.68 px step 18.73 b_inside 2.79 %".
7. Tick the boxes, write a note, pick best: PASS. The file
   `picks/director_picks_20261021-015913.json` exists. Its top-level keys equal those of
   `director_picks_11.json` (`best, clips, date, page`), and so do its `props` keys. Its clip keys
   add `render` and `draft` (and `frames` when a frame is marked), as the brief allows.
8. `render.json` lists both knobs: PASS. `knobs` = `{cont_feather: 14, front_margin: 0.3,
   parallax_push: 2, pane_becomes_view.window: [0.35, 0.97]}`. The two seeded round-12 knobs are
   there too.
9. Re-rendering from `render.json` gives the same md5: PASS. Two page re-renders gave
   `5b3ee379…` (wall 13.4 s and 11.5 s), and running the argv from the shell gave the same md5
   (11.9 s).

### Constraints discovered
- `parallax_push` is not in `mismatch_3_r12.json`'s knob list. The renderer reads it as a global,
  with default 2.5 for a quad container (`director_render.py`, `knobs.get("parallax_push", …)`). The
  1.5 in the acceptance check comes from round 12's hand-set knobs, so the UI seeds those knobs from
  the last round's `info.json`. Without that seed, the "1.5 → 2.0" step would start from 2.5.
- The renderer reads `sky` as one whole dict. A plan knob `container.params.sky.<k>` therefore has
  to send the plan's full sky dict with one key changed, and the UI does that.
- With `motion: continuous`, the renderer may move the windows of beats so that they overlap. The
  window the owner drags is the requested window, not necessarily the rendered one;
  `info.json.motion.adjusted` shows the difference. The timeline does not draw the resolved windows
  yet.
- Before the flags landed, an older renderer printed nothing per frame. In that case the page shows
  elapsed time against the last `wall_s` of the same plan and size in the job. For the first draft
  in a job there is no such number.
- The renderer was edited three times during my runs, and the md5 of the clip did not change.

### Confidence: 85%
The loop works end to end on mismatch_3 in a headless browser, with every number above measured.
What keeps the figure below 90%: no human used it in a windowed browser, only one pair was rendered,
and no 1920 render was run from the UI.

### Gaps
- The Playwright MCP failed at first with `connect ECONNREFUSED 127.0.0.1:9222`: the MCP attaches to
  a browser on that port and none was running. I started a headless Chrome
  (`--remote-debugging-port=9222`, profile in my scratchpad) and stopped it by pid afterwards.
  Nothing was tested in a headed browser or in Safari.
- My first `rm -rf .playwright-mcp` (a folder the MCP wrote into the repo root) was refused by the
  permission system. Removing its two files one by one worked, and the folder is gone.
- A Playwright call that waited on a re-render timed out after 120 s. The cause was a page bug: the
  panel redraw reset the progress line to "no task". I fixed it, along with three more page bugs
  found while driving the page: a stale panel on job switch (it made a 0.06 s "verdict" time that I
  discarded), the 0-based frame count, and a `selectRender` race that raised `TypeError … motion_px`.
- Not driven: a 1920 render from the UI; pairs other than mismatch_3 (mismatch_1/2/4/5/6 are listed
  and their knob mapping was dumped, but they were not rendered); a server restart while a task is
  running (the code marks it `lost` when its pid is gone; untested).
- `anchors.json` from `--resolve-only` is linked from the Analysis panel. Faces, discs and lines
  are not drawn as overlays (phase 3 in the design).
- A cancelled render leaves its `renders/<rid>/` folder with `state: cancelled` and no mp4. The
  rail's render count includes it.
- The favicon request returns 404 (harmless console error).
- Test jobs left in `benchmarks/runs/2026-10-21/workbench/` (gitignored):
  `mismatch_3_20261021-015336_10e3` (2 renders), `mismatch_3_20261021-015740_c234` (analysis
  only), and `mismatch_3_20261021-015759_1ef2` (4 renders, 1 cancelled).
